"use client";
import { useEffect, useState } from "react";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

type SettingsData = {
  blender: { installed: boolean; version: string };
  ffmpeg: { installed: boolean; path: string };
  kokoro: { installed: boolean; status: string };
  ollama: { available: boolean; url: string };
  storage: { total_gb: number; used_gb: number; free_gb: number };
  system: { platform: string };
};

export default function SettingsPage() {
  const [data, setData] = useState<SettingsData | null>(null);
  const [loading, setLoading] = useState(false);
  const [ollamaUrl, setOllamaUrl] = useState("http://localhost:11434");
  const [ollamaModel, setOllamaModel] = useState("llama3:latest");
  const [testMsg, setTestMsg] = useState("");

  async function loadSettings() {
    try {
      const res = await fetch(`${API}/api/settings`);
      if (res.ok) {
        setData(await res.json());
      }
    } catch {}
  }

  useEffect(() => {
    loadSettings();
  }, []);

  async function testOllamaConnection() {
    setLoading(true);
    setTestMsg("");
    try {
      const res = await fetch(`${API}/api/settings`);
      if (res.ok) {
        const s: SettingsData = await res.json();
        setData(s);
        if (s.ollama.available) {
          setTestMsg("✓ Ollama local LLM connected successfully at http://localhost:11434");
        } else {
          setTestMsg("Notice: Ollama is not currently running. ShortForge will use the built-in procedural story generator.");
        }
      }
    } catch {
      setTestMsg("Could not connect to backend settings.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main>
      <div className="eyebrow">
        <span>SYSTEM DIAGNOSTICS & HARDWARE CONFIGURATION</span>
        <Link href="/dashboard" style={{ color: "#38bdf8", fontWeight: 700 }}>
          ← Back to Dashboard
        </Link>
      </div>

      <h1>
        Settings & <span style={{ color: "#38bdf8" }}>Diagnostics.</span>
      </h1>
      <p>
        Review local hardware acceleration, Blender 3D detection, neural voice synthesis, and cloud Kaggle parameters.
      </p>

      {/* Hardware / Engine Diagnostics */}
      <section className="panel">
        <h3 style={{ margin: "0 0 16px 0", color: "#f8fafc" }}>Rendering & Pipeline Status</h3>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "16px" }}>
          {/* Blender */}
          <div style={{ background: "#0b111e", border: "1px solid #1e293b", borderRadius: "12px", padding: "16px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <strong style={{ color: "#fff" }}>Blender 3D</strong>
              <span className={`status-badge ${data?.blender.installed ? "status-completed" : "status-failed"}`}>
                {data?.blender.installed ? "Installed" : "Missing"}
              </span>
            </div>
            <div style={{ fontSize: "13px", color: "#38bdf8", marginTop: "8px" }}>
              {data?.blender.version || "Scanning for Blender binary..."}
            </div>
            <div style={{ fontSize: "11px", color: "#64748b", marginTop: "6px" }}>
              Dynamic cross-platform detection: macOS Apple Silicon, Linux/Kaggle, and Windows.
            </div>
          </div>

          {/* FFmpeg */}
          <div style={{ background: "#0b111e", border: "1px solid #1e293b", borderRadius: "12px", padding: "16px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <strong style={{ color: "#fff" }}>FFmpeg</strong>
              <span className={`status-badge ${data?.ffmpeg.installed ? "status-completed" : "status-failed"}`}>
                {data?.ffmpeg.installed ? "Ready" : "Missing"}
              </span>
            </div>
            <div style={{ fontSize: "13px", color: "#cbd5e1", marginTop: "8px" }}>
              Path: <code>{data?.ffmpeg.path}</code>
            </div>
            <div style={{ fontSize: "11px", color: "#64748b", marginTop: "6px" }}>
              H.264 video encoding, AAC audio muxing, and ducked audio sidechain compression.
            </div>
          </div>

          {/* Kokoro TTS */}
          <div style={{ background: "#0b111e", border: "1px solid #1e293b", borderRadius: "12px", padding: "16px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <strong style={{ color: "#fff" }}>Voice Synthesis</strong>
              <span className={`status-badge ${data?.kokoro.installed ? "status-completed" : "status-queued"}`}>
                {data?.kokoro.installed ? "Neural" : "Fallback"}
              </span>
            </div>
            <div style={{ fontSize: "13px", color: "#f5c84c", marginTop: "8px" }}>
              {data?.kokoro.status}
            </div>
            <div style={{ fontSize: "11px", color: "#64748b", marginTop: "6px" }}>
              Kokoro 82M high-fidelity TTS with macOS say / Linux espeak-ng fallback.
            </div>
          </div>

          {/* Storage */}
          <div style={{ background: "#0b111e", border: "1px solid #1e293b", borderRadius: "12px", padding: "16px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <strong style={{ color: "#fff" }}>Local Storage</strong>
              <span className="status-badge status-completed">Online</span>
            </div>
            <div style={{ fontSize: "13px", color: "#38bdf8", marginTop: "8px" }}>
              {data?.storage.free_gb} GB Free / {data?.storage.total_gb} GB Total
            </div>
            <div style={{ fontSize: "11px", color: "#64748b", marginTop: "6px" }}>
              Outputs saved to <code>outputs/</code> with static HTTP streaming support.
            </div>
          </div>
        </div>
      </section>

      {/* Ollama LLM Configuration */}
      <section className="panel">
        <h3 style={{ margin: "0 0 16px 0", color: "#a855f7" }}>Ollama Local LLM Integration (Optional)</h3>
        <p style={{ fontSize: "14px" }}>
          ShortForge AI can query a locally running Ollama instance for structured JSON story generation. If unreachable, it automatically uses the built-in procedural narrative engine with zero downtime.
        </p>

        <div className="form-grid">
          <div>
            <label htmlFor="ourl">Ollama Endpoint URL</label>
            <input id="ourl" value={ollamaUrl} onChange={(e) => setOllamaUrl(e.target.value)} />
          </div>
          <div>
            <label htmlFor="omodel">Model Name</label>
            <input id="omodel" value={ollamaModel} onChange={(e) => setOllamaModel(e.target.value)} />
          </div>
        </div>

        <div style={{ marginTop: "16px", display: "flex", alignItems: "center", gap: "12px" }}>
          <button type="button" className="secondary" onClick={testOllamaConnection} disabled={loading} style={{ margin: 0 }}>
            {loading ? "Testing..." : "🔍 Test Ollama Connection"}
          </button>
          {testMsg && <span style={{ fontSize: "13px", color: "#f5c84c" }}>{testMsg}</span>}
        </div>
      </section>

      {/* Kaggle Cloud GPU Setup Instructions */}
      <section className="panel">
        <h3 style={{ margin: "0 0 14px 0", color: "#38bdf8" }}>Cloud Rendering on Kaggle GPU</h3>
        <p style={{ fontSize: "14px" }}>
          For high-speed batch production or systems without a dedicated GPU, run the pre-configured notebook:
        </p>
        <div className="job-cmd" style={{ padding: "14px" }}>
          <span>Notebook Path: <code>notebooks/shortforge_kaggle.ipynb</code></span>
        </div>
        <p style={{ fontSize: "13px", color: "#94a3b8", marginTop: "10px" }}>
          Simply toggle Internet <strong>ON</strong> in Kaggle, select a GPU accelerator (T4 or P100), and run cells sequentially. Videos and project metadata are packaged directly into <code>/kaggle/working/shortforge_outputs.zip</code> for instant download.
        </p>
      </section>
    </main>
  );
}
