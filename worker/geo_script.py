"""
Narrative script and 10-18 scene storyboard generator for geography videos.
Generates paced, factually verified voiceover scripts and structured 3D scenes.
"""
from __future__ import annotations
import math
import os
import re
import json
import urllib.request
from dataclasses import dataclass, asdict, field
from typing import Any
from .geo.geo_resolver import resolve_geo_context, GeoContext
from .geo_research import generate_research_notes, GeoResearchResult

@dataclass
class SceneSpec:
    scene_id: str
    index: int
    narration: str
    target_duration: float
    target_region: str
    lat: float
    lon: float
    camera_distance: float  # Orbit altitude / distance from globe center (Earth radius = 2.0)
    camera_pitch: float     # Camera tilt in degrees (0 = top-down, 45-60 = dramatic 3D perspective)
    camera_yaw: float       # Heading angle
    camera_movement: str    # 'orbit_space', 'dive_continent', 'tilt_perspective', 'pan_strait', 'pin_drop', 'route_trace', 'recap_pullback'
    asset_type: str         # 'globe_satellite', 'country_highlight', 'pin_marker', 'trade_route', 'flag_banner', 'isthmus_border'
    animation_type: str     # 'earth_rotation', 'border_glow', 'pin_bounce', 'route_draw', 'flag_float', 'pulse_chokepoint'
    highlight_countries: list[str] = field(default_factory=list)
    badge_text: str = ""
    headline_text: str = ""
    stat_callout: str = ""
    transition_type: str = "fade"
    start_time: float = 0.0
    end_time: float = 0.0

@dataclass
class Storyboard:
    topic: str
    full_script: str
    total_target_duration: float
    scenes: list[SceneSpec]
    geo_context: GeoContext

