# ShortForge AI — GeoGlobeTales-Style Geography Video Engine

A zero-paid-API production studio for faceless vertical Shorts, featuring a full **GeoGlobeTales-style 3D Geography & History Video Engine** powered by Blender, Natural Earth datasets, Kokoro neural voiceover, and faster-whisper word-level subtitle alignment.

Vercel hosts the Next.js dashboard; FastAPI powers the job management API, and a Python worker renders 1080x1920 MP4 videos locally on your Mac, GPU server, or Kaggle notebook.

## Key Capabilities

- **3D Geographical Animation Engine**: Blender-driven 3D rotating Earth with 4K satellite textures, terrain bump/mountain visualization, ocean specular reflections, accurate Natural Earth country borders, glowing country highlighting, 3D animated location pins, animated country flags, and strategic trade route corridors.
- **Automated Research & Scripting**: Generates factually verified research notes, citation sources, historical timelines, and an engaging 60–100 second narration script.
- **Scene-by-Scene Storyboard**: Divides scripts into 10–18 structured visual scenes with exact geographical coordinates, camera distances, pitch angles, movement styles, and text overlays.
- **Kokoro Neural TTS & Audio Mixing**: Generates natural English narration with customizable voices (`heart`, `adam`, `alice`, `george`, etc.), faster-whisper word-level subtitle alignment, ducked ambient drone music, and sound effects (whoosh on transitions, pin drop pops).
- **Automated Quality Control**: Validates coordinates, asset integrity, script lengths, audio/video duration synchronization (within 0.4s), safe margins, and 1080x1920 30fps dimensions.
- **Geography Studio Dashboard**: Next.js UI featuring topic presets, visual style selector, voice selector, duration selector, preview mode, real-time job inspector, embedded video player, and storyboard viewer.
- **Queue & Automation**: Persistent job queue, batch generation (`POST /api/jobs/batch`), retry failed jobs (`POST /api/jobs/{id}/retry`), cancellation, and continuous daemon worker polling.

## 1. Requirements

- macOS (Apple Silicon supported), Windows, or Linux
- Python 3.10–3.12
- Node.js 20+
- FFmpeg (`brew install ffmpeg`)
- Blender 4.x / 5.x (`brew install --cask blender`)

## 2. Quick Setup

```bash
# Setup Python virtualenv
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt
pip install -r worker/requirements.txt

# Configure environment
cp .env.example .env
```

## 3. Run Locally

### Terminal 1 — FastAPI Backend:
```bash
source .venv/bin/activate
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```
API docs: http://127.0.0.1:8000/docs

### Terminal 2 — Render Geography Video (CLI):
```bash
source .venv/bin/activate

# Render the benchmark video:
python -m worker.cli --topic "Why is Gibraltar British?" --style geo_realistic --duration 75 --voice heart

# Or run the worker in continuous background daemon mode:
python -m worker.cli --daemon
```

### Terminal 3 — Next.js Dashboard:
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:3000 to access the **Geography Studio**.

## 4. Geography Visual Styles

- `geo_realistic`: Photorealistic satellite Earth with elevation bumps and atmospheric rim lighting.
- `geo_political`: Glowing international borders and highlighted sovereign territories/enclaves.
- `geo_terrain`: Shaded relief terrain highlighting mountain ranges and elevation.
- `geo_historical`: Historical atlas style for treaty comparisons and border shifts.

## 5. End-to-End Test Suite

Run all automated unit and integration tests:
```bash
source .venv/bin/activate
pytest -q
```
Runs tests covering:
- Geographical coordinate validation & Natural Earth boundary extraction
- Factual research note generation & timeline extraction
- 10–18 scene storyboard generation & duration scaling
- Subtitle card safe-margin enforcement
- Batch job creation, cancellation, retry, and log inspection
- Pre-render and post-render Quality Control checks

## 6. Architecture & Licensing

- **Zero-Paid-API**: All voice synthesis, transcription, 3D rendering, and video assembly run locally without paid third-party APIs.
- **Datasets**: Built on public domain Natural Earth vector boundaries and NASA Blue Marble / Natural Earth raster textures.
- **Production Assembly**: Blender handles 3D perspective scenes; FFmpeg performs smooth camera motion, audio ducking, and MP4 H.264 export.
