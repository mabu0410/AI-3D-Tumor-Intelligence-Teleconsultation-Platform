"use client";
/**
 * Module 7 — Patient Dashboard Component
 * Displays full patient profile and next scheduled follow-up appointments.
 */
import { useEffect, useState } from "react";

interface Schedule {
  id: string;
  scheduled_date: string;
  reason: string;
  status: string;
  notification_sent: boolean;
}

interface PatientProfile {
  id: string;
  name: string;
  dicom_id: string | null;
  gender: string;
  age: number;
  phone: string | null;
  email: string | null;
  schedules: Schedule[];
}

interface PatientDashboardProps {
  patientId: string;
  apiBaseUrl?: string;
}

export default function PatientDashboard({ patientId, apiBaseUrl = "/api/v1" }: PatientDashboardProps) {
  const [patient, setPatient] = useState<PatientProfile | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchPatient = () => {
    setLoading(true);
    fetch(`${apiBaseUrl}/scheduling/patient/${patientId}`)
      .then((r) => r.json())
      .then((data) => setPatient(data))
      .catch((e) => console.error("Failed to load patient:", e))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchPatient();
  }, [patientId, apiBaseUrl]);

  const handleSendReminder = async (scheduleId: string) => {
    try {
      const res = await fetch(`${apiBaseUrl}/scheduling/send-manual-reminder/${scheduleId}`, {
        method: "POST",
      });
      if (res.ok) fetchPatient(); // refresh to show "Sent" badge
    } catch {}
  };

  if (loading) {
    return (
      <div style={{ background: "#1e293b", borderRadius: 16, padding: 32, textAlign: "center", color: "#64748b" }}>
        Loading patient profile...
      </div>
    );
  }

  if (!patient || !patient.name) {
    return (
      <div style={{ background: "#1e293b", borderRadius: 16, padding: 32, textAlign: "center", color: "#ef4444" }}>
        Patient not found.
      </div>
    );
  }

  return (
    <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: 20, fontFamily: "Inter, sans-serif" }}>
      {/* Sidebar: Patient Info */}
      <div style={{ background: "#0f172a", borderRadius: 16, border: "1px solid #1e293b", padding: 24 }}>
        <div style={{ textAlign: "center", marginBottom: 20 }}>
          <div style={{
            width: 80, height: 80, borderRadius: "50%", background: "#6366f1",
            margin: "0 auto 12px", display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 32, color: "#fff", fontWeight: 700,
          }}>
            {patient.name.charAt(0)}
          </div>
          <h2 style={{ margin: 0, fontSize: 18, color: "#f1f5f9", fontWeight: 700 }}>{patient.name}</h2>
          <div style={{ fontSize: 13, color: "#94a3b8", marginTop: 4 }}>ID: {patient.dicom_id || patient.id.slice(0, 8)}</div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13 }}>
            <span style={{ color: "#64748b" }}>Age</span>
            <span style={{ color: "#e2e8f0", fontWeight: 600 }}>{patient.age}</span>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13 }}>
            <span style={{ color: "#64748b" }}>Gender</span>
            <span style={{ color: "#e2e8f0", fontWeight: 600 }}>{patient.gender}</span>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13 }}>
            <span style={{ color: "#64748b" }}>Phone</span>
            <span style={{ color: "#e2e8f0", fontWeight: 600 }}>{patient.phone || "—"}</span>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, borderTop: "1px solid #1e293b", paddingTop: 12 }}>
            <span style={{ color: "#64748b" }}>Email</span>
            <span style={{ color: "#e2e8f0", fontWeight: 600 }}>{patient.email || "—"}</span>
          </div>
        </div>
      </div>

      {/* Main: Schedules */}
      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        <h3 style={{ margin: 0, fontSize: 16, color: "#f1f5f9", fontWeight: 600, display: "flex", alignItems: "center", gap: 8 }}>
          📅 Follow-up Schedule
        </h3>

        {patient.schedules.length === 0 ? (
          <div style={{ background: "#1e293b", borderRadius: 12, padding: 32, textAlign: "center", color: "#64748b" }}>
            <div style={{ fontSize: 28, marginBottom: 8 }}>⛱️</div>
            No upcoming schedules.
          </div>
        ) : (
          patient.schedules.map((s) => {
            const date = new Date(s.scheduled_date);
            const isPast = date < new Date();
            const color = s.status === "completed" ? "#22c55e" : s.status === "cancelled" ? "#64748b" : isPast ? "#ef4444" : "#f59e0b";

            return (
              <div key={s.id} style={{
                background: "#1e293b", borderRadius: 12, padding: 20,
                borderLeft: `4px solid ${color}`,
                display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16,
              }}>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                    <span style={{ color: "#f1f5f9", fontSize: 16, fontWeight: 700 }}>
                      {date.toLocaleDateString("en-GB", { day: "2-digit", month: "long", year: "numeric" })}
                    </span>
                    <span style={{
                      padding: "2px 8px", borderRadius: 12, fontSize: 10, fontWeight: 700, textTransform: "uppercase",
                      background: `${color}22`, color: color,
                    }}>
                      {s.status}
                    </span>
                    {s.notification_sent && (
                      <span style={{ padding: "2px 8px", borderRadius: 12, fontSize: 10, background: "#166534", color: "#4ade80" }}>
                        🔔 Sent
                      </span>
                    )}
                  </div>
                  <div style={{ color: "#94a3b8", fontSize: 13 }}>{s.reason}</div>
                </div>

                {s.status === "scheduled" && (
                  <button
                    onClick={() => handleSendReminder(s.id)}
                    style={{
                      background: "#0f172a", border: "1px solid #334155", borderRadius: 8,
                      padding: "8px 14px", color: "#e2e8f0", fontSize: 12, fontWeight: 600,
                      cursor: "pointer", transition: "all 0.2s", whiteSpace: "nowrap",
                    }}
                  >
                    Send SMS Reminder
                  </button>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