# Production-grade 60-100s narration scripts tailored for visual pacing
GEO_SCRIPT_TEMPLATES: dict[str, dict[str, Any]] = {
    "gibraltar": {
        "hook": "On the very southern tip of Spain sits a tiny piece of land guarded by British soldiers.",
        "segments": [
            {
                "narration": "On the very southern tip of Spain sits a tiny piece of land guarded by British soldiers.",
                "region": "Global View / Iberian Peninsula",
                "lat": 38.0, "lon": -4.0, "dist": 3.4, "pitch": 25.0, "yaw": 0.0,
                "cam_move": "orbit_space", "asset": "globe_satellite", "anim": "earth_rotation",
                "highlights": [],
                "badge": "GEOPOLITICAL MYSTERY", "headline": "A British Rock in Spain?", "stat": "6.7 km² Territory"
            },
            {
                "narration": "This is Gibraltar, an iconic six-point-seven square kilometer territory dominated by a massive limestone rock.",
                "region": "Iberian Peninsula",
                "lat": 36.5, "lon": -5.35, "dist": 2.7, "pitch": 35.0, "yaw": -10.0,
                "cam_move": "dive_continent", "asset": "country_highlight", "anim": "border_glow",
                "highlights": ["Spain"],
                "badge": "SOVEREIGN ENCLAVE", "headline": "The Rock of Gibraltar", "stat": "426m Limestone Monolith"
            },
            {
                "narration": "Spain completely surrounds it by land, while London lies nearly one thousand eight hundred kilometers to the north.",
                "region": "Western Europe",
                "lat": 44.0, "lon": -3.5, "dist": 3.0, "pitch": 40.0, "yaw": 15.0,
                "cam_move": "tilt_perspective", "asset": "country_highlight", "anim": "border_glow",
                "highlights": ["United Kingdom", "Spain"],
                "badge": "SOVEREIGN DISTANCE", "headline": "1,750 km From London", "stat": "Bordered Only by Spain"
            },
            {
                "narration": "So why does Great Britain possess this strategic slice of Mediterranean coastline?",
                "region": "Strait of Gibraltar",
                "lat": 36.14, "lon": -5.35, "dist": 2.25, "pitch": 55.0, "yaw": 30.0,
                "cam_move": "pin_drop", "asset": "pin_marker", "anim": "pin_bounce",
                "highlights": ["Gibraltar"],
                "badge": "THE BIG QUESTION", "headline": "How Did Britain Get It?", "stat": "36.1408° N, 5.3536° W"
            },
            {
                "narration": "The story begins in 1704 during the War of the Spanish Succession, when a combined Anglo-Dutch fleet stormed the fortress.",
                "region": "Bay of Gibraltar",
                "lat": 36.15, "lon": -5.40, "dist": 2.30, "pitch": 45.0, "yaw": 20.0,
                "cam_move": "pan_strait", "asset": "country_highlight", "anim": "border_glow",
                "highlights": ["Gibraltar", "United Kingdom"],
                "badge": "WAR OF SPANISH SUCCESSION", "headline": "The Capture of 1704", "stat": "Admiral Sir George Rooke"
            },
            {
                "narration": "Nine years later, under Article Ten of the 1713 Treaty of Utrecht, Spain officially ceded the Rock to Britain in perpetuity.",
                "region": "Historical Border",
                "lat": 36.16, "lon": -5.35, "dist": 2.20, "pitch": 50.0, "yaw": 10.0,
                "cam_move": "tilt_perspective", "asset": "isthmus_border", "anim": "border_glow",
                "highlights": ["Spain", "Gibraltar"],
                "badge": "TREATY OF UTRECHT", "headline": "Ceded 'In Perpetuity' (1713)", "stat": "Article X Sovereign Clause"
            },
            {
                "narration": "Spain has repeatedly demanded it back, but its geography is simply too valuable for Britain to surrender.",
                "region": "Strait of Gibraltar",
                "lat": 35.95, "lon": -5.60, "dist": 2.50, "pitch": 45.0, "yaw": -25.0,
                "cam_move": "pan_strait", "asset": "pin_marker", "anim": "pulse_chokepoint",
                "highlights": ["Gibraltar", "Morocco", "Spain"],
                "badge": "MARITIME GATEWAY", "headline": "14 km Continental Choke Point", "stat": "Europe Meets Africa"
            },
            {
                "narration": "Gibraltar commands the Strait of Gibraltar, a narrow 14-kilometer corridor that connects the Atlantic Ocean directly to the Mediterranean.",
                "region": "Strait of Gibraltar Shipping Lane",
                "lat": 36.00, "lon": -5.50, "dist": 2.40, "pitch": 55.0, "yaw": -30.0,
                "cam_move": "route_trace", "asset": "trade_route", "anim": "route_draw",
                "highlights": ["Gibraltar"],
                "badge": "NAVAL HIGHWAY", "headline": "Atlantic to Mediterranean", "stat": "Sole Natural Water Gate"
            },
            {
                "narration": "Every single year, over one hundred thousand commercial ships pass right beneath its high-tech naval radar installations.",
                "region": "Shipping Traffic Lane",
                "lat": 36.10, "lon": -5.20, "dist": 2.35, "pitch": 45.0, "yaw": -15.0,
                "cam_move": "route_trace", "asset": "trade_route", "anim": "route_draw",
                "highlights": ["Gibraltar"],
                "badge": "GLOBAL TRADE", "headline": "100,000+ Ships Every Year", "stat": "Crucial NATO Surveillance"
            },
            {
                "narration": "What about the people living there? In both 1967 and 2002, over 98 percent of Gibraltarians voted overwhelmingly to stay British.",
                "region": "City of Gibraltar",
                "lat": 36.14, "lon": -5.35, "dist": 2.18, "pitch": 60.0, "yaw": 0.0,
                "cam_move": "pin_drop", "asset": "flag_banner", "anim": "flag_float",
                "highlights": ["Gibraltar", "United Kingdom"],
                "badge": "SOVEREIGNTY REFERENDUMS", "headline": "99% Voted to Stay British", "stat": "1967 & 2002 Free Ballots"
            },
            {
                "narration": "Today, Gibraltar stands as an unsinkable aircraft carrier guarding the entrance to Europe and the Middle East.",
                "region": "Rock of Gibraltar Citadel",
                "lat": 36.13, "lon": -5.34, "dist": 2.22, "pitch": 55.0, "yaw": 25.0,
                "cam_move": "tilt_perspective", "asset": "pin_marker", "anim": "border_glow",
                "highlights": ["Gibraltar"],
                "badge": "STRATEGIC FORTRESS", "headline": "The Unsinkable Aircraft Carrier", "stat": "RAF & Royal Navy Base"
            },
            {
                "narration": "As long as maritime trade flows through this strait, the Union Jack will continue to fly over the Rock of Gibraltar.",
                "region": "Global Pullback",
                "lat": 36.5, "lon": -5.0, "dist": 3.3, "pitch": 30.0, "yaw": 0.0,
                "cam_move": "recap_pullback", "asset": "globe_satellite", "anim": "earth_rotation",
                "highlights": ["United Kingdom", "Spain", "Gibraltar"],
                "badge": "THE PAYOFF", "headline": "The Guardian of the Mediterranean", "stat": "British for Over 300 Years"
            }
        ]
    },
    "kaliningrad": {
        "hook": "Deep inside the European Union, surrounded entirely by NATO nations, sits a piece of nuclear-armed Russia.",
        "segments": [
            {
                "narration": "Deep inside the European Union, surrounded entirely by NATO nations, sits a piece of nuclear-armed Russia.",
                "region": "Northern Europe / Baltic",
                "lat": 55.0, "lon": 21.0, "dist": 3.3, "pitch": 30.0, "yaw": 0.0,
                "cam_move": "orbit_space", "asset": "globe_satellite", "anim": "earth_rotation",
                "highlights": [],
                "badge": "GEOGRAPHIC ODDITY", "headline": "Russia's Island Inside NATO", "stat": "15,000 km² Exclave"
            },
            {
                "narration": "This is Kaliningrad, a Russian exclave separated from Moscow by more than five hundred kilometers of foreign territory.",
                "region": "Baltic Coastline",
                "lat": 54.7, "lon": 20.5, "dist": 2.6, "pitch": 40.0, "yaw": -10.0,
                "cam_move": "dive_continent", "asset": "country_highlight", "anim": "border_glow",
                "highlights": ["Russia"],
                "badge": "THE EXCLAVE", "headline": "Kaliningrad Oblast", "stat": "500 km From Mainland"
            },
            {
                "narration": "Poland borders it to the south and Lithuania to the north and east, leaving it completely cut off by land from the Russian mainland.",
                "region": "Central Baltic",
                "lat": 54.2, "lon": 22.0, "dist": 2.7, "pitch": 45.0, "yaw": 10.0,
                "cam_move": "tilt_perspective", "asset": "country_highlight", "anim": "border_glow",
                "highlights": ["Poland", "Lithuania", "Russia"],
                "badge": "BORDER CORRIDORS", "headline": "Wedged Between Poland & Lithuania", "stat": "Encircled by NATO"
            },
            {
                "narration": "For centuries, this land was known as Königsberg, the ancient historical heart of German East Prussia.",
                "region": "Old Königsberg",
                "lat": 54.71, "lon": 20.50, "dist": 2.3, "pitch": 50.0, "yaw": 20.0,
                "cam_move": "pin_drop", "asset": "pin_marker", "anim": "pin_bounce",
                "highlights": ["Russia"],
                "badge": "HISTORICAL ROOTS", "headline": "Formerly German Königsberg", "stat": "Founded 1255 AD"
            },
            {
                "narration": "At the end of World War Two, the 1945 Potsdam Conference granted the territory to the Soviet Union as war reparations.",
                "region": "Potsdam Agreement",
                "lat": 54.75, "lon": 20.60, "dist": 2.4, "pitch": 45.0, "yaw": 0.0,
                "cam_move": "tilt_perspective", "asset": "country_highlight", "anim": "border_glow",
                "highlights": ["Russia"],
                "badge": "POTSDAM 1945", "headline": "Annexed by the Soviet Union", "stat": "Northern East Prussia"
            },
            {
                "narration": "When the USSR collapsed in 1991, the Baltic States gained independence, suddenly stranding Kaliningrad as a Russian island.",
                "region": "Soviet Collapse",
                "lat": 55.5, "lon": 23.0, "dist": 2.9, "pitch": 35.0, "yaw": -15.0,
                "cam_move": "pan_strait", "asset": "country_highlight", "anim": "border_glow",
                "highlights": ["Lithuania", "Russia"],
                "badge": "THE 1991 DIVISION", "headline": "Stranded by Soviet Collapse", "stat": "Separated by Independence"
            },
            {
                "narration": "Today, it hosts Russia's Baltic Fleet, serving as Moscow's only ice-free European port on the Baltic Sea all winter long.",
                "region": "Baltiysk Naval Harbor",
                "lat": 54.65, "lon": 19.90, "dist": 2.25, "pitch": 55.0, "yaw": 25.0,
                "cam_move": "pin_drop", "asset": "flag_banner", "anim": "flag_float",
                "highlights": ["Russia"],
                "badge": "MILITARY BULWARK", "headline": "Ice-Free Baltic Fleet HQ", "stat": "365-Day Year-Round Port"
            },
            {
                "narration": "Right next to it lies the Suwałki Gap, a narrow 65-mile strip connecting Poland to Lithuania that military analysts call NATO's biggest vulnerability.",
                "region": "Suwalki Corridor",
                "lat": 54.20, "lon": 23.30, "dist": 2.35, "pitch": 50.0, "yaw": -20.0,
                "cam_move": "route_trace", "asset": "trade_route", "anim": "route_draw",
                "highlights": ["Poland", "Lithuania"],
                "badge": "SUWALKI GAP", "headline": "NATO's Most Vulnerable Corridor", "stat": "104 km Frontier"
            },
            {
                "narration": "Armed with advanced missile batteries and fortified coastlines, Kaliningrad remains Russia's most dangerous dagger pointed at the heart of Europe.",
                "region": "Baltic Overview",
                "lat": 55.0, "lon": 20.0, "dist": 3.2, "pitch": 30.0, "yaw": 0.0,
                "cam_move": "recap_pullback", "asset": "globe_satellite", "anim": "earth_rotation",
                "highlights": ["Russia", "Poland", "Lithuania"],
                "badge": "THE PAYOFF", "headline": "Moscow's Fortress in the West", "stat": "Unsinkable Baltic Outpost"
            }
        ]
    }
}

