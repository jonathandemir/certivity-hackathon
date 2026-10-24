import { memo, useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'motion/react'
import SceneRaw from './Scene.jsx'
import { loadImage, segmentDrawing, textCards } from './segment.js'
import {
  CASE, RUN, REGS, REQS, ACTIVE, PARTS, partById, partCounts, regColor, PAGES_TOTAL, LOG, HERO_REQ, DEFAULT_PART,
  pageOf, hitsOf, activationT,
} from './data.js'

const Scene = memo(SceneRaw)
const RUN_MS = 7000
const ACT_NAMES = ['Lauf', 'Zeichnung', 'Beleg']
const ease = (x) => 1 - Math.pow(1 - x, 3)
const fmtTime = (s) => (s == null ? '—' : `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(Math.round(s % 60)).padStart(2, '0')}`)

function useRun() {
  const progress = useRef(0)
  const [t, setT] = useState(0)
  const raf = useRef()
  const start = useCallback(() => {
    cancelAnimationFrame(raf.current)
    const fixed = new URLSearchParams(location.search).get('t')
    if (fixed != null) { progress.current = +fixed; setT(+fixed); return }
    const t0 = performance.now()
    const tick = (now) => {
      const k = Math.max(0, Math.min(1, (now - t0) / RUN_MS))
      progress.current = k
      setT(k)
      if (k < 1) raf.current = requestAnimationFrame(tick)
    }
    raf.current = requestAnimationFrame(tick)
  }, [])
  return { progress, t, start }
}

// Teile für die 3D-Bühne: aus der Zeichnung, sonst Namenskarten der Bauteile, sonst eine Karte mit dem Falltitel
function useSegments() {
  const [segs, setSegs] = useState([])
  useEffect(() => {
    let dead = false
    ;(async () => {
      let s = []
      if (CASE.drawing?.src) {
        try { s = segmentDrawing(await loadImage(CASE.drawing.src)) } catch (e) { console.warn('Zeichnung nicht lesbar', e) }
      }
      if (!s.length) {
        await document.fonts.ready
        const names = CASE.parts.length ? CASE.parts.map((p) => p.name) : [CASE.title || CASE.id]
        s = textCards(names).map((c, i) => ({ ...c, partId: CASE.parts[i]?.id }))
      }
      if (!dead) setSegs(s)
    })()
    return () => { dead = true }
  }, [])
  return segs
}

export default function App() {
  const [act, setAct] = useState(0)
  const [part, setPart] = useState(DEFAULT_PART)
  const [hovered, setHovered] = useState(null)
  const [picked, setPicked] = useState(null)
  const [reqId, setReqId] = useState(HERO_REQ?.id)
  const { progress, t, start } = useRun()
  const anchorOut = useRef({})
  const segs = useSegments()

  useEffect(() => { const id = setTimeout(start, 600); return () => clearTimeout(id) }, [start])

  const lock = useRef(0)
  useEffect(() => {
    const go = (d) => setAct((a) => Math.max(0, Math.min(2, a + d)))
    const key = (e) => {
      if (e.key === 'ArrowRight') go(1)
      if (e.key === 'ArrowLeft') go(-1)
      if (['1', '2', '3'].includes(e.key)) setAct(+e.key - 1)
      if (e.key === 'r') { setAct(0); start() }
    }
    const wheel = (e) => {
      if (e.target.closest('[data-scroll]')) return
      const d = Math.abs(e.deltaX) > Math.abs(e.deltaY) ? e.deltaX : e.deltaY
      if (Math.abs(d) < 18 || performance.now() < lock.current) return
      lock.current = performance.now() + 1100
      go(d > 0 ? 1 : -1)
    }
    window.addEventListener('keydown', key)
    window.addEventListener('wheel', wheel, { passive: true })
    return () => { window.removeEventListener('keydown', key); window.removeEventListener('wheel', wheel) }
  }, [start])

  // Ein Teil der Zeichnung anklicken: bei Namenskarten ist das Teil ein Bauteil, sonst nur Markierung
  const onPick = useCallback((n) => {
    setPicked(n)
    const s = segs.find((x) => x.n === n)
    if (s?.partId) setPart(s.partId)
  }, [segs])
  const openReq = (id) => { setReqId(id); setAct(2) }
  const req = REQS.find((r) => r.id === reqId) || HERO_REQ

  useEffect(() => { document.body.style.cursor = hovered && act === 1 ? 'pointer' : '' }, [hovered, act])

  return (
    <>
      <Scene act={act} progress={progress} segs={segs} hovered={hovered} setHovered={setHovered} picked={picked} onPick={onPick} anchorOut={anchorOut} />
      <Header act={act} setAct={setAct} onRun={() => { setAct(0); start() }} t={t} />
      <div className="track" style={{ transform: `translate3d(${-act * 100}vw,0,0)` }}>
        <section className="panel"><ActRun t={t} /></section>
        <section className="panel">
          <ActDrawing part={part} setPart={setPart} segs={segs} hovered={hovered} setHovered={setHovered} picked={picked} onPick={onPick}
            openReq={openReq} anchorOut={anchorOut} active={act === 1} />
        </section>
        <section className="panel">{req ? <ActEvidence req={req} active={act === 2} anchorOut={anchorOut} /> : <Empty />}</section>
      </div>
      <Footer act={act} setAct={setAct} />
    </>
  )
}

function Empty() {
  return <div className="empty">Keine Anforderungen im Ergebnis.</div>
}

function Header({ act, setAct, onRun, t }) {
  const running = t > 0 && t < 1
  return (
    <header className="hdr">
      <div className="brand"><span className="brand-dot" />BarelyLegal</div>
      <nav className="tabs">
        {ACT_NAMES.map((n, i) => (
          <button key={n} className={`tab ${act === i ? 'on' : ''}`} onClick={() => setAct(i)}>
            {act === i && <motion.span layoutId="tabpill" className="tab-pill" transition={{ type: 'spring', stiffness: 380, damping: 32 }} />}
            <span className="tab-k">0{i + 1}</span>
            <span className="tab-n">{n}</span>
          </button>
        ))}
      </nav>
      <div className="hdr-r">
        <span className="case-chip">{CASE.id}{CASE.category ? <><i>·</i>{CASE.category.split(/[ —–-]/)[0]}</> : null}</span>
        <button className={`run ${running ? 'live' : ''}`} onClick={onRun}>
          <span className="run-dot" />
          {running ? `Prüft ${Math.round(t * 100)} %` : 'Erneut prüfen'}
        </button>
      </div>
    </header>
  )
}

function Footer({ act, setAct }) {
  return (
    <footer className="ftr">
      <span className="hint"><kbd>←</kbd><kbd>→</kbd> wechseln · <kbd>R</kbd> neu prüfen</span>
      <div className="dots">
        {[0, 1, 2].map((i) => <button key={i} className={act === i ? 'on' : ''} onClick={() => setAct(i)} aria-label={ACT_NAMES[i]} />)}
      </div>
    </footer>
  )
}

/* ---------------- Akt 1: Lauf ---------------- */
function ActRun({ t }) {
  const k = ease(Math.max(0, Math.min(1, (t - 0.15) / 0.8)))
  const shown = Math.round(REQS.length * k)
  const regsOn = ACTIVE.filter((r) => t >= activationT(r.id)).length
  const line = [...LOG].reverse().find(([s]) => t >= s)?.[1] ?? ''
  return (
    <div className="run-wrap">
      <div className="run-copy">
        <div className="eyebrow">Fall {CASE.id}{CASE.title && CASE.title !== CASE.id ? ` · ${CASE.title}` : ''}</div>
        <h1 className="display">
          Ein Bauteil.<br />
          {REGS.length} Regelwerke.<br />
          <span className="num-red">{shown}</span> Pflichten.
        </h1>
        <p className="lede">
          Der Agent liest {CASE.hasSpec ? 'die Spezifikation' : 'die Zeichnung'}, wählt die einschlägigen UN-Regelungen und zieht
          jede Anforderung heraus, mit Seite und Absatz als Beleg.
        </p>
      </div>
      <div className="stats">
        <Stat k={`${regsOn}/${REGS.length}`} l="Regelungen gewählt" />
        <Stat k={shown} l="Anforderungen" />
        <Stat k={Math.round(PAGES_TOTAL * k)} l="Seiten belegt" />
        <Stat k={RUN.seconds != null ? fmtTime(RUN.seconds * Math.min(1, t)) : '—'} l="Laufzeit" />
      </div>
      <div className={`ticker ${t >= 1 ? 'done' : ''}`}>
        <span className="tk-dot" />
        <AnimatePresence mode="popLayout" initial={false}>
          <motion.span key={line} className="tk-line" initial={{ y: 14, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: -14, opacity: 0 }} transition={{ duration: 0.25 }}>
            {line}
          </motion.span>
        </AnimatePresence>
      </div>
    </div>
  )
}

function Stat({ k, l }) {
  return (
    <div className="stat">
      <div className="stat-k">{k}</div>
      <div className="stat-l">{l}</div>
    </div>
  )
}

/* ---------------- Akt 2: Zeichnung ---------------- */
function Donut({ by, total, size = 128 }) {
  const r = size / 2 - 8, C = 2 * Math.PI * r
  let acc = 0
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="donut">
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--hair)" strokeWidth="10" />
      {Object.entries(by).sort((a, b) => b[1] - a[1]).map(([reg, n]) => {
        const len = (n / Math.max(1, total)) * C
        const el = (
          <motion.circle key={reg} cx={size / 2} cy={size / 2} r={r} fill="none" stroke={regColor(reg)} strokeWidth="10"
            transform={`rotate(-90 ${size / 2} ${size / 2})`}
            initial={{ strokeDasharray: `0 ${C}` }} animate={{ strokeDasharray: `${Math.max(0, len - 3)} ${C}`, strokeDashoffset: -acc }}
            transition={{ duration: 0.7, ease: [0.2, 0.7, 0.2, 1] }} />
        )
        acc += len
        return el
      })}
      <text x="50%" y="50%" dy="0.35em" textAnchor="middle" className="donut-n">{total}</text>
    </svg>
  )
}

