"use client";
import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

type CharacterOption = {
  id: string;
  name: string;
  role: string;
  species: string;
};

type GeneratedScene = {
  scene_number: number;
  duration: number;
  narration: string;
  environment: string;
  image_prompt: string;
  animation_prompt: string;
};

type GeneratedStory = {
  title: string;
  viral_title: string;
  opening_hook: string;
  plot_summary: string;
  loop_opportunity: string;
  scenes: GeneratedScene[];
};

function CreateStoryContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [title, setTitle] = useState("The Villager Who Had Only One Heart");
  const [idea, setIdea] = useState("");
  const [genre, setGenre] = useState(searchParams.get("genre") || "emotional");
  const [duration, setDuration] = useState(50);
  const [language, setLanguage] = useState("en");
  const [voice, setVoice] = useState("heart");
  const [visualQuality, setVisualQuality] = useState("final");
  const [characters, setCharacters] = useState<CharacterOption[]>([]);
  const [selectedCharIds, setSelectedCharIds] = useState<string[]>(["mini", "steve", "iron_golem", "shadow"]);
  const [autoRender, setAutoRender] = useState(true);

  const [busy, setBusy] = useState(false);
  const [previewStory, setPreviewStory] = useState<GeneratedStory | null>(null);
  const [message, setMessage] = useState("");

  useEffect(() => {
    async function loadCharacters() {
      try {
        const r = await fetch(`${API}/api/minecraft/characters`);
        if (r.ok) {
          const list: CharacterOption[] = await r.json();
          setCharacters(list);
        }
      } catch {}
    }
    loadCharacters();
  }, []);

  function toggleChar(id: string) {
    if (selectedCharIds.includes(id)) {
      if (selectedCharIds.length > 1) {
        setSelectedCharIds(selectedCharIds.filter((c) => c !== id));
      }
    } else {
      setSelectedCharIds([...selectedCharIds, id]);
    }
  }

  async function generateStoryOutline() {
    setBusy(true);
    setMessage("");
    try {
      const res = await fetch(`${API}/api/minecraft/stories/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          genre,
          idea: idea || title,
          duration,
          language,
          character_ids: selectedCharIds
        })
      });
      if (!res.ok) throw new Error("Could not generate story outline");
      const data: GeneratedStory = await res.json();
      setPreviewStory(data);
      if (data.title) setTitle(data.title);
      setMessage("Original 10-scene story generated with zero duplicate patterns!");
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Generation error");
    } finally {
      setBusy(false);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setMessage("");
    try {
      const res = await fetch(`${API}/api/minecraft/projects`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title,
          genre,
          duration,
          language,
          voice,
          visual_quality: visualQuality,
          characters: selectedCharIds,
          custom_idea: idea,
          auto_render: autoRender
        })
      });
      if (!res.ok) throw new Error("Could not create project");
      const proj = await res.json();
      setMessage(`Project created: ${proj.id}. Redirecting to Storyboard Studio...`);
      setTimeout(() => {
        router.push(`/minecraft/storyboard/${proj.id}`);
      }, 1000);
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Creation failed");
      setBusy(false);
    }
  }

  return (
    <main>
      <div className="eyebrow">
        <span>MINECRAFT STORY CREATOR · 10-SCENE WORKFLOW</span>
        <Link href="/minecraft" style={{ color: "#38bdf8", fontWeight: 700 }}>
          ← Back to Studio
        </Link>
      </div>

      <h1>
        Create original <span style={{ color: "#a855f7" }}>Minecraft Story.</span>
      </h1>
      <p>
        Define your narrative prompt, canonical characters, and visual direction. Generates an engaging 10-scene vertical short with loop hook.
      </p>

      <form onSubmit={handleSubmit}>
        <section className="panel">
          <label htmlFor="title">Story Title</label>
          <input
            id="title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
            minLength={3}
            maxLength={500}
            placeholder="The Villager Who Had Only One Heart"
          />

          <label htmlFor="idea">Custom Story Idea / Plot Concept (Optional)</label>
          <textarea
            id="idea"
            rows={3}
            value={idea}
            onChange={(e) => setIdea(e.target.value)}
            placeholder="e.g. A small villager with only one heart uses stealth and agility to restore the town beacon while giant guardians hold off the shadow horde..."
          />

          <div className="form-grid" style={{ marginTop: "14px" }}>
            <div>
              <label htmlFor="genre">Story Genre (12 Modes)</label>
              <select id="genre" value={genre} onChange={(e) => setGenre(e.target.value)}>
                <option value="emotional">❤️ Emotional (Vulnerability & Sacrifice)</option>
                <option value="adventure">⚔️ Adventure (Epic Exploration)</option>
                <option value="friendship">🤝 Friendship (Unlikely Allies)</option>
                <option value="heroic_sacrifice">🛡️ Heroic Sacrifice (Last Stand)</option>
                <option value="survival">❄️ Survival (Extreme Elements)</option>
                <option value="mystery">🔍 Mystery (Ancient Temple)</option>
                <option value="horror">💀 Horror (General-Audience-Safe)</option>
                <option value="unexpected_twist">🌀 Unexpected Twist (Deceptive Turns)</option>
                <option value="rescue">🔥 Rescue (Nether Mission)</option>
                <option value="funny">😂 Funny (Comedic Misfortunes)</option>
                <option value="betrayal">🗡️ Betrayal (Trust & Redemption)</option>
                <option value="fantasy">✨ Fantasy (Celestial Beacons)</option>
              </select>
            </div>

            <div>
              <label htmlFor="duration">Duration (10 Scenes)</label>
              <select id="duration" value={duration} onChange={(e) => setDuration(Number(e.target.value))}>
                <option value={35}>35s (Fast Paced ~3.5s/scene)</option>
                <option value={50}>50s (Standard Pacing ~5.0s/scene)</option>
                <option value={75}>75s (Extended Story ~7.5s/scene)</option>
                <option value={90}>90s (Epic Narrative ~9.0s/scene)</option>
              </select>
            </div>

            <div>
              <label htmlFor="lang">Narration Language</label>
              <select id="lang" value={language} onChange={(e) => setLanguage(e.target.value)}>
                <option value="en">English (Kokoro Neural Voice)</option>
                <option value="hi">Hindi (Language-Aware Voice Adapter)</option>
              </select>
            </div>

            <div>
              <label htmlFor="voice">Narrator Voice</label>
              <select id="voice" value={voice} onChange={(e) => setVoice(e.target.value)}>
                <option value="heart">Heart (Warm & Expressive Female)</option>
                <option value="adam">Adam (Authoritative Male Adventurer)</option>
                <option value="alice">Alice (Clear British Female)</option>
                <option value="george">George (Classic Deep Male)</option>
                <option value="nicole">Nicole (Dynamic Narrative Female)</option>
                <option value="michael">Michael (Dark Cinematic Male)</option>
              </select>
            </div>
          </div>

          {/* Character Selection */}
          <div style={{ marginTop: "18px" }}>
            <label>Cast Characters (Select at least one)</label>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "10px", marginTop: "8px" }}>
              {characters.map((c) => {
                const isSelected = selectedCharIds.includes(c.id);
                return (
                  <button
                    key={c.id}
                    type="button"
                    onClick={() => toggleChar(c.id)}
                    style={{
                      background: isSelected ? "#a855f7" : "#0b111e",
                      color: isSelected ? "#fff" : "#94a3b8",
                      border: `1px solid ${isSelected ? "#c084fc" : "#233149"}`,
                      padding: "8px 16px",
                      borderRadius: "10px",
                      fontWeight: 700,
                      fontSize: "13px",
                      cursor: "pointer"
                    }}
                  >
                    {isSelected ? "✓ " : "+ "} {c.name} ({c.role})
                  </button>
                );
              })}
            </div>
          </div>

          <div className="toggle-row">
            <input
              type="checkbox"
              id="autoRender"
              checked={autoRender}
              onChange={(e) => setAutoRender(e.target.checked)}
            />
            <label htmlFor="autoRender" style={{ margin: 0, cursor: "pointer" }}>
              🚀 <strong>Background Auto-Render</strong> (Start Blender 3D rendering immediately upon saving)
            </label>
          </div>

          <div style={{ display: "flex", gap: "10px", marginTop: "20px" }}>
            <button type="button" className="secondary" onClick={generateStoryOutline} disabled={busy} style={{ margin: 0 }}>
              ⚡ Preview Story Outline
            </button>
            <button type="submit" className="primary" disabled={busy} style={{ margin: 0, background: "#a855f7", color: "#fff" }}>
              {busy ? "Processing..." : "🎬 Create Story & Launch Pipeline →"}
            </button>
          </div>

          {message && <p style={{ color: "#f5c84c", fontWeight: 700, marginTop: "14px" }}>{message}</p>}
        </section>
      </form>

      {/* Generated Story Preview */}
      {previewStory && (
        <section className="panel" style={{ borderColor: "#a855f7" }}>
          <span style={{ fontSize: "12px", color: "#a855f7", fontWeight: 800, textTransform: "uppercase" }}>Generated Narrative Outline</span>
          <h2 style={{ margin: "6px 0" }}>{previewStory.viral_title}</h2>
          <p style={{ color: "#e2e8f0" }}><strong>Opening Hook:</strong> {previewStory.opening_hook}</p>
          <p style={{ color: "#cbd5e1" }}><strong>Summary:</strong> {previewStory.plot_summary}</p>
          <p style={{ color: "#38bdf8", fontStyle: "italic" }}><strong>Loop Opportunity:</strong> {previewStory.loop_opportunity}</p>

          <h3 style={{ marginTop: "20px", color: "#cbd5e1" }}>10 Scenes Breakdown</h3>
          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            {previewStory.scenes.map((s, idx) => (
              <div key={idx} style={{ background: "#0b111e", padding: "12px 16px", borderRadius: "10px", border: "1px solid #1e293b" }}>
                <div style={{ display: "flex", justifyContent: "space-between", color: "#f5c84c", fontSize: "12px", fontWeight: 700 }}>
                  <span>SCENE {s.scene_number} ({s.environment})</span>
                  <span>{s.duration}s</span>
                </div>
                <div style={{ color: "#f8fafc", marginTop: "4px" }}>"{s.narration}"</div>
              </div>
            ))}
          </div>
        </section>
      )}
    </main>
  );
}

export default function CreateStoryPage() {
  return (
    <Suspense fallback={<main><p>Loading Story Creator...</p></main>}>
      <CreateStoryContent />
    </Suspense>
  );
}
