"use client";
import { useEffect, useState, use } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

const API = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

type Scene = {
  id: string;
  scene_number: number;
  duration: number;
  narration: string;
  environment: string;
  time_of_day: string;
  camera_json?: string;
  character_actions_json?: string;
  lighting?: string;
  atmosphere?: string;
  transition: string;
  image_prompt?: string;
  animation_prompt?: string;
  audio_cues_json?: string;
};

type Project = {
  id: string;
  title: string;
  genre: string;
  duration: number;
  status: string;
  viral_title?: string;
  output_path?: string;
  scenes: Scene[];
};

export default function StoryboardStudio({ params }: { params: Promise<{ projectId: string }> }) {
  const resolvedParams = use(params);
  const projectId = resolvedParams.projectId;
  const router = useRouter();

  const [project, setProject] = useState<Project | null>(null);
  const [editingSceneId, setEditingSceneId] = useState<string | null>(null);
  const [editNarr, setEditNarr] = useState("");
  const [editDur, setEditDur] = useState(5.0);
  const [editEnv, setEditEnv] = useState("Village");
  const [editTod, setEditTod] = useState("day");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  async function loadProject() {
    try {
      const res = await fetch(`${API}/api/minecraft/projects/${projectId}`);
      if (res.ok) {
        setProject(await res.json());
      }
    } catch {}
  }

  useEffect(() => {
    loadProject();
    const t = setInterval(loadProject, 4000);
    return () => clearInterval(t);
  }, [projectId]);

  function startEditing(sc: Scene) {
    setEditingSceneId(sc.id);
    setEditNarr(sc.narration);
    setEditDur(sc.duration);
    setEditEnv(sc.environment);
    setEditTod(sc.time_of_day);
  }

  async function saveScene(sceneId: string) {
    setBusy(true);
    try {
      const res = await fetch(`${API}/api/minecraft/scenes/${sceneId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          narration: editNarr,
          duration: Number(editDur),
          environment: editEnv,
          time_of_day: editTod
        })
      });
      if (res.ok) {
        setEditingSceneId(null);
        loadProject();
      }
    } catch {} finally {
      setBusy(false);
    }
  }

  async function triggerRender() {
    setBusy(true);
    setMessage("");
    try {
      const res = await fetch(`${API}/api/minecraft/projects/${projectId}/render`, {
        method: "POST"
      });
      if (!res.ok) throw new Error("Render trigger failed");
      setMessage("Rendering pipeline initiated! You can monitor progress below.");
      loadProject();
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Error initiating render");
    } finally {
      setBusy(false);
    }
  }

  if (!project) {
    return (
      <main>
        <p>Loading project storyboard...</p>
      </main>
    );
  }

  const videoFilename = project.output_path ? project.output_path.split("/").pop() : "";

  return (
    <main>
      <div className="eyebrow">
        <span>STORYBOARD STUDIO · 10-SCENE EDITABLE TIMELINE</span>
        <Link href="/minecraft" style={{ color: "#38bdf8", fontWeight: 700 }}>
          ← Back to Minecraft Projects
        </Link>
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <h1>{project.title}</h1>
          <div className="muted">
            Genre: <strong style={{ color: "#a855f7" }}>{project.genre}</strong> · Duration: {project.duration}s · Status: <span className={`status-badge status-${project.status}`}>{project.status}</span>
          </div>
          {project.viral_title && (
            <p style={{ color: "#f5c84c", margin: "6px 0 0 0", fontStyle: "italic" }}>
              "{project.viral_title}"
            </p>
          )}
        </div>

        <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
          <Link href={`/minecraft/animation/${projectId}`} className="action-btn">
            🎥 Animation Studio
          </Link>
          <Link href={`/minecraft/audio/${projectId}`} className="action-btn">
            🎙️ Voice & Audio
          </Link>
          <button className="primary" onClick={triggerRender} disabled={busy || project.status === "rendering"} style={{ margin: 0, background: "#a855f7", color: "#fff" }}>
            {project.status === "rendering" ? "Rendering in Progress..." : "🚀 Launch 3D Render →"}
          </button>
        </div>
      </div>

      {message && <p style={{ color: "#f5c84c", fontWeight: 700, marginTop: "14px" }}>{message}</p>}

      {/* Video Player if Completed */}
      {project.status === "completed" && videoFilename && (
        <section className="panel" style={{ borderColor: "#2ed573", marginTop: "20px" }}>
          <h3 style={{ color: "#2ed573", marginTop: 0 }}>🎉 Production Video Ready</h3>
          <div className="video-preview-box">
            <video className="video-player" controls playsInline src={`${API}/outputs/${videoFilename}`} />
            <div className="video-meta">
              <h4>Exported ShortForge MP4</h4>
              <div className="meta-badges">
                <span className="m-badge">1080x1920 (9:16)</span>
                <span className="m-badge">30 FPS</span>
                <span className="m-badge">H.264 / AAC</span>
                <span className="m-badge">{project.duration}s</span>
              </div>
              <p style={{ fontSize: "13px", color: "#cbd5e1" }}>
                File: <code>{project.output_path}</code>
              </p>
              <a href={`${API}/outputs/${videoFilename}`} download className="primary" style={{ padding: "10px 18px", fontSize: "14px", textDecoration: "none" }}>
                ⬇️ Download MP4 Short
              </a>
            </div>
          </div>
        </section>
      )}

      {/* Scenes List */}
      <section className="panel">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
          <h3 style={{ margin: 0 }}>Scene-by-Scene Storyboard ({project.scenes.length} Scenes)</h3>
          <span className="muted">Total Duration: {project.scenes.reduce((acc, s) => acc + s.duration, 0).toFixed(1)}s</span>
        </div>

        <div className="scenes-grid">
          {project.scenes.map((sc) => {
            const isEditing = editingSceneId === sc.id;

            return (
              <div key={sc.id} className="scene-row">
                <div className="scene-header">
                  <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                    <span style={{ fontWeight: 800, color: "#f5c84c", fontSize: "16px" }}>
                      SCENE {sc.scene_number}
                    </span>
                    <span className="m-badge">{sc.duration.toFixed(1)}s</span>
                    <span className="m-badge" style={{ color: "#38bdf8" }}>{sc.environment}</span>
                    <span className="m-badge">{sc.time_of_day.toUpperCase()}</span>
                  </div>

                  <div>
                    {isEditing ? (
                      <div style={{ display: "flex", gap: "6px" }}>
                        <button className="action-btn" onClick={() => saveScene(sc.id)} disabled={busy} style={{ background: "#2ed573", color: "#000" }}>
                          Save
                        </button>
                        <button className="action-btn" onClick={() => setEditingSceneId(null)}>
                          Cancel
                        </button>
                      </div>
                    ) : (
                      <button className="action-btn" onClick={() => startEditing(sc)}>
                        ✎ Edit Scene
                      </button>
                    )}
                  </div>
                </div>

                {/* Narration view / edit */}
                {isEditing ? (
                  <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                    <textarea rows={2} value={editNarr} onChange={(e) => setEditNarr(e.target.value)} />
                    <div className="form-grid">
                      <div>
                        <label style={{ margin: "0 0 4px 0", fontSize: "12px" }}>Duration (s)</label>
                        <input type="number" step="0.5" value={editDur} onChange={(e) => setEditDur(Number(e.target.value))} />
                      </div>
                      <div>
                        <label style={{ margin: "0 0 4px 0", fontSize: "12px" }}>Environment</label>
                        <select value={editEnv} onChange={(e) => setEditEnv(e.target.value)}>
                          <option value="Village">Village</option>
                          <option value="Forest">Forest</option>
                          <option value="Cave">Cave</option>
                          <option value="Mountain">Mountain</option>
                          <option value="Nether">Nether</option>
                          <option value="Snow">Snow</option>
                          <option value="Desert">Desert</option>
                          <option value="Castle">Castle</option>
                          <option value="Underground_Mine">Underground Mine</option>
                        </select>
                      </div>
                      <div>
                        <label style={{ margin: "0 0 4px 0", fontSize: "12px" }}>Time of Day</label>
                        <select value={editTod} onChange={(e) => setEditTod(e.target.value)}>
                          <option value="dawn">Dawn</option>
                          <option value="day">Day</option>
                          <option value="dusk">Dusk</option>
                          <option value="night">Night</option>
                          <option value="storm">Storm</option>
                        </select>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="scene-narr">"{sc.narration}"</div>
                )}

                {/* Image & Animation Prompts */}
                {sc.image_prompt && (
                  <div className="prompt-box">
                    <strong style={{ color: "#38bdf8" }}>🖼️ Image Prompt:</strong> {sc.image_prompt}
                  </div>
                )}

                {sc.animation_prompt && (
                  <div className="prompt-box">
                    <strong style={{ color: "#a855f7" }}>🎥 Animation Prompt:</strong> {sc.animation_prompt}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </section>
    </main>
  );
}
