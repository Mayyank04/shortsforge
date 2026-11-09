"use client";
import { useEffect, useState } from "react";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

type RenderJob = {
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

export default function RenderQueue() {
  const [renders, setRenders] = useState<RenderJob[]>([]);
  const [filter, setFilter] = useState("all");
  const [selectedLogs, setSelectedLogs] = useState<{ id: string; logs: string } | null>(null);

  async function loadRenders() {
    try {
      const res = await fetch(`${API}/api/renders`);
      if (res.ok) {
        setRenders(await res.json());
      }
    } catch {}
  }

  useEffect(() => {
    loadRenders();
    const t = setInterval(loadRenders, 3500);
    return () => clearInterval(t);
  }, []);

  async function retryJob(item: RenderJob) {
    try {
      if (item.type === "minecraft") {
        await fetch(`${API}/api/minecraft/projects/${item.id}/render`, { method: "POST" });
      } else {
        await fetch(`${API}/api/jobs/${item.id}/retry?auto_render=true`, { method: "POST" });
      }
      loadRenders();
    } catch {}
  }

  async function cancelJob(item: RenderJob) {
    try {
      if (item.type === "geography") {
        await fetch(`${API}/api/jobs/${item.id}/cancel`, { method: "POST" });
      }
      loadRenders();
    } catch {}
  }

  async function viewLogs(item: RenderJob) {
    try {
      const res = await fetch(`${API}/api/jobs/${item.id}/logs`);
      if (res.ok) {
        const d = await res.json();
        setSelectedLogs({ id: item.id, logs: d.logs || "No detailed logs recorded." });
      }
    } catch {
      setSelectedLogs({ id: item.id, logs: "Could not fetch logs." });
    }
  }

  const filtered = renders.filter((r) => {
    if (filter === "all") return true;
    if (filter === "running") return ["running", "rendering", "rendering_3d", "queued"].includes(r.status);
    if (filter === "completed") return r.status === "completed";
    if (filter === "failed") return r.status === "failed";
    return true;
  });

  return (
    <main>
      <div className="eyebrow">
        <span>RENDER QUEUE · PERSISTENT EXECUTION</span>
        <span className="api-pill api-online">● Live Engine</span>
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <h1>
            Render <span style={{ color: "#38bdf8" }}>Queue.</span>
          </h1>
          <p>
            Real-time tracking of 3D Blender scene generation, audio synthesis, and FFmpeg video assembly.
          </p>
        </div>

        {/* Filter Tabs */}
        <div style={{ display: "flex", gap: "6px" }}>
          {["all", "running", "completed", "failed"].map((f) => (
            <button
              key={f}
              type="button"
              className={`action-btn ${filter === f ? "primary" : ""}`}
              style={{
                textTransform: "capitalize",
                background: filter === f ? "#38bdf8" : "#1e293b",
                color: filter === f ? "#090d18" : "#cbd5e1"
              }}
              onClick={() => setFilter(f)}
            >
              {f} ({renders.filter((r) => f === "all" ? true : f === "running" ? ["running", "rendering", "rendering_3d", "queued"].includes(r.status) : r.status === f).length})
            </button>
          ))}
        </div>
      </div>

      {/* Render Jobs List */}
      <section className="panel" style={{ marginTop: "20px" }}>
        {filtered.length === 0 ? (
          <p className="muted" style={{ textAlign: "center", padding: "30px 0" }}>
            No render jobs matching filter '{filter}'.
          </p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
            {filtered.map((item) => {
              const videoFilename = item.output_path ? item.output_path.split("/").pop() : "";

              return (
                <div key={item.id} style={{ background: "#0b111e", border: "1px solid #1e293b", borderRadius: "12px", padding: "16px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "12px" }}>
                    <div>
                      <div style={{ fontSize: "17px", fontWeight: 700, color: "#f8fafc" }}>{item.title}</div>
                      <div className="muted" style={{ marginTop: "4px" }}>
                        ID: <code>{item.id}</code> · Type: <strong style={{ color: item.type === "minecraft" ? "#a855f7" : "#38bdf8", textTransform: "capitalize" }}>{item.type}</strong> · Duration: {item.duration}s · Voice: {item.voice}
                      </div>
                      {item.error && (
                        <div style={{ color: "#ff8793", fontSize: "12px", marginTop: "6px", fontFamily: "monospace" }}>
                          Error: {item.error}
                        </div>
                      )}
                    </div>
                    <span className={`status-badge status-${item.status}`}>{item.status}</span>
                  </div>

                  <div style={{ display: "flex", gap: "8px", marginTop: "14px", alignItems: "center" }}>
                    {item.status === "completed" && videoFilename && (
                      <a href={`${API}/outputs/${videoFilename}`} download className="action-btn" style={{ color: "#2ed573", borderColor: "rgba(46,213,115,0.4)" }}>
                        ⬇️ Download MP4
                      </a>
                    )}
                    {item.status === "failed" && (
                      <button className="action-btn" onClick={() => retryJob(item)}>
                        🔄 Retry Job
                      </button>
                    )}
                    {["queued", "running"].includes(item.status) && (
                      <button className="action-btn danger" onClick={() => cancelJob(item)}>
                        ✕ Cancel
                      </button>
                    )}
                    <button className="action-btn" onClick={() => viewLogs(item)}>
                      📋 View Logs
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>

      {/* Logs Modal */}
      {selectedLogs && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.8)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 100, padding: "20px" }}>
          <div className="panel" style={{ maxWidth: "700px", width: "100%", maxHeight: "80vh", overflowY: "auto", margin: 0 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
              <h3 style={{ margin: 0 }}>Execution Logs ({selectedLogs.id})</h3>
              <button className="action-btn" onClick={() => setSelectedLogs(null)}>✕ Close</button>
            </div>
            <pre style={{ background: "#060912", padding: "16px", borderRadius: "10px", fontSize: "12px", color: "#a5f3fc", overflowX: "auto" }}>
              {selectedLogs.logs}
            </pre>
          </div>
        </div>
      )}
    </main>
  );
}
