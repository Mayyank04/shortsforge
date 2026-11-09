"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

const API = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

type Project = {
  id: string;
  title: string;
  genre: string;
  duration: number;
  language: string;
  voice: string;
  status: string;
  viral_title?: string;
  output_path?: string;
  created_at: string;
};

const GENRES = [
  { id: "emotional", name: "❤️ Emotional", desc: "Vulnerability, high stakes & sacrifice" },
  { id: "adventure", name: "⚔️ Adventure", desc: "Epic journey across biomes & ruins" },
  { id: "friendship", name: "🤝 Friendship", desc: "Unbreakable bond between unlikely allies" },
  { id: "heroic_sacrifice", name: "🛡️ Heroic Sacrifice", desc: "Standing tall when all else falls back" },
  { id: "survival", name: "❄️ Survival", desc: "Harsh elements & relentless threats" },
  { id: "mystery", name: "🔍 Mystery", desc: "Ancient secrets and forbidden dungeons" },
  { id: "horror", name: "💀 Horror (Safe)", desc: "Atmospheric tension and eerie entities" },
  { id: "unexpected_twist", name: "🌀 Unexpected Twist", desc: "Nothing is what it appears to be" },
  { id: "rescue", name: "🔥 Rescue", desc: "High-octane mission into the Nether" },
  { id: "funny", name: "😂 Funny", desc: "Hilarious mishaps and accidental victory" },
  { id: "betrayal", name: "🗡️ Betrayal", desc: "Broken trust redeemed through bravery" },
  { id: "fantasy", name: "✨ Fantasy", desc: "Mystical beacons & celestial events" },
];

export default function MinecraftStudio() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  async function loadProjects() {
    try {
      const res = await fetch(`${API}/api/minecraft/projects`);
      if (res.ok) {
        setProjects(await res.json());
      }
    } catch {}
  }

  useEffect(() => {
    loadProjects();
    const t = setInterval(loadProjects, 3500);
    return () => clearInterval(t);
  }, []);

  async function createBenchmarkStory() {
    setLoading(true);
    setMessage("");
    try {
      const res = await fetch(`${API}/api/minecraft/projects`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: "The Villager Who Had Only One Heart",
          genre: "emotional",
          duration: 50,
          language: "en",
          voice: "heart",
          visual_quality: "final",
          characters: ["mini", "steve", "iron_golem", "shadow"],
          auto_render: true
        })
      });
      if (!res.ok) throw new Error("Could not queue benchmark story");
      const proj = await res.json();
      setMessage(`Benchmark Story Queued: ${proj.id}. Rendering 10 scenes in background...`);
      loadProjects();
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Creation failed");
    } finally {
      setLoading(false);
    }
  }

  async function deleteProject(id: string) {
    if (!confirm("Delete this story project?")) return;
    try {
      await fetch(`${API}/api/minecraft/projects/${id}`, { method: "DELETE" });
      loadProjects();
    } catch {}
  }

  return (
    <main>
      <div className="eyebrow">
        <span>MINECRAFT STORY STUDIO · VOXEL ANIMATION</span>
        <span className="nav-brand-badge">PRO MODE</span>
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <h1>
            Minecraft <span style={{ color: "#a855f7" }}>Story Studio.</span>
          </h1>
          <p>
            Generate cinematic 10-scene animated voxel films with canonical characters, dynamic cameras, and Kokoro voiceover.
          </p>
        </div>
        <div style={{ display: "flex", gap: "10px" }}>
          <button className="primary" onClick={createBenchmarkStory} disabled={loading} style={{ background: "#a855f7", color: "#fff" }}>
            🏆 Render Benchmark Story →
          </button>
          <Link href="/minecraft/create" className="secondary" style={{ padding: "14px 22px", borderRadius: "10px" }}>
            + Create Custom Story
          </Link>
        </div>
      </div>

      {message && <p style={{ color: "#f5c84c", fontWeight: 700 }}>{message}</p>}

      {/* 12 Genres Showcase */}
      <section className="panel" style={{ marginTop: "24px" }}>
        <h3 style={{ margin: "0 0 14px 0", color: "#cbd5e1" }}>Supported Story Genres</h3>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", gap: "12px" }}>
          {GENRES.map((g) => (
            <Link
              key={g.id}
              href={`/minecraft/create?genre=${g.id}`}
              style={{
                background: "#0b111e",
                padding: "14px",
                borderRadius: "12px",
                border: "1px solid #1e293b",
                display: "flex",
                flexDirection: "column",
                gap: "4px",
                transition: "all .15s"
              }}
            >
              <div style={{ fontWeight: 700, fontSize: "14px", color: "#f8fafc" }}>{g.name}</div>
              <div style={{ fontSize: "11px", color: "#8290a8", lineHeight: 1.4 }}>{g.desc}</div>
            </Link>
          ))}
        </div>
      </section>

      {/* Projects List */}
      <section className="panel">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
          <h3 style={{ margin: 0 }}>Minecraft Story Projects</h3>
          <span className="muted">{projects.length} Total Projects</span>
        </div>

        {projects.length === 0 ? (
          <div style={{ textAlign: "center", padding: "40px", background: "#0b111e", borderRadius: "12px" }}>
            <p style={{ color: "#a855f7", fontWeight: 700 }}>No Minecraft story projects yet.</p>
            <p className="muted">Click "Render Benchmark Story" or "+ Create Custom Story" to start your first production.</p>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
            {projects.map((p) => {
              const videoFilename = p.output_path ? p.output_path.split("/").pop() : "";
              return (
                <div key={p.id} style={{ background: "#0b111e", border: "1px solid #233149", borderRadius: "14px", padding: "18px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "12px" }}>
                    <div>
                      <div style={{ fontSize: "18px", fontWeight: 800, color: "#fff" }}>{p.title}</div>
                      <div className="muted" style={{ marginTop: "4px" }}>
                        Genre: <strong style={{ color: "#a855f7", textTransform: "capitalize" }}>{p.genre}</strong> · {p.duration}s · Lang: {p.language.toUpperCase()} · Voice: {p.voice}
                      </div>
                      {p.viral_title && (
                        <div style={{ fontSize: "13px", color: "#f5c84c", marginTop: "4px", fontStyle: "italic" }}>
                          Hook: "{p.viral_title}"
                        </div>
                      )}
                    </div>
                    <span className={`status-badge status-${p.status}`}>{p.status}</span>
                  </div>

                  {/* Actions & Direct Links */}
                  <div style={{ display: "flex", gap: "8px", marginTop: "14px", flexWrap: "wrap" }}>
                    <Link href={`/minecraft/storyboard/${p.id}`} className="action-btn">
                      🎬 Storyboard & Scenes
                    </Link>
                    <Link href={`/minecraft/animation/${p.id}`} className="action-btn">
                      🎥 Animation
                    </Link>
                    <Link href={`/minecraft/audio/${p.id}`} className="action-btn">
                      🎙️ Voice & Audio
                    </Link>
                    {p.status === "completed" && videoFilename && (
                      <a href={`${API}/outputs/${videoFilename}`} download className="action-btn" style={{ color: "#2ed573", borderColor: "rgba(46,213,115,0.4)" }}>
                        ⬇️ Download MP4
                      </a>
                    )}
                    <button className="action-btn danger" onClick={() => deleteProject(p.id)}>
                      🗑️ Delete
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>
    </main>
  );
}
