"use client";
/**
 * Module 5 — Progression Chart Component
 * Recharts area chart showing tumor volume & malignancy over time:
 *   - Historical measurements (solid line)
 *   - 3-month forecast (dashed)
 *   - 6-month forecast (dashed, lighter)
 *   - Invasion speed badge
 */
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ReferenceLine, ResponsiveContainer,
} from "recharts";

interface TimePoint {
  label: string;           // e.g. "Baseline", "3 months", "6 months"
  volume_mm3?: number;
  malignancy_prob?: number;
  isForecast?: boolean;
}

interface ProgressionChartProps {
  patientId: string;
  current?: { volume_mm3: number; malignancy_probability: number; scan_date: string } | null;
  prediction3m?: { volume_mm3: number; malignancy_probability: number; volume_change_pct: number; risk_level: string } | null;
  prediction6m?: { volume_mm3: number; malignancy_probability: number; volume_change_pct: number; risk_level: string } | null;
  invasionSpeed?: string | null;
  invasionProbs?: { slow: number; medium: number; fast: number } | null;
}

const INVASION_COLORS: Record<string, string> = {
  Slow: "#22c55e",
  Medium: "#f59e0b",
  Fast: "#ef4444",
};

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: "#1e293b", border: "1px solid #334155",
      borderRadius: 10, padding: "12px 16px", fontSize: 12,
    }}>
      <div style={{ fontWeight: 700, color: "#f1f5f9", marginBottom: 6 }}>{label}</div>
      {payload.map((p: any) => (
        <div key={p.name} style={{ color: p.color, marginBottom: 2 }}>
          {p.name}: <strong>{typeof p.value === "number" ? p.value.toFixed(2) : p.value}</strong>
          {p.name.includes("Volume") ? " mm³" : "%"}
        </div>
      ))}
    </div>
  );
};

