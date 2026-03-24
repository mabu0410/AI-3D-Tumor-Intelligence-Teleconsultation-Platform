"use client";
import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function Sidebar() {
  const pathname = usePathname();

  const links = [
    { name: "Dashboard", path: "/", icon: "📊" },
    { name: "M1: 3D Segmentation", path: "/segmentation", icon: "🧠" },
    { name: "M2: 3D Reconstruction", path: "/reconstruction", icon: "🧊" },
    { name: "M3: Feature Insights", path: "/features", icon: "📐" },
    { name: "M4: Classification", path: "/classification", icon: "🔬" },
    { name: "M5: Progression", path: "/progression", icon: "📈" },
    { name: "M6: Teleconsultation", path: "/telemedicine", icon: "🤝" },
    { name: "M7: Patient Schedule", path: "/scheduling", icon: "📅" },
  ];

  return (
    <div style={{
      width: 280,
      background: "#0f172a",
      borderRight: "1px solid #1e293b",
      display: "flex",
      flexDirection: "column",
      padding: "24px 16px",
    }}>
      {/* Brand */}
      <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "0 12px 32px" }}>
        <div style={{
          width: 36, height: 36, borderRadius: 8,
          background: "linear-gradient(135deg, #6366f1, #8b5cf6)",
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: 18, boxShadow: "0 4px 12px rgba(99, 102, 241, 0.3)"
        }}>
          ✨
        </div>
        <div>
          <div style={{ fontSize: 16, fontWeight: 800, color: "#f8fafc", letterSpacing: "-0.02em" }}>
            AI 3D Tumor
          </div>
          <div style={{ fontSize: 11, color: "#94a3b8", fontWeight: 500, letterSpacing: "0.05em", textTransform: "uppercase" }}>
            Intelligence Platform
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav style={{ display: "flex", flexDirection: "column", gap: 6, flex: 1 }}>
        <div style={{ fontSize: 10, fontWeight: 700, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.1em", padding: "0 12px 8px" }}>
          Modules
        </div>
        
        {links.map((link) => {
          const isActive = pathname === link.path;
          return (
            <Link key={link.path} href={link.path} style={{ textDecoration: 'none' }}>
              <div style={{
                display: "flex", alignItems: "center", gap: 12,
                padding: "10px 14px", borderRadius: 10,
                background: isActive ? "#1e293b" : "transparent",
                color: isActive ? "#f8fafc" : "#94a3b8",
                borderLeft: isActive ? "3px solid #6366f1" : "3px solid transparent",
                transition: "all 0.2s ease",
                cursor: "pointer",
                fontWeight: isActive ? 600 : 500,
              }}>
                <span style={{ fontSize: 18, filter: isActive ? "none" : "grayscale(0.8) opacity(0.7)" }}>
                  {link.icon}
                </span>
                <span style={{ fontSize: 13 }}>{link.name}</span>
              </div>
            </Link>
          );
        })}
      </nav>

      {/* User profile snippet */}
      <div style={{
        marginTop: "auto", padding: 16, borderRadius: 12,
        background: "#1e293b", border: "1px solid #334155",
        display: "flex", alignItems: "center", gap: 12
      }}>
        <div style={{ width: 32, height: 32, borderRadius: "50%", background: "#475569", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14 }}>
          👨‍⚕️
        </div>
        <div>
          <div style={{ fontSize: 13, fontWeight: 600, color: "#f8fafc" }}>Dr. Administrator</div>
          <div style={{ fontSize: 11, color: "#94a3b8" }}>Oncology Dept.</div>
        </div>
      </div>
    </div>
  );
}
