# shellcheck shell=bash
# Gemeinsame Funktionen für scripts/*. Wird gesourct, nicht ausgeführt.
# Läuft mit bash 3.2 (macOS) und Linux. Keine GNU-only-Befehle (kein timeout, setsid, readlink -f, sed -i).
set -u

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "$REPO_ROOT" || exit 1

# Git darf in Skripten nie einen Editor öffnen (Agenten können nicht tippen).
export GIT_MERGE_AUTOEDIT=no
export GIT_EDITOR=true

# Geteilte Dateien: gehören nur auf main (Ausnahme docs/LOG.md, siehe AGENTS.md).
SHARED_PATHS="AGENTS.md CLAUDE.md README.md docs experiments scripts .claude .gitignore .gitattributes"

if [ -t 2 ]; then
  C_RED=$'\033[31m'; C_YEL=$'\033[33m'; C_GRN=$'\033[32m'; C_BLD=$'\033[1m'; C_OFF=$'\033[0m'
else
  C_RED=; C_YEL=; C_GRN=; C_BLD=; C_OFF=
fi

die()  { printf '%sFEHLER:%s %s\n' "$C_RED" "$C_OFF" "$*" >&2; exit 1; }
warn() { printf '%sWARNUNG:%s %s\n' "$C_YEL" "$C_OFF" "$*" >&2; }
ok()   { printf '%sOK:%s %s\n' "$C_GRN" "$C_OFF" "$*" >&2; }
note() { printf '%s\n' "$*" >&2; }

me()        { git config user.name 2>/dev/null || echo "${USER:-unbekannt}"; }
host()      { uname -n | cut -d. -f1; }
now()       { date '+%Y-%m-%d %H:%M:%S %z'; }
now_short() { date '+%Y-%m-%d %H:%M'; }

current_branch() { git symbolic-ref --short -q HEAD; }
short_head()     { git rev-parse --short HEAD 2>/dev/null; }
has_ref()        { git rev-parse -q --verify "$1" >/dev/null 2>&1; }

# Befehl mit Zeitlimit (Ersatz für GNU timeout): perl alarm überlebt exec.
with_timeout() {
  local secs=$1; shift
  if command -v perl >/dev/null 2>&1; then
    perl -e 'alarm shift @ARGV; exec @ARGV or exit 127' "$secs" "$@"
  else
    "$@"
  fi
}

fetch_origin() { # [sekunden]
  git remote get-url origin >/dev/null 2>&1 || return 1
  with_timeout "${1:-60}" git -c http.lowSpeedLimit=1000 -c http.lowSpeedTime=20 fetch --quiet --prune --tags origin
}

# Uncommittete Änderungen an getrackten Dateien (optional ohne bestimmte Pfade).
dirty_tracked() { # [pfad-ausschlüsse...]
  local ex=() p
  for p in "$@"; do ex+=(":(exclude)$p"); done
  git status --porcelain --untracked-files=no -- . ${ex[@]+"${ex[@]}"}
}
untracked_files() { git status --porcelain --untracked-files=all | sed -n 's/^?? //p'; }

operation_in_progress() {
  local d
  for d in rebase-merge rebase-apply MERGE_HEAD CHERRY_PICK_HEAD REVERT_HEAD; do
    [ -e "$(git rev-parse --git-path "$d")" ] && { echo "$d"; return 0; }
  done
  return 1
}

# Commits, die noch auf keinem origin-Branch liegen.
unpushed_commits() { git log --oneline HEAD --not --remotes=origin 2>/dev/null; }

# Minuten seit dem ältesten ungepushten Commit (leer, wenn keiner).
unpushed_age_min() {
  local t
  t=$(git log --format=%ct HEAD --not --remotes=origin 2>/dev/null | tail -n 1)
  [ -n "$t" ] && echo $(( ( $(date +%s) - t ) / 60 ))
}

