import { useEffect, useRef, useState } from 'react'
import { motion } from 'motion/react'
import { api, fmtSec, fmtDate, KIND } from './lib.js'

const STAGES = ['Fall lesen', 'Regelungen wählen', 'Anforderungen ziehen', 'Abgabe schreiben']

export default function Runs({ state, refresh, openRun, say, currentRun }) {
  const [tab, setTab] = useState('alle')
  // Laufende Prüfungen abfragen, bis sie fertig sind
  const running = state?.runs.filter((r) => r.state === 'running') || []
  useEffect(() => {
    if (!running.length) return
    const t = setInterval(refresh, 1500)
    return () => clearInterval(t)
  }, [running.length, refresh])
  const prev = useRef(new Set())
  useEffect(() => {
    const now = new Set(running.map((r) => r.id))
    for (const id of prev.current) if (!now.has(id)) {
      const r = state.runs.find((x) => x.id === id)
      if (r?.state === 'done') say(`Prüfung ${id} fertig: ${r.n} Anforderungen`)
      if (r?.state === 'failed') say(`Prüfung ${id} fehlgeschlagen, Log ansehen`, 'err')
    }
    prev.current = now
  }, [state]) // eslint-disable-line react-hooks/exhaustive-deps

  const runs = (state?.runs || []).filter((r) => tab === 'alle' || (tab === 'eigene' ? r.kind === 'lauf' : r.kind !== 'lauf'))
  return (
    <div className="runs">
      <section className="runs-left">
        <Composer state={state} refresh={refresh} say={say} />
        <div className="h-label">Fälle im Paket und eigene Uploads</div>
        <div className="cases">
          {(state?.cases || []).map((c) => <CaseCard key={c.id} c={c} state={state} refresh={refresh} say={say} />)}
        </div>
      </section>
      <section className="runs-right">
        <div className="runs-head">
          <h2 className="h2">Läufe</h2>
          <div className="mini-tabs">
            {[['alle', 'Alle'], ['eigene', 'Eigene'], ['messungen', 'Messungen']].map(([k, l]) => (
              <button key={k} className={tab === k ? 'on' : ''} onClick={() => setTab(k)}>{l}</button>
            ))}
          </div>
        </div>
        <div className="run-table">
          <div className="rt-head">
            <span />
            <span>Lauf</span>
            <span className="num">Regelungen</span>
            <span className="num">Anforderungen</span>
            <span className="num">Seiten</span>
            <span className="num">Dauer</span>
            <span />
          </div>
          {runs.map((r) => <RunRow key={r.id} r={r} openRun={openRun} current={r.id === currentRun} />)}
          {!runs.length && <div className="empty-row">Noch keine Läufe.</div>}
        </div>
      </section>
    </div>
  )
}

