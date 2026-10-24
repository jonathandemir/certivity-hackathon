import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'motion/react'
import { api, STATUS, ROLE } from './lib.js'

const ROW = 86
const statusOf = (run, id) => run.review[id]?.status || 'open'

export default function Reqs({ run, color, filters, setFilters, reqId, setReqId, setReview, say }) {
  const parts = useMemo(() => [...run.case.parts, { id: 'device', n: run.case.parts.length + 1, name: 'Gesamtgerät' }], [run])
  const partName = useMemo(() => Object.fromEntries(parts.map((p) => [p.id, p.name])), [parts])
  const q = filters.q.trim().toLowerCase()
  const base = useMemo(() => run.reqs.filter((r) => (!filters.part || r.part === filters.part) && (!q || `${r.id} ${r.reg} ${r.para} ${r.text}`.toLowerCase().includes(q))), [run, filters.part, q])
  const list = useMemo(() => base.filter((r) => (!filters.reg || r.reg === filters.reg) && (!filters.status || statusOf(run, r.id) === filters.status)), [base, filters.reg, filters.status, run])
  const sel = list.find((r) => r.id === reqId) || list[0]
  useEffect(() => { if (sel && sel.id !== reqId) setReqId(sel.id) }, [sel, reqId, setReqId])

  const listRef = useRef()
  const searchRef = useRef()
  const move = useCallback((d) => {
    if (!list.length) return
    const i = Math.max(0, Math.min(list.length - 1, list.findIndex((r) => r.id === sel?.id) + d))
    setReqId(list[i].id)
  }, [list, sel, setReqId])
  const mark = useCallback((status) => {
    if (!sel) return
    setReview(sel.id, { status })
    if (status !== 'open') move(1)
  }, [sel, setReview, move])

  useEffect(() => {
    const key = (e) => {
      if (e.metaKey || e.ctrlKey || e.altKey) return
      if (e.target.closest('input, textarea')) { if (e.key === 'Escape') e.target.blur(); return }
      if (e.key === 'j' || e.key === 'ArrowDown') { e.preventDefault(); move(1) }
      else if (e.key === 'k' || e.key === 'ArrowUp') { e.preventDefault(); move(-1) }
      else if (e.key === 'a') mark('accepted')
      else if (e.key === 'x') mark('rejected')
      else if (e.key === 'u') mark('open')
      else if (e.key === '/') { e.preventDefault(); searchRef.current?.focus() }
      else if (e.key === 'n') { e.preventDefault(); document.querySelector('.ev-note')?.focus() }
      else if (e.key === 'Escape') setFilters({ reg: null, part: null, status: null, q: '' })
    }
    window.addEventListener('keydown', key)
    return () => window.removeEventListener('keydown', key)
  }, [move, mark, setFilters])

  // ausgewählte Zeile im Blick halten
  useLayoutEffect(() => {
    const el = listRef.current
    if (!el || !sel) return
    const i = list.findIndex((r) => r.id === sel.id)
    const top = i * ROW, bottom = top + ROW
    if (top < el.scrollTop + 8) el.scrollTop = Math.max(0, top - ROW)
    else if (bottom > el.scrollTop + el.clientHeight - 8) el.scrollTop = bottom - el.clientHeight + ROW
  }, [sel, list])

  const counts = useMemo(() => {
    const c = { open: 0, accepted: 0, rejected: 0 }
    for (const r of base) if (!filters.reg || r.reg === filters.reg) c[statusOf(run, r.id)]++
    return c
  }, [base, filters.reg, run])
  const reviewed = run.reqs.length - run.reqs.filter((r) => statusOf(run, r.id) === 'open').length

  return (
    <div className="reqs">
      <aside className="compass">
        <Wheel run={run} base={base} color={color} reg={filters.reg} setReg={(reg) => setFilters((f) => ({ ...f, reg: f.reg === reg ? null : reg }))} shown={list.length} />
        <div className="c-block">
          <div className="h-label">Status</div>
          <div className="status-row">
            {Object.entries(STATUS).map(([k, s]) => (
              <button key={k} className={`st-chip ${k} ${filters.status === k ? 'on' : ''}`} onClick={() => setFilters((f) => ({ ...f, status: f.status === k ? null : k }))}>
                <StatusDot s={k} /><b>{counts[k]}</b><span>{s.label}</span>
              </button>
            ))}
          </div>
          <div className="progress"><i style={{ width: `${(reviewed / Math.max(1, run.reqs.length)) * 100}%` }} /></div>
          <div className="progress-l">{reviewed} von {run.reqs.length} geprüft</div>
        </div>
        <div className="c-block grow">
          <div className="h-label">Bauteile <span className="hint-inline">Zuordnung per Wortabgleich</span></div>
          <div className="parts" data-scroll>
            {parts.map((p) => {
              const n = run.reqs.filter((r) => r.part === p.id && (!filters.reg || r.reg === filters.reg)).length
              if (!n) return null
              const max = Math.max(...parts.map((x) => run.reqs.filter((r) => r.part === x.id).length), 1)
              return (
                <button key={p.id} className={`part ${filters.part === p.id ? 'on' : ''}`} onClick={() => setFilters((f) => ({ ...f, part: f.part === p.id ? null : p.id }))}>
                  <span className="part-n">{p.n}</span>
                  <span className="part-name">{p.name}</span>
                  <span className="part-c">{n}</span>
                  <i className="part-bar" style={{ width: `${(n / max) * 100}%` }} />
                </button>
              )
            })}
          </div>
        </div>
      </aside>

      <section className="list-col">
        <div className="list-head">
          <div className="search">
            <svg width="16" height="16" viewBox="0 0 16 16"><circle cx="7" cy="7" r="5" fill="none" stroke="currentColor" strokeWidth="1.6" /><path d="M11 11l3.5 3.5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" /></svg>
            <input ref={searchRef} value={filters.q} onChange={(e) => setFilters((f) => ({ ...f, q: e.target.value }))} placeholder="Suchen in Text, Absatz, ID" />
            <kbd>/</kbd>
          </div>
          <ExportMenu run={run} />
        </div>
        <div className="chips">
          {filters.reg && <Chip c={color(filters.reg)} onX={() => setFilters((f) => ({ ...f, reg: null }))}>{filters.reg}</Chip>}
          {filters.part && <Chip onX={() => setFilters((f) => ({ ...f, part: null }))}>{partName[filters.part]}</Chip>}
          {filters.status && <Chip onX={() => setFilters((f) => ({ ...f, status: null }))}>{STATUS[filters.status].label}</Chip>}
          <span className="chips-n">{list.length} {list.length === 1 ? 'Anforderung' : 'Anforderungen'}</span>
          {list.length > 0 && list.length <= 400 && (filters.reg || filters.part || filters.status || q) && (
            <span className="bulk">
              <button onClick={() => { setReview(list.map((r) => r.id), { status: 'accepted' }); say(`${list.length} bestätigt`) }}>alle bestätigen</button>
              <button onClick={() => { setReview(list.map((r) => r.id), { status: 'rejected' }); say(`${list.length} verworfen`) }}>alle verwerfen</button>
            </span>
          )}
        </div>
        <VirtualList listRef={listRef} list={list} sel={sel} setReqId={setReqId} run={run} color={color} partName={partName} />
        <div className="keys">
          <span><kbd>J</kbd><kbd>K</kbd> blättern</span>
          <span><kbd>A</kbd> bestätigen</span>
          <span><kbd>X</kbd> verwerfen</span>
          <span><kbd>U</kbd> offen</span>
          <span><kbd>N</kbd> Notiz</span>
          <span><kbd>Esc</kbd> Filter weg</span>
        </div>
      </section>

      <section className="evidence">
        <AnimatePresence mode="wait">
          {sel ? <Evidence key={sel.id} run={run} req={sel} color={color} setReview={setReview} mark={mark} move={move} setReqId={setReqId} partName={partName} /> : <div className="ev-empty">Keine Anforderung im Filter.</div>}
        </AnimatePresence>
      </section>
      <Thread selId={sel?.id} />
    </div>
  )
}

