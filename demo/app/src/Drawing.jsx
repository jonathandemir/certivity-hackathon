import { useEffect, useMemo, useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'

const damp = THREE.MathUtils.damp
const INK = new THREE.Color('#18181b')
const RED = new THREE.Color('#ff2a1f')
const HOV = new THREE.Color('#9a2a20')

function roundedRect(w, h, r) {
  const s = new THREE.Shape()
  const x = -w / 2, y = -h / 2
  s.moveTo(x + r, y); s.lineTo(x + w - r, y); s.quadraticCurveTo(x + w, y, x + w, y + r)
  s.lineTo(x + w, y + h - r); s.quadraticCurveTo(x + w, y + h, x + w - r, y + h)
  s.lineTo(x + r, y + h); s.quadraticCurveTo(x, y + h, x, y + h - r)
  s.lineTo(x, y + r); s.quadraticCurveTo(x, y, x + r, y)
  return new THREE.ShapeGeometry(s, 8)
}

// Bildmaßstab -> Welt: Zeichnung höchstens 5.4 breit und 3.6 hoch
export function layout(segs) {
  if (!segs.length) return { k: 1, items: [] }
  const W = segs[0].imgW, H = segs[0].imgH
  const k = Math.min(5.4 / W, 3.6 / H)
  const n = segs.length
  const spacing = Math.min(1.7, 6.5 / Math.max(1, n - 1))
  const items = segs.map((s, i) => ({
    ...s,
    cx: (s.x + s.w / 2 - W / 2) * k,
    cy: -(s.y + s.h / 2 - H / 2) * k,
    sw: s.w * k,
    sh: s.h * k,
    ez: (i - (n - 1) / 2) * spacing,
  }))
  return { k, W: W * k, H: H * k, items }
}

function Piece({ it, explode, hovered, selected, interactive, onHover, onPick, anchors }) {
  const g = useRef(), card = useRef(), lines = useRef()
  const tex = useMemo(() => {
    const t = new THREE.CanvasTexture(it.canvas)
    t.colorSpace = THREE.SRGBColorSpace
    t.anisotropy = 8
    return t
  }, [it.canvas])
  const geo = useMemo(() => roundedRect(it.sw + 0.16, it.sh + 0.16, 0.08), [it.sw, it.sh])
  const plane = useMemo(() => new THREE.PlaneGeometry(it.sw, it.sh), [it.sw, it.sh])
  useEffect(() => () => tex.dispose(), [tex])
  useFrame((_, dt) => {
    const e = explode.current
    const lift = (selected ? 0.35 : 0) + (hovered ? 0.18 : 0)
    // In der Explosion rücken die Teile zur Mitte und fächern sich in die Tiefe auf
    g.current.position.x = damp(g.current.position.x, it.cx * (1 - 0.72 * e), 5, dt)
    g.current.position.y = damp(g.current.position.y, it.cy * (1 - 0.72 * e) + lift * 0.3, 5, dt)
    g.current.position.z = damp(g.current.position.z, it.ez * e + lift, 5, dt)
    card.current.material.opacity = damp(card.current.material.opacity, Math.min(1, e * 2.2) * 0.96, 6, dt)
    const target = selected ? RED : hovered ? HOV : INK
    lines.current.material.color.lerp(target, 1 - Math.exp(-8 * dt))
    if (anchors) anchors.current[`pos${it.n}`] = { obj: g.current, local: [0, it.sh / 2 + 0.08, 0.01] }
  })
  return (
    <group ref={g} position={[it.cx, it.cy, 0]}>
      <mesh ref={card} geometry={geo} castShadow
        onPointerOver={interactive ? (e) => (e.stopPropagation(), onHover(it.n)) : undefined}
        onPointerOut={interactive ? (e) => (e.stopPropagation(), onHover(null)) : undefined}
        onClick={interactive ? (e) => (e.stopPropagation(), onPick(it.n)) : undefined}>
        <meshStandardMaterial color="#ffffff" emissive="#ffffff" emissiveIntensity={0.5} roughness={0.85} transparent opacity={0} side={THREE.DoubleSide} />
      </mesh>
      <mesh ref={lines} geometry={plane} position={[0, 0, 0.004]}>
        <meshBasicMaterial map={tex} transparent depthWrite={false} color={INK} toneMapped={false} side={THREE.DoubleSide} />
      </mesh>
    </group>
  )
}

export default function DrawingObject({ segs, explodeTarget, hovered, selected, interactive, onHover, onPick, anchors }) {
  const explode = useRef(0)
  const base = useRef()
  const L = useMemo(() => layout(segs), [segs])
  const minEz = useMemo(() => Math.min(0, ...L.items.map((i) => i.ez)), [L])
  const baseGeo = useMemo(() => (L.items.length ? roundedRect(L.W + 0.5, L.H + 0.5, 0.18) : null), [L])
  useFrame((_, dt) => {
    explode.current = damp(explode.current, explodeTarget, 3, dt)
    if (base.current) {
      base.current.material.opacity = Math.max(0, 1 - explode.current * 2.5)
      base.current.position.z = minEz * explode.current - 0.04
    }
    if (anchors && base.current) anchors.current.obj = { obj: base.current, local: [0, L.H / 2 + 0.25, 0] }
  })
  if (!L.items.length) return null
  return (
    <group>
      <mesh ref={base} geometry={baseGeo} position={[0, 0, -0.02]} castShadow>
        <meshStandardMaterial color="#ffffff" emissive="#ffffff" emissiveIntensity={0.55} roughness={0.9} transparent />
      </mesh>
      {L.items.map((it) => (
        <Piece key={it.n} it={it} explode={explode} hovered={hovered === it.n} selected={selected === it.n}
          interactive={interactive} onHover={onHover} onPick={onPick} anchors={anchors} />
      ))}
    </group>
  )
}
