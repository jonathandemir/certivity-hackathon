// Alle Daten kommen aus window.CERTREQ (data.js neben index.html, erzeugt von demo/prepare.py).
// Nichts hier ist auf einen bestimmten Fall zugeschnitten.

const EMPTY = {
  case: { id: 'kein-fall', title: 'No case loaded', parts: [], functions: [], hasSpec: false, drawing: null },
  run: {}, regs: [], reqs: [], pages: {}, hits: {}, pagesTotal: 0,
}
const D = (typeof window !== 'undefined' && window.CERTREQ) || EMPTY

export const CASE = D.case
export const RUN = D.run || {}
export const RUN_ID = D.runId || ''
// Heckleuchte des Worked Example: eigenes 3D-Modell nach der Explosionszeichnung (RearLamp.jsx)
export const IS_LAMP = (D.case?.id || '') === 'dev-rear-lamp'
// In der Werkbank eingebettet (Ansicht „Überblick“): eigene Kopfzeile schlanker, Belege springen in die Werkbank
export const EMBED = typeof location !== 'undefined' && new URLSearchParams(location.search).has('embed')
export const REGS = D.regs
export const REQS = D.reqs
export const PAGES_TOTAL = D.pagesTotal || new Set(REQS.map((r) => `${r.reg}#${r.version}#${r.page}`)).size

// Aktive Regelungen = solche mit Anforderungen, nach Anzahl absteigend
export const ACTIVE = REGS.filter((r) => r.count > 0).sort((a, b) => b.count - a.count)
const PALETTE = ['#E9A100', '#00A386', '#7A5CFF', '#2F6BFF', '#E2557A', '#0FA3C7', '#9C7A00', '#3FAE4A', '#B0458F', '#5B6CFF', '#C76A28', '#2E8B7A']
const COLOR = Object.fromEntries(ACTIVE.map((r, i) => [r.id, PALETTE[i % PALETTE.length]]))
export const regColor = (id) => COLOR[id] || '#9A9AA1'
export const regTitle = (id) => REGS.find((r) => r.id === id)?.title || ''

// Bauteile aus der Spezifikation, plus Sammelposten für alles, was keinem Bauteil zugeordnet ist
export const PARTS = [
  ...CASE.parts.map((p) => ({ id: p.id, n: p.n, name: p.name })),
  { id: 'device', n: CASE.parts.length + 1, name: 'Whole device', note: 'not assigned to a part' },
]
export const partById = Object.fromEntries(PARTS.map((p) => [p.id, p]))
export const partCounts = Object.fromEntries(
  PARTS.map((p) => {
    const rs = REQS.filter((r) => r.part === p.id)
    const by = {}
    for (const r of rs) by[r.reg] = (by[r.reg] || 0) + 1
    return [p.id, { total: rs.length, by }]
  }),
)
export const DEFAULT_PART =
  [...PARTS].filter((p) => p.id !== 'device' && partCounts[p.id].total > 0).sort((a, b) => partCounts[b.id].total - partCounts[a.id].total)[0]?.id || 'device'

export const pageOf = (r) => D.pages[`${r.reg}#${r.version}#${r.page}`]
export const hitsOf = (r) => D.hits[r.id] || []

export const HERO_REQ =
  REQS.find((r) => r.part === DEFAULT_PART && pageOf(r) && hitsOf(r).length) || REQS.find((r) => pageOf(r) && hitsOf(r).length) || REQS[0]

// Agentenlauf: Der Abtaststrahl umrundet den Ring zwischen SWEEP0 und SWEEP1 einmal.
export const SWEEP0 = 0.12
export const SWEEP1 = 0.9
export const regAngle = (id) => (Math.max(0, REGS.findIndex((r) => r.id === id)) / Math.max(1, REGS.length)) * Math.PI * 2
export const activationT = (id) => SWEEP0 + (regAngle(id) / (Math.PI * 2)) * (SWEEP1 - SWEEP0)

export const LOG = [
  [0.0, CASE.hasSpec ? `Reading spec · ${CASE.title}` : CASE.drawing ? 'Reading exploded drawing' : `Case ${CASE.id}`],
  [0.06, CASE.parts.length ? `Found ${CASE.parts.length} main parts` : 'Splitting the drawing into parts'],
  [0.1, `Screening ${REGS.length} UN regulations`],
  ...ACTIVE.map((r) => [activationT(r.id), `${r.id} · ${r.title} · ${r.count}`]).sort((a, b) => a[0] - b[0]),
  [0.92, 'Citing page and paragraph for every requirement'],
  [0.995, `Done · ${REQS.length} requirements from ${ACTIVE.length} regulations`],
]