function Chip({ children, c, onX }) {
  return <span className="chip">{c && <i style={{ background: c }} />}{children}<button onClick={onX}>×</button></span>
}

export function StatusDot({ s }) {
  if (s === 'accepted') return <svg className="sd" width="16" height="16" viewBox="0 0 16 16"><circle cx="8" cy="8" r="7" fill="var(--ok)" /><path d="M4.8 8.3l2.2 2.2 4.2-4.6" fill="none" stroke="#fff" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" /></svg>
  if (s === 'rejected') return <svg className="sd" width="16" height="16" viewBox="0 0 16 16"><circle cx="8" cy="8" r="7" fill="var(--red)" /><path d="M5.5 5.5l5 5M10.5 5.5l-5 5" stroke="#fff" strokeWidth="1.8" strokeLinecap="round" /></svg>
  return <svg className="sd" width="16" height="16" viewBox="0 0 16 16"><circle cx="8" cy="8" r="6.2" fill="none" stroke="#b9b5ac" strokeWidth="1.6" /></svg>
}

function VirtualList({ listRef, list, sel, setReqId, run, color, partName }) {
  const [top, setTop] = useState(0)
  const [h, setH] = useState(800)
  useEffect(() => {
    const el = listRef.current
    if (!el) return
    const ro = new ResizeObserver(() => setH(el.clientHeight))
    ro.observe(el)
    return () => ro.disconnect()
  }, [listRef])
  const from = Math.max(0, Math.floor(top / ROW) - 6), to = Math.min(list.length, Math.ceil((top + h) / ROW) + 6)
  return (
    <div className="vlist" ref={listRef} onScroll={(e) => setTop(e.currentTarget.scrollTop)} data-scroll>
      <div style={{ height: list.length * ROW, position: 'relative' }}>
        {list.slice(from, to).map((r, k) => {
          const i = from + k
          const st = statusOf(run, r.id)
          return (
            <button key={r.id} data-req={r.id} className={`row ${sel?.id === r.id ? 'sel' : ''} ${st}`} style={{ top: i * ROW }} onClick={() => setReqId(r.id)}>
              <StatusDot s={st} />
              <span className="pg" style={{ '--c': color(r.reg) }}>{r.page}</span>
              <span className="row-b">
                <span className="row-ref">{r.reg} · § {r.para}<em>{partName[r.part]}</em>{run.review[r.id]?.note && <em className="has-note">Notiz</em>}</span>
                <span className="row-t">{r.text}</span>
              </span>
            </button>
          )
        })}
      </div>
    </div>
  )
}

