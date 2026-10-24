import { useEffect, useMemo, useState } from 'react'
import { motion } from 'motion/react'
import { api, wordDiff, fmtSec } from './lib.js'

const TYPES = {
  modified: { label: 'Geändert', sign: '~', cls: 'mod' },
  removed: { label: 'Entfernt', sign: '−', cls: 'rem' },
  added: { label: 'Neu', sign: '+', cls: 'add' },
}

// Versionsvergleich (Sub-Goal, AP7): alte → neue Fassung einer Regelung, Wirkung auf die Anforderungen.
export default function Compare({ state, say }) {
  const folders = state?.subgoals || []
  const [id, setId] = useState('')
  const [res, setRes] = useState(null)
  const [busy, setBusy] = useState(false)
  const [type, setType] = useState(null)
  useEffect(() => { if (!id && folders.length) setId(folders[0].id) }, [folders, id])
  const run = async (force = false) => {
    if (!id) return
    setBusy(true)
    try { setRes(await api('/api/subgoal', { method: 'POST', body: { id, force } })) } catch (e) { say(e.message, 'err') } finally { setBusy(false) }
  }
  useEffect(() => { if (id && folders.find((f) => f.id === id)?.done) run() }, [id]) // eslint-disable-line react-hooks/exhaustive-deps
  const old = useMemo(() => Object.fromEntries((res?.requirements || []).map((r) => [r.id, r])), [res])
  const changes = res?.submission.changes || []
  const counts = { modified: 0, removed: 0, added: 0 }
  for (const c of changes) counts[c.change]++
  const shown = changes.filter((c) => !type || c.change === type)

  return (
    <div className="cmp">
      <div className="cmp-head">
        <div>
          <div className="h-label">Versionsvergleich · Sub-Goal</div>
          {res ? (
            <div className="cmp-title">
              <span className="ct-reg">{res.regulation}</span>
              <span className="ct-v old">{res.old}</span>
              <svg width="64" height="20" viewBox="0 0 64 20"><path d="M2 10 H58 M50 3 L58 10 L50 17" fill="none" stroke="var(--red)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>
              <span className="ct-v new">{res.new}</span>
            </div>
          ) : (
            <div className="cmp-title muted">Alte und neue Fassung vergleichen, Wirkung auf bestehende Anforderungen</div>
          )}
        </div>
        <div className="cmp-ctrl">
          <div className="mini-tabs">
            {folders.map((f) => <button key={f.id} className={id === f.id ? 'on' : ''} onClick={() => { setId(f.id); setRes(null) }}>{f.id}</button>)}
          </div>
          <button className="primary" disabled={!id || busy} onClick={() => run(!!res)}>{busy ? 'Vergleicht …' : res ? 'Neu vergleichen' : 'Vergleichen'}</button>
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
          <div className="cmp-meta">{res.requirements.length} alte Anforderungen geprüft · {fmtSec(res.seconds)} · regelbasiert, ohne KI</div>
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
        {!res && !busy && <div className="cmp-empty">Ordner wählen und vergleichen. Dauert wenige Sekunden.</div>}
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
