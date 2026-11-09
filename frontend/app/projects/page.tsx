"use client";
import { useEffect, useState } from "react";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

type ProjectItem = {
  id: string;
  type: string;
  title: string;
  status: string;
  duration: number;
  voice: string;
  output_path?: string;
  created_at: string;
};

export default function ProjectLibrary() {
  const [items, setItems] = useState<ProjectItem[]>([]);
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");
  const [sortBy, setSortBy] = useState<"date" | "duration">("date");

  async function loadData() {
    try {
      const res = await fetch(`${API}/api/renders`);
      if (res.ok) {
        setItems(await res.json());
      }
    } catch {}
  }

  useEffect(() => {
    loadData();
  }, []);

  async function duplicateProject(item: ProjectItem) {
    if (item.type === "minecraft") {
      try {
        await fetch(`${API}/api/minecraft/projects/${item.id}/duplicate`, { method: "POST" });
        loadData();
      } catch {}
    }
  }

  const filtered = items.filter((p) => {
    const matchesSearch = p.title.toLowerCase().includes(search.toLowerCase());
    const matchesType = typeFilter === "all" || p.type === typeFilter;
    return matchesSearch && matchesType;
  }).sort((a, b) => {
    if (sortBy === "duration") return b.duration - a.duration;
    return (b.created_at || "").localeCompare(a.created_at || "");
  });

  return (
    <main>
      <div className="eyebrow">
        <span>PROJECT ARCHIVE & LIBRARY</span>
        <span className="muted">{items.length} Total Projects</span>
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <h1>
            Project <span style={{ color: "#38bdf8" }}>Library.</span>
          </h1>
          <p>
            Explore, reopen, duplicate, and export all generated Minecraft and Geography video productions.
          </p>
        </div>
        <div style={{ display: "flex", gap: "8px" }}>
          <Link href="/minecraft/create" className="primary" style={{ background: "#a855f7", color: "#fff", padding: "10px 18px", fontSize: "14px" }}>
            + New Minecraft Story
          </Link>
          <Link href="/" className="primary" style={{ background: "#38bdf8", color: "#090d18", padding: "10px 18px", fontSize: "14px" }}>
            + New Geography Video
          </Link>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <section className="panel" style={{ padding: "18px 22px" }}>
        <div style={{ display: "flex", gap: "14px", flexWrap: "wrap", alignItems: "center" }}>
          <div style={{ flex: 1, minWidth: "220px" }}>
            <input
              placeholder="Search projects by title or keywords..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <div style={{ display: "flex", gap: "6px" }}>
            {["all", "minecraft", "geography"].map((t) => (
              <button
                key={t}
                type="button"
                className={`action-btn ${typeFilter === t ? "primary" : ""}`}
                style={{
                  textTransform: "capitalize",
                  background: typeFilter === t ? "#38bdf8" : "#0e1526",
                  color: typeFilter === t ? "#090d18" : "#cbd5e1"
                }}
                onClick={() => setTypeFilter(t)}
              >
                {t}
              </button>
            ))}
          </div>

          <div>
            <select value={sortBy} onChange={(e) => setSortBy(e.target.value as "date" | "duration")} style={{ padding: "10px 14px", width: "auto" }}>
              <option value="date">Sort by Date</option>
              <option value="duration">Sort by Duration</option>
            </select>
          </div>
        </div>
      </section>

      {/* Project Cards Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: "16px", marginTop: "20px" }}>
        {filtered.length === 0 ? (
          <p className="muted" style={{ gridColumn: "1 / -1", textAlign: "center", padding: "40px 0" }}>
            No projects found matching current search criteria.
          </p>
        ) : (
          filtered.map((p) => {
            const videoFilename = p.output_path ? p.output_path.split("/").pop() : "";

            return (
              <div key={p.id} className="panel" style={{ margin: 0, display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "8px" }}>
                    <span className="m-badge" style={{ color: p.type === "minecraft" ? "#a855f7" : "#38bdf8", fontWeight: 700 }}>
                      {p.type.toUpperCase()}
                    </span>
                    <span className={`status-badge status-${p.status}`}>{p.status}</span>
                  </div>

                  <h3 style={{ margin: "4px 0 8px 0", fontSize: "17px", color: "#f8fafc" }}>{p.title}</h3>
                  <div className="muted" style={{ fontSize: "12px" }}>
                    Duration: {p.duration}s · Voice: {p.voice}
                  </div>
                </div>

                <div style={{ display: "flex", gap: "6px", marginTop: "16px", flexWrap: "wrap" }}>
                  {p.type === "minecraft" ? (
                    <Link href={`/minecraft/storyboard/${p.id}`} className="action-btn" style={{ flex: 1, textAlign: "center" }}>
                      Open Storyboard
                    </Link>
                  ) : (
                    <Link href={`/?jobId=${p.id}`} className="action-btn" style={{ flex: 1, textAlign: "center" }}>
                      Open Studio
                    </Link>
                  )}

                  {p.type === "minecraft" && (
                    <button className="action-btn" onClick={() => duplicateProject(p)} title="Duplicate">
                      📋 Duplicate
                    </button>
                  )}

                  {p.status === "completed" && videoFilename && (
                    <a href={`${API}/outputs/${videoFilename}`} download className="action-btn" style={{ color: "#2ed573", borderColor: "rgba(46,213,115,0.4)" }}>
                      ⬇️ MP4
                    </a>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </main>
  );
}
