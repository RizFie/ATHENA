import json
import urllib.request

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen3:8b-q4_K_M"

payload = {
    "model": MODEL,
    "messages": [
        {"role": "user", "content": "You are Athena, a research assistant. Introduce yourself in one sentence."}
    ],
    "think": False,
    "stream": False
}

print(json.dumps(payload, indent=2))