function ExportMenu({ run }) {
  const [open, setOpen] = useState(false)
  const id = encodeURIComponent(run.runId)
  return (
    <div className="export">
      <button className="ghost sm" onClick={() => setOpen((o) => !o)}>Export ▾</button>
      {open && (
        <div className="pop right" onMouseLeave={() => setOpen(false)}>
          <a className="pop-row" href={`/api/export?run=${id}&fmt=json`}><b>Abgabe-JSON</b><span>Plattformformat, ohne Verworfene</span></a>
          <a className="pop-row" href={`/api/export?run=${id}&fmt=csv`}><b>Tabelle (CSV)</b><span>mit Status und Notizen</span></a>
        </div>
      )}
    </div>
  )
}

function Evidence({ run, req, color, setReview, mark, move, setReqId, partName }) {
  const [page, setPage] = useState(null)
  const [err, setErr] = useState('')
  const [note, setNote] = useState(run.review[req.id]?.note || '')
  const scroller = useRef()
  const st = statusOf(run, req.id)
  const sel = run.run.selection.find((s) => s.regulation === req.reg)
  const regTitle = run.regs.find((r) => r.id === req.reg)?.title
  useEffect(() => {
    let dead = false
    setErr('')
    api(`/api/hits?run=${encodeURIComponent(run.runId)}&reg=${encodeURIComponent(req.reg)}&ver=${encodeURIComponent(req.version)}&page=${req.page}`)
      .then((d) => !dead && setPage(d)).catch((e) => !dead && setErr(e.message))
    return () => { dead = true }
  }, [run.runId, req.reg, req.version, req.page])
  const lines = page?.hits?.[req.id] || []
  // zur Markierung scrollen, sobald das Bild steht
  const onImg = () => {
    const el = scroller.current
    if (!el || !lines.length) return
    const y = lines[0][1] * el.scrollHeight
    el.scrollTo({ top: Math.max(0, y - el.clientHeight * 0.35), behavior: 'smooth' })
  }
  return (
    <motion.div className="ev" initial={{ opacity: 0, x: 12 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -8 }} transition={{ duration: 0.18 }}>
      <div className="ev-top">
        <div className="ev-id">
          <span className="ev-dot" style={{ background: color(req.reg) }} />
          <b>{req.id}</b><span>{req.reg} · § {req.para} · Seite {req.page}{page?.of ? ` von ${page.of}` : ''}</span>
        </div>
        <div className="ev-actions">
          <button className={`act ok ${st === 'accepted' ? 'on' : ''}`} onClick={() => mark(st === 'accepted' ? 'open' : 'accepted')}><StatusDot s="accepted" />Bestätigen<kbd>A</kbd></button>
          <button className={`act no ${st === 'rejected' ? 'on' : ''}`} onClick={() => mark(st === 'rejected' ? 'open' : 'rejected')}><StatusDot s="rejected" />Verwerfen<kbd>X</kbd></button>
          <button className="act icon" onClick={() => move(-1)} title="vorherige (K)">↑</button>
          <button className="act icon" onClick={() => move(1)} title="nächste (J)">↓</button>
        </div>
      </div>
      <p className="ev-text">{req.text}</p>
      <div className="ev-meta">
        <div><span>Regelung</span><b>{req.reg} <i>v{req.version}</i></b><em>{regTitle}</em></div>
        <div><span>Bauteil</span><b>{partName[req.part]}</b><em>Wortabgleich</em></div>
        {sel && <div className="wide"><span>Warum diese Regelung · {ROLE[sel.role] || sel.role}</span><em className="reason">{sel.reason}</em></div>}
      </div>
      <textarea className="ev-note" rows={1} value={note} placeholder="Notiz (N) …" onChange={(e) => setNote(e.target.value)}
        onBlur={() => note !== (run.review[req.id]?.note || '') && setReview(req.id, { note })} />
      <div className="page-wrap">
        <div className="page-bar">
          <span>Original-PDF · {req.reg} {req.version} · Seite {req.page}</span>
          {page?.pdf && <a href={page.pdf} target="_blank" rel="noreferrer">öffnen ↗</a>}
        </div>
        <div className="page-scroll" ref={scroller}>
          {err && <div className="page-err">{err}</div>}
          {page?.src && (
            <div className="page" style={{ aspectRatio: `${page.w} / ${page.h}` }}>
              <img src={page.src} alt="" onLoad={onImg} draggable={false} />
              {Object.entries(page.hits || {}).map(([id, ls]) => ls.map(([x, y, w, h], k) => (
                <span key={id + k} className={`mark ${id === req.id ? 'sel' : ''}`} data-thread={id === req.id && k === 0 ? 'end' : undefined}
                  title={id === req.id ? '' : `${id} anzeigen`} onClick={() => id !== req.id && setReqId(id)}
                  style={{ left: `${x * 100}%`, top: `${y * 100}%`, width: `${w * 100}%`, height: `${h * 100}%`, '--c': color(req.reg) }} />
              )))}
              {!lines.length && page && <span className="page-miss">Absatz {req.para} auf der Seite nicht exakt gefunden</span>}
            </div>
          )}
          {!page && !err && <div className="page-ph"><span className="spin" />Seite wird gerendert</div>}
        </div>
      </div>
    </motion.div>
  )
}

