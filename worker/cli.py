import argparse, os, sys, time
from pathlib import Path
import requests
from dotenv import load_dotenv
load_dotenv()
from .render import render

def main():
    p = argparse.ArgumentParser(description="Render a ShortForge vertical short")
    p.add_argument("--topic", required=False, help="Video topic to render directly")
    p.add_argument(
        "--style",
        choices=["mixed", "2d", "3d", "geo_realistic", "geo_political", "geo_terrain", "geo_historical"],
        default="geo_realistic"
    )
    p.add_argument("--duration", type=int, default=75)
    p.add_argument("--voice", default="heart", help="Kokoro voice (heart, adam, alice, george, etc.)")
    p.add_argument("--preview", action="store_true", help="Render fast preview at 540x960")
    p.add_argument("--daemon", action="store_true", help="Run background worker continuously polling the API")
    p.add_argument("--poll-interval", type=int, default=3, help="Seconds between queue polling in daemon mode")
    p.add_argument("--output-dir", default=os.getenv("OUTPUT_DIR", "outputs"))
    p.add_argument("--api-url", default=os.getenv("SHORTFORGE_API_URL", "http://127.0.0.1:8000"))
    p.add_argument("--job-id", help="Render a queued job already created in the dashboard")
    args = p.parse_args()

    base = (args.api_url or "http://127.0.0.1:8000").rstrip("/")

    if args.daemon:
        print(f"Starting ShortForge Worker Daemon polling {base} every {args.poll_interval}s...")
        while True:
            try:
                r = requests.get(f"{base}/api/jobs", timeout=10)
                if r.ok:
                    jobs = r.json()
                    queued_jobs = [j for j in jobs if j.get("status") == "queued"]
                    if queued_jobs:
                        job = queued_jobs[0]
                        job_id = job["id"]
                        print(f"Found queued job: {job_id} ({job.get('topic')})")
                        process_single_job(job_id, base, args.output_dir)
            except Exception as e:
                print(f"Daemon polling error: {e}")
            time.sleep(args.poll_interval)
        return

    if not args.job_id and not args.topic:
        p.error("Either --topic, --job-id, or --daemon must be provided")

    if args.job_id:
        process_single_job(args.job_id, base, args.output_dir, preview=args.preview)
    else:
        path, meta = render(
            topic=args.topic,
            style=args.style,
            duration=args.duration,
            output_dir=args.output_dir,
            voice=args.voice,
            preview=args.preview
        )
        print(f"Rendered: {path}")

        if args.api_url:
            try:
                r = requests.post(
                    f"{base}/api/jobs",
                    json={"topic": args.topic, "style": args.style, "duration": args.duration, "voice": args.voice},
                    timeout=10
                )
                if r.ok:
                    new_id = r.json()["id"]
                    requests.post(
                        f"{base}/api/jobs/{new_id}/status",
                        json={"status": "completed", "output_path": str(Path(path).resolve())},
                        timeout=10
                    )
                    print("Registered and completed API job:", new_id)
            except requests.RequestException as exc:
                print("Could not register API job (video was still rendered):", exc)

def process_single_job(job_id: str, base_api_url: str, output_dir: str, preview: bool = False):
    try:
        response = requests.get(f"{base_api_url}/api/jobs/{job_id}", timeout=10)
        response.raise_for_status()
        job = response.json()
    except Exception as exc:
        print(f"Failed to fetch job {job_id} from {base_api_url}: {exc}", file=sys.stderr)
        sys.exit(1)

    topic = job["topic"]
    style = job.get("style", "geo_realistic")
    duration = int(job.get("duration", 75))
    voice = job.get("voice", "heart")
    job_preview = job.get("preview", preview)

    try:
        requests.post(
            f"{base_api_url}/api/jobs/{job_id}/status",
            json={"status": "running"},
            timeout=10
        ).raise_for_status()
    except Exception as exc:
        print(f"Warning: Failed to update job status to 'running': {exc}", file=sys.stderr)

    try:
        path, meta = render(
            topic=topic,
            style=style,
            duration=duration,
            output_dir=output_dir,
            voice=voice,
            preview=job_preview
        )
        print(f"Rendered: {path}")

        requests.post(
            f"{base_api_url}/api/jobs/{job_id}/status",
            json={"status": "completed", "output_path": str(Path(path).resolve()), "error": None},
            timeout=10
        ).raise_for_status()
        print(f"Job {job_id} status updated to 'completed'")
    except Exception as exc:
        error_msg = f"{type(exc).__name__}: {str(exc)}"
        print(f"Render failed: {error_msg}", file=sys.stderr)
        try:
            requests.post(
                f"{base_api_url}/api/jobs/{job_id}/status",
                json={"status": "failed", "error": error_msg},
                timeout=10
            )
            print(f"Job {job_id} status updated to 'failed' with error: {error_msg}")
        except Exception as status_err:
            print(f"Failed to report failure to API: {status_err}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
