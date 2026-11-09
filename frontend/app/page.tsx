"use client";
import { useEffect, useState } from "react";

type Job = {
  id: string;
  topic: string;
  style: string;
  duration: number;
  voice?: string;
  preview?: boolean;
  status: "queued" | "running" | "researching" | "scripting" | "generating_voice" | "rendering_3d" | "assembling" | "completed" | "failed" | "cancelled" | string;
  output_path?: string | null;
  error?: string | null;
  logs?: string | null;
  metadata_json?: string | null;
  created_at: string;
};

type Metadata = {
  topic: string;
  style: string;
  voice: string;
  duration: number;
  video: string;
  resolution: string;
  fps: number;
  file_size_bytes: number;
  render_time_seconds: number;
  research?: {
    title: string;
    summary: string;
    strategic_importance: string;
    claims: Array<{ statement: string; category: string; verification_source: string; year_or_metric: string }>;
    timeline: Array<{ year: string; event: string }>;
  };
  storyboard?: {
    num_scenes: number;
    scenes: Array<{
      id: string;
      narration: string;
      duration: number;
      region: string;
      lat: number;
      lon: number;
      badge: string;
      headline: string;
      stat: string;
    }>;
  };
};

const API = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

const PRESET_TOPICS = [
  "Why is Gibraltar British?",
  "Why does Russia have an isolated territory?",
  "Why are there two Irelands?",
  "Why is the Suez Canal important?",
  "How did the Himalayas form?",
  "Why does India have so many different climates?",
];

