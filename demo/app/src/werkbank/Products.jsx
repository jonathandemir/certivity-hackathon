import { useEffect, useMemo, useState } from 'react'
import { motion } from 'motion/react'
import { api, fmtSec, ROLE } from './lib.js'
import { Composer } from './Composer.jsx'

// Seitenleiste: jedes Produkt genau einmal, gruppiert, mit seinem besten Ergebnis
export function ProductList({ products, current, pick, onNew }) {
  const [q, setQ] = useState('')
  const groups = useMemo(() => {
    const s = q.trim().toLowerCase()
    const out = []
    for (const p of products || []) {
      if (s && !`${p.title} ${p.id}`.toLowerCase().includes(s)) continue
      let g = out.find((x) => x.key === p.group)
      if (!g) out.push((g = { key: p.group, label: p.groupLabel, items: [] }))
      g.items.push(p)
    }
    return out
  }, [products, q])
  return (
    <aside className="pl">
      <div className="pl-top">
        <input className="pl-search" value={q} onChange={(e) => setQ(e.target.value)} placeholder={`${products?.length || 0} Produkte durchsuchen`} />
        <button className="pl-new" onClick={onNew} title="Eigenes Produkt hochladen und prüfen">+</button>
      </div>
      <div className="pl-scroll">
        {groups.map((g) => (
          <section key={g.key} className="pl-group">
            <div className="pl-glabel">{g.label}<span>{g.items.length}</span></div>
            {g.items.map((p) => (
              <button key={p.id} className={`pl-row ${p.id === current ? 'on' : ''}`} onClick={() => pick(p.id)}>
                {p.id === current && <motion.span layoutId="plpill" className="pl-pill" transition={{ type: 'spring', stiffness: 420, damping: 36 }} />}
                <span className="pl-name">{p.title}</span>
                <span className="pl-meta">
                  {p.running ? <span className="pl-live"><span className="spin" />läuft</span> : <Badge best={p.best} />}
                </span>
              </button>
            ))}
          </section>
        ))}
        {!groups.length && <div className="pl-empty">Kein Produkt gefunden.</div>}
      </div>
    </aside>
  )
}

function Badge({ best }) {
  if (!best) return <span className="pl-kind none">ungeprüft</span>
  const tone = best.score == null ? '' : +best.score >= 0.9 ? 'good' : +best.score >= 0.7 ? 'mid' : 'low'
  return (
    <>
      <span className="pl-kind">{best.kind === 'run' ? `${best.n} Anf.` : `${best.regs} Reg.`}</span>
      {best.score != null && <span className={`pl-score ${tone}`}>{best.score}</span>}
    </>
  )
}

