// Zerlegt eine Explosionszeichnung (Strichbild) in ihre Teile: In Explosionsdarstellungen sind die Teile
// durch Weißraum getrennt, also reicht eine Zusammenhangsanalyse auf dem leicht verdickten Strichbild.
// Ergebnis je Teil: eine Canvas mit dem Strich als Alpha (weiß, wird im 3D-Material eingefärbt) und die Lage im Bild.

export function loadImage(src) {
  return new Promise((res, rej) => {
    const im = new Image()
    im.onload = () => res(im)
    im.onerror = rej
    im.src = src
  })
}

export function segmentDrawing(img, { maxParts = 8, minShare = 0.015 } = {}) {
  const W = img.naturalWidth, H = img.naturalHeight
  const full = document.createElement('canvas')
  full.width = W; full.height = H
  const fctx = full.getContext('2d', { willReadFrequently: true })
  fctx.fillStyle = '#fff'; fctx.fillRect(0, 0, W, H)
  fctx.drawImage(img, 0, 0)
  const px = fctx.getImageData(0, 0, W, H).data

  // Arbeitsraster: lange Kante ~600 px
  const s = Math.min(1, 600 / Math.max(W, H))
  const w = Math.max(1, Math.round(W * s)), h = Math.max(1, Math.round(H * s))
  const ink = new Uint8Array(w * h)
  for (let y = 0; y < H; y++) {
    const ly = Math.min(h - 1, Math.floor(y * s))
    for (let x = 0; x < W; x++) {
      const i = (y * W + x) * 4
      const g = 0.299 * px[i] + 0.587 * px[i + 1] + 0.114 * px[i + 2]
      if (g < 170) ink[ly * w + Math.min(w - 1, Math.floor(x * s))] = 1
    }
  }
  // Verdicken (Box-Maximum, separierbar), damit Striche eines Teils zusammenhängen
  const r = Math.max(2, Math.round(0.007 * Math.max(w, h)))
  const tmp = new Uint8Array(w * h), dil = new Uint8Array(w * h)
  for (let y = 0; y < h; y++) {
    let run = 0
    for (let x = 0; x < w + r; x++) {
      if (x < w && ink[y * w + x]) run = 2 * r + 1
      if (run > 0) { const xx = x - r; if (xx >= 0 && xx < w) tmp[y * w + xx] = 1; run-- }
    }
  }
  for (let x = 0; x < w; x++) {
    let run = 0
    for (let y = 0; y < h + r; y++) {
      if (y < h && tmp[y * w + x]) run = 2 * r + 1
      if (run > 0) { const yy = y - r; if (yy >= 0 && yy < h) dil[yy * w + x] = 1; run-- }
    }
  }
  // Komponenten markieren
  const lab = new Int32Array(w * h)
  const comps = []
  const stack = new Int32Array(w * h)
  for (let i0 = 0; i0 < w * h; i0++) {
    if (!dil[i0] || lab[i0]) continue
    const id = comps.length + 1
    let sp = 0, inkN = 0, x0 = w, y0 = h, x1 = 0, y1 = 0
    stack[sp++] = i0; lab[i0] = id
    while (sp) {
      const i = stack[--sp], x = i % w, y = (i / w) | 0
      if (ink[i]) inkN++
      if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y
      if (x > 0 && dil[i - 1] && !lab[i - 1]) { lab[i - 1] = id; stack[sp++] = i - 1 }
      if (x < w - 1 && dil[i + 1] && !lab[i + 1]) { lab[i + 1] = id; stack[sp++] = i + 1 }
      if (y > 0 && dil[i - w] && !lab[i - w]) { lab[i - w] = id; stack[sp++] = i - w }
      if (y < h - 1 && dil[i + w] && !lab[i + w]) { lab[i + w] = id; stack[sp++] = i + w }
    }
    comps.push({ id, ink: inkN, x0, y0, x1, y1 })
  }
  const total = comps.reduce((a, c) => a + c.ink, 0) || 1
  const kept = comps.filter((c) => c.ink / total >= minShare).sort((a, b) => b.ink - a.ink).slice(0, maxParts)
  if (!kept.length) return []
  // Kleine Reste dem Teil zuschlagen, dessen Rahmen sie enthält (sonst dem nächstgelegenen)
  const owner = new Int32Array(comps.length + 1).fill(-1)
  kept.forEach((c, k) => (owner[c.id] = k))
  for (const c of comps) {
    if (owner[c.id] >= 0) continue
    const cx = (c.x0 + c.x1) / 2, cy = (c.y0 + c.y1) / 2
    let best = -1, bd = Infinity
    kept.forEach((k, j) => {
      const inside = cx >= k.x0 && cx <= k.x1 && cy >= k.y0 && cy <= k.y1
      const kx = (k.x0 + k.x1) / 2, ky = (k.y0 + k.y1) / 2
      const d = (inside ? 0 : 1e6) + (kx - cx) ** 2 + (ky - cy) ** 2
      if (d < bd) { bd = d; best = j }
    })
    owner[c.id] = best
  }
  // Rahmen je Teil in voller Auflösung, dann Strich als Alpha in eigene Canvas schreiben
  const parts = kept.map(() => ({ x0: W, y0: H, x1: 0, y1: 0 }))
  for (const c of comps) {
    const p = parts[owner[c.id]]
    p.x0 = Math.min(p.x0, c.x0 / s); p.y0 = Math.min(p.y0, c.y0 / s); p.x1 = Math.max(p.x1, (c.x1 + 1) / s); p.y1 = Math.max(p.y1, (c.y1 + 1) / s)
  }
  const pad = Math.round(0.01 * Math.max(W, H))
  const outs = parts.map((p) => {
    const x0 = Math.max(0, Math.floor(p.x0) - pad), y0 = Math.max(0, Math.floor(p.y0) - pad)
    const x1 = Math.min(W, Math.ceil(p.x1) + pad), y1 = Math.min(H, Math.ceil(p.y1) + pad)
    const cw = Math.max(1, x1 - x0), ch = Math.max(1, y1 - y0)
    return { x0, y0, cw, ch, data: new ImageData(cw, ch) }
  })
  for (let y = 0; y < H; y++) {
    const ly = Math.min(h - 1, Math.floor(y * s))
    for (let x = 0; x < W; x++) {
      const i = (y * W + x) * 4
      const g = 0.299 * px[i] + 0.587 * px[i + 1] + 0.114 * px[i + 2]
      if (g > 235) continue
      const l = lab[ly * w + Math.min(w - 1, Math.floor(x * s))]
      if (!l) continue
      const k = owner[l]
      const o = outs[k]
      const xx = x - o.x0, yy = y - o.y0
      if (xx < 0 || yy < 0 || xx >= o.cw || yy >= o.ch) continue
      const j = (yy * o.cw + xx) * 4
      o.data.data[j] = o.data.data[j + 1] = o.data.data[j + 2] = 255
      o.data.data[j + 3] = Math.min(255, (255 - g) * 1.25)
    }
  }
  // Striche leicht verdicken, damit sie verkleinert im Raum nicht verblassen
  const rr = Math.max(1, Math.round(Math.max(W, H) / 900))
  for (const o of outs) thicken(o.data, rr)
  const res = outs.map((o) => {
    const c = document.createElement('canvas')
    c.width = o.cw; c.height = o.ch
    c.getContext('2d').putImageData(o.data, 0, 0)
    return { canvas: c, x: o.x0, y: o.y0, w: o.cw, h: o.ch }
  })
  // Lesereihenfolge: oben nach unten, dann links nach rechts
  res.sort((a, b) => (Math.abs(a.y - b.y) > 0.15 * H ? a.y - b.y : a.x - b.x))
  return res.map((r, i) => ({ ...r, n: i + 1, imgW: W, imgH: H }))
}

