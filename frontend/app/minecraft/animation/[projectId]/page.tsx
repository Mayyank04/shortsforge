"use client";
import { useEffect, useState, use } from "react";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

type Scene = {
  id: string;
  scene_number: number;
  duration: number;
  narration: string;
  environment: string;
  time_of_day: string;
  lighting?: string;
  atmosphere?: string;
  transition: string;
};

type Project = {
  id: string;
  title: string;
  genre: string;
  status: string;
  scenes: Scene[];
};

export default function AnimationStudio({ params }: { params: Promise<{ projectId: string }> }) {
  const resolvedParams = use(params);
  const projectId = resolvedParams.projectId;

  const [project, setProject] = useState<Project | null>(null);
  const [selectedSceneNum, setSelectedSceneNum] = useState<number>(1);
  const [cameraShot, setCameraShot] = useState("medium_shot");
  const [cameraMove, setCameraMove] = useState("slow_dolly_in");
  const [charAction, setCharAction] = useState("walking");
  const [charEmotion, setCharEmotion] = useState("determined");
  const [lighting, setLighting] = useState("warm golden sunlight");
  const [environment, setEnvironment] = useState("Village");
  const [timeOfDay, setTimeOfDay] = useState("day");
  const [fps, setFps] = useState(30);
  const [statusMsg, setStatusMsg] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch(`${API}/api/minecraft/projects/${projectId}`);
        if (res.ok) {
          const data: Project = await res.json();
          setProject(data);
          if (data.scenes && data.scenes.length > 0) {
            const sc = data.scenes[0];
            setEnvironment(sc.environment);
            setTimeOfDay(sc.time_of_day);
          }
        }
      } catch {}
    }
    load();
  }, [projectId]);

  async function saveAnimationSettings() {
    if (!project) return;
    const currentScene = project.scenes.find((s) => s.scene_number === selectedSceneNum);
    if (!currentScene) return;

    setBusy(true);
    setStatusMsg("");
    try {
      const res = await fetch(`${API}/api/minecraft/scenes/${currentScene.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          environment,
          time_of_day: timeOfDay,
          lighting,
          camera_json: JSON.stringify({ shot: cameraShot, movement: cameraMove }),
          character_actions_json: JSON.stringify([{ action: charAction, emotion: charEmotion }])
        })
      });
      if (res.ok) {
        setStatusMsg(`Scene ${selectedSceneNum} animation parameters updated successfully!`);
      }
    } catch (e) {
      setStatusMsg("Failed to update animation settings");
    } finally {
      setBusy(false);
    }
  }

  if (!project) {
    return <main><p>Loading Animation Studio...</p></main>;
  }

  return (
    <main>
      <div className="eyebrow">
        <span>BLENDER 3D ANIMATION ENGINE · VOXEL RIGGING</span>
        <Link href={`/minecraft/storyboard/${projectId}`} style={{ color: "#38bdf8", fontWeight: 700 }}>
          ← Back to Storyboard
        </Link>
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <h1>
            Animation <span style={{ color: "#a855f7" }}>Studio.</span>
          </h1>
          <p>
            Configure articulated limb actions, procedural voxel biomes, cinematic camera movements, and lighting keyframes for Blender.
          </p>
        </div>
        <div style={{ display: "flex", gap: "10px" }}>
          <button className="primary" onClick={saveAnimationSettings} disabled={busy} style={{ background: "#a855f7", color: "#fff" }}>
            {busy ? "Saving..." : "💾 Save Animation Settings"}
          </button>
        </div>
      </div>

      {statusMsg && <p style={{ color: "#f5c84c", fontWeight: 700 }}>{statusMsg}</p>}

      {/* Scene Selector Pill Navigation */}
      <div style={{ display: "flex", gap: "8px", overflowX: "auto", padding: "12px 0" }}>
        {project.scenes.map((s) => (
          <button
            key={s.id}
            type="button"
            className={`action-btn ${selectedSceneNum === s.scene_number ? "primary" : ""}`}
            style={{
              background: selectedSceneNum === s.scene_number ? "#a855f7" : "#0e1526",
              color: selectedSceneNum === s.scene_number ? "#fff" : "#94a3b8",
              borderColor: selectedSceneNum === s.scene_number ? "#c084fc" : "#233149",
              padding: "10px 16px"
            }}
            onClick={() => {
              setSelectedSceneNum(s.scene_number);
              setEnvironment(s.environment);
              setTimeOfDay(s.time_of_day);
            }}
          >
            Scene {s.scene_number}
          </button>
        ))}
      </div>

      {/* Animation Controls Panel */}
      <section className="panel">
        <h3 style={{ margin: "0 0 16px 0", color: "#f8fafc" }}>
          Scene {selectedSceneNum} Animation Controls
        </h3>

        <div className="form-grid">
          <div>
            <label htmlFor="shot">Camera Shot Type</label>
            <select id="shot" value={cameraShot} onChange={(e) => setCameraShot(e.target.value)}>
              <option value="extreme_close_up">Extreme Close-Up (Emotional Focus)</option>
              <option value="close_up">Close-Up (Character Expression)</option>
              <option value="medium_shot">Medium Shot (Character & Surroundings)</option>
              <option value="wide_shot">Wide Shot (Environment Scale)</option>
              <option value="establishing_shot">Establishing Shot (World Intro)</option>
              <option value="low_angle">Low Angle (Heroic / Threatening)</option>
              <option value="high_angle">High Angle (Overlook)</option>
              <option value="tracking_shot">Tracking Shot (Following Movement)</option>
              <option value="orbit">Orbit (360 Degree Rotation)</option>
            </select>
          </div>

          <div>
            <label htmlFor="camMove">Camera Trajectory</label>
            <select id="camMove" value={cameraMove} onChange={(e) => setCameraMove(e.target.value)}>
              <option value="slow_dolly_in">Slow Dolly In (Building Focus)</option>
              <option value="slow_dolly_out">Slow Dolly Out (Grand Reveal)</option>
              <option value="orbit">Orbital Rotation</option>
              <option value="crane_down">Crane Down</option>
              <option value="crane_up">Crane Up</option>
              <option value="pan_right">Smooth Pan Right</option>
            </select>
          </div>

          <div>
            <label htmlFor="action">Character Articulated Action</label>
            <select id="action" value={charAction} onChange={(e) => setCharAction(e.target.value)}>
              <option value="walking">Walking (Sinusoidal Limb Swing)</option>
              <option value="running">Running (High Amplitude & Torso Lean)</option>
              <option value="jumping">Jumping (Z Translation & Leg Tuck)</option>
              <option value="falling">Falling (Drop & Limb Splay)</option>
              <option value="waving">Waving (Arm Overhead Oscillation)</option>
              <option value="celebrating">Celebrating (Victory Arms V-Shape)</option>
              <option value="pointing">Pointing (Direct Forward Extension)</option>
              <option value="fighting">Fighting (Attack Arc Swing)</option>
              <option value="reaching">Reaching (Forward Grasp)</option>
              <option value="carrying">Carrying (Object Grip Forward)</option>
              <option value="looking_scared">Looking Scared (Torso Recoil)</option>
            </select>
          </div>

          <div>
            <label htmlFor="emotion">Facial & Expression State</label>
            <select id="emotion" value={charEmotion} onChange={(e) => setCharEmotion(e.target.value)}>
              <option value="determined">Determined</option>
              <option value="vulnerable">Vulnerable / Fragile</option>
              <option value="triumphant">Triumphant</option>
              <option value="alarmed">Alarmed</option>
              <option value="menacing">Menacing</option>
              <option value="grateful">Grateful</option>
            </select>
          </div>

          <div>
            <label htmlFor="env">Procedural Biome</label>
            <select id="env" value={environment} onChange={(e) => setEnvironment(e.target.value)}>
              <option value="Village">Village (Oak Houses, Lamps & Square)</option>
              <option value="Forest">Forest (Lush Birch & Oak Foliage)</option>
              <option value="Cave">Cave (Stone Walls & Shadows)</option>
              <option value="Mountain">Mountain (High Elevation Cliffs)</option>
              <option value="Nether">Nether (Lava Lakes & Netherrack)</option>
              <option value="Snow">Snow (Ice Terrain & Pine Trees)</option>
              <option value="Desert">Desert (Sandstone & Cacti)</option>
              <option value="Castle">Castle (Fortress Battlements)</option>
              <option value="Underground_Mine">Underground Mine (Support Beams)</option>
            </select>
          </div>

          <div>
            <label htmlFor="tod">Time of Day & Sunlight</label>
            <select id="tod" value={timeOfDay} onChange={(e) => setTimeOfDay(e.target.value)}>
              <option value="day">Day (Bright Sun & Soft Bounce)</option>
              <option value="dawn">Dawn (Golden Morning Rim Light)</option>
              <option value="dusk">Dusk (Dramatic Amber Sunset)</option>
              <option value="night">Night (Deep Blue Moonlight)</option>
              <option value="storm">Storm (Lightning Strobe & Heavy Rain)</option>
            </select>
          </div>
        </div>

        <div style={{ marginTop: "16px" }}>
          <label htmlFor="lightingText">Lighting Keyframe Specification</label>
          <input id="lightingText" value={lighting} onChange={(e) => setLighting(e.target.value)} />
        </div>
      </section>
    </main>
  );
}
