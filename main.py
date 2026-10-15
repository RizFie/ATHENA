import json
import urllib.request

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen3:8b-q4_K_M"

conversations = [{"role": "system", "content": "You are Athena, a helpful research assistant. Answer the user's questions clearly and accurately."},]

def ask_athena(conversation):
    payload = {
        "model": MODEL,
        "messages": conversation,
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
    while True:
        query = input("> ")
        
        if query.strip().lower() == "/bye":
            print("Goodbye!")
            break

        # Append user's query to memory for context
        conversations.append({"role": "user", "content": query})

        answer = ask_athena(conversations)

        # Also append model's answer to memory for context
        conversations.append({"role": "assistant", "content": answer})

        print("Athena:",answer)
