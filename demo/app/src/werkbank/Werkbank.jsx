import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'motion/react'
import { api, makeColors, readHash, writeHash } from './lib.js'
import Reqs from './Reqs.jsx'
import Selection from './Selection.jsx'
import Compare from './Compare.jsx'
import { ProductList, ProductHead, SelectionOnly, NewProduct } from './Products.jsx'

// Ein Produkt, ein Ergebnis: links jedes Produkt genau einmal, rechts sein bestes Ergebnis in vier Ansichten
const VIEWS = [
  ['ueberblick', 'Overview', true],
  ['anforderungen', 'Requirements', true],
  ['regelungen', 'Regulations', false],
  ['aenderungen', 'Changes', false],
]

export default function Werkbank() {
  const init = useMemo(readHash, [])
  const [view, setView] = useState(init.view)
  const [state, setState] = useState(null)
  const [pid, setPid] = useState(init.product)
  const [run, setRun] = useState(null)
  const [reqId, setReqId] = useState(init.req)
  const [filters, setFilters] = useState({ reg: null, part: null, status: null, q: '' })
  const [palette, setPalette] = useState(false)
  const [adding, setAdding] = useState(false)
  const [toast, setToast] = useState(null)

  const say = useCallback((msg, kind = 'ok') => { setToast({ msg, kind, k: Date.now() }) }, [])
  useEffect(() => { if (!toast) return; const t = setTimeout(() => setToast(null), 2600); return () => clearTimeout(t) }, [toast])

  const refresh = useCallback(async () => {
    try { const s = await api('/api/state'); setState(s); return s } catch (e) { say(`Server not reachable: ${e.message}`, 'err') }
  }, [say])
  useEffect(() => { refresh() }, [refresh])

  const products = state?.products || []
  const product = products.find((p) => p.id === pid)
  const runId = product?.best?.kind === 'run' ? product.best.runId : null
  const full = !!runId

  // Start: erstes Produkt mit vollem Lauf (die Certivity-Leuchte)
  useEffect(() => {
    if (!state || product) return
    const p = products.find((x) => x.best?.kind === 'run') || products[0]
    if (p) setPid(p.id)
  }, [state, product, products])

  // Ansichten, die einen vollen Lauf brauchen, fallen bei reinen Auswahl-Ergebnissen auf „Regelungen“ zurück
  useEffect(() => { if (product && !full && VIEWS.find((v) => v[0] === view)?.[2]) setView('regelungen') }, [product, full, view])

  useEffect(() => {
    setRun(null)
    if (!runId) return
    let dead = false
    api(`/api/run?id=${encodeURIComponent(runId)}`).then((d) => { if (!dead) setRun(d) }).catch((e) => say(e.message, 'err'))
    setFilters({ reg: null, part: null, status: null, q: '' })
    return () => { dead = true }
  }, [runId, say])

  useEffect(() => writeHash({ view, product: pid, req: reqId }), [view, pid, reqId])

  // Laufende Prüfungen abfragen; ist eine fertig, ist ihr Ergebnis (falls besser) sofort das neue beste
  const live = products.filter((p) => p.running).map((p) => p.id).join(',')
  const prevLive = useRef('')
  useEffect(() => {
    const before = prevLive.current.split(',').filter(Boolean)
    prevLive.current = live
    for (const id of before) if (!live.split(',').includes(id)) {
      const p = products.find((x) => x.id === id)
      say(p?.best?.kind === 'run' ? `${p.title}: check done` : `${p?.title || id}: check ended, log in out/runs`, p?.best?.kind === 'run' ? 'ok' : 'err')
    }
    if (!live) return
    const t = setInterval(refresh, 2000)
    return () => clearInterval(t)
  }, [live]) // eslint-disable-line react-hooks/exhaustive-deps

  const color = useMemo(() => (run ? makeColors(run.regs) : () => '#999'), [run])
  const setReview = useCallback(async (ids, patch) => {
    if (!run) return
    const list = Array.isArray(ids) ? ids : [ids]
    setRun((r) => {
      const review = { ...r.review }
      for (const id of list) {
        const cur = { ...(review[id] || {}), ...patch }
        if ((cur.status || 'open') === 'open' && !cur.note) delete review[id]
        else review[id] = cur
      }
      return { ...r, review }
    })
    try { await api('/api/review', { method: 'POST', body: { run: run.runId, ids: list, ...patch } }) } catch (e) { say(e.message, 'err') }
  }, [run, say])

  const pick = useCallback((id) => { setPid(id); setReqId('') }, [])
  const present = useCallback(() => { if (runId) window.open(`/present/${encodeURIComponent(runId)}/`, '_blank') }, [runId])
  const start = useCallback(async (mode) => {
    try { await api('/api/runs', { method: 'POST', body: { case: pid, mode } }); say(`Check of ${product?.title} started`); refresh() } catch (e) { say(e.message, 'err') }
  }, [pid, product, refresh, say])

  useEffect(() => {
    const key = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); setPalette((p) => !p) }
      if (e.target.closest('input, textarea')) return
      if (e.altKey || e.metaKey || e.ctrlKey) return
      const i = ['1', '2', '3', '4'].indexOf(e.key)
      if (i >= 0 && (full || !VIEWS[i][2])) setView(VIEWS[i][0])
      if (e.key === 'p' && runId) present()
    }
    window.addEventListener('keydown', key)
    return () => window.removeEventListener('keydown', key)
  }, [present, runId, full])

  // Aus dem eingebetteten Überblick: „In der Werkbank prüfen“ öffnet die Anforderung samt PDF-Beleg
  useEffect(() => {
    const msg = (e) => {
      if (e.origin !== location.origin || e.data?.type !== 'certreq:req') return
      setReqId(e.data.id); setView('anforderungen')
    }
    window.addEventListener('message', msg)
    return () => window.removeEventListener('message', msg)
  }, [])
  const openReq = useCallback((id) => { setReqId(id); setFilters({ reg: null, part: null, status: null, q: '' }); setView('anforderungen') }, [])

  return (
    <div className="wb">
      <header className="wb-hdr">
        <div className="brand"><span className="brand-dot" />BarelyLegal</div>
        <nav className="seg">
          {VIEWS.map(([k, label, needsRun], i) => (
            <button key={k} className={`seg-b ${view === k ? 'on' : ''}`} disabled={needsRun && !full} title={needsRun && !full ? 'Only after a full check' : ''} onClick={() => setView(k)}>
              {view === k && <motion.span layoutId="segpill" className="seg-pill" transition={{ type: 'spring', stiffness: 400, damping: 34 }} />}
              <span className="seg-k">{i + 1}</span>{label}
            </button>
          ))}
        </nav>
        <div className="hdr-actions">
          <button className="ghost" onClick={() => setPalette(true)} title="Search product, view or requirement"><span>Search</span><kbd>⌘K</kbd></button>
        </div>
      </header>

      <div className="wb-body">
        <ProductList products={products} current={pid} pick={pick} onNew={() => setAdding(true)} />
        <main className="wb-main">
          <ProductHead p={product} llm={state?.llm} start={start} present={present} />
          <div className="wb-view">
            {!state ? <Loading /> : !product ? <div className="loading">No product selected.</div> : (
              <>
                {view === 'ueberblick' && full && <Overview runId={runId} />}
                {view === 'anforderungen' && full && (run ? <Reqs run={run} color={color} filters={filters} setFilters={setFilters} reqId={reqId} setReqId={setReqId} setReview={setReview} say={say} /> : <Loading />)}
                {view === 'regelungen' && (full ? (run ? <Selection run={run} color={color} goReqs={(reg) => { setFilters((f) => ({ ...f, reg })); setView('anforderungen') }} /> : <Loading />) : <SelectionOnly pid={pid} say={say} />)}
                {view === 'aenderungen' && <Compare state={state} run={run} say={say} openReq={openReq} />}
              </>
            )}
          </div>
        </main>
      </div>

      <AnimatePresence>{adding && <NewProduct state={state} refresh={refresh} say={say} close={(id) => { setAdding(false); if (typeof id === 'string') pick(id) }} />}</AnimatePresence>
      <AnimatePresence>{palette && <Palette products={products} run={run} close={() => setPalette(false)} setView={(v) => (full || !VIEWS.find((x) => x[0] === v)?.[2]) && setView(v)} pick={pick} setReqId={(id) => { setReqId(id); setView('anforderungen') }} present={present} />}</AnimatePresence>
      <AnimatePresence>
        {toast && (
          <motion.div key={toast.k} className={`toast ${toast.kind}`} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 20 }}>
            {toast.msg}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

// Überblick = die 3D-Präsentation des Laufs, eingebettet (eigenes Bundle mit three.js, daher als Rahmen)
function Overview({ runId }) {
  const [ready, setReady] = useState(false)
  return (
    <div className="ov">
      {!ready && <div className="loading ov-load"><span className="spin" />Building overview …</div>}
      <iframe key={runId} title="Overview" className={`ov-frame ${ready ? 'on' : ''}`} onLoad={() => setReady(true)}
        src={`/present/${encodeURIComponent(runId)}/?embed=1`} />
    </div>
  )
}

function Loading() {
  return <div className="loading"><span className="spin" />Loading run …</div>
}

function Palette({ products, run, close, setView, pick, setReqId, present }) {
  const [q, setQ] = useState('')
  const [i, setI] = useState(0)
  const inp = useRef()
  useEffect(() => inp.current?.focus(), [])
  const items = useMemo(() => {
    const s = q.trim().toLowerCase()
    const m = (t) => !s || t.toLowerCase().includes(s)
    const out = []
    for (const [k, l] of VIEWS) if (m(l)) out.push({ g: 'View', label: l, run: () => setView(k) })
    if (run) {
      out.push(...[
        { g: 'Action', label: 'Export submission (JSON, without rejected)', run: () => window.open(`/api/export?run=${encodeURIComponent(run.runId)}&fmt=json`) },
        { g: 'Action', label: 'Export table (CSV)', run: () => window.open(`/api/export?run=${encodeURIComponent(run.runId)}&fmt=csv`) },
        { g: 'Action', label: 'Open 3D presentation', run: present },
      ].filter((x) => m(x.label)))
      if (s.length >= 2) {
        const hits = run.reqs.filter((r) => `${r.id} ${r.reg} ${r.para} ${r.text}`.toLowerCase().includes(s)).slice(0, 8)
        out.push(...hits.map((r) => ({ g: 'Requirement', label: `${r.id} · ${r.reg} § ${r.para}`, sub: r.text, run: () => setReqId(r.id) })))
      }
    }
    for (const p of products.filter((p) => m(`${p.title} ${p.id}`)).slice(0, 8))
      out.push({ g: 'Product', label: p.title, sub: p.groupLabel, run: () => pick(p.id) })
    return out
  }, [q, products, run, setView, pick, setReqId, present])
  useEffect(() => setI(0), [q])
  const go = (it) => { it.run(); close() }
  return (
    <motion.div className="pal-bg" onMouseDown={close} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
      <motion.div className="pal" onMouseDown={(e) => e.stopPropagation()} initial={{ y: -12, scale: 0.98 }} animate={{ y: 0, scale: 1 }} exit={{ y: -12, scale: 0.98 }}>
        <input ref={inp} value={q} onChange={(e) => setQ(e.target.value)} placeholder="Product, view, requirement (ID, paragraph, text) …"
          onKeyDown={(e) => {
            if (e.key === 'Escape') close()
            if (e.key === 'ArrowDown') { e.preventDefault(); setI((x) => Math.min(items.length - 1, x + 1)) }
            if (e.key === 'ArrowUp') { e.preventDefault(); setI((x) => Math.max(0, x - 1)) }
            if (e.key === 'Enter' && items[i]) go(items[i])
          }} />
        <div className="pal-list">
          {items.map((it, k) => (
            <button key={k} className={`pal-row ${k === i ? 'on' : ''}`} onMouseEnter={() => setI(k)} onClick={() => go(it)}>
              <span className="pal-g">{it.g}</span>
              <span className="pal-l">{it.label}{it.sub && <span className="pal-s">{it.sub}</span>}</span>
            </button>
          ))}
          {!items.length && <div className="pal-empty">Nothing found.</div>}
        </div>
      </motion.div>
    </motion.div>
  )
}
