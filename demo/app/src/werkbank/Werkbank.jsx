import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'motion/react'
import { api, makeColors, readHash, writeHash, KIND, fmtDate } from './lib.js'
import Runs from './Runs.jsx'
import Reqs from './Reqs.jsx'
import Selection from './Selection.jsx'
import Compare from './Compare.jsx'

const VIEWS = [
  ['pruefungen', 'Prüfungen'],
  ['ueberblick', 'Überblick'],
  ['anforderungen', 'Anforderungen'],
  ['auswahl', 'Auswahl'],
  ['vergleich', 'Änderungen'],
]

export default function Werkbank() {
  const init = useMemo(readHash, [])
  const [view, setView] = useState(init.view)
  const [state, setState] = useState(null)
  const [runId, setRunId] = useState(init.run)
  const [run, setRun] = useState(null)
  const [reqId, setReqId] = useState(init.req)
  const [filters, setFilters] = useState({ reg: null, part: null, status: null, q: '' })
  const [palette, setPalette] = useState(false)
  const [toast, setToast] = useState(null)
  const [switcher, setSwitcher] = useState(false)

  const say = useCallback((msg, kind = 'ok') => { setToast({ msg, kind, k: Date.now() }) }, [])
  useEffect(() => { if (!toast) return; const t = setTimeout(() => setToast(null), 2600); return () => clearTimeout(t) }, [toast])

  const refresh = useCallback(async () => {
    try { setState(await api('/api/state')) } catch (e) { say(`Server nicht erreichbar: ${e.message}`, 'err') }
  }, [say])
  useEffect(() => { refresh() }, [refresh])

  // Standardlauf: jüngster eigener fertiger Lauf, sonst beste Messung (E016-a), sonst der jüngste
  useEffect(() => {
    if (!state || runId) return
    const done = state.runs.filter((r) => r.state === 'done')
    const pick = done.find((r) => r.kind === 'lauf') || done.find((r) => r.id === 'E016-a') || done[0]
    if (pick) setRunId(pick.id)
  }, [state, runId])

  useEffect(() => {
    if (!runId) return
    let dead = false
    setRun(null)
    api(`/api/run?id=${encodeURIComponent(runId)}`).then((d) => { if (!dead) setRun(d) }).catch((e) => say(e.message, 'err'))
    setFilters({ reg: null, part: null, status: null, q: '' })
    return () => { dead = true }
  }, [runId, say])

  useEffect(() => writeHash({ view, run: runId, req: reqId }), [view, runId, reqId])

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

  const openRun = useCallback((id, v = 'anforderungen') => { setRunId(id); setReqId(''); setView(v); setSwitcher(false) }, [])
  const present = useCallback(() => { if (runId) window.open(`/present/${encodeURIComponent(runId)}/`, '_blank') }, [runId])

  useEffect(() => {
    const key = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); setPalette((p) => !p) }
      if (e.target.closest('input, textarea')) return
      if (e.altKey || e.metaKey || e.ctrlKey) return
      const i = ['1', '2', '3', '4', '5'].indexOf(e.key)
      if (i >= 0) setView(VIEWS[i][0])
      if (e.key === 'p' && runId) present()
    }
    window.addEventListener('keydown', key)
    return () => window.removeEventListener('keydown', key)
  }, [present, runId])

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

  const runMeta = state?.runs.find((r) => r.id === runId)
  return (
    <div className="wb">
      <header className="wb-hdr">
        <div className="brand"><span className="brand-dot" />BarelyLegal<span className="brand-sub">Werkbank</span></div>
        <div className="run-pill-wrap">
          <button className="run-pill" onClick={() => setSwitcher((s) => !s)} disabled={!state}>
            <span className="rp-case">{run?.case.title || runMeta?.case || 'Kein Lauf'}</span>
            <span className="rp-id">{runId ? `${KIND[runMeta?.kind] || 'Lauf'} ${runId}` : 'wählen'}</span>
            <span className="rp-caret">▾</span>
          </button>
          <AnimatePresence>
            {switcher && state && (
              <motion.div className="pop" initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }}>
                {state.runs.filter((r) => r.state === 'done').slice(0, 24).map((r) => (
                  <button key={r.id} className={`pop-row ${r.id === runId ? 'on' : ''}`} onClick={() => openRun(r.id, view === 'pruefungen' ? 'anforderungen' : view)}>
                    <span className="pr-kind">{KIND[r.kind]}</span>
                    <span className="pr-id">{r.id}</span>
                    <span className="pr-n">{r.n} Anf. · {r.regs} Reg.</span>
                    <span className="pr-date">{fmtDate(r.started)}</span>
                  </button>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
        <nav className="seg">
          {VIEWS.map(([k, label], i) => (
            <button key={k} className={`seg-b ${view === k ? 'on' : ''}`} onClick={() => setView(k)}>
              {view === k && <motion.span layoutId="segpill" className="seg-pill" transition={{ type: 'spring', stiffness: 400, damping: 34 }} />}
              <span className="seg-k">{i + 1}</span>{label}
            </button>
          ))}
        </nav>
        <div className="hdr-actions">
          <button className="ghost" onClick={() => setPalette(true)} title="Ansicht, Lauf oder Anforderung suchen"><span>Suchen</span><kbd>⌘K</kbd></button>
          <button className="ghost" onClick={present} disabled={!runId} title="Überblick als Vollbild für den Beamer (P)">Vollbild ↗</button>
          <button className="primary" onClick={() => setView('pruefungen')}>Neue Prüfung</button>
        </div>
      </header>

      <main className="wb-main" onClick={() => switcher && setSwitcher(false)}>
        {view === 'pruefungen' && <Runs state={state} refresh={refresh} openRun={openRun} say={say} currentRun={runId} />}
        {view === 'anforderungen' && (run ? <Reqs run={run} color={color} filters={filters} setFilters={setFilters} reqId={reqId} setReqId={setReqId} setReview={setReview} say={say} /> : <Loading />)}
        {view === 'ueberblick' && (runId ? <Overview runId={runId} /> : <Loading />)}
        {view === 'auswahl' && (run ? <Selection run={run} color={color} goReqs={(reg) => { setFilters((f) => ({ ...f, reg })); setView('anforderungen') }} /> : <Loading />)}
        {view === 'vergleich' && <Compare state={state} run={run} say={say} openReq={openReq} />}
      </main>

      <AnimatePresence>{palette && <Palette state={state} run={run} close={() => setPalette(false)} setView={setView} openRun={openRun} setReqId={(id) => { setReqId(id); setView('anforderungen') }} present={present} />}</AnimatePresence>
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
      {!ready && <div className="loading ov-load"><span className="spin" />Baue Überblick …</div>}
      <iframe key={runId} title="Überblick" className={`ov-frame ${ready ? 'on' : ''}`} onLoad={() => setReady(true)}
        src={`/present/${encodeURIComponent(runId)}/?embed=1`} />
    </div>
  )
}

function Loading() {
  return <div className="loading"><span className="spin" />Lade Lauf …</div>
}

function Palette({ state, run, close, setView, openRun, setReqId, present }) {
  const [q, setQ] = useState('')
  const [i, setI] = useState(0)
  const inp = useRef()
  useEffect(() => inp.current?.focus(), [])
  const items = useMemo(() => {
    const s = q.trim().toLowerCase()
    const m = (t) => !s || t.toLowerCase().includes(s)
    const out = []
    for (const [k, l] of VIEWS) if (m(l)) out.push({ g: 'Ansicht', label: l, run: () => setView(k) })
    if (run) {
      out.push(...[
        { g: 'Aktion', label: 'Abgabe exportieren (JSON, ohne Verworfene)', run: () => window.open(`/api/export?run=${encodeURIComponent(run.runId)}&fmt=json`) },
        { g: 'Aktion', label: 'Tabelle exportieren (CSV)', run: () => window.open(`/api/export?run=${encodeURIComponent(run.runId)}&fmt=csv`) },
        { g: 'Aktion', label: '3D-Präsentation öffnen', run: present },
      ].filter((x) => m(x.label)))
      if (s.length >= 2) {
        const hits = run.reqs.filter((r) => `${r.id} ${r.reg} ${r.para} ${r.text}`.toLowerCase().includes(s)).slice(0, 8)
        out.push(...hits.map((r) => ({ g: 'Anforderung', label: `${r.id} · ${r.reg} § ${r.para}`, sub: r.text, run: () => setReqId(r.id) })))
      }
    }
    for (const r of (state?.runs || []).filter((r) => r.state === 'done' && m(`${r.id} ${r.case} ${KIND[r.kind]}`)).slice(0, 6))
      out.push({ g: 'Lauf', label: `${KIND[r.kind]} ${r.id}`, sub: `${r.case} · ${r.n} Anforderungen`, run: () => openRun(r.id) })
    return out
  }, [q, state, run, setView, openRun, setReqId, present])
  useEffect(() => setI(0), [q])
  const go = (it) => { it.run(); close() }
  return (
    <motion.div className="pal-bg" onMouseDown={close} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
      <motion.div className="pal" onMouseDown={(e) => e.stopPropagation()} initial={{ y: -12, scale: 0.98 }} animate={{ y: 0, scale: 1 }} exit={{ y: -12, scale: 0.98 }}>
        <input ref={inp} value={q} onChange={(e) => setQ(e.target.value)} placeholder="Ansicht, Lauf, Anforderung (ID, Absatz, Text) …"
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
          {!items.length && <div className="pal-empty">Nichts gefunden.</div>}
        </div>
      </motion.div>
    </motion.div>
  )
}
