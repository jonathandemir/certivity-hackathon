import { useMemo, useState } from 'react'
import { motion } from 'motion/react'
import { ROLE } from './lib.js'

// Auswahl erklärt: alle Regelungen auf einem Kreis, gewählte groß und farbig, verworfene als Ring,
// rechts die Begründungen aus der Pipeline (.meta.json selection).
export default function Selection({ run, color, goReqs }) {
  const [hover, setHover] = useState(null)
  const why = useMemo(() => Object.fromEntries(run.run.selection.map((s) => [s.regulation, s])), [run])
  const chosen = run.regs.filter((r) => r.count > 0 || (why[r.id] && why[r.id].role !== 'rejected')).sort((a, b) => b.count - a.count)
  const rejected = run.run.selection.filter((s) => s.role === 'rejected')
  const rest = run.regs.filter((r) => !chosen.includes(r) && !why[r.id])
  const S = 640, c = S / 2, R = 236
  const maxN = Math.max(1, ...run.regs.map((r) => r.count))
  return (
    <div className="sel-view">
      <div className="sel-left">
        <svg width={S} height={S} viewBox={`0 0 ${S} ${S}`} className="sel-svg">
          <circle cx={c} cy={c} r={R} fill="none" stroke="var(--hair)" />
          <circle cx={c} cy={c} r={R - 44} fill="none" stroke="var(--hair)" strokeDasharray="2 6" />
          {run.regs.map((r, i) => {
            const a = -Math.PI / 2 + (i / run.regs.length) * Math.PI * 2
            const x = c + R * Math.cos(a), y = c + R * Math.sin(a)
            const on = chosen.includes(r)
            const rej = why[r.id]?.role === 'rejected'
            const role = why[r.id]?.role
            const rad = on ? 7 + 15 * Math.sqrt(r.count / maxN) : rej ? 6 : 3
            const lx = c + (R + (on ? 34 + rad : 22)) * Math.cos(a), ly = c + (R + (on ? 34 + rad : 22)) * Math.sin(a)
            const dim = hover && hover !== r.id
            return (
              <g key={r.id} onMouseEnter={() => setHover(r.id)} onMouseLeave={() => setHover(null)} style={{ cursor: on ? 'pointer' : 'default', opacity: dim ? 0.35 : 1, transition: 'opacity .2s' }} onClick={() => on && goReqs(r.id)}>
                {on && <motion.line x1={c + (R - 44) * Math.cos(a)} y1={c + (R - 44) * Math.sin(a)} x2={x} y2={y} stroke={color(r.id)} strokeWidth="1.2" initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 0.8, delay: 0.1 + i * 0.01 }} />}
                {on ? (
                  <>
                    {role === 'installation' && <circle cx={x} cy={y} r={rad + 5} fill="none" stroke={color(r.id)} strokeDasharray="3 3" />}
                    {role === 'cross-cutting' && <circle cx={x} cy={y} r={rad + 5} fill="none" stroke={color(r.id)} />}
                    <motion.circle cx={x} cy={y} r={rad} fill={color(r.id)} initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: 'spring', delay: 0.3 + i * 0.01 }} style={{ transformOrigin: `${x}px ${y}px` }} />
                  </>
                ) : rej ? (
                  <circle cx={x} cy={y} r={rad} fill="var(--bg)" stroke="#9c978d" strokeWidth="1.4" />
                ) : (
                  <circle cx={x} cy={y} r={rad} fill="#cdc9c0" />
                )}
                {(on || rej || hover === r.id) && (
                  <text x={lx} y={ly} textAnchor={Math.cos(a) > 0.2 ? 'start' : Math.cos(a) < -0.2 ? 'end' : 'middle'} dominantBaseline="middle"
                    className={`sel-lbl ${on ? 'on' : ''}`}>{r.id.replace('UN ', '')}</text>
                )}
              </g>
            )
          })}
        </svg>
        <div className="sel-center">
          {hover ? (
            <>
              <b style={{ color: color(hover) }}>{hover}</b>
              <span>{run.regs.find((r) => r.id === hover)?.title}</span>
              <em>{why[hover] ? (ROLE[why[hover].role] || why[hover].role) : chosen.some((r) => r.id === hover) ? 'gewählt' : 'nicht betrachtet'}</em>
            </>
          ) : (
            <>
              <b>{chosen.length}<small> / {run.regs.length}</small></b>
              <span>Regelungen gewählt für</span>
              <em>{run.case.title}</em>
            </>
          )}
        </div>
        <div className="sel-legend">
          <span><i className="lg-dot" />gewählt, Größe = Anforderungen</span>
          <span><i className="lg-dash" />Anbau</span>
          <span><i className="lg-ring" />Querschnitt</span>
          <span><i className="lg-rej" />verworfen mit Grund</span>
        </div>
      </div>

      <div className="sel-right" data-scroll>
        {!run.run.selection.length && (
          <div className="note-box">Dieser Lauf hat keine Begründungen gespeichert (Auswahl {run.run.select || 'B0'}). Läufe im Modus „Bestmarke“ erklären jede Regelung.</div>
        )}
        <div className="h-label">Gewählt · {chosen.length}</div>
        {chosen.map((r) => (
          <div key={r.id} className={`why ${hover === r.id ? 'hi' : ''}`} onMouseEnter={() => setHover(r.id)} onMouseLeave={() => setHover(null)}>
            <span className="why-dot" style={{ background: color(r.id) }} />
            <div className="why-b">
              <div className="why-h"><b>{r.id}</b><span>{r.title}</span>{why[r.id] && <i className={`role ${why[r.id].role}`}>{ROLE[why[r.id].role] || why[r.id].role}</i>}</div>
              {why[r.id]?.reason && <p>{why[r.id].reason}</p>}
            </div>
            <button className="why-n" onClick={() => goReqs(r.id)} disabled={!r.count}><b>{r.count}</b><span>Anf. →</span></button>
          </div>
        ))}
        {rejected.length > 0 && <div className="h-label">Bewusst verworfen · {rejected.length}</div>}
        {rejected.map((s) => (
          <div key={s.regulation} className={`why rej ${hover === s.regulation ? 'hi' : ''}`} onMouseEnter={() => setHover(s.regulation)} onMouseLeave={() => setHover(null)}>
            <span className="why-dot ring" />
            <div className="why-b">
              <div className="why-h"><b>{s.regulation}</b><span>{run.regs.find((r) => r.id === s.regulation)?.title}</span></div>
              <p>{s.reason}</p>
            </div>
          </div>
        ))}
        <div className="h-label">Nicht betrachtet · {rest.length}</div>
        <div className="rest">{rest.map((r) => <span key={r.id} title={r.title} onMouseEnter={() => setHover(r.id)} onMouseLeave={() => setHover(null)}>{r.id.replace('UN ', '')}</span>)}</div>
      </div>
    </div>
  )
}
