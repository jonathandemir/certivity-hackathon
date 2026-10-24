// 3D-Heckleuchte, Maß für Maß aus der Explosionszeichnung des Falls dev-rear-lamp (exploded_view.png, 1714 × 1857 px)
// nachgebaut: gleiche Umrisse, gleiche Lage der Bauteile. Dadurch passt die technische Skizze zum Modell; im Akt
// „Zeichnung" wird das Modell selbst als Strichzeichnung (Kanten) gezeigt. Bauteilnamen wie in Certivitys Brief:
// Schlusslicht = Lichtleiter oben, Bremslicht = LED-Block links, Rückfahrscheinwerfer = Tasche rechts,
// Außenscheibe = vordere Schale, Rückstrahler = Feld auf der Scheibe. Gehäuse = Gesamtgerät.
import { useMemo, useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'
import { PARTS } from './data.js'

const LITE = typeof location !== 'undefined' && new URLSearchParams(location.search).has('lite')
const damp = THREE.MathUtils.damp
const K = 5.4 / 1714 // Pixel der Zeichnung → Welt
const X = (px) => (px - 857) * K
const Y = (py) => -(py - 425) * K // Gehäuse-Zeichnung oben, Mitte bei y ≈ 425

// Außenkontur (obere Zeichnung, Gehäuse); die Scheibe hat dieselbe Kontur
const OUTLINE = [[35, 705], [48, 560], [80, 420], [140, 300], [240, 205], [380, 150], [560, 110], [800, 75], [1100, 45],
  [1380, 22], [1520, 15], [1610, 45], [1675, 130], [1700, 260], [1705, 560], [1698, 800], [1610, 840], [900, 800],
  [400, 770], [95, 740]]

function shape(points, s = 1, cx = 870, cy = 430) {
  const sh = new THREE.Shape()
  points.forEach(([x, y], i) => {
    const px = cx + (x - cx) * s, py = cy + (y - cy) * s
    i ? sh.lineTo(X(px), Y(py)) : sh.moveTo(X(px), Y(py))
  })
  sh.closePath()
  return sh
}
function rect(x0, y0, x1, y1, r = 0) {
  const s = new THREE.Shape()
  const a = X(x0), b = Y(y1), c = X(x1), d = Y(y0), rr = r * K
  s.moveTo(a + rr, b); s.lineTo(c - rr, b); s.quadraticCurveTo(c, b, c, b + rr); s.lineTo(c, d - rr)
  s.quadraticCurveTo(c, d, c - rr, d); s.lineTo(a + rr, d); s.quadraticCurveTo(a, d, a, d - rr); s.lineTo(a, b + rr)
  s.quadraticCurveTo(a, b, a + rr, b)
  return s
}
const ext = (s, depth, bevel = 0.02) => new THREE.ExtrudeGeometry(s, { depth, bevelEnabled: bevel > 0, bevelThickness: bevel, bevelSize: bevel, bevelSegments: 4, curveSegments: 48 })

// Bauteile: Schlüssel, Lage in z (montiert) und Versatz in der Explosion, Ankerpunkt für die Hinweislinie (Pixel)
const PIECES = [
  { key: 'housing', label: 'Gehäuse', match: [], z: -0.55, ez: -3.2, anchor: [1580, 120] },
  { key: 'stop', label: 'Stop lamp', match: ['stop'], z: -0.18, ez: -1.6, anchor: [520, 330] },
  { key: 'tail', label: 'Rear position lamp', match: ['position', 'tail'], z: -0.12, ez: -0.4, anchor: [1050, 205] },
  { key: 'reversing', label: 'Reversing lamp', match: ['revers'], z: -0.2, ez: 0.8, anchor: [1370, 470] },
  { key: 'lens', label: 'Outer lens', match: ['lens'], z: 0.22, ez: 2.2, anchor: [500, 160] },
  { key: 'retro', label: 'Retro-reflector', match: ['retro', 'reflector'], z: 0.3, ez: 3.2, anchor: [1370, 1460 - 975] },
]

export function lampPartId(piece) {
  if (!piece.match.length) return 'device'
  const hit = PARTS.find((p) => p.id !== 'device' && piece.match.some((m) => p.name.toLowerCase().includes(m)))
  return hit?.id || 'device'
}
export const LAMP_SEGS = PIECES.map((p, i) => ({ n: i + 1, partId: lampPartId(p), key: p.key }))

const INK = new THREE.Color('#18181b')
const SEL = new THREE.Color('#ff2a1f')

function useGeometry() {
  return useMemo(() => {
    const outline = shape(OUTLINE)
    const housing = ext(outline, 0.5, 0.05)
    housing.translate(0, 0, -0.5)
    const recess = new THREE.ShapeGeometry(shape(OUTLINE, 0.9), 48)
    const windowG = ext(rect(878, 352, 1064, 604, 6), 0.06, 0.01)
    // Schlusslicht: Lichtleiter oben (Trapez mit gerundetem rechtem Ende)
    const tailS = new THREE.Shape()
    ;[[612, 285], [705, 214], [900, 205], [1200, 196], [1440, 190], [1468, 205], [1480, 250], [1480, 312], [1060, 300]]
      .forEach(([x, y], i) => (i ? tailS.lineTo(X(x), Y(y)) : tailS.moveTo(X(x), Y(y))))
    tailS.closePath()
    const tail = ext(tailS, 0.1, 0.02)
    // Bremslicht: Block mit 8 LED-Kammern und 3 × 8 Reflektorschalen
    const block = ext(rect(178, 322, 866, 716, 12), 0.08, 0.015)
    const led = new THREE.CylinderGeometry(0.035, 0.035, 0.05, 24)
    led.rotateX(Math.PI / 2)
    const chamber = ext(rect(827, 375, 887, 475, 6), 0.03, 0.006)
    chamber.translate(0, 0, -0.03)
    const cup = new THREE.SphereGeometry(0.11, 28, 14, 0, Math.PI * 2, 0, Math.PI / 2)
    cup.rotateX(-Math.PI / 2)
    cup.scale(1, 0.62, 0.5)
    // Rückfahrscheinwerfer: Tasche mit Facettenraster und Halbkreis-Reflektor
    const pocket = ext(rect(1228, 460, 1515, 752, 30), 0.12, 0.02)
    const dome = new THREE.SphereGeometry(65 * K, 32, 16, 0, Math.PI)
    // Außenscheibe und Rückstrahler (untere Zeichnung, Scheibe hat dieselbe Kontur)
    const lens = ext(outline, 0.04, 0.05)
    const retro = ext(rect(1215, 1420 - 975, 1525, 1662 - 975, 26), 0.05, 0.012)
    return { housing, recess, windowG, tail, block, led, chamber, cup, pocket, dome, lens, retro }
  }, [])
}

function Edges({ geometry, sketch, color = INK, threshold = 25 }) {
  const eg = useMemo(() => new THREE.EdgesGeometry(geometry, threshold), [geometry, threshold])
  const m = useRef()
  useFrame((_, dt) => {
    if (m.current) m.current.opacity = damp(m.current.opacity, sketch.current ? 0.95 : 0.22, 5, dt)
  })
  return (
    <lineSegments geometry={eg}>
      <lineBasicMaterial ref={m} color={color} transparent opacity={0.22} />
    </lineSegments>
  )
}

// Material, das im Strichzeichnungs-Modus zu Papierweiß blendet
function useSketchMaterial(base) {
  return useMemo(() => {
    const m = new THREE.MeshStandardMaterial(base)
    m.userData.base = { color: new THREE.Color(base.color), emissive: new THREE.Color(base.emissive || '#000'), ei: base.emissiveIntensity ?? 0, opacity: base.opacity ?? 1 }
    return m
  }, []) // eslint-disable-line react-hooks/exhaustive-deps
}
const PAPER = new THREE.Color('#fbfaf6')
function blend(m, k, dt, hi) {
  const b = m.userData.base
  const t = 1 - Math.exp(-6 * dt)
  m.color.lerp(k ? PAPER : hi ? SEL : b.color, t)
  m.emissive.lerp(k ? PAPER : b.emissive, t)
  m.emissiveIntensity = damp(m.emissiveIntensity, k ? 0.35 : b.ei, 6, dt)
  if (m.transparent) m.opacity = damp(m.opacity, k ? 0.92 : b.opacity, 6, dt)
}

export default function RearLamp({ explodeTarget, sketchMode = false, hovered, selected, interactive, onHover, onPick, anchors }) {
  const G = useGeometry()
  const explode = useRef(0)
  const sketch = useRef(sketchMode)
  sketch.current = sketchMode
  const groups = useRef({})
  const M = {
    housing: useSketchMaterial({ color: '#1c1d21', roughness: 0.55, metalness: 0.2 }),
    recess: useSketchMaterial({ color: '#2a2b30', roughness: 0.7 }),
    tail: useSketchMaterial({ color: '#ff3b2f', emissive: '#ff2a1f', emissiveIntensity: 1.6, roughness: 0.3 }),
    block: useSketchMaterial({ color: '#3a1412', roughness: 0.5 }),
    cup: useSketchMaterial({ color: '#d9d4cc', metalness: 0.9, roughness: 0.18 }),
    led: useSketchMaterial({ color: '#ff5a4f', emissive: '#ff2a1f', emissiveIntensity: 2.2 }),
    pocket: useSketchMaterial({ color: '#e9e7e2', metalness: 0.75, roughness: 0.22 }),
    lens: useSketchMaterial({ color: '#c8231b', roughness: 0.12, metalness: 0.05, transparent: true, opacity: LITE ? 0.55 : 0.42 }),
    retro: useSketchMaterial({ color: '#9c1a14', roughness: 0.35, metalness: 0.3 }),
  }
  useFrame((_, dt) => {
    explode.current = damp(explode.current, explodeTarget, 3, dt)
    const e = explode.current
    PIECES.forEach((p, i) => {
      const g = groups.current[p.key]
      if (!g) return
      const n = i + 1
      const lift = (selected === n ? 0.35 : 0) + (hovered === n ? 0.15 : 0)
      g.position.z = damp(g.position.z, p.z + p.ez * e + lift, 5, dt)
      g.position.y = damp(g.position.y, e * (i - 2.5) * 0.12 + lift * 0.2, 5, dt)
      if (anchors) {
        const [ax, ay] = p.anchor
        anchors.current[`pos${n}`] = { obj: g, local: [X(ax), Y(ay), 0.2] }
      }
    })
    const hi = (key) => {
      const n = PIECES.findIndex((p) => p.key === key) + 1
      return selected === n || hovered === n
    }
    const k = sketch.current
    blend(M.housing, k, dt, hi('housing')); blend(M.recess, k, dt, false)
    blend(M.tail, k, dt, hi('tail')); blend(M.block, k, dt, hi('stop')); blend(M.cup, k, dt, false); blend(M.led, k, dt, false)
    blend(M.pocket, k, dt, hi('reversing')); blend(M.lens, k, dt, hi('lens')); blend(M.retro, k, dt, hi('retro'))
    if (anchors && groups.current.housing) anchors.current.obj = { obj: groups.current.housing, local: [0, Y(10), 0.3] }
  })
  const ev = (n) => (interactive ? {
    onPointerOver: (e) => (e.stopPropagation(), onHover(n)),
    onPointerOut: (e) => (e.stopPropagation(), onHover(null)),
    onClick: (e) => (e.stopPropagation(), onPick(n)),
  } : {})
  const cups = []
  for (const y of [512, 592, 672]) for (let i = 0; i < 8; i++) cups.push([238 + i * 81.5, y])
  const leds = Array.from({ length: 8 }, (_, i) => [240 + i * 81.5, 420])
  const set = (key) => (el) => { if (el) groups.current[key] = el }
  return (
    <group rotation={[0.06, -0.18, 0]} scale={0.95}>
      <group ref={set('housing')} {...ev(1)}>
        <mesh geometry={G.housing} material={M.housing} castShadow />
        <Edges geometry={G.housing} sketch={sketch} threshold={35} />
        <mesh geometry={G.recess} material={M.recess} position={[0, 0, 0.012]} />
        <mesh geometry={G.windowG} material={M.recess} position={[0, 0, 0.0]} />
        <Edges geometry={G.windowG} sketch={sketch} />
      </group>
      <group ref={set('stop')} {...ev(2)}>
        <mesh geometry={G.block} material={M.block} castShadow />
        <Edges geometry={G.block} sketch={sketch} />
        {leds.map(([x, y], i) => (
          <group key={`l${i}`} position={[X(x), Y(y), 0.1]}>
            <mesh geometry={G.chamber} material={M.block} />
            <mesh geometry={G.led} material={M.led} />
          </group>
        ))}
        {cups.map(([x, y], i) => <mesh key={i} geometry={G.cup} material={M.cup} position={[X(x), Y(y), 0.1]} />)}
      </group>
      <group ref={set('tail')} {...ev(3)}>
        <mesh geometry={G.tail} material={M.tail} />
        <Edges geometry={G.tail} sketch={sketch} />
      </group>
      <group ref={set('reversing')} {...ev(4)}>
        <mesh geometry={G.pocket} material={M.pocket} castShadow />
        <Edges geometry={G.pocket} sketch={sketch} />
        {Array.from({ length: 5 }, (_, i) => (
          <mesh key={i} position={[X(1270 + i * 55), Y(560), 0.15]}>
            <boxGeometry args={[0.006, 0.42, 0.01]} />
            <meshBasicMaterial color="#8a8780" />
          </mesh>
        ))}
        <mesh geometry={G.dome} material={M.pocket} position={[X(1400), Y(470), 0.14]} rotation={[0, 0, Math.PI]} />
      </group>
      <group ref={set('lens')} {...ev(5)}>
        <mesh geometry={G.lens} material={M.lens} />
        <Edges geometry={G.lens} sketch={sketch} color={new THREE.Color('#6b1410')} />
        {[[250, 1340, 760, 1080], [80, 1700, 450, 1330], [1120, 1270, 1450, 1040], [600, 1790, 1150, 1290]].map(([x0, y0, x1, y1], i) => {
          const a = new THREE.Vector3(X(x0), Y(y0 - 975), 0.07), b = new THREE.Vector3(X(x1), Y(y1 - 975), 0.07)
          const g = new THREE.BufferGeometry().setFromPoints([a, b])
          return <lineSegments key={i} geometry={g}><lineBasicMaterial color="#ffd6d2" transparent opacity={0.6} /></lineSegments>
        })}
      </group>
      <group ref={set('retro')} {...ev(6)}>
        <mesh geometry={G.retro} material={M.retro} castShadow />
        <Edges geometry={G.retro} sketch={sketch} />
        {Array.from({ length: 6 }, (_, i) => (
          <mesh key={i} position={[X(1265 + i * 45), Y(1540 - 975), 0.07]}>
            <boxGeometry args={[0.012, 0.66, 0.012]} />
            <meshStandardMaterial color="#5c0f0b" />
          </mesh>
        ))}
      </group>
    </group>
  )
}