function Callouts({ segs, picked, hovered, setHovered, onPick, anchorOut, active }) {
  const [pos, setPos] = useState(null)
  useEffect(() => {
    if (!active || !segs.length) return
    let raf
    const loop = () => {
      const A = anchorOut.current
      const pts = segs.map((s) => ({ n: s.n, label: s.partId ? partById[s.partId]?.name : `Teil ${s.n}`, ...(A[`pos${s.n}`] || { x: 0, y: 0 }) }))
      const order = [...pts].sort((a, b) => a.x - b.x)
      const W = window.innerWidth, x0 = W * 0.055 + 80, x1 = W * 0.52, top = window.innerHeight * 0.22
      const step = order.length > 1 ? (x1 - x0) / (order.length - 1) : 0
      const next = order.map((p, i) => ({ ...p, tx: order.length > 1 ? x0 + i * step : W * 0.25, ty: top + (i % 2) * 60 }))
      setPos((old) => (old && JSON.stringify(old) === JSON.stringify(next) ? old : next))
      raf = requestAnimationFrame(loop)
    }
    raf = requestAnimationFrame(loop)
    return () => cancelAnimationFrame(raf)
  }, [active, anchorOut, segs])
  if (!pos) return null
  return (
    <>
      <svg className="callout-svg">
        {pos.map((p) => {
          const on = p.n === picked || p.n === hovered
          const ty = p.ty + 22
          return (
            <g key={p.n} className={on ? 'on' : ''}>
              <path d={`M ${p.tx} ${ty} L ${p.tx} ${ty + (p.y - ty) * 0.4} L ${p.x} ${p.y}`} />
              <circle cx={p.x} cy={p.y} r={on ? 5 : 3.5} />
            </g>
          )
        })}
      </svg>
      {pos.map((p) => (
        <button key={p.n} className={`callout ${p.n === picked ? 'active' : ''} ${p.n === hovered ? 'hover' : ''}`}
          style={{ left: p.tx, top: p.ty }} onMouseEnter={() => setHovered(p.n)} onMouseLeave={() => setHovered(null)} onClick={() => onPick(p.n)}>
          <span className="tag-n">{p.n}</span>
          <span className="tag-name">{p.label}</span>
        </button>
      ))}
    </>
  )
}

