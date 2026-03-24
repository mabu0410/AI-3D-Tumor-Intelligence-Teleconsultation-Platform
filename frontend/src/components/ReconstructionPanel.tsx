"use client";
/**
 * Module 2 — Reconstruction Dashboard Panel
 * Shows geometric features alongside the 3D viewer.
 */
import dynamic from "next/dynamic";

// Dynamically import Three.js viewer to avoid SSR issues
const TumorViewer3D = dynamic(() => import("./TumorViewer3D"), { ssr: false });

interface GeometricFeatures {
  volume_mm3: number;
  surface_area_mm2: number;
  sphericity: number;
  roughness_index: number;
  compactness: number;
  elongation: number;
  max_diameter_mm: number;
}

interface ReconstructionPanelProps {
  caseId: string;
  features: GeometricFeatures | null;
  meshUrl: string;
}

const MetricCard = ({ label, value, unit, color }: {
  label: string; value: number | null; unit: string; color: string;
}) => (
  <div style={{
    background: "#1e293b", borderRadius: 10, padding: "14px 16px",
    borderLeft: `3px solid ${color}`,
  }}>
    <div style={{ color: "#94a3b8", fontSize: 11, marginBottom: 6 }}>{label}</div>
    <div style={{ color: "#f1f5f9", fontSize: 20, fontWeight: 700 }}>
      {value != null ? value.toLocaleString("en", { maximumFractionDigits: 3 }) : "—"}
      <span style={{ fontSize: 12, color: "#94a3b8", marginLeft: 4 }}>{unit}</span>
    </div>
  </div>
);

const SphericitySemaphore = ({ value }: { value: number | null }) => {
  if (value == null) return null;
  const color = value >= 0.8 ? "#22c55e" : value >= 0.6 ? "#f59e0b" : "#ef4444";
  const label = value >= 0.8 ? "Regular (Low Risk)" : value >= 0.6 ? "Moderate" : "Irregular (High Risk)";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 8 }}>
      <div style={{ width: 10, height: 10, borderRadius: "50%", background: color }} />
      <span style={{ fontSize: 12, color }}>{label}</span>
    </div>
  );
};

export default function ReconstructionPanel({ caseId, features, meshUrl }: ReconstructionPanelProps) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 320px", gap: 20, height: 520 }}>
      {/* 3D Viewer */}
      <div style={{ borderRadius: 16, overflow: "hidden", background: "#0f172a", border: "1px solid #334155" }}>
        <TumorViewer3D meshUrl={meshUrl} caseId={caseId} />
      </div>

      {/* Features panel */}
      <div style={{ display: "flex", flexDirection: "column", gap: 12, overflowY: "auto" }}>
        <h3 style={{ color: "#f1f5f9", fontSize: 14, fontWeight: 600, margin: 0 }}>
          📐 Geometric Features
        </h3>

        <MetricCard label="Volume" value={features?.volume_mm3 ?? null} unit="mm³" color="#6366f1" />
        <MetricCard label="Surface Area" value={features?.surface_area_mm2 ?? null} unit="mm²" color="#06b6d4" />
        <MetricCard label="Max Diameter" value={features?.max_diameter_mm ?? null} unit="mm" color="#f59e0b" />
        <MetricCard label="Elongation" value={features?.elongation ?? null} unit="" color="#8b5cf6" />

        {/* Sphericity with visual indicator */}
        <div style={{
          background: "#1e293b", borderRadius: 10, padding: "14px 16px",
          borderLeft: "3px solid #22c55e",
        }}>
          <div style={{ color: "#94a3b8", fontSize: 11, marginBottom: 6 }}>Sphericity</div>
          <div style={{ color: "#f1f5f9", fontSize: 20, fontWeight: 700 }}>
            {features?.sphericity != null ? features.sphericity.toFixed(4) : "—"}
          </div>
          <SphericitySemaphore value={features?.sphericity ?? null} />
          {/* Visual bar */}
          <div style={{ marginTop: 8, height: 4, background: "#334155", borderRadius: 2 }}>
            <div style={{
              height: "100%", borderRadius: 2,
              width: `${(features?.sphericity ?? 0) * 100}%`,
              background: "linear-gradient(90deg, #ef4444, #f59e0b, #22c55e)",
              transition: "width 0.6s ease",
            }} />
          </div>
        </div>

        {/* Roughness */}
        <div style={{
          background: "#1e293b", borderRadius: 10, padding: "14px 16px",
          borderLeft: "3px solid #ef4444",
        }}>
          <div style={{ color: "#94a3b8", fontSize: 11, marginBottom: 6 }}>Surface Roughness</div>
          <div style={{ color: "#f1f5f9", fontSize: 20, fontWeight: 700 }}>
            {features?.roughness_index != null ? features.roughness_index.toFixed(6) : "—"}
          </div>
          <div style={{ color: "#94a3b8", fontSize: 11, marginTop: 4 }}>
            {features?.roughness_index != null
              ? features.roughness_index > 0.3 ? "⚠️ High irregularity" : "✅ Normal surface"
              : ""}
          </div>
        </div>

        {/* Download buttons */}
        <div style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 4 }}>
          <a
            href={`/api/v1/reconstruction/mesh/${caseId}/stl`}
            style={{
              padding: "10px 0", borderRadius: 8, background: "#1e293b",
              color: "#6366f1", textAlign: "center", fontSize: 13, fontWeight: 600,
              border: "1px solid #334155", textDecoration: "none",
            }}
          >
            ⬇ Download STL (3D Print)
          </a>
          <a
            href={`/api/v1/reconstruction/mesh/${caseId}/obj`}
            style={{
              padding: "10px 0", borderRadius: 8, background: "#1e293b",
              color: "#94a3b8", textAlign: "center", fontSize: 13,
              border: "1px solid #334155", textDecoration: "none",
            }}
          >
            ⬇ Download OBJ
          </a>
        </div>
      </div>
    </div>
  );
}
