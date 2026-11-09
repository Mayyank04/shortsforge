"use client";
import { useEffect, useState } from "react";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

type Stats = {
  total_projects: number;
  completed_videos: number;
  processing_jobs: number;
  failed_jobs: number;
  geography_projects: number;
  minecraft_projects: number;
};

type RenderItem = {
  id: string;
  type: string;
  title: string;
  status: string;
  duration: number;
  voice: string;
  output_path?: string;
  error?: string;
  created_at: string;
};

type SettingsData = {
  blender: { installed: boolean; version: string };
  ffmpeg: { installed: boolean; path: string };
  kokoro: { installed: boolean; status: string };
  ollama: { available: boolean; url: string };
  storage: { total_gb: number; used_gb: number; free_gb: number };
  system: { platform: string };
};

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [recent, setRecent] = useState<RenderItem[]>([]);
  const [diag, setDiag] = useState<SettingsData | null>(null);
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);

  async function fetchDashboardData() {
    try {
      const h = await fetch(`${API}/health`, { cache: "no-store" });
      if (h.ok) {
        setApiOnline(true);
        const [rStats, rRecent, rSettings] = await Promise.all([
          fetch(`${API}/api/renders/stats`),
          fetch(`${API}/api/renders`),
          fetch(`${API}/api/settings`)
        ]);
        if (rStats.ok) setStats(await rStats.json());
        if (rRecent.ok) setRecent(await rRecent.json());
        if (rSettings.ok) setDiag(await rSettings.json());
      } else {
        setApiOnline(false);
      }
    } catch {
      setApiOnline(false);
    }
  }

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 4000);
    return () => clearInterval(interval);
  }, []);

  return (
    <main>
      <div className="eyebrow">
        <span>PRODUCTION CONTROL WORKSTATION</span>
        <span className={`api-pill ${apiOnline ? "api-online" : "api-offline"}`}>
          {apiOnline === null ? "Connecting..." : apiOnline ? "● API Online (Port 8000)" : "○ API Disconnected"}
        </span>
      </div>

      <h1>
        Studio <span style={{ color: "#38bdf8" }}>Dashboard.</span>
      </h1>
      <p>
        Unified automated video pipeline for 3D Minecraft explainer shorts and GeoGlobeTales geography videos.
      </p>

      {/* Metrics Grid */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-value">{stats ? stats.total_projects : "—"}</div>
          <div className="stat-label">Total Projects</div>
        </div>
        <div className="stat-card" style={{ borderColor: "rgba(46,213,115,0.4)" }}>
          <div className="stat-value" style={{ color: "#2ed573" }}>{stats ? stats.completed_videos : "—"}</div>
          <div className="stat-label">Completed Videos</div>
        </div>
        <div className="stat-card" style={{ borderColor: "rgba(56,189,248,0.4)" }}>
          <div className="stat-value" style={{ color: "#38bdf8" }}>{stats ? stats.processing_jobs : "—"}</div>
          <div className="stat-label">Rendering in Progress</div>
        </div>
        <div className="stat-card" style={{ borderColor: "rgba(255,71,87,0.4)" }}>
          <div className="stat-value" style={{ color: "#ff4757" }}>{stats ? stats.failed_jobs : "—"}</div>
          <div className="stat-label">Failed Jobs</div>
        </div>
      </div>

      {/* Quick Launch Studios */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px", marginTop: "20px" }}>
        <div className="panel" style={{ border: "1px solid #a855f7", margin: 0 }}>
          <span style={{ fontSize: "12px", color: "#a855f7", fontWeight: 800, textTransform: "uppercase" }}>New Studio Mode</span>
          <h2 style={{ margin: "8px 0" }}>🎬 Minecraft Story Studio</h2>
          <p style={{ fontSize: "14px" }}>
            Create cinematic 10-scene animated voxel stories with canonical characters (Mini, Steve, Golem, Shadow), dynamic cameras, and Kokoro narration.
          </p>
          <div style={{ display: "flex", gap: "10px", marginTop: "16px" }}>
            <Link href="/minecraft/create" className="primary" style={{ padding: "10px 18px", fontSize: "14px" }}>
              ✨ Create Story →
            </Link>
            <Link href="/minecraft/characters" className="secondary" style={{ padding: "10px 18px", fontSize: "14px", margin: 0 }}>
              👤 Characters
            </Link>
          </div>
        </div>

        <div className="panel" style={{ border: "1px solid #38bdf8", margin: 0 }}>
          <span style={{ fontSize: "12px", color: "#38bdf8", fontWeight: 800, textTransform: "uppercase" }}>Existing Engine</span>
          <h2 style={{ margin: "8px 0" }}>🌍 Geography Studio</h2>
          <p style={{ fontSize: "14px" }}>
            Generate GeoGlobeTales-style 3D rotating Earth explainers with Natural Earth international borders, satellite textures, and terrain bumps.
          </p>
          <div style={{ display: "flex", gap: "10px", marginTop: "16px" }}>
            <Link href="/" className="primary" style={{ padding: "10px 18px", fontSize: "14px", background: "#38bdf8", color: "#090d18" }}>
              🗺️ Open Geography Studio →
            </Link>
          </div>
        </div>
      </div>

      {/* System Dependency Status */}
      <section className="panel">
        <h3 style={{ margin: "0 0 16px 0", color: "#cbd5e1" }}>Hardware & Dependency Diagnostics</h3>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "14px" }}>
          <div style={{ background: "#0b111e", padding: "14px", borderRadius: "10px" }}>
            <div style={{ fontSize: "12px", color: "#8290a8" }}>Blender 3D Binary</div>
            <div style={{ fontWeight: 700, color: diag?.blender.installed ? "#2ed573" : "#ff4757", marginTop: "4px" }}>
              {diag?.blender.installed ? "● Installed" : "○ Missing"}
            </div>
            <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "4px" }}>{diag?.blender.version}</div>
          </div>
          <div style={{ background: "#0b111e", padding: "14px", borderRadius: "10px" }}>
            <div style={{ fontSize: "12px", color: "#8290a8" }}>FFmpeg Assembly</div>
            <div style={{ fontWeight: 700, color: diag?.ffmpeg.installed ? "#2ed573" : "#ff4757", marginTop: "4px" }}>
              {diag?.ffmpeg.installed ? "● Ready" : "○ Not in PATH"}
            </div>
            <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "4px" }}>H.264 & AAC Encoder</div>
          </div>
          <div style={{ background: "#0b111e", padding: "14px", borderRadius: "10px" }}>
            <div style={{ fontSize: "12px", color: "#8290a8" }}>Kokoro Neural TTS</div>
            <div style={{ fontWeight: 700, color: diag?.kokoro.installed ? "#2ed573" : "#f5c84c", marginTop: "4px" }}>
              {diag?.kokoro.status}
            </div>
            <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "4px" }}>English & Hindi Audio</div>
          </div>
          <div style={{ background: "#0b111e", padding: "14px", borderRadius: "10px" }}>
            <div style={{ fontSize: "12px", color: "#8290a8" }}>Disk Space</div>
            <div style={{ fontWeight: 700, color: "#38bdf8", marginTop: "4px" }}>
              {diag ? `${diag.storage.free_gb} GB Free` : "—"}
            </div>
            <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "4px" }}>Output Directory Ready</div>
          </div>
        </div>
      </section>

      {/* Recent Production Activity */}
      <section className="panel">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
          <h3 style={{ margin: 0 }}>Recent Activity</h3>
          <Link href="/renders" style={{ fontSize: "13px", color: "#38bdf8", fontWeight: 700 }}>
            View Full Queue →
          </Link>
        </div>

        {recent.length === 0 ? (
          <p className="muted">No jobs recorded yet. Launch your first project above.</p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            {recent.slice(0, 6).map((item) => (
              <div key={item.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", background: "#0b111e", padding: "14px 18px", borderRadius: "10px", border: "1px solid #1e293b" }}>
                <div>
                  <div style={{ fontWeight: 700, color: "#f8fafc" }}>{item.title}</div>
                  <div style={{ fontSize: "12px", color: "#8290a8", marginTop: "2px" }}>
                    Type: <span style={{ color: item.type === "minecraft" ? "#a855f7" : "#38bdf8", textTransform: "capitalize" }}>{item.type}</span> · {item.duration}s · Voice: {item.voice}
                  </div>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                  <span className={`status-badge status-${item.status}`}>{item.status}</span>
                  {item.type === "minecraft" ? (
                    <Link href={`/minecraft/storyboard/${item.id}`} className="action-btn">
                      Inspect
                    </Link>
                  ) : (
                    <Link href={`/?jobId=${item.id}`} className="action-btn">
                      Inspect
                    </Link>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