const PAGE = 80
function ActDrawing({ part, setPart, segs, hovered, setHovered, picked, onPick, openReq, anchorOut, active }) {
  const p = partById[part]
  const pc = partCounts[part]
  const list = useMemo(() => REQS.filter((r) => r.part === part), [part])
  const [limit, setLimit] = useState(PAGE)
  useEffect(() => setLimit(PAGE), [part])
  return (
    <div className="draw-wrap">
      <div className="draw-left">
        <div className="eyebrow">{CASE.drawing ? 'Explosionszeichnung, automatisch in Teile zerlegt' : 'Bauteile aus der Spezifikation'}</div>
      </div>
      <Callouts segs={segs} picked={picked} hovered={hovered} setHovered={setHovered} onPick={onPick} anchorOut={anchorOut} active={active} />
      <div className="draw-right">
        <div className="partbar" data-scroll>
          {PARTS.filter((x) => partCounts[x.id].total > 0).map((x) => (
            <button key={x.id} className={`pchip ${x.id === part ? 'on' : ''}`} onClick={() => setPart(x.id)}>
              {x.name}<span className="pchip-c">{partCounts[x.id].total}</span>
            </button>
          ))}
        </div>
        <AnimatePresence mode="wait">
          <motion.div key={p.id} initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.28 }}>
            <div className="part-head">
              <div>
                <div className="eyebrow">{p.id === 'device' ? p.note : `Bauteil ${p.n} · Zuordnung per Wortabgleich`}</div>
                <h2 className="part-name">{p.name}</h2>
              </div>
              <Donut by={pc.by} total={pc.total} />
            </div>
            <div className="legend">
              {Object.entries(pc.by).sort((a, b) => b[1] - a[1]).slice(0, 4).map(([reg, n]) => (
                <span key={reg} className="lg"><i style={{ background: regColor(reg) }} />{reg} <b>{n}</b></span>
              ))}
            </div>
          </motion.div>
        </AnimatePresence>
        <div className="reqlist" data-scroll>
          {list.slice(0, limit).map((r, i) => (
            <motion.button key={r.id} className="req" onClick={() => openReq(r.id)}
              initial={{ opacity: 0, x: 24 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: Math.min(i, 8) * 0.035 }}>
              <span className="req-page" style={{ '--c': regColor(r.reg) }}>{r.page}</span>
              <span className="req-body">
                <span className="req-ref">{r.reg} · § {r.para}</span>
                <span className="req-text">{r.text}</span>
              </span>
              <span className="req-go">→</span>
            </motion.button>
          ))}
          {list.length > limit && <button className="more" onClick={() => setLimit((l) => l + PAGE * 2)}>Weitere {list.length - limit} anzeigen</button>}
        </div>
      </div>
    </div>
  )
}