// Belegfaden: rote Linie von der gewählten Zeile zur markierten Stelle im PDF
function Thread({ selId }) {
  const [d, setD] = useState('')
  useEffect(() => {
    let raf
    const loop = () => {
      const row = document.querySelector('.row.sel')
      const end = document.querySelector('[data-thread="end"]')
      const list = document.querySelector('.vlist')?.getBoundingClientRect()
      const pg = document.querySelector('.page-scroll')?.getBoundingClientRect()
      let next = ''
      if (row && end && list && pg) {
        const a = row.getBoundingClientRect(), b = end.getBoundingClientRect()
        const ay = a.top + a.height / 2, by = b.top + b.height / 2
        if (ay > list.top && ay < list.bottom && by > pg.top && by < pg.bottom) {
          const ax = a.right + 2, bx = b.left - 3, mx = (ax + bx) / 2
          next = `M ${ax} ${ay} C ${mx} ${ay}, ${mx} ${by}, ${bx} ${by}`
        }
      }
      setD((o) => (o === next ? o : next))
      raf = requestAnimationFrame(loop)
    }
    raf = requestAnimationFrame(loop)
    return () => cancelAnimationFrame(raf)
  }, [selId])
  return (
    <svg className="thread">
      {d && <path d={d} />}
      {d && <circle r="4" cx={d.split(' ')[1]} cy={d.split(' ')[2]} />}
    </svg>
  )
}

