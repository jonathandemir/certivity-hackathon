// Handgebaute 3D-Heckleuchte (nur Fall dev-rear-lamp). Derzeit NICHT eingebunden: die App nutzt den allgemeinen
// Weg über die Zeichnung (Drawing.jsx). Zum Wiederverwenden an die neue data.js anpassen (countsByReg, PARTS-Ids).

import { useMemo, useRef } from 'react'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { ContactShadows, Environment, Lightformer, Html } from '@react-three/drei'
import { EffectComposer, Bloom } from '@react-three/postprocessing'
import * as THREE from 'three'
import Lamp, { ANCHOR } from './Lamp.jsx'
import { REGS, regAngle, activationT, regColor, countsByReg, SWEEP0, SWEEP1 } from '../data.js'

const damp = THREE.MathUtils.damp
export const LITE = new URLSearchParams(location.search).has('lite')

// Bühnenzustand je Akt: Lage der Leuchte und Explosionsgrad
const ACTS = [
  { pos: [2.0, -0.05, 0], rot: [0.06, -0.42, 0], s: 1, ex: 0, orbit: 1 },
  { pos: [-2.45, -0.45, 0], rot: [0.24, -0.9, 0.02], s: 0.66, ex: 1, orbit: 0 },
  { pos: [-4.0, -1.85, 0], rot: [0.25, -0.5, 0.02], s: 0.46, ex: 0.3, orbit: 0 },
]

function Rig({ act, children, spin }) {
  const g = useRef()
  const t0 = useRef(0)
  useFrame((state, dt) => {
    const A = ACTS[act]
    const o = g.current
    t0.current += dt
    const wob = (act === 0 ? Math.sin(t0.current * 0.35) * 0.14 : act === 1 ? Math.sin(t0.current * 0.25) * 0.04 : 0) + state.pointer.x * 0.12
    for (const [k, i] of [['x', 0], ['y', 1], ['z', 2]]) {
      o.position[k] = damp(o.position[k], A.pos[i], 2.6, dt)
      o.rotation[k] = damp(o.rotation[k], A.rot[i] + (k === 'y' ? wob : k === 'x' ? -state.pointer.y * 0.06 : 0), 2.6, dt)
    }
    const s = damp(o.scale.x, A.s, 2.6, dt)
    o.scale.setScalar(s)
  })
  return <group ref={g}>{children}</group>
}

function Orbit({ act, progress }) {
  const ring = useRef()
  const sweep = useRef()
  const dots = useRef([])
  const vis = useRef(1)
  const R = 3.45
  const sel = useMemo(() => new Set(countsByReg.map((c) => c.id)), [])
  useFrame((state, dt) => {
    vis.current = damp(vis.current, ACTS[act].orbit, 4, dt)
    const t = progress.current
    const s = Math.min(1, Math.max(0, (t - SWEEP0) / (SWEEP1 - SWEEP0)))
    ring.current.scale.setScalar(0.6 + 0.4 * vis.current)
    ring.current.visible = vis.current > 0.02
    ring.current.rotation.z += dt * 0.05 * (t >= 1 ? 1 : 0)
    sweep.current.rotation.z = s * Math.PI * 2 - 0.5
    sweep.current.visible = t > SWEEP0 && t < SWEEP1 + 0.02
    REGS.forEach((r, i) => {
      const m = dots.current[i]
      if (!m) return
      const on = sel.has(r.id) && t >= activationT(r.id)
      const target = on ? 2.6 : s * Math.PI * 2 > regAngle(r.id) && t < 1.01 ? 0.75 : 1
      m.scale.setScalar(damp(m.scale.x, target, 6, dt))
    })
  })
  return (
    <group ref={ring} rotation={[1.22, 0, 0.12]}>
      <mesh>
        <torusGeometry args={[R, 0.006, 8, 256]} />
        <meshBasicMaterial color="#b9b6ae" />
      </mesh>
      <mesh>
        <torusGeometry args={[R + 0.32, 0.003, 8, 256]} />
        <meshBasicMaterial color="#d6d3cc" />
      </mesh>
      <mesh ref={sweep}>
        <torusGeometry args={[R, 0.03, 8, 64, 0.5]} />
        <meshBasicMaterial color="#ff2a1f" toneMapped={false} />
      </mesh>
      {REGS.map((r, i) => {
        const a = regAngle(r.id)
        const on = sel.has(r.id)
        const c = countsByReg.find((x) => x.id === r.id)
        return (
          <group key={r.id} position={[Math.cos(a) * R, Math.sin(a) * R, 0]}>
            <mesh ref={(el) => (dots.current[i] = el)}>
              <sphereGeometry args={[on ? 0.05 : 0.032, 24, 12]} />
              {on ? (
                <meshStandardMaterial color={regColor(r.id)} emissive={regColor(r.id)} emissiveIntensity={0.6} roughness={0.3} />
              ) : (
                <meshStandardMaterial color="#bdb9b0" roughness={0.5} />
              )}
            </mesh>
            {on && <OrbitLabel id={r.id} c={c} progress={progress} act={act} />}
          </group>
        )
      })}
    </group>
  )
}