/* ---------------- Akt 3: Beleg ---------------- */
function ActEvidence({ req, active, anchorOut }) {
  const page = pageOf(req)
  const lines = hitsOf(req)
  const part = partById[req.part] || partById.device
  const n0 = useRef(), nLast = useRef(), hl = useRef(), wrap = useRef(), lp = useRef()
  const [paths, setPaths] = useState({ a: '', b: '', c: '' })

  useEffect(() => {
    if (!active) return
    let raf
    const loop = () => {
      const W = wrap.current?.getBoundingClientRect()
      const A = anchorOut.current.obj
      const b0 = n0.current?.getBoundingClientRect(), b1 = nLast.current?.getBoundingClientRect(), h = hl.current?.getBoundingClientRect()
      if (W && b0 && b1 && h) {
        const ox = W.left, oy = W.top
        let a = ''
        if (A) {
          const sx = A.x - ox, sy = A.y - oy, ex = b0.left + 10 - ox, ey = b0.top + 20 - oy
          a = `M ${sx} ${sy} C ${sx} ${sy - 140}, ${ex} ${ey + 140}, ${ex} ${ey}`
        }
        const L = lp.current?.getBoundingClientRect()
        const fx = b1.left + 22 - ox, fy = b1.top + 10 - oy
        const hx = h.left - ox - 4, hy = h.top + h.height / 2 - oy
        let b, c = ''
        if (L) {
          const ly = L.top + L.height / 2 - oy, rx = L.right - ox, tx = L.left + L.width / 2 - ox, tyy = L.top - oy
          b = `M ${fx} ${fy} C ${tx} ${fy}, ${tx} ${fy}, ${tx} ${tyy}`
          c = `M ${rx} ${ly} C ${(rx + hx) / 2} ${ly}, ${(rx + hx) / 2} ${hy}, ${hx} ${hy}`
        } else {
          const mx = (fx + hx) / 2
          b = `M ${fx} ${fy} C ${mx} ${fy}, ${mx} ${hy}, ${hx} ${hy}`
        }
        setPaths((p) => (p.a === a && p.b === b && p.c === c ? p : { a, b, c }))
      }
      raf = requestAnimationFrame(loop)
    }
    raf = requestAnimationFrame(loop)
    return () => cancelAnimationFrame(raf)
  }, [active, req.id, anchorOut])

  const first = lines[0]
  const ar = page ? page.w / page.h : 595 / 842
  return (
    <div className="ev-wrap" ref={wrap}>
      <div className="ev-left">
        <div className="eyebrow">Beleg · {req.id}</div>
        <blockquote className={`quote ${req.text.length > 260 ? 'long' : ''}`}>
          <span className="q-mark">“</span>{req.text}
        </blockquote>
        <div className="chain">
          {[
            [part.name, part.id === 'device' ? 'Gesamtgerät' : `Bauteil ${part.n}`, '#ff2a1f'],
            [req.reg, `Version ${req.version}`, regColor(req.reg)],
            [`§ ${req.para}`, 'Absatz'],
            [`Seite ${req.page}`, page?.of ? `von ${page.of} im PDF` : 'im Original-PDF'],
          ].map(([k, s, c], i, arr) => (
            <div key={i} className="node" ref={i === 0 ? n0 : i === arr.length - 1 ? nLast : undefined}>
              <span className="node-c" style={{ '--c': c || 'var(--ink)' }} />
              <span className="node-k">{k}</span>
              <span className="node-s">{s}</span>
            </div>
          ))}
        </div>
      </div>
      <div className="ev-right">
        <div className="sheet-stage" style={{ '--ar': ar }}>
          <div className="sheet">
            {page ? (
              <>
                <img src={page.src} alt={`${req.reg} Seite ${req.page}`} draggable={false} />
                {lines.map(([x, y, w, h], i) => (
                  <motion.span key={req.id + i} className="hl" ref={i === 0 ? hl : undefined}
                    style={{ left: `${x * 100}%`, top: `${y * 100}%`, width: `${w * 100}%`, height: `${h * 100}%` }}
                    initial={{ scaleX: 0 }} animate={{ scaleX: active ? 1 : 0 }} transition={{ delay: active ? 0.6 + i * 0.2 : 0, duration: 0.45, ease: [0.6, 0, 0.2, 1] }} />
                ))}
                {!lines.length && <span className="hl-miss" ref={hl}>Absatz {req.para} auf dieser Seite nicht exakt gefunden</span>}
              </>
            ) : (
              <div className="sheet-fallback">
                <div className="sf-head">{req.reg}, version {req.version} · page {req.page}</div>
                <p><b>{req.para}</b> <span className="hl-inline" ref={hl}>{req.text}</span></p>
                <div className="sf-note">Seite nicht eingebettet</div>
              </div>
            )}
          </div>
          {page && first && (
            <div className="loupe" ref={lp} style={{ backgroundImage: `url(${page.src})`, '--fx': first[0] + Math.min(first[2], 0.5) * 0.45, '--fy': first[1] + first[3] / 2 }} />
          )}
        </div>
      </div>
      <svg className="ev-svg">
        {[['a', 0.3, 0.9], ['b', 0.9, 0.9], ['c', 1.6, 0.5]].map(([k, d, dur]) => (
          <motion.path key={k + req.id} d={paths[k]} className="trace" initial={{ pathLength: 0 }} animate={{ pathLength: active ? 1 : 0 }} transition={{ duration: dur, delay: active ? d : 0 }} />
        ))}
      </svg>
    </div>
  )
}
