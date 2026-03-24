"use client";
/**
 * Module 4 — Risk Score Card Component
 * Displays classification result with visual risk indicators.
 */

interface ClassificationResult {
  label: "benign" | "malignant" | "indeterminate" | null;
  malignancy_probability: number | null;
  risk_score: number | null;
  risk_level: "Low" | "Moderate" | "High" | null;
  recommendation: string | null;
  color: "green" | "orange" | "red" | null;
  model_used: string | null;
  cnn_result?: { malignant_prob: number; model: string } | null;
  xgboost_result?: { malignant_prob: number } | null;
}

interface RiskScoreCardProps {
  caseId: string;
  result: ClassificationResult | null;
  isLoading?: boolean;
}

const COLORS = {
  green: { bg: "#052e16", border: "#22c55e", text: "#22c55e", badge: "#166534" },
  orange: { bg: "#431407", border: "#f59e0b", text: "#f59e0b", badge: "#92400e" },
  red: { bg: "#450a0a", border: "#ef4444", text: "#ef4444", badge: "#7f1d1d" },
};

const LabelIcon = ({ label }: { label: string | null }) => {
  if (label === "benign") return <span>✅</span>;
  if (label === "malignant") return <span>⚠️</span>;
  return <span>🔍</span>;
};

const ProbabilityBar = ({ value, color }: { value: number; color: string }) => (
  <div style={{ marginTop: 8 }}>
    <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "#94a3b8", marginBottom: 4 }}>
      <span>Benign</span>
      <span>Malignant</span>
    </div>
    <div style={{ height: 8, background: "#1e293b", borderRadius: 4, overflow: "hidden" }}>
      <div style={{
        height: "100%",
        width: `${(value ?? 0) * 100}%`,
        background: color === "green"
          ? "linear-gradient(90deg, #22c55e, #16a34a)"
          : color === "red"
          ? "linear-gradient(90deg, #f59e0b, #ef4444)"
          : "linear-gradient(90deg, #f59e0b, #f97316)",
        borderRadius: 4,
        transition: "width 0.8s ease",
      }} />
    </div>
  </div>
);

export default function RiskScoreCard({ caseId, result, isLoading }: RiskScoreCardProps) {
  if (isLoading) {
    return (
      <div style={{
        background: "#1e293b", borderRadius: 16, padding: 24,
        border: "1px solid #334155", textAlign: "center", color: "#94a3b8",
      }}>
        <div style={{ fontSize: 32, marginBottom: 12 }}>🔬</div>
        <div>Analyzing tumor characteristics...</div>
        <div style={{
          height: 4, background: "#334155", borderRadius: 2, margin: "16px 0 0",
          overflow: "hidden",
        }}>
          <div style={{
            height: "100%", width: "60%", background: "#6366f1",
            borderRadius: 2, animation: "pulse 1.5s infinite",
          }} />
        </div>
      </div>
    );
  }

  if (!result || result.label === null) {
    return (
      <div style={{
        background: "#1e293b", borderRadius: 16, padding: 24,
        border: "1px dashed #334155", textAlign: "center", color: "#94a3b8",
      }}>
        <div style={{ fontSize: 28, marginBottom: 8 }}>🧠</div>
        <div style={{ fontSize: 14 }}>Classification not yet run</div>
        <div style={{ fontSize: 12, marginTop: 4, color: "#475569" }}>
          Run segmentation → features → classification
        </div>
      </div>
    );
  }

  const colors = COLORS[result.color ?? "orange"];
  const riskPercent = Math.round((result.risk_score ?? 0) * 100);
  const malPercent = Math.round((result.malignancy_probability ?? 0) * 100);

  return (
    <div style={{
      background: colors.bg, borderRadius: 16, padding: 24,
      border: `2px solid ${colors.border}`,
    }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 20 }}>
        <div style={{ fontSize: 36 }}>
          <LabelIcon label={result.label} />
        </div>
        <div>
          <div style={{
            display: "inline-block", padding: "3px 12px", borderRadius: 20,
            background: colors.badge, color: colors.text,
            fontSize: 13, fontWeight: 700, textTransform: "uppercase",
          }}>
            {result.label?.replace("_", " ")} — {result.risk_level} Risk
          </div>
          <div style={{ color: "#94a3b8", fontSize: 11, marginTop: 4 }}>
            Case {caseId.slice(0, 8)}…
          </div>
        </div>
      </div>

      {/* Risk Score Gauge */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
          <span style={{ fontSize: 12, color: "#94a3b8" }}>Risk Score</span>
          <span style={{ fontSize: 20, fontWeight: 800, color: colors.text }}>
            {riskPercent}%
          </span>
        </div>
        <div style={{ height: 12, background: "#0f172a", borderRadius: 6, overflow: "hidden" }}>
          <div style={{
            height: "100%",
            width: `${riskPercent}%`,
            background: `linear-gradient(90deg, #22c55e, #f59e0b, #ef4444)`,
            borderRadius: 6,
            transition: "width 1s ease",
          }} />
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", marginTop: 4, fontSize: 10, color: "#475569" }}>
          <span>0%</span><span>35%</span><span>65%</span><span>100%</span>
        </div>
      </div>

      {/* Model breakdown */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 20 }}>
        <div style={{ background: "#0f172a", borderRadius: 10, padding: 12 }}>
          <div style={{ fontSize: 11, color: "#64748b", marginBottom: 4 }}>3D CNN</div>
          <div style={{ fontSize: 22, fontWeight: 700, color: colors.text }}>
            {Math.round((result.cnn_result?.malignant_prob ?? 0) * 100)}%
          </div>
          <ProbabilityBar
            value={result.cnn_result?.malignant_prob ?? 0}
            color={result.color ?? "orange"}
          />
        </div>
        <div style={{ background: "#0f172a", borderRadius: 10, padding: 12 }}>
          <div style={{ fontSize: 11, color: "#64748b", marginBottom: 4 }}>XGBoost</div>
          <div style={{ fontSize: 22, fontWeight: 700, color: colors.text }}>
            {Math.round((result.xgboost_result?.malignant_prob ?? 0) * 100)}%
          </div>
          <ProbabilityBar
            value={result.xgboost_result?.malignant_prob ?? 0}
            color={result.color ?? "orange"}
          />
        </div>
      </div>

      {/* Recommendation */}
      <div style={{
        background: "#0f172a", borderRadius: 10, padding: 14,
        borderLeft: `3px solid ${colors.border}`,
      }}>
        <div style={{ fontSize: 11, color: "#64748b", marginBottom: 4 }}>📋 Recommendation</div>
        <div style={{ fontSize: 13, color: "#e2e8f0", lineHeight: 1.6 }}>
          {result.recommendation}
        </div>
      </div>

      {/* Model badge */}
      {result.model_used && (
        <div style={{ marginTop: 12, textAlign: "right", fontSize: 10, color: "#334155" }}>
          Model: {result.model_used}
        </div>
      )}
    </div>
  );
}