export default function Home() {
  const [activeTab, setActiveTab] = useState<"geo" | "classic">("geo");
  const [topic, setTopic] = useState("Why is Gibraltar British?");
  const [style, setStyle] = useState("geo_realistic");
  const [voice, setVoice] = useState("heart");
  const [duration, setDuration] = useState(75);
  const [preview, setPreview] = useState(false);
  const [autoRender, setAutoRender] = useState(true);

  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [selectedMeta, setSelectedMeta] = useState<Metadata | null>(null);
  const [activeInspectorTab, setActiveInspectorTab] = useState<"video" | "storyboard" | "script" | "logs">("video");
  const [logsText, setLogsText] = useState("");

  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);

  async function checkHealthAndRefresh() {
    try {
      const res = await fetch(`${API}/health`, { cache: "no-store" });
      if (res.ok) {
        setApiOnline(true);
        const r = await fetch(`${API}/api/jobs`, { cache: "no-store" });
        if (r.ok) {
          const list: Job[] = await r.json();
          setJobs(list);
          // Update selected job if active
          if (selectedJob) {
            const updated = list.find((j) => j.id === selectedJob.id);
            if (updated) {
              setSelectedJob(updated);
              if (updated.metadata_json) {
                try {
                  setSelectedMeta(JSON.parse(updated.metadata_json));
                } catch {}
              }
            }
          }
        }
      } else {
        setApiOnline(false);
      }
    } catch {
      setApiOnline(false);
    }
  }

  useEffect(() => {
    checkHealthAndRefresh();
    const t = setInterval(checkHealthAndRefresh, 3000);
    return () => clearInterval(t);
  }, [selectedJob?.id]);

  async function createJob(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setMessage("");
    try {
      const r = await fetch(`${API}/api/jobs?auto_render=${autoRender}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic, style, duration, voice, preview }),
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data.detail || "Could not create job");
      setMessage(`Job queued: ${data.id}. ${autoRender ? "Rendering in background..." : "Run worker CLI to render."}`);
      await checkHealthAndRefresh();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Request failed");
    } finally {
      setBusy(false);
    }
  }

  async function batchQueuePresets() {
    setBusy(true);
    setMessage("");
    try {
      const jobsToQueue = PRESET_TOPICS.slice(0, 3).map((t) => ({
        topic: t,
        style: "geo_realistic",
        duration: 75,
        voice: "heart",
        preview: false,
      }));
      const r = await fetch(`${API}/api/jobs/batch`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ jobs: jobsToQueue }),
      });
      if (!r.ok) throw new Error("Batch queue failed");
      setMessage("Queued 3 canonical geography topics!");
      await checkHealthAndRefresh();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Batch queue failed");
    } finally {
      setBusy(false);
    }
  }

  async function retryJob(jobId: string) {
    try {
      await fetch(`${API}/api/jobs/${jobId}/retry?auto_render=true`, { method: "POST" });
      await checkHealthAndRefresh();
    } catch {}
  }

  async function cancelJob(jobId: string) {
    try {
      await fetch(`${API}/api/jobs/${jobId}/cancel`, { method: "POST" });
      await checkHealthAndRefresh();
    } catch {}
  }

  async function viewJobDetails(job: Job) {
    setSelectedJob(job);
    if (job.metadata_json) {
      try {
        setSelectedMeta(JSON.parse(job.metadata_json));
      } catch {
        setSelectedMeta(null);
      }
    } else {
      setSelectedMeta(null);
    }
    // Fetch logs
    try {
      const r = await fetch(`${API}/api/jobs/${job.id}/logs`);
      if (r.ok) {
        const d = await r.json();
        setLogsText(d.logs || "No logs available.");
      }
    } catch {}
  }

  function getStatusClass(status: string) {
    switch (status) {
      case "completed":
        return "status-completed";
      case "failed":
        return "status-failed";
      case "cancelled":
        return "status-cancelled";
      case "running":
      case "rendering_3d":
      case "scripting":
      case "generating_voice":
        return "status-running";
      default:
        return "status-queued";
    }
  }

  const videoFilename = selectedJob?.output_path ? selectedJob.output_path.split("/").pop() : "";

  return (
    <main>
      <div className="eyebrow">
        <span>SHORTFORGE AI · GEOGLOBETALES STUDIO</span>
        <span className={`api-pill ${apiOnline ? "api-online" : "api-offline"}`}>
          {apiOnline === null ? "Checking API..." : apiOnline ? "● API Online (Port 8000)" : "○ API Disconnected"}
        </span>
      </div>

      <h1>
        Create faceless <span style={{ color: "#f5c84c" }}>Geography Shorts.</span>
      </h1>
      <p>
        Turn any geographical mystery, territorial conflict or historical border dispute into an authentic GeoGlobeTales-style 3D animated explainer.
      </p>

      {/* Tabs */}
      <div className="tabs-nav">
        <button
          className={`tab-btn ${activeTab === "geo" ? "active" : ""}`}
          onClick={() => {
            setActiveTab("geo");
            setStyle("geo_realistic");
            setDuration(75);
          }}
        >
          🌍 Geography Studio (Blender 3D)
        </button>
        <button
          className={`tab-btn ${activeTab === "classic" ? "active" : ""}`}
          onClick={() => {
            setActiveTab("classic");
            setStyle("mixed");
            setDuration(35);
          }}
        >
          🎬 Classic 2D Shorts
        </button>
      </div>

      {/* Main Studio Panel */}
      <section className="panel">
        <h2>{activeTab === "geo" ? "Configure Geography Video" : "Create Classic Short"}</h2>

        {activeTab === "geo" && (
          <div>
            <span style={{ fontSize: "13px", color: "#94a3b8" }}>Quick Topic Presets:</span>
            <div className="presets-grid">
              {PRESET_TOPICS.map((preset) => (
                <button key={preset} type="button" className="chip" onClick={() => setTopic(preset)}>
                  {preset}
                </button>
              ))}
            </div>
          </div>
        )}

        <form onSubmit={createJob}>
          <label htmlFor="topic">Topic / Title</label>
          <input
            id="topic"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            minLength={4}
            maxLength={500}
            required
            placeholder="Why is Gibraltar British?"
          />

          <div className="form-grid">
            {activeTab === "geo" ? (
              <div>
                <label htmlFor="style">Visual Style</label>
                <select id="style" value={style} onChange={(e) => setStyle(e.target.value)}>
                  <option value="geo_realistic">🛰️ Satellite Realistic 3D (Photorealistic Earth & Terrain)</option>
                  <option value="geo_political">🗺️ Political Borders 3D (Country Highlighting)</option>
                  <option value="geo_terrain">🏔️ Shaded Relief Terrain (Mountain & Elevation Focus)</option>
                  <option value="geo_historical">📜 Historical Atlas (Treaties & Border Comparisons)</option>
                </select>
              </div>
            ) : (
              <div>
                <label htmlFor="style">Visual Style</label>
                <select id="style" value={style} onChange={(e) => setStyle(e.target.value)}>
                  <option value="mixed">Mixed 2D / 3D-inspired</option>
                  <option value="2d">2D cartoon</option>
                  <option value="3d">3D-inspired scenes</option>
                </select>
              </div>
            )}

            <div>
              <label htmlFor="voice">Narration Voice (Kokoro Neural)</label>
              <select id="voice" value={voice} onChange={(e) => setVoice(e.target.value)}>
                <option value="heart">Heart (Warm & Engaging Female)</option>
                <option value="adam">Adam (Authoritative Male)</option>
                <option value="alice">Alice (Clear British Female)</option>
                <option value="george">George (Classic British Male)</option>
                <option value="nicole">Nicole (Energetic Narrative Female)</option>
                <option value="michael">Michael (Documentary Male)</option>
              </select>
            </div>

            <div>
              <label htmlFor="duration">Target Duration</label>
              <select id="duration" value={duration} onChange={(e) => setDuration(Number(e.target.value))}>
                {activeTab === "geo" ? (
                  <>
                    <option value={60}>60 seconds (Fast Explainer)</option>
                    <option value={75}>75 seconds (Standard Pacing)</option>
                    <option value={90}>90 seconds (In-depth Narrative)</option>
                    <option value={100}>100 seconds (Documentary Short)</option>
                  </>
                ) : (
                  <>
                    <option value={20}>20 seconds</option>
                    <option value={35}>35 seconds</option>
                    <option value={45}>45 seconds</option>
                    <option value={60}>60 seconds</option>
                  </>
                )}
              </select>
            </div>
          </div>

          <div className="toggle-row">
            <input
              type="checkbox"
              id="preview"
              checked={preview}
              onChange={(e) => setPreview(e.target.checked)}
            />
            <label htmlFor="preview" style={{ margin: 0, cursor: "pointer" }}>
              ⚡ <strong>Fast Preview Mode</strong> (Render at 540x960 for quick iteration)
            </label>

            <span style={{ margin: "0 10px", color: "#334155" }}>|</span>

            <input
              type="checkbox"
              id="autoRender"
              checked={autoRender}
              onChange={(e) => setAutoRender(e.target.checked)}
            />
            <label htmlFor="autoRender" style={{ margin: 0, cursor: "pointer" }}>
              🚀 <strong>Background Auto-Render</strong> (Start rendering immediately upon queueing)
            </label>
          </div>

          <div>
            <button className="primary" disabled={busy}>
              {busy ? "Queueing…" : "🚀 Generate Video Project →"}
            </button>
            {activeTab === "geo" && (
              <button type="button" className="secondary" disabled={busy} onClick={batchQueuePresets}>
                ⚡ Batch Queue Presets
              </button>
            )}
          </div>
        </form>

        {message && <p role="status" style={{ marginTop: "14px", color: "#f5c84c" }}>{message}</p>}
      </section>

      {/* Selected Project Inspector & Video Player */}
      {selectedJob && (
        <section className="panel" style={{ borderColor: "#38bdf8", boxShadow: "0 0 20px rgba(56,189,248,0.1)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
            <div>
              <span style={{ fontSize: "12px", color: "#38bdf8", fontWeight: 700, textTransform: "uppercase" }}>
                Active Project Inspector
              </span>
              <h2 style={{ margin: "4px 0" }}>{selectedJob.topic}</h2>
              <div className="muted">
                ID: <code>{selectedJob.id}</code> · Style: {selectedJob.style} · Voice: {selectedJob.voice || "heart"} · Duration: {selectedJob.duration}s
              </div>
            </div>
            <span className={`status-badge ${getStatusClass(selectedJob.status)}`}>{selectedJob.status}</span>
          </div>

          {/* Inspector Tabs */}
          <div className="tabs-nav" style={{ marginTop: "16px" }}>
            <button
              className={`tab-btn ${activeInspectorTab === "video" ? "active" : ""}`}
              onClick={() => setActiveInspectorTab("video")}
            >
              ▶️ Video Player
            </button>
            <button
              className={`tab-btn ${activeInspectorTab === "storyboard" ? "active" : ""}`}
              onClick={() => setActiveInspectorTab("storyboard")}
            >
              🎬 Storyboard & Scenes ({selectedMeta?.storyboard?.num_scenes || "—"})
            </button>
            <button
              className={`tab-btn ${activeInspectorTab === "script" ? "active" : ""}`}
              onClick={() => setActiveInspectorTab("script")}
            >
              📜 Research & Script
            </button>
            <button
              className={`tab-btn ${activeInspectorTab === "logs" ? "active" : ""}`}
              onClick={() => setActiveInspectorTab("logs")}
            >
              📋 Worker Logs
            </button>
          </div>

          {/* Inspector Content */}
          {activeInspectorTab === "video" && (
            <div>
              {selectedJob.status === "completed" && videoFilename ? (
                <div className="video-preview-box">
                  <video
                    className="video-player"
                    controls
                    playsInline
                    src={`${API}/outputs/${videoFilename}`}
                  />
                  <div className="video-meta">
                    <h4>Exported Video Details</h4>
                    <div className="meta-badges">
                      <span className="m-badge">Resolution: {selectedMeta?.resolution || "1080x1920"}</span>
                      <span className="m-badge">Aspect: 9:16 Vertical</span>
                      <span className="m-badge">FPS: 30</span>
                      <span className="m-badge">Duration: {selectedMeta?.duration?.toFixed(1) || selectedJob.duration}s</span>
                      <span className="m-badge">Render Time: {selectedMeta?.render_time_seconds || "—"}s</span>
                    </div>
                    <p style={{ fontSize: "14px", color: "#cbd5e1" }}>
                      Output Path: <code style={{ wordBreak: "break-all" }}>{selectedJob.output_path}</code>
                    </p>
                    <a
                      href={`${API}/outputs/${videoFilename}`}
                      download
                      className="primary"
                      style={{
                        textDecoration: "none",
                        display: "inline-block",
                        padding: "10px 18px",
                        fontSize: "14px",
                      }}
                    >
                      ⬇️ Download MP4 Video
                    </a>
                  </div>
                </div>
              ) : selectedJob.status === "failed" ? (
                <div className="job-error">
                  <strong>Render Error:</strong> {selectedJob.error}
                  <div style={{ marginTop: "10px" }}>
                    <button className="action-btn" onClick={() => retryJob(selectedJob.id)}>
                      🔄 Retry Render
                    </button>
                  </div>
                </div>
              ) : (
                <div style={{ padding: "30px", textAlign: "center", background: "#0b111e", borderRadius: "12px" }}>
                  <p style={{ color: "#38bdf8", fontWeight: 700 }}>⏳ Video is currently rendering...</p>
                  <p className="muted">Status: {selectedJob.status}. The preview will appear here automatically when rendering finishes.</p>
                </div>
              )}
            </div>
          )}

          {activeInspectorTab === "storyboard" && (
            <div>
              {selectedMeta?.storyboard?.scenes ? (
                <div className="storyboard-scroll">
                  {selectedMeta.storyboard.scenes.map((s, idx) => (
                    <div key={s.id} className="scene-card">
                      <div className="scene-card-header">
                        <span>{s.id.toUpperCase()}</span>
                        <span>{s.duration.toFixed(1)}s</span>
                      </div>
                      <div className="scene-card-region">{s.region}</div>
                      <div style={{ fontSize: "11px", color: "#94a3b8", marginBottom: "6px" }}>
                        📍 {s.lat.toFixed(2)}°, {s.lon.toFixed(2)}°
                      </div>
                      <div className="scene-card-narr">"{s.narration}"</div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="muted">Storyboard metadata will appear once the video finishes rendering.</p>
              )}
            </div>
          )}

          {activeInspectorTab === "script" && (
            <div>
              {selectedMeta?.research ? (
                <div>
                  <h3 style={{ color: "#f5c84c", marginTop: 0 }}>{selectedMeta.research.title}</h3>
                  <p style={{ color: "#e2e8f0" }}>{selectedMeta.research.summary}</p>
                  <h4>Verified Historical Claims:</h4>
                  <ul>
                    {selectedMeta.research.claims.map((c, i) => (
                      <li key={i} style={{ marginBottom: "8px", color: "#cbd5e1" }}>
                        <strong>[{c.category.toUpperCase()}]</strong> {c.statement}{" "}
                        <span className="muted">({c.verification_source})</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : (
                <p className="muted">Research notes will be populated upon completion.</p>
              )}
            </div>
          )}

          {activeInspectorTab === "logs" && (
            <div>
              <pre
                style={{
                  background: "#080c16",
                  padding: "16px",
                  borderRadius: "10px",
                  fontSize: "12px",
                  color: "#a5f3fc",
                  overflowX: "auto",
                  maxHeight: "300px",
                }}
              >
                {logsText || "No logs available."}
              </pre>
            </div>
          )}
        </section>
      )}

      {/* Projects List */}
      <section className="panel">
        <h2>Recent Video Projects</h2>
        {jobs.length === 0 ? (
          <p>No projects yet. Create your first geography short above.</p>
        ) : (
          jobs.map((j) => (
            <div className="job" key={j.id}>
              <div className="job-header">
                <div>
                  <div className="job-title">{j.topic}</div>
                  <div className="muted" style={{ marginTop: "4px" }}>
                    ID: <code>{j.id}</code> · {j.style} · {j.duration}s · {new Date(j.created_at).toLocaleString()}
                  </div>
                </div>
                <span className={`status-badge ${getStatusClass(j.status)}`}>{j.status}</span>
              </div>

              <div className="job-actions">
                <button className="action-btn" onClick={() => viewJobDetails(j)}>
                  🔍 Inspect Project
                </button>
                {j.status === "failed" && (
                  <button className="action-btn" onClick={() => retryJob(j.id)}>
                    🔄 Retry
                  </button>
                )}
                {j.status === "queued" && (
                  <button className="action-btn danger" onClick={() => cancelJob(j.id)}>
                    ✕ Cancel
                  </button>
                )}
              </div>

              {j.status === "completed" && j.output_path && (
                <div className="job-output">
                  <strong>Exported Video:</strong> <code>{j.output_path}</code>
                </div>
              )}

              {j.status === "queued" && (
                <div className="job-cmd">
                  <span>Render CLI: <code>python -m worker.cli --job-id {j.id}</code></span>
                </div>
              )}
            </div>
          ))
        )}
      </section>

      <p className="muted" style={{ marginTop: "30px", textAlign: "center" }}>
        ShortForge AI · GeoGlobeTales-Style Geography Engine · Powered by Blender 5.2 & Natural Earth Datasets
      </p>
    </main>
  );
}
