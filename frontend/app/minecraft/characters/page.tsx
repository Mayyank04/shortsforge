"use client";
import { useEffect, useState } from "react";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

type Character = {
  id: string;
  name: string;
  role: string;
  species: string;
  skin_tone: string;
  clothing_primary: string;
  clothing_secondary: string;
  hair_style: string;
  hair_color: string;
  personality?: string;
  voice_preference: string;
  reference_image_path?: string;
};

export default function CharacterLibrary() {
  const [characters, setCharacters] = useState<Character[]>([]);
  const [showModal, setShowModal] = useState(false);
  const [name, setName] = useState("");
  const [role, setRole] = useState("protagonist");
  const [species, setSpecies] = useState("human");
  const [skinTone, setSkinTone] = useState("#c68653");
  const [clothingPrimary, setClothingPrimary] = useState("#2563eb");
  const [clothingSecondary, setClothingSecondary] = useState("#1e293b");
  const [hairColor, setHairColor] = useState("#3e2723");
  const [personality, setPersonality] = useState("");
  const [voice, setVoice] = useState("heart");
  const [message, setMessage] = useState("");

  async function loadCharacters() {
    try {
      const res = await fetch(`${API}/api/minecraft/characters`);
      if (res.ok) {
        setCharacters(await res.json());
      }
    } catch {}
  }

  useEffect(() => {
    loadCharacters();
  }, []);

  async function handleCreateCharacter(e: React.FormEvent) {
    e.preventDefault();
    setMessage("");
    try {
      const res = await fetch(`${API}/api/minecraft/characters`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name,
          role,
          species,
          skin_tone: skinTone,
          clothing_primary: clothingPrimary,
          clothing_secondary: clothingSecondary,
          hair_style: "short",
          hair_color: hairColor,
          personality,
          voice_preference: voice
        })
      });
      if (!res.ok) throw new Error("Failed to create character");
      setShowModal(false);
      setName("");
      setPersonality("");
      loadCharacters();
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Error creating character");
    }
  }

  async function deleteCharacter(id: string) {
    if (!confirm("Delete this character profile?")) return;
    try {
      await fetch(`${API}/api/minecraft/characters/${id}`, { method: "DELETE" });
      loadCharacters();
    } catch {}
  }

  return (
    <main>
      <div className="eyebrow">
        <span>CANONICAL VOXEL ASSETS · CHARACTER CONSISTENCY</span>
        <Link href="/minecraft" style={{ color: "#38bdf8", fontWeight: 700 }}>
          ← Back to Studio
        </Link>
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <h1>
            Character <span style={{ color: "#a855f7" }}>Library.</span>
          </h1>
          <p>
            Persistent 3D voxel character specifications. Guarantees 100% visual and geometric consistency across all 10 scenes in every story.
          </p>
        </div>
        <button className="primary" onClick={() => setShowModal(true)} style={{ background: "#a855f7", color: "#fff" }}>
          + New Canonical Character
        </button>
      </div>

      {message && <p style={{ color: "#f5c84c", fontWeight: 700 }}>{message}</p>}

      {/* Characters Grid */}
      <div className="char-grid">
        {characters.map((c) => {
          const refImgName = c.reference_image_path ? c.reference_image_path.split("/").pop() : `${c.id}_reference.png`;
          const imgSrc = `${API}/assets/characters/${refImgName}`;

          return (
            <div key={c.id} className="char-card">
              <div style={{ height: "200px", background: "#060913", display: "flex", alignItems: "center", justifyContent: "center", borderBottom: "1px solid #1e293b", position: "relative" }}>
                <img
                  src={imgSrc}
                  alt={c.name}
                  style={{ maxHeight: "190px", maxWidth: "100%", objectFit: "contain" }}
                  onError={(e) => {
                    // Fallback to SVG placeholder if file not yet on disk
                    (e.target as HTMLElement).style.display = "none";
                  }}
                />
                <span style={{ position: "absolute", bottom: "8px", left: "10px", fontSize: "10px", color: "#64748b", fontFamily: "monospace" }}>
                  #{c.id}
                </span>
              </div>

              <div className="char-body">
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div className="char-name">{c.name}</div>
                  <span className="char-role">{c.role}</span>
                </div>

                <div style={{ fontSize: "12px", color: "#38bdf8" }}>
                  Species: <strong>{c.species.toUpperCase()}</strong> · Voice: <strong>{c.voice_preference}</strong>
                </div>

                <p className="char-desc" style={{ minHeight: "45px" }}>
                  {c.personality || "Courageous adventurer ready for the blocky realm."}
                </p>

                <div style={{ display: "flex", alignItems: "center", gap: "8px", marginTop: "auto" }}>
                  <span style={{ fontSize: "11px", color: "#64748b" }}>Palette:</span>
                  <div className="char-swatches">
                    <div className="char-swatch" style={{ background: c.skin_tone }} title="Skin" />
                    <div className="char-swatch" style={{ background: c.clothing_primary }} title="Primary Clothing" />
                    <div className="char-swatch" style={{ background: c.clothing_secondary }} title="Secondary Clothing" />
                    <div className="char-swatch" style={{ background: c.hair_color }} title="Hair" />
                  </div>
                </div>

                <div style={{ display: "flex", gap: "6px", marginTop: "12px" }}>
                  <Link href={`/minecraft/create?character=${c.id}`} className="action-btn" style={{ flex: 1, textAlign: "center" }}>
                    + Add to Story
                  </Link>
                  {!["mini", "steve", "iron_golem", "shadow"].includes(c.id) && (
                    <button className="action-btn danger" onClick={() => deleteCharacter(c.id)}>
                      ✕
                    </button>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Create Modal */}
      {showModal && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.75)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 100, padding: "20px" }}>
          <div className="panel" style={{ maxWidth: "540px", width: "100%", maxHeight: "90vh", overflowY: "auto", margin: 0 }}>
            <h2 style={{ marginTop: 0 }}>Create New Canonical Character</h2>
            <form onSubmit={handleCreateCharacter}>
              <label htmlFor="cname">Character Name</label>
              <input id="cname" value={name} onChange={(e) => setName(e.target.value)} required placeholder="e.g. Luna" />

              <div className="form-grid">
                <div>
                  <label htmlFor="crole">Role</label>
                  <select id="crole" value={role} onChange={(e) => setRole(e.target.value)}>
                    <option value="protagonist">Protagonist (Hero)</option>
                    <option value="companion">Companion (Sidekick)</option>
                    <option value="mentor">Mentor (Guide)</option>
                    <option value="antagonist">Antagonist (Rival/Threat)</option>
                    <option value="guardian">Guardian (Protector)</option>
                  </select>
                </div>
                <div>
                  <label htmlFor="cspecies">Species / Body Type</label>
                  <select id="cspecies" value={species} onChange={(e) => setSpecies(e.target.value)}>
                    <option value="villager">Villager (Distinctive Nose)</option>
                    <option value="human">Human Adventurer</option>
                    <option value="golem">Iron Golem (Heavy Heavyweight)</option>
                    <option value="shadow">Shadow (Dark Silhouette)</option>
                  </select>
                </div>
              </div>

              <div className="form-grid">
                <div>
                  <label htmlFor="cskin">Skin Tone</label>
                  <input id="cskin" type="color" value={skinTone} onChange={(e) => setSkinTone(e.target.value)} style={{ height: "46px", padding: "4px" }} />
                </div>
                <div>
                  <label htmlFor="cprimary">Primary Outfit Color</label>
                  <input id="cprimary" type="color" value={clothingPrimary} onChange={(e) => setClothingPrimary(e.target.value)} style={{ height: "46px", padding: "4px" }} />
                </div>
                <div>
                  <label htmlFor="csecondary">Secondary Outfit Color</label>
                  <input id="csecondary" type="color" value={clothingSecondary} onChange={(e) => setClothingSecondary(e.target.value)} style={{ height: "46px", padding: "4px" }} />
                </div>
                <div>
                  <label htmlFor="chair">Hair Color</label>
                  <input id="chair" type="color" value={hairColor} onChange={(e) => setHairColor(e.target.value)} style={{ height: "46px", padding: "4px" }} />
                </div>
              </div>

              <label htmlFor="cpers">Personality & Backstory</label>
              <textarea id="cpers" rows={3} value={personality} onChange={(e) => setPersonality(e.target.value)} placeholder="Courageous explorer with a heart of gold..." />

              <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "20px" }}>
                <button type="button" className="secondary" onClick={() => setShowModal(false)} style={{ margin: 0 }}>
                  Cancel
                </button>
                <button type="submit" className="primary" style={{ margin: 0, background: "#a855f7", color: "#fff" }}>
                  Save Character Profile
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </main>
  );
}