function Wheel({ run, base, color, reg, setReg, shown }) {
  const [hover, setHover] = useState(null)
  const S = 244, c = S / 2, R = 92, RT = 114
  const counts = useMemo(() => {
    const m = {}
    for (const r of base) m[r.reg] = (m[r.reg] || 0) + 1
    return Object.entries(m).sort((a, b) => b[1] - a[1])
  }, [base])
  const total = counts.reduce((a, [, n]) => a + n, 0) || 1
  const gap = counts.length > 1 ? 0.035 : 0
  let acc = -Math.PI / 2
  const arcs = counts.map(([id, n]) => {
    const span = (n / total) * Math.PI * 2
    const a0 = acc + gap / 2, a1 = acc + span - gap / 2
    acc += span
    return { id, n, a0, a1: Math.max(a0 + 0.01, a1) }
  })
  const arc = (r, a0, a1) => {
    const large = a1 - a0 > Math.PI ? 1 : 0
    return `M ${c + r * Math.cos(a0)} ${c + r * Math.sin(a0)} A ${r} ${r} 0 ${large} 1 ${c + r * Math.cos(a1)} ${c + r * Math.sin(a1)}`
  }
  const h = hover || reg
  const hi = h && run.regs.find((r) => r.id === h)
  return (
    <div className="wheel">
      <svg width={S} height={S} viewBox={`0 0 ${S} ${S}`}>
        {run.regs.map((r, i) => {
          const a = -Math.PI / 2 + (i / run.regs.length) * Math.PI * 2
          const on = r.count > 0
          return <line key={r.id} x1={c + (RT - (on ? 7 : 3)) * Math.cos(a)} y1={c + (RT - (on ? 7 : 3)) * Math.sin(a)} x2={c + RT * Math.cos(a)} y2={c + RT * Math.sin(a)}
            stroke={on ? color(r.id) : '#cfcbc2'} strokeWidth={on ? 2.4 : 1.2} strokeLinecap="round" />
        })}
        {arcs.map((a) => (
          <path key={a.id} d={arc(R, a.a0, a.a1)} fill="none" stroke={color(a.id)} strokeLinecap="butt"
            strokeWidth={reg === a.id || hover === a.id ? 22 : 16} opacity={reg && reg !== a.id ? 0.25 : 1}
            style={{ transition: 'stroke-width .2s, opacity .2s', cursor: 'pointer' }}
            onMouseEnter={() => setHover(a.id)} onMouseLeave={() => setHover(null)} onClick={() => setReg(a.id)} />
        ))}
      </svg>
      <div className="wheel-c">
        {hi ? (
          <>
            <b style={{ color: color(hi.id) }}>{counts.find(([id]) => id === hi.id)?.[1] || 0}</b>
            <span className="wc-id">{hi.id}</span>
            <span className="wc-t">{hi.title}</span>
          </>
        ) : (
          <>
            <b>{shown}</b>
            <span className="wc-id">Anforderungen</span>
            <span className="wc-t">{counts.length} Regelungen · {run.pagesTotal} Seiten</span>
          </>
        )}
      </div>
    </div>
  )
}
