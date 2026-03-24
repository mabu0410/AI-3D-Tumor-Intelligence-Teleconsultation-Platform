export default function HomePage() {
  return (
    <main style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "100vh", gap: "1rem" }}>
      <h1 style={{ fontSize: "2rem", fontWeight: 700, color: "#6366f1" }}>
        🧠 AI 3D Tumor Intelligence Platform
      </h1>
      <p style={{ color: "#94a3b8", fontSize: "1.1rem" }}>
        Platform hỗ trợ chẩn đoán và theo dõi khối u AI-powered
      </p>
      <div style={{ display: "flex", gap: "1rem", marginTop: "1rem" }}>
        <a href="/dashboard" style={{ padding: "0.75rem 1.5rem", background: "#6366f1", borderRadius: "8px", color: "#fff" }}>Dashboard</a>
        <a href="/upload" style={{ padding: "0.75rem 1.5rem", border: "1px solid #6366f1", borderRadius: "8px", color: "#6366f1" }}>Upload DICOM</a>
      </div>
    </main>
  );
}
