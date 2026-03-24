"use client";
/**
 * Module 6 — Teleconsultation Room
 * Real-time consultation UI with:
 *   - WebSocket connection to /api/v1/telemedicine/ws/{consultationId}
 *   - Live chat between specialist and referring doctor
 *   - Annotation list from backend
 *   - E-signature button
 *   - Participant list
 */
import { useEffect, useRef, useState, useCallback } from "react";

interface ChatMessage {
  user_id: string;
  role: string;
  message: string;
  timestamp: string;
}

interface Annotation {
  label: string;
  x: number;
  y: number;
  z: number;
  timestamp?: string;
  user_id?: string;
}

interface ConsultationRoomProps {
  consultationId: string;
  currentUserId: string;
  currentUserRole: "specialist" | "doctor" | "viewer";
  apiBaseUrl?: string;
}

const WS_BASE = typeof window !== "undefined"
  ? `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}`
  : "ws://localhost:8000";

export default function ConsultationRoom({
  consultationId,
  currentUserId,
  currentUserRole,
  apiBaseUrl = "/api/v1",
}: ConsultationRoomProps) {
  const wsRef = useRef<WebSocket | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  const [connected, setConnected] = useState(false);
  const [participants, setParticipants] = useState<{ user_id: string; role: string }[]>([]);
  const [chat, setChat] = useState<ChatMessage[]>([]);
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [notes, setNotes] = useState("");
  const [status, setStatus] = useState("pending");
  const [signedAt, setSignedAt] = useState<string | null>(null);
  const [isSigning, setIsSigning] = useState(false);

  // Connect WebSocket
  useEffect(() => {
    const wsUrl = `${WS_BASE}${apiBaseUrl}/telemedicine/ws/${consultationId}?user_id=${currentUserId}&role=${currentUserRole}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        handleMessage(msg);
      } catch {}
    };

    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);

    // Load current participants on mount
    fetch(`${apiBaseUrl}/telemedicine/${consultationId}/participants`)
      .then((r) => r.json())
      .then((d) => setParticipants(d.participants ?? []))
      .catch(() => {});

    // Load consultation detail
    fetch(`${apiBaseUrl}/telemedicine/${consultationId}`)
      .then((r) => r.json())
      .then((d) => {
        setStatus(d.status ?? "pending");
        setNotes(d.notes ?? "");
        if (d.annotations?.markers) setAnnotations(d.annotations.markers);
        if (d.signed_at) setSignedAt(d.signed_at);
      })
      .catch(() => {});

    return () => {
      ws.close();
    };
  }, [consultationId, currentUserId, currentUserRole, apiBaseUrl]);

  const handleMessage = useCallback((msg: any) => {
    switch (msg.type) {
      case "user_joined":
        setParticipants((p) => [...p.filter((u) => u.user_id !== msg.user_id), { user_id: msg.user_id, role: msg.role }]);
        break;
      case "user_left":
        setParticipants((p) => p.filter((u) => u.user_id !== msg.user_id));
        break;
      case "chat":
        setChat((c) => [...c, msg as ChatMessage]);
        setTimeout(() => chatEndRef.current?.scrollIntoView({ behavior: "smooth" }), 50);
        break;
      case "annotation":
        if (msg.data?.markers) setAnnotations(msg.data.markers);
        break;
      case "signed":
        setStatus("completed");
        setSignedAt(msg.signed_at);
        break;
    }
  }, []);

  const sendChat = () => {
    if (!chatInput.trim() || !wsRef.current || !connected) return;
    wsRef.current.send(JSON.stringify({
      type: "chat",
      message: chatInput.trim(),
    }));
    setChat((c) => [...c, {
      user_id: currentUserId,
      role: currentUserRole,
      message: chatInput.trim(),
      timestamp: new Date().toISOString(),
    }]);
    setChatInput("");
    setTimeout(() => chatEndRef.current?.scrollIntoView({ behavior: "smooth" }), 50);
  };

  const handleSign = async () => {
    if (currentUserRole !== "specialist") return;
    setIsSigning(true);
    try {
      const res = await fetch(`${apiBaseUrl}/telemedicine/sign/${consultationId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ specialist_id: currentUserId }),
      });
      if (res.ok) {
        const data = await res.json();
        setStatus("completed");
        setSignedAt(data.signed_at);
      }
    } finally {
      setIsSigning(false);
    }
  };

  const handleSaveNotes = async () => {
    await fetch(`${apiBaseUrl}/telemedicine/annotate/${consultationId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ annotations: { markers: annotations }, notes }),
    });
  };

  const statusColor: Record<string, string> = {
    pending: "#f59e0b",
    in_review: "#6366f1",
    completed: "#22c55e",
  };

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 320px", gap: 16, height: "80vh", fontFamily: "Inter, sans-serif" }}>
      {/* Main panel */}
      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        {/* Status bar */}
        <div style={{
          background: "#1e293b", borderRadius: 12, padding: "12px 20px",
          display: "flex", alignItems: "center", gap: 16,
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <div style={{ width: 8, height: 8, borderRadius: "50%", background: connected ? "#22c55e" : "#94a3b8" }} />
            <span style={{ color: "#94a3b8", fontSize: 12 }}>{connected ? "Live" : "Disconnected"}</span>
          </div>
          <div style={{
            padding: "3px 12px", borderRadius: 20,
            background: `${statusColor[status] ?? "#6366f1"}22`,
            color: statusColor[status] ?? "#6366f1",
            fontSize: 12, fontWeight: 700, textTransform: "capitalize",
          }}>
            {status.replace("_", " ")}
          </div>
          {signedAt && (
            <span style={{ color: "#22c55e", fontSize: 11 }}>
              ✅ Signed {new Date(signedAt).toLocaleString()}
            </span>
          )}
          <span style={{ marginLeft: "auto", color: "#64748b", fontSize: 11 }}>
            ID: {consultationId.slice(0, 12)}…
          </span>
        </div>

        {/* Clinical Notes */}
        <div style={{ background: "#1e293b", borderRadius: 12, padding: 20, flex: 1 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
            <h3 style={{ color: "#f1f5f9", fontSize: 14, fontWeight: 600, margin: 0 }}>
              📋 Clinical Notes
            </h3>
            <button
              onClick={handleSaveNotes}
              disabled={currentUserRole === "viewer"}
              style={{
                padding: "6px 14px", borderRadius: 6, border: "none",
                background: "#6366f1", color: "#fff", fontSize: 12,
                cursor: currentUserRole === "viewer" ? "not-allowed" : "pointer",
                opacity: currentUserRole === "viewer" ? 0.5 : 1,
              }}
            >
              Save Notes
            </button>
          </div>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            disabled={currentUserRole === "viewer" || status === "completed"}
            placeholder="Enter clinical observations, differential diagnosis, and recommendations..."
            style={{
              width: "100%", minHeight: 200, background: "#0f172a",
              border: "1px solid #334155", borderRadius: 8, padding: 12,
              color: "#f1f5f9", fontSize: 13, lineHeight: 1.7,
              resize: "vertical", fontFamily: "inherit",
            }}
          />
        </div>

        {/* Annotations list */}
        {annotations.length > 0 && (
          <div style={{ background: "#1e293b", borderRadius: 12, padding: 20 }}>
            <h3 style={{ color: "#f1f5f9", fontSize: 14, fontWeight: 600, margin: "0 0 12px" }}>
              📍 3D Annotations ({annotations.length})
            </h3>
            <div style={{ display: "flex", flexDirection: "column", gap: 8, maxHeight: 180, overflowY: "auto" }}>
              {annotations.map((ann, i) => (
                <div key={i} style={{
                  background: "#0f172a", borderRadius: 8, padding: "8px 12px",
                  display: "flex", justifyContent: "space-between", alignItems: "center",
                }}>
                  <div>
                    <span style={{ color: "#6366f1", fontWeight: 600, fontSize: 12 }}>#{i + 1}</span>
                    <span style={{ color: "#f1f5f9", fontSize: 12, marginLeft: 8 }}>{ann.label}</span>
                  </div>
                  <span style={{ color: "#64748b", fontSize: 10, fontFamily: "monospace" }}>
                    ({ann.x.toFixed(1)}, {ann.y.toFixed(1)}, {ann.z.toFixed(1)})
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* E-Signature */}
        {currentUserRole === "specialist" && status !== "completed" && (
          <button
            onClick={handleSign}
            disabled={isSigning}
            style={{
              padding: "14px 0", borderRadius: 12,
              background: isSigning ? "#334155" : "linear-gradient(135deg, #6366f1, #4f46e5)",
              color: "#fff", fontSize: 15, fontWeight: 700, border: "none",
              cursor: isSigning ? "not-allowed" : "pointer",
              transition: "all 0.2s",
            }}
          >
            {isSigning ? "⏳ Signing..." : "✍️ Sign & Complete Consultation"}
          </button>
        )}

        {status === "completed" && (
          <div style={{
            padding: 16, borderRadius: 12, background: "#052e16",
            border: "1px solid #22c55e", textAlign: "center", color: "#22c55e",
          }}>
            ✅ Consultation completed and signed
          </div>
        )}
      </div>

      {/* Sidebar: Chat + Participants */}
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {/* Participants */}
        <div style={{ background: "#1e293b", borderRadius: 12, padding: 16 }}>
          <h4 style={{ color: "#94a3b8", fontSize: 11, fontWeight: 600, margin: "0 0 10px", textTransform: "uppercase", letterSpacing: "0.1em" }}>
            Online ({participants.length})
          </h4>
          {participants.length === 0 ? (
            <div style={{ color: "#475569", fontSize: 12 }}>No participants</div>
          ) : (
            participants.map((p) => (
              <div key={p.user_id} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                <div style={{
                  width: 28, height: 28, borderRadius: "50%",
                  background: p.role === "specialist" ? "#6366f1" : "#334155",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 12, color: "#fff", fontWeight: 700,
                }}>
                  {p.user_id.slice(0, 1).toUpperCase()}
                </div>
                <div>
                  <div style={{ color: "#f1f5f9", fontSize: 12 }}>{p.user_id.slice(0, 10)}</div>
                  <div style={{ color: "#64748b", fontSize: 10 }}>{p.role}</div>
                </div>
                {p.user_id === currentUserId && (
                  <span style={{ marginLeft: "auto", fontSize: 9, color: "#6366f1" }}>You</span>
                )}
              </div>
            ))
          )}
        </div>

        {/* Chat */}
        <div style={{ background: "#1e293b", borderRadius: 12, padding: 16, flex: 1, display: "flex", flexDirection: "column" }}>
          <h4 style={{ color: "#94a3b8", fontSize: 11, fontWeight: 600, margin: "0 0 10px", textTransform: "uppercase", letterSpacing: "0.1em" }}>
            Live Chat
          </h4>
          <div style={{ flex: 1, overflowY: "auto", minHeight: 200, maxHeight: 340, marginBottom: 12 }}>
            {chat.length === 0 ? (
              <div style={{ color: "#475569", fontSize: 12, textAlign: "center", paddingTop: 20 }}>
                No messages yet
              </div>
            ) : (
              chat.map((m, i) => (
                <div key={i} style={{
                  marginBottom: 10,
                  display: "flex",
                  flexDirection: m.user_id === currentUserId ? "row-reverse" : "row",
                  gap: 8, alignItems: "flex-end",
                }}>
                  <div style={{
                    maxWidth: "80%", padding: "8px 12px", borderRadius: 10,
                    background: m.user_id === currentUserId ? "#6366f133" : "#0f172a",
                    border: m.user_id === currentUserId ? "1px solid #6366f1" : "1px solid #1e293b",
                  }}>
                    <div style={{ fontSize: 9, color: "#64748b", marginBottom: 2 }}>
                      {m.user_id === currentUserId ? "You" : m.user_id.slice(0, 8)}
                      {" · "}{new Date(m.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </div>
                    <div style={{ color: "#f1f5f9", fontSize: 12, wordBreak: "break-word" }}>
                      {m.message}
                    </div>
                  </div>
                </div>
              ))
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Input */}
          <div style={{ display: "flex", gap: 8 }}>
            <input
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendChat()}
              placeholder="Type a message..."
              disabled={!connected}
              style={{
                flex: 1, padding: "8px 12px", background: "#0f172a",
                border: "1px solid #334155", borderRadius: 8,
                color: "#f1f5f9", fontSize: 12, outline: "none",
              }}
            />
            <button
              onClick={sendChat}
              disabled={!connected || !chatInput.trim()}
              style={{
                padding: "8px 14px", borderRadius: 8, border: "none",
                background: "#6366f1", color: "#fff", fontSize: 12,
                cursor: "pointer", opacity: connected ? 1 : 0.5,
              }}
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
