// API, Farben, Text-Diff: alles, was die Ansichten gemeinsam brauchen.

export async function api(path, opts = {}) {
  const res = await fetch(path, {
    ...opts,
    headers: opts.body ? { 'Content-Type': 'application/json' } : undefined,
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(data.error || `${res.status}`)
  return data
}

const PALETTE = ['#E9A100', '#00A386', '#7A5CFF', '#2F6BFF', '#E2557A', '#0FA3C7', '#9C7A00', '#3FAE4A', '#B0458F', '#5B6CFF', '#C76A28', '#2E8B7A']
export function makeColors(regs) {
  const active = regs.filter((r) => r.count > 0).sort((a, b) => b.count - a.count)
  const map = Object.fromEntries(active.map((r, i) => [r.id, PALETTE[i % PALETTE.length]]))
  return (id) => map[id] || '#A7A39A'
}

export const STATUS = {
  open: { label: 'Offen', key: 'U' },
  accepted: { label: 'Bestätigt', key: 'A' },
  rejected: { label: 'Verworfen', key: 'X' },
}

export const fmtSec = (s) => {
  if (s == null) return '—'
  s = Math.round(s)
  return s < 60 ? `${s} s` : `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')} min`
}
export const fmtDate = (iso) => {
  if (!iso) return ''
  const d = new Date(iso)
  if (isNaN(d)) return iso
  const today = new Date()
  const same = d.toDateString() === today.toDateString()
  return same ? d.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' }) : d.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit' }) + ' ' + d.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })
}

// Wort-Diff (LCS) für den Versionsvergleich: liefert [{t, op: '=', '-', '+'}]
export function wordDiff(a, b) {
  const A = (a || '').split(/(\s+)/).filter(Boolean)
  const B = (b || '').split(/(\s+)/).filter(Boolean)
  const n = A.length, m = B.length
  if (n * m > 4_000_000) return [{ t: a, op: '-' }, { t: b, op: '+' }]
  const L = Array.from({ length: n + 1 }, () => new Uint16Array(m + 1))
  for (let i = n - 1; i >= 0; i--) for (let j = m - 1; j >= 0; j--) L[i][j] = A[i] === B[j] ? L[i + 1][j + 1] + 1 : Math.max(L[i + 1][j], L[i][j + 1])
  const out = []
  let i = 0, j = 0
  const push = (t, op) => { const last = out[out.length - 1]; if (last && last.op === op) last.t += t; else out.push({ t, op }) }
  while (i < n && j < m) {
    if (A[i] === B[j]) { push(A[i], '='); i++; j++ }
    else if (L[i + 1][j] >= L[i][j + 1]) push(A[i++], '-')
    else push(B[j++], '+')
  }
  while (i < n) push(A[i++], '-')
  while (j < m) push(B[j++], '+')
  return out
}

export function readHash() {
  const p = new URLSearchParams(location.hash.slice(1))
  return { view: p.get('v') || 'ueberblick', product: p.get('p') || '', req: p.get('req') || '' }
}
export function writeHash(h) {
  const p = new URLSearchParams()
  if (h.product) p.set('p', h.product)
  if (h.view) p.set('v', h.view)
  if (h.req) p.set('req', h.req)
  const s = '#' + p.toString()
  if (location.hash !== s) history.replaceState(null, '', s)
}

export const ROLE = { component: 'Bauteil', installation: 'Anbau', 'cross-cutting': 'Querschnitt', rejected: 'verworfen' }
