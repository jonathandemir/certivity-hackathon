import { useEffect, useRef, useState } from 'react'
import { api } from './lib.js'

export function Composer({ state, refresh, say, done }) {
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
      } else say(`${f.name}: only .md/.txt or images`, 'err')
    }
  }
  const go = async () => {
    setBusy(true)
    try {
      const c = await api('/api/cases', { method: 'POST', body: { name: name || 'my product', spec: spec?.text || '', image: img } })
      await api('/api/runs', { method: 'POST', body: { case: c.id, mode } })
      say(`Product ${c.id} created, check running`)
      setSpec(null); setImg(null); setName('')
      await refresh()
      done?.(c.id)
    } catch (e) { say(e.message, 'err') } finally { setBusy(false) }
  }
  const ready = spec || img
  return (
    <div className="composer">
      <div className="h-label">Check your own product</div>
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
              <b>{[spec && 'Spec', img && 'Drawing'].filter(Boolean).join(' + ')}</b>
              <span>{[spec?.name, img?.name].filter(Boolean).join(' · ')}</span>
            </>
          ) : (
            <>
              <b>Spec and/or drawing</b>
              <span>drop here or click · .md .txt .png .jpg</span>
            </>
          )}
        </div>
        <input ref={file} type="file" multiple accept=".md,.txt,image/*" hidden onChange={(e) => take([...e.target.files])} />
      </div>
      <div className="comp-row">
        <input className="field" value={name} onChange={(e) => setName(e.target.value)} placeholder="Product name, e.g. front bumper" />
      </div>
      <div className="modes">
        <button className={mode === 'best' ? 'on' : ''} disabled={!state?.llm} onClick={() => setMode('best')}>
          <b>Best</b><span>{state?.llm ? 'AI selection + extraction, ~4 min' : 'needs an LLM key (.env.local)'}</span>
        </button>
        <button className={mode === 'fast' ? 'on' : ''} onClick={() => setMode('fast')}>
          <b>Fast</b><span>no AI (baseline B0), ~20 s</span>
        </button>
      </div>
      <button className="primary wide" disabled={!ready || busy} onClick={go}>{busy ? 'Starting …' : 'Start check'}</button>
    </div>
  )
}
