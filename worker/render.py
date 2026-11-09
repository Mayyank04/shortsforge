import os, subprocess, tempfile, json
from pathlib import Path
from .script import make_script, split_scenes
from .voice import generate_voice
from .visuals import make_scene

def run(cmd):
    subprocess.run(cmd, check=True)

def render(
    topic: str,
    style: str = "mixed",
    duration: int = 35,
    output_dir: str = "outputs",
    voice: str = "heart",
    preview: bool = False
):
    # Route Minecraft styles or topics directly to the Minecraft Story Studio engine
    is_minecraft = (
        style.startswith("minecraft") or
        any(k in topic.lower() for k in ["minecraft", "villager", "one heart", "creeper", "iron golem", "nether", "steve"])
    )
    if is_minecraft:
        from .minecraft.pipeline import render_minecraft_video
        genre = style.replace("minecraft_", "") if style.startswith("minecraft_") else "adventure"
        if genre == "minecraft":
            genre = "adventure"
        return render_minecraft_video(
            topic=topic,
            genre=genre,
            duration=duration,
            voice=voice,
            preview=preview,
            output_dir=output_dir
        )

    # Route geography styles or geography topics directly to the GeoGlobeTales engine
    is_geo_topic = (
        style.startswith("geo") or
        any(k in topic.lower() for k in ["gibraltar", "kaliningrad", "suez", "ireland", "himalayas", "climate", "geography"])
    )

    if is_geo_topic:
        from .geo_pipeline import render_geo_video
        return render_geo_video(
            topic=topic,
            duration=duration,
            voice=voice,
            style=style if style.startswith("geo") else "geo_realistic",
            preview=preview,
            output_dir=output_dir
        )

    out = Path(output_dir); out.mkdir(parents=True, exist_ok=True)
    slug = "".join(c.lower() if c.isalnum() else "-" for c in topic)[:45].strip("-") or "short"
    final = out / f"{slug}.mp4"
    script = make_script(topic, duration)
    scenes = split_scenes(script, 6)
    with tempfile.TemporaryDirectory(prefix="shortforge-") as td:
        temp = Path(td)
        audio = temp / "voice.wav"
        generate_voice(script, audio)
        # Determine actual audio length and divide scenes evenly.
        probe = subprocess.check_output([
            "ffprobe","-v","error","-show_entries","format=duration",
            "-of","default=noprint_wrappers=1:nokey=1",str(audio)], text=True).strip()
        total = max(float(probe), 8.0)
        per_scene = total / len(scenes)
        inputs = []
        for i, line in enumerate(scenes):
            img = temp / f"scene_{i:02d}.png"
            make_scene(line, i, style, img)
            clip = temp / f"clip_{i:02d}.mp4"
            # Gentle zoom creates motion without external video assets.
            run(["ffmpeg","-y","-loop","1","-i",str(img),"-t",str(per_scene),
                 "-vf", "scale=1188:2112,zoompan=z='min(zoom+0.0008,1.08)':d=1:s=1080x1920:fps=30,format=yuv420p",
                 "-r","30","-an","-c:v","libx264","-preset","veryfast",str(clip)])
            inputs.append(clip)
        concat = temp / "concat.txt"
        concat.write_text("".join(f"file '{p.as_posix()}'\n" for p in inputs))
        silent = temp / "silent.mp4"
        run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(concat),"-c","copy",str(silent)])
        run(["ffmpeg","-y","-i",str(silent),"-i",str(audio),"-shortest",
             "-c:v","copy","-c:a","aac","-b:a","192k","-movflags","+faststart",str(final)])
    metadata = {"topic": topic, "style": style, "duration": duration, "script": script, "video": str(final)}
    final.with_suffix(".json").write_text(json.dumps(metadata, indent=2))
    return final, script