function RunRow({ r, openRun, current }) {
  const [log, setLog] = useState('')
  const [open, setOpen] = useState(false)
  useEffect(() => {
    if (r.state !== 'running' && !open) return
    let dead = false
    const load = () => api(`/api/status?id=${encodeURIComponent(r.id)}`).then((s) => !dead && setLog(s.log || '')).catch(() => {})
    load()
    const t = r.state === 'running' ? setInterval(load, 1500) : null
    return () => { dead = true; if (t) clearInterval(t) }
  }, [r.state, r.id, open])
  const p = r.state === 'running' ? Math.min(0.95, (r.elapsed || 0) / (r.typical || 120)) : 1
  const stage = Math.min(STAGES.length - 1, Math.floor(p * STAGES.length))
  const done = r.state === 'done'
  return (
    <div className={`rt-row ${r.state} ${current ? 'current' : ''}`}>
      <div className="rt-main" onClick={() => (done ? openRun(r.id) : setOpen((o) => !o))}>
        <Ring p={p} state={r.state} />
        <span className="rt-name">
          <span className="rt-case">{r.case || '—'}</span>
          <span className="rt-sub"><i className={`kind ${r.kind}`}>{KIND[r.kind]}</i>{r.id}{r.mode ? ` · ${r.mode}` : ''} · {fmtDate(r.started)}</span>
        </span>
        <span className="num">{done ? r.regs : '—'}</span>
        <span className="num strong">{done ? r.n : '—'}</span>
        <span className="num">{done ? r.pages : '—'}</span>
        <span className="num">{r.state === 'running' ? fmtSec(r.elapsed) : fmtSec(r.seconds)}</span>
        <span className="rt-act">
          {done && <button className="link" onClick={(e) => { e.stopPropagation(); window.open(`/present/${encodeURIComponent(r.id)}/`, '_blank') }}>Präsentation ↗</button>}
          {done && <button className="pill-btn">Öffnen</button>}
          {!done && <button className="link">{open || r.state === 'running' ? 'Log' : 'Log ▾'}</button>}
        </span>
      </div>
      {(r.state === 'running' || open) && (
        <div className="rt-detail">
          {r.state === 'running' && (
            <div className="stages">
              {STAGES.map((s, i) => <span key={s} className={i < stage ? 'past' : i === stage ? 'now' : ''}><i />{s}</span>)}
              <span className="eta">üblich ~{fmtSec(r.typical)}</span>
            </div>
          )}
          <pre className="log">{log.trim() || (r.state === 'running' ? 'läuft, noch keine Ausgabe …' : 'kein Log')}</pre>
        </div>
      )}
    </div>
  )
}

function Ring({ p, state }) {
  const R = 13, C = 2 * Math.PI * R
  const col = state === 'failed' || state === 'interrupted' ? 'var(--red)' : state === 'done' ? 'var(--ok)' : 'var(--ink)'
  return (
    <svg className={`ring ${state}`} width="34" height="34" viewBox="0 0 34 34">
      <circle cx="17" cy="17" r={R} fill="none" stroke="var(--hair)" strokeWidth="3" />
      <motion.circle cx="17" cy="17" r={R} fill="none" stroke={col} strokeWidth="3" strokeLinecap="round" transform="rotate(-90 17 17)"
        initial={false} animate={{ strokeDasharray: `${C * p} ${C}` }} transition={{ duration: 0.6 }} />
      {state === 'done' && <path d="M11.5 17.5 l3.5 3.5 l7 -8" fill="none" stroke="var(--ok)" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />}
      {(state === 'failed' || state === 'interrupted') && <path d="M13 13 l8 8 M21 13 l-8 8" stroke="var(--red)" strokeWidth="2.4" strokeLinecap="round" />}
    </svg>
  )
}

function CaseCard({ c, state, refresh, say }) {
  const start = async (mode) => {
    try { await api('/api/runs', { method: 'POST', body: { case: c.id, mode } }); say(`Prüfung von ${c.title} gestartet`); refresh() } catch (e) { say(e.message, 'err') }
  }
  return (
    <div className="case-card">
      <div className="cc-thumb">
        {c.hasDrawing ? <img src={`/api/drawing?case=${encodeURIComponent(c.id)}`} alt="" /> : <span className="cc-noimg">Nur Spezifikation</span>}
      </div>
      <div className="cc-body">
        <div className="cc-title">{c.title}</div>
        <div className="cc-meta">
          <span className={c.hasSpec ? 'on' : ''}>Spec</span>
          <span className={c.hasDrawing ? 'on' : ''}>Zeichnung</span>
          <span className="src">{c.source === 'upload' ? 'Upload' : 'Paket'}</span>
        </div>
        <div className="cc-actions">
          <button className="pill-btn dark" disabled={!state?.llm} title={state?.llm ? '' : 'Kein LLM-Key (.env.local)'} onClick={() => start('best')}>Prüfen</button>
          <button className="pill-btn" onClick={() => start('fast')}>Schnell, ohne KI</button>
        </div>
      </div>
    </div>
  )
}

