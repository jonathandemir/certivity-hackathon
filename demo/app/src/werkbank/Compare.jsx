import { useEffect, useMemo, useState } from 'react'
import { motion } from 'motion/react'
import { api, wordDiff, fmtSec } from './lib.js'

const TYPES = {
  modified: { label: 'Geändert', sign: '~', cls: 'mod' },
  removed: { label: 'Entfernt', sign: '−', cls: 'rem' },
  added: { label: 'Neu', sign: '+', cls: 'add' },
}

// Änderungen (Sub-Goal, AP7): alte → neue Fassung einer Regelung, Wirkung auf die Anforderungen.
// Quellen: (1) zitierte Regelungen des geöffneten Laufs, für die es eine neuere Fassung gibt („Was ändert sich für MEIN
// Bauteil?“), (2) die Sub-Goal-Ordner des Pakets (dev, Sonntag heldout).
export default function Compare({ state, run, say, openReq }) {
  const folders = state?.subgoals || []
  const updates = run?.updates || []
  const sources = useMemo(() => [
    ...updates.map((u) => ({ key: `run:${u.reg}`, kind: 'run', reg: u.reg, label: u.reg.replace('UN ', ''), sub: `${u.from} → ${u.to}`, n: u.n })),
    ...folders.map((f) => ({ key: `pkg:${f.id}`, kind: 'pkg', id: f.id, label: `Paket ${f.id}`, done: f.done })),
  ], [updates, folders])
  const [key, setKey] = useState('')
  const [picked, setPicked] = useState(false) // von Hand gewählt → nicht mehr automatisch umschalten
  const [res, setRes] = useState(null)
  const [busy, setBusy] = useState(false)
  const [type, setType] = useState(null)
  const src = sources.find((x) => x.key === key)
  useEffect(() => {
    if (sources.length && (!src || (!picked && key !== sources[0].key))) { setKey(sources[0].key); setRes(null) }
  }, [sources, key, src, picked])
  const go = async (force = false) => {
    if (!src) return
    setBusy(true)
    try {
      const body = src.kind === 'run' ? { run: run.runId, reg: src.reg, force } : { id: src.id, force }
      setRes(await api(src.kind === 'run' ? '/api/impact' : '/api/subgoal', { method: 'POST', body }))
    } catch (e) { say(e.message, 'err') } finally { setBusy(false) }
  }
  useEffect(() => { if (src && (src.kind === 'run' || src.done)) go() }, [key, run?.runId]) // eslint-disable-line react-hooks/exhaustive-deps
  const old = useMemo(() => Object.fromEntries((res?.requirements || []).map((r) => [r.id, r])), [res])
  const changes = res?.submission.changes || []
  const counts = { modified: 0, removed: 0, added: 0 }
  for (const c of changes) counts[c.change]++
  const shown = changes.filter((c) => !type || c.change === type)

  return (
    <div className="cmp">
      <div className="cmp-head">
        <div>
          <div className="h-label">{src?.kind === 'run' ? `Neue Fassung · Wirkung auf Lauf ${run?.runId}` : 'Versionsvergleich · Sub-Goal'}</div>
          {res ? (
            <div className="cmp-title">
              <span className="ct-reg">{res.regulation}</span>
              <span className="ct-v old">{res.old}</span>
              <svg width="64" height="20" viewBox="0 0 64 20"><path d="M2 10 H58 M50 3 L58 10 L50 17" fill="none" stroke="var(--red)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>
              <span className="ct-v new">{res.new}</span>
            </div>
          ) : (
            <div className="cmp-title muted">{busy ? 'Vergleiche Fassungen …' : sources.length ? 'Neue Fassung prüfen: was ändert sich für die Anforderungen?' : 'Für die zitierten Regelungen gibt es keine neuere Fassung im Paket.'}</div>
          )}
        </div>
        <div className="cmp-ctrl">
          <div className="mini-tabs">
            {sources.map((x) => (
              <button key={x.key} className={key === x.key ? 'on' : ''} onClick={() => { setKey(x.key); setPicked(true); setRes(null); setType(null) }} title={x.kind === 'run' ? `${x.n} Anforderungen dieses Laufs` : 'Sub-Goal-Ordner des Pakets'}>
                {x.label}{x.sub && <em className="mt-sub">{x.sub}</em>}
              </button>
            ))}
          </div>
          <button className="primary" disabled={!src || busy} onClick={() => go(!!res)}>{busy ? 'Vergleicht …' : res ? 'Neu vergleichen' : 'Vergleichen'}</button>
        </div>
      </div>

      {res && (
        <div className="cmp-stats">
          {Object.entries(TYPES).map(([k, t]) => (
            <button key={k} className={`cstat ${t.cls} ${type === k ? 'on' : ''}`} onClick={() => setType(type === k ? null : k)}>
              <span className="cs-c">{t.sign}</span><b>{counts[k]}</b><span>{t.label}</span>
              {res.eval && <em>Treffer {res.eval[k].tp}/{res.eval[k].expected}</em>}
            </button>
          ))}
          {res.eval && (
            <div className="cstat score">
              <Gauge v={res.eval.all.f2} />
              <span>F2 lokal<br /><em>R {res.eval.all.recall.toFixed(2)} · P {res.eval.all.precision.toFixed(2)}</em></span>
            </div>
          )}
          <div className="cmp-meta">{res.requirements.length} {res.run ? `Anforderungen aus Lauf ${res.run}` : 'alte Anforderungen'} geprüft · {fmtSec(res.seconds)} · regelbasiert, ohne KI</div>
        </div>
      )}

      <div className="changes" data-scroll>
        {shown.map((c, i) => {
          const t = TYPES[c.change]
          const o = c.requirement_id ? old[c.requirement_id] : null
          const diff = c.change === 'modified' && o ? wordDiff(o.text, c.new_text) : null
          return (
            <motion.div key={i} className={`change ${t.cls}`} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: Math.min(i, 12) * 0.03 }}>
              <span className="ch-sign">{t.sign}</span>
              <div className="ch-b">
                <div className="ch-h">
                  <b>{c.requirement_id || 'neue Anforderung'}</b>
                  {o && <span>alt § {o.source.paragraph} · S. {o.source.page}</span>}
                  {c.source && <span>neu § {c.source.paragraph} · S. {c.source.page}</span>}
                  {res.run && c.requirement_id && <button className="link ch-open" onClick={() => openReq(c.requirement_id)}>Anforderung öffnen →</button>}
                </div>
                {diff && <p className="ch-t">{diff.map((d, k) => d.op === '=' ? <span key={k}>{d.t}</span> : d.op === '-' ? <del key={k}>{d.t}</del> : <ins key={k}>{d.t}</ins>)}</p>}
                {c.change === 'removed' && <p className="ch-t"><del>{o?.text}</del></p>}
                {c.change === 'added' && <p className="ch-t"><ins>{c.new_text}</ins></p>}
                <p className="ch-r">{c.reason}</p>
              </div>
            </motion.div>
          )
        })}
        {res && !shown.length && <div className="empty-row">Keine Änderungen dieses Typs.</div>}
        {!res && !busy && <div className="cmp-empty">{sources.length ? 'Quelle wählen und vergleichen. Dauert wenige Sekunden.' : 'Nichts zu vergleichen.'}</div>}
        {busy && !res && <div className="cmp-empty"><span className="spin" /> Liest beide Fassungen und gleicht Satz für Satz ab …</div>}
      </div>
    </div>
  )
}

function Gauge({ v }) {
  const R = 22, C = 2 * Math.PI * R
  return (
    <svg width="56" height="56" viewBox="0 0 56 56" className="gauge">
      <circle cx="28" cy="28" r={R} fill="none" stroke="var(--hair)" strokeWidth="5" />
      <motion.circle cx="28" cy="28" r={R} fill="none" stroke="var(--ink)" strokeWidth="5" strokeLinecap="round" transform="rotate(-90 28 28)"
        initial={{ strokeDasharray: `0 ${C}` }} animate={{ strokeDasharray: `${C * v} ${C}` }} transition={{ duration: 0.9 }} />
      <text x="28" y="29" textAnchor="middle" dominantBaseline="middle">{v.toFixed(2)}</text>
    </svg>
  )
}
