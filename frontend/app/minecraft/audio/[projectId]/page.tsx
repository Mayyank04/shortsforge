"use client";
import { useEffect, useState, use } from "react";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

type Scene = {
  id: string;
  scene_number: number;
  duration: number;
  narration: string;
  audio_cues_json?: string;
};

type Project = {
  id: string;
  title: string;
  language: string;
  voice: string;
  scenes: Scene[];
};

export default function AudioStudio({ params }: { params: Promise<{ projectId: string }> }) {
  const resolvedParams = use(params);
  const projectId = resolvedParams.projectId;

  const [project, setProject] = useState<Project | null>(null);
  const [voice, setVoice] = useState("heart");
  const [language, setLanguage] = useState("en");
  const [speed, setSpeed] = useState(1.05);
  const [bgmVol, setBgmVol] = useState(-18);
  const [statusMsg, setStatusMsg] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch(`${API}/api/minecraft/projects/${projectId}`);
        if (res.ok) {
          const data: Project = await res.json();
          setProject(data);
          setVoice(data.voice || "heart");
          setLanguage(data.language || "en");
        }
      } catch {}
    }
    load();
  }, [projectId]);

  async function saveAudioSettings() {
    if (!project) return;
    setBusy(true);
    setStatusMsg("");
    try {
      const res = await fetch(`${API}/api/minecraft/projects/${projectId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ voice, language })
      });
      if (res.ok) {
        setStatusMsg("Audio & narrator preferences saved successfully!");
      }
    } catch {
      setStatusMsg("Failed to save audio settings");
    } finally {
      setBusy(false);
    }
  }

  if (!project) {
    return <main><p>Loading Voice & Audio Studio...</p></main>;
  }

  return (
    <main>
      <div className="eyebrow">
        <span>KOKORO NEURAL AUDIO & SFX MIXING · DUCKED BGM</span>
        <Link href={`/minecraft/storyboard/${projectId}`} style={{ color: "#38bdf8", fontWeight: 700 }}>
          ← Back to Storyboard
        </Link>
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <h1>
            Voice & <span style={{ color: "#a855f7" }}>Audio Studio.</span>
          </h1>
          <p>
            Configure neural voice models, language-aware synthesis (English & Hindi), sidechain music ducking, and sound effect cues.
          </p>
        </div>
        <button className="primary" onClick={saveAudioSettings} disabled={busy} style={{ background: "#a855f7", color: "#fff" }}>
          {busy ? "Saving..." : "💾 Save Audio Settings"}
        </button>
      </div>

      {statusMsg && <p style={{ color: "#f5c84c", fontWeight: 700 }}>{statusMsg}</p>}

      {/* Audio Engine Configuration */}
      <section className="panel">
        <h3 style={{ margin: "0 0 16px 0", color: "#f8fafc" }}>Audio Engine Settings</h3>

        <div className="form-grid">
          <div>
            <label htmlFor="lang">Narration Language</label>
            <select id="lang" value={language} onChange={(e) => setLanguage(e.target.value)}>
              <option value="en">English (Kokoro 82M Neural Synthesis)</option>
              <option value="hi">Hindi (Language-Aware Voice Adapter)</option>
            </select>
          </div>

          <div>
            <label htmlFor="voice">Voice Profile</label>
            <select id="voice" value={voice} onChange={(e) => setVoice(e.target.value)}>
              <option value="heart">Heart (Warm & Expressive Female)</option>
              <option value="adam">Adam (Authoritative Male)</option>
              <option value="alice">Alice (Clear British Female)</option>
              <option value="george">George (Documentary British Male)</option>
              <option value="nicole">Nicole (Dynamic Narrative Female)</option>
              <option value="michael">Michael (Cinematic Deep Male)</option>
            </select>
          </div>

          <div>
            <label htmlFor="speed">Speaking Speed: {speed.toFixed(2)}x</label>
            <input
              id="speed"
              type="range"
              min="0.85"
              max="1.30"
              step="0.05"
              value={speed}
              onChange={(e) => setSpeed(Number(e.target.value))}
            />
          </div>

          <div>
            <label htmlFor="bgm">BGM Ducking Volume: {bgmVol} dB</label>
            <input
              id="bgm"
              type="range"
              min="-28"
              max="-10"
              step="1"
              value={bgmVol}
              onChange={(e) => setBgmVol(Number(e.target.value))}
            />
          </div>
        </div>
      </section>

      {/* Subtitles & Typography */}
      <section className="panel">
        <h3 style={{ margin: "0 0 16px 0", color: "#cbd5e1" }}>Synchronized Vertical Subtitles</h3>
        <div style={{ background: "#0b111e", padding: "16px", borderRadius: "12px", border: "1px solid #1e293b", display: "flex", gap: "20px", flexWrap: "wrap", alignItems: "center" }}>
          <div style={{ width: "240px", height: "140px", background: "#060912", borderRadius: "10px", display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", border: "1px solid #233149", padding: "10px", textAlign: "center" }}>
            <span style={{ fontSize: "10px", color: "#38bdf8", fontWeight: 800, marginBottom: "6px" }}>SCENE 1/10 · EMOTIONAL</span>
            <div style={{ background: "rgba(10,15,28,0.9)", border: "1px solid #f5c84c", borderRadius: "6px", padding: "6px 10px", fontSize: "11px", color: "#fff", fontWeight: 700 }}>
              Mini was born with only <span style={{ color: "#f5c84c" }}>one heart</span>.
            </div>
          </div>
          <div style={{ flex: 1, minWidth: "260px" }}>
            <h4 style={{ margin: "0 0 6px 0", color: "#f5c84c" }}>Safe Vertical Formatting (1080x1920)</h4>
            <p style={{ fontSize: "13px", color: "#94a3b8", margin: 0, lineHeight: 1.5 }}>
              Strict safe margins prevent caption cutoff from mobile video players. Active words are highlighted in amber gold (#f5c84c) over a frosted black backdrop card.
            </p>
          </div>
        </div>
      </section>

      {/* Scene Narration Cues */}
      <section className="panel">
        <h3 style={{ margin: "0 0 16px 0", color: "#cbd5e1" }}>Scene Narration Scripts & Sound Cues</h3>
        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          {project.scenes.map((s) => (
            <div key={s.id} style={{ background: "#0b111e", padding: "14px 18px", borderRadius: "10px", border: "1px solid #1e293b" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                <span style={{ fontWeight: 800, color: "#f5c84c", fontSize: "13px" }}>SCENE {s.scene_number}</span>
                <span className="m-badge">{s.duration.toFixed(1)}s</span>
              </div>
              <div style={{ color: "#f8fafc", fontSize: "14px" }}>"{s.narration}"</div>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