print_conflict_help() { # modus upstream
  local mode=$1 up=$2 files
  files=$(git diff --name-only --diff-filter=U | sed 's/^/    /')
  {
    printf '\n%sKONFLIKT%s beim %s von %s in %s. Es wurde NICHTS gepusht.\n' "$C_RED$C_BLD" "$C_OFF" "$mode" "$up" "$(current_branch 2>/dev/null || echo '(rebase)')"
    printf 'Betroffene Dateien:\n%s\n' "${files:-    (keine Dateien mit Konfliktmarkern)}"
    printf 'So geht es weiter:\n'
    printf '  - Nur eigene Dateien selbst lösen. Fremde Dateien: erst den Menschen fragen.\n'
    printf '  - docs/LOG.md: beide Einträge behalten (nur anhängen).\n'
    if [ "$mode" = rebase ]; then
      printf '  - Gelöst: git add <datei> && git rebase --continue, danach scripts/sync\n'
      printf '  - Abbrechen (sicher, nichts geht verloren): git rebase --abort\n'
    else
      printf '  - Gelöst: git add <datei> && git commit --no-edit, danach scripts/sync\n'
      printf '  - Abbrechen (sicher, nichts geht verloren): git merge --abort\n'
    fi
  } >&2
}

# Holt origin/<branch> in den aktuellen Branch.
# Ohne lokale Merge-Commits: git pull --rebase. Mit lokalen Merge-Commits: git pull --no-rebase,
# weil ein Rebase über Merge-Commits fremde Commits neu abspielt und Konflikte erzeugt.
# Rückgabe 0 = ok, 1 = Konflikt/Fehler (Meldung ist schon ausgegeben).
integrate_upstream() {
  local branch up behind merges
  branch=$(current_branch) || { warn "Detached HEAD"; return 1; }
  up="origin/$branch"
  has_ref "refs/remotes/$up" || return 0
  behind=$(git rev-list --count "HEAD..$up")
  [ "$behind" -eq 0 ] && return 0
  merges=$(git rev-list --merges --count "$up..HEAD")
  if [ "$merges" -gt 0 ]; then
    note "Hole $behind Commit(s) von $up per merge (lokal $merges Merge-Commit(s), daher kein Rebase)."
    if ! git pull --quiet --no-rebase --ff --no-edit origin "$branch"; then
      print_conflict_help merge "$up"; return 1
    fi
  else
    note "Hole $behind Commit(s) von $up per rebase."
    if ! git pull --quiet --rebase origin "$branch"; then
      print_conflict_help rebase "$up"; return 1
    fi
  fi
  return 0
}

# Merged origin/main in einen persönlichen Branch, aber nur, wenn es konfliktfrei geht.
merge_main_if_clean() {
  local branch n conflicts
  branch=$(current_branch) || return 0
  [ "$branch" = main ] && return 0
  has_ref refs/remotes/origin/main || return 0
  n=$(git rev-list --count HEAD..origin/main)
  [ "$n" -eq 0 ] && return 0
  if git merge --quiet --no-edit origin/main >/dev/null 2>&1; then
    note "main gemergt: $n neue Commit(s) vom Team übernommen."
  else
    conflicts=$(git diff --name-only --diff-filter=U | tr '\n' ' ')
    git merge --abort >/dev/null 2>&1
    warn "origin/main ($n Commits) lässt sich nicht konfliktfrei mergen (${conflicts:-unbekannt}). Merge abgebrochen, nichts verändert. Bewusst lösen: git merge origin/main"
  fi
  return 0
}

# Warnt, wenn auf einem persönlichen Branch geteilte Dateien geändert wurden.
warn_shared_on_branch() {
  local branch files
  branch=$(current_branch) || return 0
  [ "$branch" = main ] && return 0
  has_ref refs/remotes/origin/main || return 0
  # shellcheck disable=SC2086
  files=$(git diff --name-only origin/main...HEAD -- $SHARED_PATHS ':(exclude)docs/LOG.md' 2>/dev/null)
  [ -z "$files" ] && return 0
  warn "Auf Branch $branch sind geteilte Dateien geändert (gehören auf main, siehe AGENTS.md):"
  printf '%s\n' "$files" | sed 's/^/    /' >&2
  note "    Richtig: MAIN=\$(scripts/main-wt) und dort ändern, committen, \"\$MAIN/scripts/sync\"."
}

# Pfad eines main-Checkouts (dieser Checkout, ein anderer Worktree oder .worktrees/main).
find_main_checkout() {
  if [ "$(current_branch)" = main ]; then echo "$REPO_ROOT"; return 0; fi
  git worktree list --porcelain | awk '
    /^worktree /{p=substr($0,10)}
    /^branch refs\/heads\/main$/{print p; exit}'
}
