import os, re, json, urllib.request

def make_script(topic: str, duration: int = 35) -> str:
    clean = topic.strip().rstrip(".!?")
    # Optional local LLM: no paid API key, but Ollama must be installed and running.
    model = os.getenv("OLLAMA_MODEL", "").strip()
    if model:
        base = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
        prompt = (
            f"Write a factual, engaging {duration}-second vertical video narration about: {clean}. "
            "Start with a strong 2-second hook. Use short spoken sentences, no headings, "
            "no fabricated facts, and end with a memorable payoff. Return narration only."
        )
        try:
            body = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode()
            req = urllib.request.Request(base + "/api/generate", data=body,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=180) as response:
                result = json.loads(response.read().decode())
            generated = result.get("response", "").strip()
            if generated:
                # Clean LLM stage directions, timestamps, and narrator tags
                cleaned_text = re.sub(r"\(.*?\)|\[.*?\]", "", generated)
                cleaned_text = re.sub(r"(?i)^(?:narrator|voiceover|host):\s*", "", cleaned_text, flags=re.MULTILINE)
                cleaned_text = re.sub(r"[\"\']", "", cleaned_text)
                cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()
                if cleaned_text:
                    return cleaned_text
                return generated
        except Exception as exc:
            print(f"Local Ollama unavailable; using built-in script template: {exc}")

    return (
        f"What if I told you this story: {clean}. "
        f"It sounds impossible, but the details are even stranger. "
        f"First, one small decision changed everything. "
        f"Then the situation became much bigger than anyone expected. "
        f"And here's the surprising part: the outcome was not what people predicted. "
        f"So remember this story the next time someone says it cannot be done."
    )

def split_scenes(script: str, count: int = 6):
    sentences = re.split(r"(?<=[.!?])\s+", script.strip())
    sentences = [s for s in sentences if s]
    if not sentences:
        return ["A story worth remembering."]
    return [sentences[min(i, len(sentences)-1)] for i in range(count)]
