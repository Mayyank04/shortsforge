import os, subprocess, tempfile
from pathlib import Path

def generate_voice(text: str, output: Path):
    engine = os.getenv("TTS_ENGINE", "system").lower()
    output.parent.mkdir(parents=True, exist_ok=True)
    if engine == "kokoro":
        try:
            import soundfile as sf
            from kokoro import KPipeline
            import numpy as np
            pipeline = KPipeline(lang_code="a")
            chunks = []
            for _, _, audio in pipeline(text, voice="af_heart"):
                chunks.append(np.asarray(audio))
            if not chunks:
                raise RuntimeError("Kokoro returned no audio")
            sf.write(str(output), np.concatenate(chunks), 24000)
            return
        except Exception as exc:
            raise RuntimeError(f"Kokoro TTS failed. Check its model setup and dependencies: {exc}") from exc

    # macOS system voice; Linux can use espeak-ng. Windows users can install eSpeak NG.
    system = os.uname().sysname if hasattr(os, "uname") else "Windows"
    if system == "Darwin":
        aiff = output.with_suffix(".aiff")
        subprocess.run(["say", "-o", str(aiff), text], check=True)
        subprocess.run(["ffmpeg", "-y", "-i", str(aiff), "-ar", "24000", str(output)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        aiff.unlink(missing_ok=True)
    else:
        cmd = ["espeak-ng", "-w", str(output), text]
        subprocess.run(cmd, check=True)