// Ohne Zeichnung: je Bauteil eine Karte mit dem Namen (Text als Alpha, Farbe kommt aus dem Material)
export function textCards(names) {
  const cols = names.length > 3 ? 2 : 1
  return names.map((name, i) => {
    const c = document.createElement('canvas')
    c.width = 1200; c.height = 620
    const g = c.getContext('2d')
    g.fillStyle = '#fff'
    g.textBaseline = 'middle'
    let size = 132
    g.font = `640 ${size}px "Schibsted Grotesk Variable", sans-serif`
    const words = name.split(' ')
    let line = '', lines = []
    for (const w of words) { const t = line ? line + ' ' + w : w; if (g.measureText(t).width > 1060 && line) { lines.push(line); line = w } else line = t }
    lines.push(line)
    lines = lines.slice(0, 3)
    lines.forEach((l, k) => g.fillText(l, 70, 350 + (k - (lines.length - 1) / 2) * size * 1.02))
    g.font = '600 52px "Schibsted Grotesk Variable", sans-serif'
    g.fillText(String(i + 1).padStart(2, '0'), 70, 80)
    const col = i % cols, row = Math.floor(i / cols)
    const rows = Math.ceil(names.length / cols)
    return { canvas: c, x: col * 1320, y: row * 740, w: 1200, h: 620, n: i + 1, imgW: cols * 1320 - 120, imgH: rows * 740 - 120, text: true }
  })
}

// Striche um r Pixel verbreitern (Maximum über das Alpha, separierbar)
function thicken(img, r) {
  const { width: w, height: h, data } = img
  const a = new Uint8ClampedArray(w * h), b = new Uint8ClampedArray(w * h)
  for (let i = 0; i < w * h; i++) a[i] = data[i * 4 + 3]
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    let m = 0
    for (let d = -r; d <= r; d++) { const xx = x + d; if (xx >= 0 && xx < w) { const v = a[y * w + xx]; if (v > m) m = v } }
    b[y * w + x] = m
  }
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    let m = 0
    for (let d = -r; d <= r; d++) { const yy = y + d; if (yy >= 0 && yy < h) { const v = b[yy * w + x]; if (v > m) m = v } }
    const i = (y * w + x) * 4
    data[i] = data[i + 1] = data[i + 2] = 255
    data[i + 3] = m
  }
}