function OrbitLabel({ id, c, progress, act }) {
  const el = useRef()
  useFrame(() => {
    if (!el.current) return
    const t = progress.current
    const on = t >= activationT(id) && act === 0
    el.current.classList.toggle('on', on)
    const k = Math.min(1, Math.max(0, (t - activationT(id)) / 0.12))
    const n = el.current.querySelector('.ol-n')
    if (n) n.textContent = String(Math.round(c.n * k))
  })
  return (
    <Html center zIndexRange={[15, 0]} style={{ pointerEvents: 'none' }}>
      <div ref={el} className="orbit-label" style={{ '--c': regColor(id) }}>
        <span className="ol-dot" />
        <span className="ol-id">{id.replace('UN ', '')}</span>
        <span className="ol-n">0</span>
      </div>
    </Html>
  )
}

// Projiziert den Anker des gewählten Bauteils auf den Bildschirm (für die Belegkette im HTML)
function AnchorProbe({ anchors, selected, out }) {
  const { camera, size } = useThree()
  const v = useMemo(() => new THREE.Vector3(), [])
  useFrame(() => {
    for (const id of Object.keys(ANCHOR)) {
      const g = anchors.current[id]
      if (!g) continue
      v.set(...ANCHOR[id])
      g.localToWorld(v)
      v.project(camera)
      out.current[id] = { x: (v.x * 0.5 + 0.5) * size.width, y: (-v.y * 0.5 + 0.5) * size.height }
    }
    if (out.current[selected]) out.current.sel = out.current[selected]
  })
  return null
}

export default function Scene({ act, progress, selected, hovered, setHovered, onPick, anchorOut }) {
  const anchors = useRef({})
  return (
    <Canvas
      className="stage"
      shadows
      dpr={LITE ? 1 : [1, 2]}
      camera={{ position: [0, 0.35, 12.5], fov: 32 }}
      gl={{ antialias: true, toneMapping: THREE.ACESFilmicToneMapping }}
      onPointerMissed={() => setHovered(null)}
    >
      <color attach="background" args={['#f3f2ee']} />
      <ambientLight intensity={0.5} />
      <directionalLight position={[4, 6, 6]} intensity={1.6} castShadow />
      <Environment resolution={256}>
        <group rotation={[-Math.PI / 3, 0, 0]}>
          <Lightformer form="rect" intensity={4} position={[0, 5, -9]} scale={[12, 2, 1]} />
          <Lightformer form="rect" intensity={2} position={[-6, 1, 2]} rotation-y={Math.PI / 2} scale={[8, 2, 1]} />
          <Lightformer form="rect" intensity={2} position={[6, -1, 2]} rotation-y={-Math.PI / 2} scale={[8, 2, 1]} />
          <Lightformer form="ring" intensity={3} position={[0, 2, 6]} scale={3} />
        </group>
      </Environment>
      <Rig act={act}>
        <Lamp
          explodeTarget={ACTS[act].ex}
          selected={act >= 1 ? selected : null}
          hovered={act === 1 ? hovered : null}
          setHovered={setHovered}
          onPick={onPick}
          interactive={act === 1}
          labelsOn={false}
          glow={1}
          anchors={anchors}
        />
        <Orbit act={act} progress={progress} />
      </Rig>
      <AnchorProbe anchors={anchors} selected={selected} out={anchorOut} />
      <ContactShadows position={[0, -2.15, 0]} opacity={0.35} scale={22} blur={2.6} far={4} />
      {!LITE && (
        <EffectComposer multisampling={4}>
          <Bloom luminanceThreshold={1} mipmapBlur intensity={0.9} radius={0.7} />
        </EffectComposer>
      )}
    </Canvas>
  )
}
