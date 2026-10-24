"""Kosten-Experimente ohne Änderung am Repo-Code: patcht certreq zur Laufzeit und startet `certreq run`.

    cd <repo> && CERTREQ_PROVIDER=anthropic CERTREQ_LLM_CACHE=0 .venv/bin/python experiments/costexp/costexp.py \
        [--cache] [--batch 24 18000] [--effort low] [--dry] -- <certreq run argumente>

--cache   System-Prompt mit cache_control (Anthropic Prompt Caching), Cache-Lese/Schreib-Tokens werden mitgezählt
--batch   BATCH_PARAS / BATCH_CHARS der LLM-Extraktion (Standard 12 / 9000)
--effort  effort nur für die Extraktion (Auswahl bleibt wie im Code)
--dry     kein API-Aufruf: Prompts zählen (Zeichen, Aufrufe), Antwort = leere Liste
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
import certreq.llm as llm  # noqa: E402
import certreq.llm_anthropic as la  # noqa: E402
import certreq.llmextract as lx  # noqa: E402
from certreq.__main__ import main  # noqa: E402

argv = sys.argv[1:]
own, run_args = (argv[:argv.index("--")], argv[argv.index("--") + 1:]) if "--" in argv else ([], argv)
opts = {"cache": "--cache" in own, "dry": "--dry" in own, "effort": None, "batch": None}
if "--batch" in own:
    i = own.index("--batch")
    opts["batch"] = (int(own[i + 1]), int(own[i + 2]))
if "--effort" in own:
    opts["effort"] = own[own.index("--effort") + 1]

if opts["batch"]:
    lx.BATCH_PARAS, lx.BATCH_CHARS = opts["batch"]

if opts["effort"]:
    _orig_ask = llm.ask_json

    def ask_json(*a, **kw):
        if kw.get("name") == "requirements":
            kw["effort"] = opts["effort"]
        return _orig_ask(*a, **kw)
    llm.ask_json = ask_json

_orig_request = la.request


def request(model, messages, response_format, effort=None):
    params = _orig_request(model, messages, response_format, effort)
    if opts["cache"]:
        params["system"] = [{"type": "text", "text": params["system"], "cache_control": {"type": "ephemeral"}}]
    return params
la.request = request

def call_counting(model, messages, response_format, effort=None):
    """Wie la.call, zusätzlich Cache-Felder getrennt zählen."""
    params = la.request(model, messages, response_format, effort)
    with la.client().beta.messages.stream(**params) as stream:
        msg = stream.get_final_message()
    if msg.stop_reason in ("refusal", "max_tokens"):
        raise RuntimeError(f"{model}: stop_reason {msg.stop_reason}")
    text = "".join(b.text for b in msg.content if b.type == "text")
    u = msg.usage
    cr = getattr(u, "cache_read_input_tokens", 0) or 0
    cw = getattr(u, "cache_creation_input_tokens", 0) or 0
    return text, {"prompt_tokens": (u.input_tokens or 0) + cr + cw, "completion_tokens": u.output_tokens or 0,
                  "input_uncached": u.input_tokens or 0, "cache_read": cr, "cache_write": cw,
                  "fallbacks": sum(1 for b in msg.content if b.type == "fallback")}


def call_dry(model, messages, response_format, effort=None):
    params = la.request(model, messages, response_format, effort)
    sys_chars = sum(len(b["text"]) for b in params["system"]) if isinstance(params["system"], list) else len(params["system"])
    user_chars = sum(len(m["content"]) for m in params["messages"] if isinstance(m["content"], str))
    name = response_format.get("json_schema", {}).get("name")
    if name == "requirements":
        answer = '{"paragraphs": []}'
    else:
        answer = None  # Auswahl im Dry-Run nicht simulierbar
    if answer is None:
        raise SystemExit("--dry braucht --regs (feste Auswahl), sonst ruft die Auswahl das Modell")
    return answer, {"prompt_tokens": 0, "completion_tokens": 0, "sys_chars": sys_chars, "user_chars": user_chars,
                    "effort_" + str(params["output_config"]["effort"]): 1}


la.call = call_dry if opts["dry"] else call_counting
print(f"costexp: {opts}", file=sys.stderr)
sys.exit(main(["run", *run_args]))
