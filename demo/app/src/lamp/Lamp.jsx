// Handgebaute 3D-Heckleuchte (nur Fall dev-rear-lamp). Derzeit NICHT eingebunden: die App nutzt den allgemeinen
// Weg über die Zeichnung (Drawing.jsx). Zum Wiederverwenden an die neue data.js anpassen (countsByReg, PARTS-Ids).

import { useMemo, useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import { Html, RoundedBox } from '@react-three/drei'
import * as THREE from 'three'
import { PARTS, partCounts } from '../data.js'
const LITE = new URLSearchParams(location.search).has('lite')

// Umriss nach der Explosionszeichnung des Falls (exploded_view.png): links niedrig, rechts hoch und gerundet.
export function outlineShape(s = 1) {
  const S = new THREE.Shape()
  const p = (x, y) => [x * s, y * s]
  S.moveTo(...p(-2.43, -0.81))
  S.lineTo(...p(-2.25, -0.91))
  S.lineTo(...p(2.18, -1.21))
  S.lineTo(...p(2.44, -1.13))
  S.lineTo(...p(2.47, 0.53))
  S.quadraticCurveTo(...p(2.47, 1.22), ...p(1.73, 1.22))
  S.lineTo(...p(-0.76, 1.09))
  S.bezierCurveTo(...p(-2.09, 0.76), ...p(-2.38, -0.06), ...p(-2.43, -0.81))
  return S
}

const damp = THREE.MathUtils.damp

// z-Lage montiert und Zusatzversatz in der Explosion, je Bauteil
const LAYOUT = {
  housing: [0, -0.3, -3.9],
  stop: [0, -0.18, -2.3],
  reversing: [0, -0.06, -0.8],
  tail: [0, 0.06, 0.7],
  retro: [0, 0.18, 2.2],
  lens: [0, 0.3, 3.8],
}
// Ankerpunkt für Beschriftung (lokal), oben rechts am Bauteil
const ANCHOR = {
  lens: [-0.6, 1.15, 0.45],
  tail: [-1.2, 0.68, 0.17],
  stop: [-1.0, -0.1, 0.12],
  reversing: [0.28, 0.2, 0.2],
  retro: [1.5, -0.1, 0.2],
  housing: [0.6, 0.95, 0.02],
}

function Part({ id, explode, active, hovered, onOver, onOut, onPick, interactive, children, labelsOn, anchors }) {
  const g = useRef()
  useFrame((_, dt) => {
    if (!g.current) return
    const L = LAYOUT[id]
    const e = explode.current
    const lift = (active ? 0.4 : 0) + (hovered ? 0.2 : 0)
    g.current.position.x = damp(g.current.position.x, e * L[0], 5, dt)
    g.current.position.y = damp(g.current.position.y, e * (L[1] + lift * 0.5), 5, dt)
    g.current.position.z = damp(g.current.position.z, e * (L[2] + lift), 5, dt)
    if (anchors) anchors.current[id] = g.current
  })
  const p = PARTS.find((x) => x.id === id)
  const c = partCounts[id]
  return (
    <group
      ref={g}
      onPointerOver={interactive ? (e) => (e.stopPropagation(), onOver(id)) : undefined}
      onPointerOut={interactive ? (e) => (e.stopPropagation(), onOut(id)) : undefined}
      onClick={interactive ? (e) => (e.stopPropagation(), onPick(id)) : undefined}
    >
      {children}
      <Html position={ANCHOR[id]} zIndexRange={[20, 0]} style={{ pointerEvents: 'none' }}>
        <div className={`tag ${labelsOn ? 'on' : ''} ${active ? 'active' : ''} ${hovered ? 'hover' : ''}`}>
          <span className="tag-n">{p.n}</span>
          <span className="tag-name">{p.de}</span>
          <span className="tag-c">{c.total}</span>
        </div>
      </Html>
    </group>
  )
}

export default function Lamp({ explodeTarget, selected, hovered, setHovered, onPick, interactive, labelsOn, glow, anchors }) {
  const explode = useRef(0)
  useFrame((_, dt) => {
    explode.current = damp(explode.current, explodeTarget, 3.2, dt)
  })

  const geo = useMemo(() => {
    const outline = outlineShape(1)
    const housing = new THREE.ExtrudeGeometry(outline, { depth: 0.62, bevelEnabled: true, bevelThickness: 0.08, bevelSize: 0.07, bevelSegments: 6, curveSegments: 64 })
    housing.translate(0, 0, -0.66)
    const inner = new THREE.ShapeGeometry(outlineShape(0.93), 64)
    const lens = new THREE.ExtrudeGeometry(outline, { depth: 0.04, bevelEnabled: true, bevelThickness: 0.07, bevelSize: 0.06, bevelSegments: 8, curveSegments: 96 })
    lens.translate(0, 0, 0.36)
    const tailCurve = new THREE.CatmullRomCurve3([
      new THREE.Vector3(-2.05, -0.55, 0.12),
      new THREE.Vector3(-2.0, 0.15, 0.12),
      new THREE.Vector3(-1.2, 0.68, 0.12),
      new THREE.Vector3(0.4, 0.86, 0.12),
      new THREE.Vector3(1.7, 0.9, 0.12),
      new THREE.Vector3(2.12, 0.55, 0.12),
      new THREE.Vector3(2.12, -0.85, 0.12),
    ])
    const tail = new THREE.TubeGeometry(tailCurve, 200, 0.045, 16, false)
    const cup = new THREE.SphereGeometry(0.105, 32, 16, 0, Math.PI * 2, 0, Math.PI / 2)
    cup.rotateX(-Math.PI / 2)
    const prism = new THREE.ConeGeometry(0.075, 0.07, 4)
    prism.rotateX(Math.PI / 2)
    prism.rotateZ(Math.PI / 4)
    return { housing, inner, lens, tail, cup, prism }
  }, [])

  const cups = useMemo(() => {
    const a = []
    for (const y of [-0.25, -0.48, -0.71]) for (let k = 0; k < 8; k++) a.push([-1.84 + k * 0.235, y])
    return a
  }, [])
  const prisms = useMemo(() => {
    const a = []
    for (let i = 0; i < 6; i++) for (let j = 0; j < 6; j++) a.push([1.17 + i * 0.135, -0.86 + j * 0.135])
    return a
  }, [])

  const common = { explode, hovered: false, onOver: setHovered, onOut: () => setHovered(null), onPick, interactive, labelsOn, anchors }
  const red = new THREE.Color('#ff2a1f')
  const g = glow ?? 1

  return (
    <group>
      <Part id="housing" {...common} active={selected === 'housing'} hovered={hovered === 'housing'}>
        <mesh geometry={geo.housing} castShadow>
          <meshPhysicalMaterial color="#3d3d43" roughness={0.5} metalness={0.1} clearcoat={0.5} clearcoatRoughness={0.35} />
        </mesh>
        <mesh geometry={geo.inner} position={[0, 0, 0.03]}>
          <meshStandardMaterial color="#141416" roughness={0.6} />
        </mesh>
        {/* Leiterplatte */}
        <mesh position={[-1.0, -0.47, 0.035]}>
          <boxGeometry args={[2.05, 0.82, 0.03]} />
          <meshStandardMaterial color="#173d2b" roughness={0.5} />
        </mesh>
        {[[-1.7, -0.2], [-1.2, -0.75], [-0.4, -0.3]].map(([x, y], i) => (
          <mesh key={i} position={[x, y, 0.06]}>
            <boxGeometry args={[0.16, 0.12, 0.03]} />
            <meshStandardMaterial color="#0b0b0c" roughness={0.3} metalness={0.4} />
          </mesh>
        ))}
      </Part>

      <Part id="stop" {...common} active={selected === 'stop'} hovered={hovered === 'stop'}>
        <mesh position={[-1.02, -0.48, 0.07]}>
          <boxGeometry args={[2.0, 0.78, 0.05]} />
          <meshStandardMaterial color="#1b1b1e" roughness={0.5} />
        </mesh>
        {cups.map(([x, y], i) => (
          <group key={i} position={[x, y, 0.1]}>
            <mesh geometry={geo.cup}>
              <meshStandardMaterial color="#e9e9ee" metalness={1} roughness={0.12} side={THREE.DoubleSide} />
            </mesh>
            <mesh position={[0, 0, 0.02]} rotation={[Math.PI / 2, 0, 0]}>
              <cylinderGeometry args={[0.03, 0.03, 0.03, 16]} />
              <meshStandardMaterial color={red} emissive={red} emissiveIntensity={3.2 * g} toneMapped={false} />
            </mesh>
          </group>
        ))}
        {Array.from({ length: 8 }, (_, k) => (
          <mesh key={k} position={[-1.84 + k * 0.235, 0.02, 0.11]} rotation={[Math.PI / 2, 0, 0]}>
            <cylinderGeometry args={[0.035, 0.035, 0.02, 16]} />
            <meshStandardMaterial color={red} emissive={red} emissiveIntensity={1.6 * g} toneMapped={false} />
          </mesh>
        ))}
      </Part>

      <Part id="reversing" {...common} active={selected === 'reversing'} hovered={hovered === 'reversing'}>
        <RoundedBox args={[0.6, 0.72, 0.12]} radius={0.05} position={[0.28, -0.14, 0.12]}>
          <meshPhysicalMaterial color="#ffffff" emissive="#fff6e8" emissiveIntensity={0.9 * g} roughness={0.15} transmission={0.2} toneMapped={false} />
        </RoundedBox>
      </Part>

      <Part id="tail" {...common} active={selected === 'tail'} hovered={hovered === 'tail'}>
        <mesh geometry={geo.tail}>
          <meshStandardMaterial color={red} emissive={red} emissiveIntensity={2.2 * g} toneMapped={false} />
        </mesh>
      </Part>

      <Part id="retro" {...common} active={selected === 'retro'} hovered={hovered === 'retro'}>
        <RoundedBox args={[0.88, 0.88, 0.05]} radius={0.04} position={[1.51, -0.52, 0.1]}>
          <meshStandardMaterial color="#5a0d0b" roughness={0.4} />
        </RoundedBox>
        {prisms.map(([x, y], i) => (
          <mesh key={i} geometry={geo.prism} position={[x, y, 0.16]}>
            <meshPhysicalMaterial color="#d11a12" metalness={0.3} roughness={0.12} clearcoat={1} />
          </mesh>
        ))}
      </Part>

      <Part id="lens" {...common} active={selected === 'lens'} hovered={hovered === 'lens'}>
        <mesh geometry={geo.lens}>
          <meshPhysicalMaterial
            color="#ff8173"
            transmission={LITE ? 0 : 1}
            opacity={LITE ? 0.45 : 1}
            thickness={0.25}
            roughness={0.06}
            ior={1.49}
            clearcoat={1}
            clearcoatRoughness={0.04}
            attenuationColor="#ff2a1f"
            attenuationDistance={3.5}
            transparent
          />
        </mesh>
      </Part>
    </group>
  )
}

export { ANCHOR }