function Composer({ state, refresh, say }) {
  const [spec, setSpec] = useState(null) // {name, text}
  const [img, setImg] = useState(null) // {name, b64}
  const [name, setName] = useState('')
  const [mode, setMode] = useState('best')
  const [drag, setDrag] = useState(false)
  const [busy, setBusy] = useState(false)
  const file = useRef()
  useEffect(() => { if (state && !state.llm) setMode('fast') }, [state])

  const take = async (files) => {
    for (const f of files) {
      if (/\.(md|txt)$/i.test(f.name)) {
        const text = await f.text()
        setSpec({ name: f.name, text })
        const t = text.match(/^#\s*(?:spec\s*:\s*)?(.+)$/im)
        if (t && !name) setName(t[1].trim())
      } else if (/^image\//.test(f.type)) {
        const b64 = await new Promise((res) => { const r = new FileReader(); r.onload = () => res(r.result); r.readAsDataURL(f) })
        setImg({ name: f.name, b64 })
        if (!name) setName(f.name.replace(/\.[^.]+$/, ''))
      } else say(`${f.name}: nur .md/.txt oder Bilder`, 'err')
    }
  }
  const go = async () => {
    setBusy(true)
    try {
      const c = await api('/api/cases', { method: 'POST', body: { name: name || 'eigener Fall', spec: spec?.text || '', image: img } })
      await api('/api/runs', { method: 'POST', body: { case: c.id, mode } })
      say(`Fall ${c.id} angelegt, Prüfung läuft`)
      setSpec(null); setImg(null); setName('')
      refresh()
    } catch (e) { say(e.message, 'err') } finally { setBusy(false) }
  }
  const ready = spec || img
  return (
    <div className="composer">
      <div className="h-label">Neue Prüfung</div>
      <div
        className={`drop ${drag ? 'drag' : ''} ${ready ? 'has' : ''}`}
        onDragOver={(e) => { e.preventDefault(); setDrag(true) }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => { e.preventDefault(); setDrag(false); take([...e.dataTransfer.files]) }}
        onClick={() => file.current.click()}
      >
        <svg className="drop-ring" viewBox="0 0 200 200"><circle cx="100" cy="100" r="92" /></svg>
        {img ? <img className="drop-img" src={img.b64} alt="" /> : null}
        <div className="drop-text">
          {ready ? (
            <>
              <b>{[spec && 'Spezifikation', img && 'Zeichnung'].filter(Boolean).join(' + ')}</b>
              <span>{[spec?.name, img?.name].filter(Boolean).join(' · ')}</span>
            </>
          ) : (
            <>
              <b>Spezifikation und/oder Zeichnung</b>
              <span>hierher ziehen oder klicken · .md .txt .png .jpg</span>
            </>
          )}
        </div>
        <input ref={file} type="file" multiple accept=".md,.txt,image/*" hidden onChange={(e) => take([...e.target.files])} />
      </div>
      <div className="comp-row">
        <input className="field" value={name} onChange={(e) => setName(e.target.value)} placeholder="Name des Falls, z. B. Frontstoßfänger" />
      </div>
      <div className="modes">
        <button className={mode === 'best' ? 'on' : ''} disabled={!state?.llm} onClick={() => setMode('best')}>
          <b>Bestmarke</b><span>{state?.llm ? 'LLM-Auswahl + Extraktion, ~4 min' : 'braucht LLM-Key (.env.local)'}</span>
        </button>
        <button className={mode === 'fast' ? 'on' : ''} onClick={() => setMode('fast')}>
          <b>Schnell</b><span>ohne KI (Baseline B0), ~20 s</span>
        </button>
      </div>
      <button className="primary wide" disabled={!ready || busy} onClick={go}>{busy ? 'Startet …' : 'Prüfung starten'}</button>
    </div>
  )
}