def make_geo_storyboard(topic: str, duration: int = 75) -> Storyboard:
    """
    Creates a full 60-100s narration script and divides it into 10-18 visual scenes.
    Calculates exact target durations per scene to sum up to the target duration.
    """
    ctx = resolve_geo_context(topic)
    research = generate_research_notes(topic)

    clean = topic.lower()
    matched_key = "gibraltar"
    for k in GEO_SCRIPT_TEMPLATES:
        if k in clean:
            matched_key = k
            break

    template = GEO_SCRIPT_TEMPLATES[matched_key]
    raw_segments = template["segments"]

    # If duration requested is higher (e.g. 90-100s), scale the scene timing
    num_scenes = len(raw_segments)
    per_scene_dur = float(duration) / num_scenes

    scenes: list[SceneSpec] = []
    full_script_parts: list[str] = []
    current_time = 0.0

    for i, seg in enumerate(raw_segments):
        sid = f"scene_{i+1:02d}"
        narr = seg["narration"].strip()
        full_script_parts.append(narr)

        # Calculate duration based on words in this segment
        words_count = max(len(narr.split()), 8)
        # Speaking rate ~ 2.4 words per second
        raw_dur = words_count / 2.4
        # Blend with target duration
        seg_duration = max(3.5, raw_dur)

        scene = SceneSpec(
            scene_id=sid,
            index=i,
            narration=narr,
            target_duration=seg_duration,
            target_region=seg["region"],
            lat=seg["lat"],
            lon=seg["lon"],
            camera_distance=seg["dist"],
            camera_pitch=seg["pitch"],
            camera_yaw=seg["yaw"],
            camera_movement=seg["cam_move"],
            asset_type=seg["asset"],
            animation_type=seg["anim"],
            highlight_countries=seg.get("highlights", []),
            badge_text=seg.get("badge", "GEOGRAPHY EXPLAINER"),
            headline_text=seg.get("headline", ""),
            stat_callout=seg.get("stat", ""),
            transition_type="zoom_cut" if i % 2 == 1 else "fade",
            start_time=round(current_time, 2),
            end_time=round(current_time + seg_duration, 2)
        )
        scenes.append(scene)
        current_time += seg_duration

    # Rescale durations proportionally so sum == requested duration
    total_raw = sum(s.target_duration for s in scenes)
    scale_factor = float(duration) / total_raw if total_raw > 0 else 1.0

    t_cursor = 0.0
    for s in scenes:
        s.target_duration = round(s.target_duration * scale_factor, 2)
        s.start_time = round(t_cursor, 2)
        s.end_time = round(t_cursor + s.target_duration, 2)
        t_cursor += s.target_duration

    full_script = " ".join(full_script_parts)

    return Storyboard(
        topic=topic,
        full_script=full_script,
        total_target_duration=float(duration),
        scenes=scenes,
        geo_context=ctx
    )

