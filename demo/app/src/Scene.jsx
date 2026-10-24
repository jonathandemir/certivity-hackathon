import { useMemo, useRef } from 'react'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { ContactShadows, Environment, Lightformer, Html } from '@react-three/drei'
import { EffectComposer, Bloom } from '@react-three/postprocessing'
import * as THREE from 'three'
import DrawingObject from './Drawing.jsx'
import { REGS, ACTIVE, regAngle, activationT, regColor, SWEEP0, SWEEP1 } from './data.js'

const damp = THREE.MathUtils.damp
export const LITE = new URLSearchParams(location.search).has('lite')

// Bühnenzustand je Akt: Lage des Objekts und Explosionsgrad
const ACTS = [
  { pos: [2.0, 0.0, 0], rot: [0.06, -0.38, 0], s: 1, ex: 0.1, orbit: 1 },
  { pos: [-2.3, -0.3, 0], rot: [0.2, -0.82, 0.02], s: 0.95, ex: 1, orbit: 0 },
  { pos: [-4.25, -1.9, 0], rot: [0.18, -0.6, 0.02], s: 0.42, ex: 0.5, orbit: 0 },
]

function Rig({ act, children }) {
  const g = useRef()
  const t0 = useRef(0)
  useFrame((state, dt) => {
    const A = ACTS[act]
    const o = g.current
    t0.current += dt
    const wob = (act === 0 ? Math.sin(t0.current * 0.35) * 0.12 : act === 1 ? Math.sin(t0.current * 0.25) * 0.04 : 0) + state.pointer.x * 0.1
    for (const [k, i] of [['x', 0], ['y', 1], ['z', 2]]) {
      o.position[k] = damp(o.position[k], A.pos[i], 2.6, dt)
      o.rotation[k] = damp(o.rotation[k], A.rot[i] + (k === 'y' ? wob : k === 'x' ? -state.pointer.y * 0.05 : 0), 2.6, dt)
    }
    o.scale.setScalar(damp(o.scale.x, A.s, 2.6, dt))
  })
  return <group ref={g}>{children}</group>
}

const LABELED = new Set(ACTIVE.slice(0, 6).map((r) => r.id))
const ACTIVE_SET = new Set(ACTIVE.map((r) => r.id))

function Orbit({ act, progress }) {
  const ring = useRef(), sweep = useRef(), dots = useRef([])
  const vis = useRef(1)
  const R = 3.45
  useFrame((_, dt) => {
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
      const on = ACTIVE_SET.has(r.id) && t >= activationT(r.id)
      const target = on ? 2.4 : s * Math.PI * 2 > regAngle(r.id) && t < 1.01 ? 0.75 : 1
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
        const on = ACTIVE_SET.has(r.id)
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
            {LABELED.has(r.id) && <OrbitLabel reg={r} progress={progress} act={act} />}
          </group>
        )
      })}
    </group>
  )
}

function OrbitLabel({ reg, progress, act }) {
  const el = useRef()
  useFrame(() => {
    if (!el.current) return
    const t = progress.current
    el.current.classList.toggle('on', t >= activationT(reg.id) && act === 0)
    const k = Math.min(1, Math.max(0, (t - activationT(reg.id)) / 0.12))
    const n = el.current.querySelector('.ol-n')
    if (n) n.textContent = String(Math.round(reg.count * k))
  })
  return (
    <Html center zIndexRange={[15, 0]} style={{ pointerEvents: 'none' }}>
      <div ref={el} className="orbit-label" style={{ '--c': regColor(reg.id) }}>
        <span className="ol-dot" />
        <span className="ol-id">{reg.id.replace('UN ', '')}</span>
        <span className="ol-n">0</span>
      </div>
    </Html>
  )
}

// Projiziert Ankerpunkte (Teile der Zeichnung, Objekt) auf den Bildschirm, für Hinweislinien im HTML
function AnchorProbe({ anchors, out }) {
  const { camera, size } = useThree()
  const v = useMemo(() => new THREE.Vector3(), [])
  useFrame(() => {
    for (const [key, a] of Object.entries(anchors.current)) {
      if (!a?.obj) continue
      v.set(...a.local)
      a.obj.localToWorld(v)
      v.project(camera)
      out.current[key] = { x: (v.x * 0.5 + 0.5) * size.width, y: (-v.y * 0.5 + 0.5) * size.height }
    }
  })
  return null
}

export default function Scene({ act, progress, segs, hovered, setHovered, picked, onPick, anchorOut }) {
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
      <ambientLight intensity={0.9} />
      <directionalLight position={[3, 6, 8]} intensity={1.4} castShadow shadow-mapSize={[2048, 2048]} />
      <Environment resolution={256}>
        <group rotation={[-Math.PI / 3, 0, 0]}>
          <Lightformer form="rect" intensity={4} position={[0, 5, -9]} scale={[12, 2, 1]} />
          <Lightformer form="rect" intensity={2} position={[-6, 1, 2]} rotation-y={Math.PI / 2} scale={[8, 2, 1]} />
          <Lightformer form="rect" intensity={2} position={[6, -1, 2]} rotation-y={-Math.PI / 2} scale={[8, 2, 1]} />
          <Lightformer form="ring" intensity={3} position={[0, 2, 6]} scale={3} />
        </group>
      </Environment>
      <Rig act={act}>
        <DrawingObject
          segs={segs}
          explodeTarget={ACTS[act].ex}
          hovered={act === 1 ? hovered : null}
          selected={act === 1 ? picked : null}
          interactive={act === 1}
          onHover={setHovered}
          onPick={onPick}
          anchors={anchors}
        />
        <Orbit act={act} progress={progress} />
      </Rig>
      <AnchorProbe anchors={anchors} out={anchorOut} />
      <ContactShadows position={[0, -2.3, 0]} opacity={0.32} scale={22} blur={2.8} far={5} />
      {!LITE && (
        <EffectComposer multisampling={4}>
          <Bloom luminanceThreshold={1} mipmapBlur intensity={0.9} radius={0.7} />
        </EffectComposer>
      )}
    </Canvas>
  )
}
