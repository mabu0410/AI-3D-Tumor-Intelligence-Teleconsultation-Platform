"use client";
/**
 * Module 2 — Three.js 3D Tumor Viewer
 * Loads a GLB mesh from the backend and renders it with:
 *   - Orbit controls (rotate/zoom/pan)
 *   - Ambient + directional lighting
 *   - Toggle: wireframe / solid / cross-section
 *   - Tumor annotation markers
 */
import { useEffect, useRef, useState, useCallback } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader";

interface TumorViewerProps {
  meshUrl: string;      // e.g. /api/v1/reconstruction/mesh/{caseId}/glb
  caseId: string;
  onFeaturesLoaded?: (features: Record<string, number>) => void;
}

type RenderMode = "solid" | "wireframe" | "transparent";

export default function TumorViewer3D({ meshUrl, caseId, onFeaturesLoaded }: TumorViewerProps) {
  const mountRef = useRef<HTMLDivElement>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const meshRef = useRef<THREE.Group | null>(null);
  const [renderMode, setRenderMode] = useState<RenderMode>("solid");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const applyRenderMode = useCallback((mode: RenderMode) => {
    if (!meshRef.current) return;
    meshRef.current.traverse((child) => {
      if (child instanceof THREE.Mesh) {
        const mat = child.material as THREE.MeshStandardMaterial;
        if (mode === "wireframe") {
          mat.wireframe = true;
          mat.transparent = false;
          mat.opacity = 1;
        } else if (mode === "transparent") {
          mat.wireframe = false;
          mat.transparent = true;
          mat.opacity = 0.45;
        } else {
          mat.wireframe = false;
          mat.transparent = false;
          mat.opacity = 1;
        }
      }
    });
  }, []);

  useEffect(() => {
    if (!mountRef.current) return;
    const container = mountRef.current;
    const width = container.clientWidth;
    const height = container.clientHeight;

    // ── Scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0f172a);
    scene.fog = new THREE.Fog(0x0f172a, 50, 200);

    // ── Camera
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(0, 0, 80);

    // ── Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    container.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // ── Lighting
    const ambient = new THREE.AmbientLight(0xffffff, 0.4);
    scene.add(ambient);

    const dirLight = new THREE.DirectionalLight(0xffffff, 1.2);
    dirLight.position.set(50, 80, 60);
    dirLight.castShadow = true;
    scene.add(dirLight);

    const fillLight = new THREE.DirectionalLight(0x6366f1, 0.6);
    fillLight.position.set(-40, -20, -30);
    scene.add(fillLight);

    const rimLight = new THREE.PointLight(0x06b6d4, 0.8, 150);
    rimLight.position.set(0, 50, -50);
    scene.add(rimLight);

    // ── Grid helper
    const grid = new THREE.GridHelper(100, 20, 0x334155, 0x1e293b);
    grid.position.y = -30;
    scene.add(grid);

    // ── Controls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.minDistance = 10;
    controls.maxDistance = 300;
    controls.autoRotate = false;
    controls.autoRotateSpeed = 1.5;

    // ── Load GLB mesh
    const loader = new GLTFLoader();
    loader.load(
      meshUrl,
      (gltf) => {
        const group = gltf.scene;
        meshRef.current = group;

        // Auto-center and scale
        const box = new THREE.Box3().setFromObject(group);
        const center = box.getCenter(new THREE.Vector3());
        const size = box.getSize(new THREE.Vector3());
        const maxDim = Math.max(size.x, size.y, size.z);
        const scale = 40 / maxDim;

        group.position.sub(center);
        group.scale.setScalar(scale);

        // Apply tumor material (pinkish-red, semi-transparent)
        group.traverse((child) => {
          if (child instanceof THREE.Mesh) {
            child.castShadow = true;
            child.receiveShadow = true;
            child.material = new THREE.MeshStandardMaterial({
              color: 0xe05252,
              roughness: 0.45,
              metalness: 0.1,
              side: THREE.DoubleSide,
            });
          }
        });

        scene.add(group);
        setLoading(false);
      },
      (progress) => {
        // progress event
      },
      (err) => {
        setError(`Failed to load mesh: ${err}`);
        setLoading(false);
      }
    );

    // ── Resize handler
    const handleResize = () => {
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener("resize", handleResize);

    // ── Animation loop
    let frameId: number;
    const animate = () => {
      frameId = requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    return () => {
      cancelAnimationFrame(frameId);
      window.removeEventListener("resize", handleResize);
      controls.dispose();
      renderer.dispose();
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, [meshUrl]);

  // Apply render mode changes
  useEffect(() => {
    applyRenderMode(renderMode);
  }, [renderMode, applyRenderMode]);

  const btnStyle = (active: boolean): React.CSSProperties => ({
    padding: "6px 14px",
    borderRadius: "6px",
    border: "none",
    cursor: "pointer",
    fontSize: "12px",
    fontWeight: 600,
    background: active ? "#6366f1" : "#1e293b",
    color: active ? "#fff" : "#94a3b8",
    transition: "all 0.2s",
  });

  return (
    <div style={{ position: "relative", width: "100%", height: "100%", minHeight: 480 }}>
      {/* Canvas mount */}
      <div ref={mountRef} style={{ width: "100%", height: "100%", borderRadius: 12 }} />

      {/* Loading overlay */}
      {loading && (
        <div style={{
          position: "absolute", inset: 0, display: "flex", alignItems: "center",
          justifyContent: "center", background: "rgba(15,23,42,0.85)", borderRadius: 12,
        }}>
          <div style={{ textAlign: "center", color: "#94a3b8" }}>
            <div style={{ fontSize: 36, marginBottom: 12 }}>🧠</div>
            <div>Loading 3D model...</div>
          </div>
        </div>
      )}

      {/* Error overlay */}
      {error && (
        <div style={{
          position: "absolute", inset: 0, display: "flex", alignItems: "center",
          justifyContent: "center", background: "rgba(15,23,42,0.9)", borderRadius: 12,
        }}>
          <div style={{ color: "#ef4444", textAlign: "center" }}>
            <div style={{ fontSize: 28, marginBottom: 8 }}>⚠️</div>
            <div>{error}</div>
          </div>
        </div>
      )}

      {/* Controls bar */}
      {!loading && !error && (
        <div style={{
          position: "absolute", top: 16, left: 16,
          display: "flex", gap: 8,
          background: "rgba(15,23,42,0.8)",
          padding: "8px 12px",
          borderRadius: 8,
          backdropFilter: "blur(8px)",
        }}>
          <span style={{ color: "#94a3b8", fontSize: 12, alignSelf: "center", marginRight: 4 }}>View:</span>
          {(["solid", "wireframe", "transparent"] as RenderMode[]).map((mode) => (
            <button key={mode} style={btnStyle(renderMode === mode)} onClick={() => setRenderMode(mode)}>
              {mode.charAt(0).toUpperCase() + mode.slice(1)}
            </button>
          ))}
        </div>
      )}

      {/* Case ID badge */}
      <div style={{
        position: "absolute", bottom: 12, right: 16,
        fontSize: 10, color: "#334155",
        fontFamily: "monospace",
      }}>
        Case: {caseId.slice(0, 8)}…
      </div>
    </div>
  );
}