// Kopfzeile des Produkts: was ist das beste Ergebnis, woher stammt es, neu prüfen
export function ProductHead({ p, llm, start, present }) {
  const [menu, setMenu] = useState(false)
  if (!p) return null
  const b = p.best
  return (
    <div className="ph">
      <div className="ph-l">
        <div className="ph-group">{p.groupLabel}</div>
        <h1 className="ph-title">{p.title}</h1>
        <div className="ph-best">
          {p.running ? (
            <span><span className="spin" /> Prüfung läuft · {fmtSec(p.running.elapsed)} von üblich ~{fmtSec(p.running.typical)}</span>
          ) : !b ? (
            <span>Noch nicht geprüft</span>
          ) : b.kind === 'run' ? (
            <span>
              Bestes Ergebnis{b.of > 1 ? ` aus ${b.of} Läufen` : ''}: <b>{b.n} Anforderungen</b> aus <b>{b.regs} {b.regs === 1 ? 'Regelung' : 'Regelungen'}</b>
              {b.score && <> · {b.scoreLabel} <b>{b.score}</b></>}
            </span>
          ) : (
            <span>
              Bestes Ergebnis: Auswahl von <b>{b.regs} {b.regs === 1 ? 'Regelung' : 'Regelungen'}</b>{b.score && <> · {b.scoreLabel} <b>{b.score}</b> gegen belegte Genehmigung</>}
              <span className="ph-hint"> · Anforderungen noch nicht gezogen</span>
            </span>
          )}
        </div>
      </div>
      <div className="ph-r">
        {b?.kind === 'run' && <button className="ghost sm" onClick={present} title="Überblick als Vollbild (P)">Vollbild ↗</button>}
        <div className="ph-run">
          <button className="primary" disabled={!!p.running} onClick={() => setMenu((m) => !m)}>{b?.kind === 'run' ? 'Neu prüfen' : 'Anforderungen ziehen'} ▾</button>
          {menu && (
            <motion.div className="pop right" initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} onMouseLeave={() => setMenu(false)}>
              <button className="pop-row" disabled={!llm} onClick={() => { setMenu(false); start('best') }}>
                <b>Bestmarke</b><span>{llm ? 'KI-Auswahl + Extraktion, ~4 min' : 'braucht LLM-Key (.env.local)'}</span>
              </button>
              <button className="pop-row" onClick={() => { setMenu(false); start('fast') }}>
                <b>Schnell</b><span>ohne KI, ~20 s</span>
              </button>
              <div className="pop-note">Das beste Ergebnis bleibt stehen, ein neuer Lauf ersetzt es nur, wenn er besser ist.</div>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  )
}

// Produkt ohne vollen Lauf: gewählte Regelungen gegen die belegte Genehmigung, dazu die Spezifikation
export function SelectionOnly({ pid, say }) {
  const [d, setD] = useState(null)
  useEffect(() => {
    let dead = false
    setD(null)
    api(`/api/product?id=${encodeURIComponent(pid)}`).then((x) => !dead && setD(x)).catch((e) => say(e.message, 'err'))
    return () => { dead = true }
  }, [pid, say])
  if (!d) return <div className="loading"><span className="spin" />Lade Produkt …</div>
  const LABEL = { hit: 'Treffer', ok: 'vertretbar', wrong: 'zu viel', missing: 'fehlt' }
  return (
    <div className="so">
      <section className="so-card">
        <div className="h-label">Gewählte Regelungen{d.selRun && <span className="hint-inline">aus Auswahl-Test {d.selRun}{d.selModel ? ` · ${d.selModel}` : ''}</span>}</div>
        {!d.selection.length && <div className="so-empty">Für dieses Produkt gibt es noch kein Ergebnis. Oben „Anforderungen ziehen“ startet die volle Prüfung.</div>}
        <div className="so-list">
          {d.selection.map((s) => (
            <div key={s.reg} className={`so-row ${s.status}`}>
              <span className="so-reg">{s.reg}</span>
              <span className="so-body">
                <span className="so-t">{s.title}</span>
                {s.reason && <span className="so-why">{s.role && <i>{ROLE[s.role] || s.role}</i>}{s.reason}</span>}
              </span>
              <span className={`so-st ${s.status}`}>{LABEL[s.status]}</span>
            </div>
          ))}
        </div>
        {d.gold && (
          <div className="so-gold">
            <div className="h-label">Belegte Genehmigung (Musterlösung)</div>
            <div className="so-chips">
              {(d.gold.sure || []).map((r) => <span key={r} className="chip sure">{r}</span>)}
              {(d.gold.unsure || []).map((r) => <span key={r} className="chip unsure" title="vertretbar, zählt nicht">{r} ?</span>)}
            </div>
            {d.gold.basis && <p className="so-basis">{d.gold.basis}</p>}
            {d.gold.source && <a className="so-src" href={d.gold.source} target="_blank" rel="noreferrer">Quelle öffnen ↗</a>}
          </div>
        )}
      </section>
      <section className="so-card">
        <div className="h-label">Spezifikation</div>
        <Md text={d.spec} />
      </section>
    </div>
  )
}

export function NewProduct({ state, refresh, say, close }) {
  return (
    <motion.div className="pal-bg" onMouseDown={close} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
      <motion.div className="np" onMouseDown={(e) => e.stopPropagation()} initial={{ y: -12, scale: 0.98 }} animate={{ y: 0, scale: 1 }} exit={{ y: -12, scale: 0.98 }}>
        <Composer state={state} refresh={refresh} say={say} done={close} />
      </motion.div>
    </motion.div>
  )
}

// Kleine Markdown-Ansicht für Spezifikationen (Überschriften, Listen, Absätze)
function Md({ text }) {
  if (!text) return <p>—</p>
  const out = []
  let list = null
  text.split('\n').forEach((line, i) => {
    const t = line.trim()
    if (/^[-*]\s+/.test(t)) { (list ||= []).push(t.replace(/^[-*]\s+/, '')); return }
    if (list) { out.push(<ul key={`u${i}`}>{list.map((x, k) => <li key={k}>{x}</li>)}</ul>); list = null }
    if (!t) return
    if (/^#\s/.test(t)) out.push(<h3 key={i}>{t.replace(/^#\s*(spec\s*:\s*)?/i, '')}</h3>)
    else if (/^#{2,}\s/.test(t)) out.push(<h4 key={i}>{t.replace(/^#+\s*/, '')}</h4>)
    else out.push(<p key={i}>{t}</p>)
  })
  if (list) out.push(<ul key="end">{list.map((x, k) => <li key={k}>{x}</li>)}</ul>)
  return <div className="md">{out}</div>
}
