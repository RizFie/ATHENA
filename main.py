import json
import urllib.request

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen3:8b-q4_K_M"

def ask_athena(query):
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are Athena, a helpful research assistant. Answer the user's questions clearly and accurately."},
            {"role": "user", "content": query},
        ],
        "think": False,
        "stream": False
    }

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        OLLAMA_URL,
        data = data,
        headers = {"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(request, timeout=120) as response:
        result = json.loads(response.read().decode("utf-8"))

    return result["message"]["content"]

if __name__ == "__main__":
    query = input("> ")
    answer = ask_athena(query)
    print(answer)