export default function ProgressionChart({
  patientId, current, prediction3m, prediction6m, invasionSpeed, invasionProbs,
}: ProgressionChartProps) {
  const invasionColor = INVASION_COLORS[invasionSpeed ?? "Slow"] ?? "#6366f1";

  // Build chart data
  const chartData: any[] = [];
  if (current) {
    chartData.push({
      label: "Current",
      volume: Math.round(current.volume_mm3),
      malignancy: Math.round(current.malignancy_probability * 100),
      isForecast: false,
    });
  }
  if (prediction3m) {
    chartData.push({
      label: "+3 months",
      volume_forecast: Math.round(prediction3m.volume_mm3 ?? 0),
      malignancy_forecast: Math.round((prediction3m.malignancy_probability ?? 0) * 100),
      isForecast: true,
    });
  }
  if (prediction6m) {
    chartData.push({
      label: "+6 months",
      volume_forecast: Math.round(prediction6m.volume_mm3 ?? 0),
      malignancy_forecast: Math.round((prediction6m.malignancy_probability ?? 0) * 100),
      isForecast: true,
    });
  }

  if (chartData.length === 0) {
    return (
      <div style={{
        background: "#1e293b", borderRadius: 16, padding: 32,
        textAlign: "center", color: "#94a3b8",
      }}>
        <div style={{ fontSize: 32, marginBottom: 10 }}>📈</div>
        <div>No prediction data yet.</div>
        <div style={{ fontSize: 12, color: "#475569", marginTop: 4 }}>
          Run classification on at least 2 timepoints first.
        </div>
      </div>
    );
  }

  return (
    <div style={{ background: "#0f172a", borderRadius: 16, padding: 24, border: "1px solid #1e293b" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 24 }}>
        <div>
          <h3 style={{ color: "#f1f5f9", fontSize: 16, fontWeight: 700, margin: 0 }}>
            📈 Tumor Progression Forecast
          </h3>
          <div style={{ color: "#64748b", fontSize: 12, marginTop: 4 }}>
            Patient {patientId.slice(0, 8)}…
          </div>
        </div>

        {/* Invasion speed badge */}
        {invasionSpeed && (
          <div style={{
            background: `${invasionColor}22`, border: `1px solid ${invasionColor}`,
            borderRadius: 20, padding: "4px 14px",
            color: invasionColor, fontSize: 13, fontWeight: 700,
          }}>
            {invasionSpeed === "Fast" ? "⚡" : invasionSpeed === "Medium" ? "⚠️" : "✅"} {invasionSpeed} Growth
          </div>
        )}
      </div>

      {/* 3m / 6m quick stats */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 24 }}>
        {prediction3m && (
          <div style={{
            background: "#1e293b", borderRadius: 12, padding: 16,
            borderLeft: "3px solid #6366f1",
          }}>
            <div style={{ color: "#94a3b8", fontSize: 11 }}>3-Month Forecast</div>
            <div style={{ color: "#f1f5f9", fontSize: 22, fontWeight: 800, marginTop: 4 }}>
              {prediction3m.volume_change_pct >= 0 ? "+" : ""}{prediction3m.volume_change_pct?.toFixed(1)}%
            </div>
            <div style={{ fontSize: 12, marginTop: 2 }}>
              <span style={{
                color: prediction3m.risk_level === "High" ? "#ef4444" :
                       prediction3m.risk_level === "Moderate" ? "#f59e0b" : "#22c55e",
              }}>
                ● {prediction3m.risk_level} Risk
              </span>
            </div>
          </div>
        )}
        {prediction6m && (
          <div style={{
            background: "#1e293b", borderRadius: 12, padding: 16,
            borderLeft: "3px solid #8b5cf6",
          }}>
            <div style={{ color: "#94a3b8", fontSize: 11 }}>6-Month Forecast</div>
            <div style={{ color: "#f1f5f9", fontSize: 22, fontWeight: 800, marginTop: 4 }}>
              {prediction6m.volume_change_pct >= 0 ? "+" : ""}{prediction6m.volume_change_pct?.toFixed(1)}%
            </div>
            <div style={{ fontSize: 12, marginTop: 2 }}>
              <span style={{
                color: prediction6m.risk_level === "High" ? "#ef4444" :
                       prediction6m.risk_level === "Moderate" ? "#f59e0b" : "#22c55e",
              }}>
                ● {prediction6m.risk_level} Risk
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Volume chart */}
      <div style={{ marginBottom: 8 }}>
        <div style={{ color: "#64748b", fontSize: 11, marginBottom: 8 }}>VOLUME (mm³)</div>
        <ResponsiveContainer width="100%" height={180}>
          <AreaChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="volGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="volForeGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.2} />
                <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="label" tick={{ fill: "#64748b", fontSize: 11 }} />
            <YAxis tick={{ fill: "#64748b", fontSize: 11 }} />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone" dataKey="volume" name="Volume (actual)"
              stroke="#6366f1" fill="url(#volGrad)" strokeWidth={2}
              connectNulls
            />
            <Area
              type="monotone" dataKey="volume_forecast" name="Volume (forecast)"
              stroke="#8b5cf6" fill="url(#volForeGrad)"
              strokeWidth={2} strokeDasharray="6 3" connectNulls
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Malignancy chart */}
      <div>
        <div style={{ color: "#64748b", fontSize: 11, marginBottom: 8 }}>MALIGNANCY RISK (%)</div>
        <ResponsiveContainer width="100%" height={130}>
          <AreaChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="malGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="label" tick={{ fill: "#64748b", fontSize: 11 }} />
            <YAxis domain={[0, 100]} tick={{ fill: "#64748b", fontSize: 11 }} />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine y={65} stroke="#ef444460" strokeDasharray="4 2" label={{ value: "High Risk", fill: "#ef4444", fontSize: 9 }} />
            <ReferenceLine y={35} stroke="#f59e0b60" strokeDasharray="4 2" label={{ value: "Moderate", fill: "#f59e0b", fontSize: 9 }} />
            <Area
              type="monotone" dataKey="malignancy" name="Malignancy (actual)"
              stroke="#ef4444" fill="url(#malGrad)" strokeWidth={2} connectNulls
            />
            <Area
              type="monotone" dataKey="malignancy_forecast" name="Malignancy (forecast)"
              stroke="#f97316" fill="none" strokeWidth={2} strokeDasharray="6 3" connectNulls
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Invasion speed breakdown */}
      {invasionProbs && (
        <div style={{ marginTop: 20, display: "flex", gap: 8 }}>
          {Object.entries(invasionProbs).map(([speed, prob]) => (
            <div key={speed} style={{
              flex: 1, background: "#1e293b", borderRadius: 8, padding: "10px 12px",
              borderTop: `3px solid ${INVASION_COLORS[speed.charAt(0).toUpperCase() + speed.slice(1)] ?? "#6366f1"}`,
            }}>
              <div style={{ fontSize: 10, color: "#64748b" }}>{speed.toUpperCase()}</div>
              <div style={{ fontSize: 18, fontWeight: 700, color: "#f1f5f9" }}>
                {Math.round((prob as number) * 100)}%
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
