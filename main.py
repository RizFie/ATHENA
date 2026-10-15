import json
import urllib.request
import urllib.error
from ddgs import DDGS

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen3:8b-q4_K_M"
MEMORY_FILE = "memory.json"

def load_memory():
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as file:
            conversations = json.load(file)

        if not isinstance(conversations, list):
            raise ValueError("Memory must be a list.")

        if not conversations or conversations[0].get("role") != "system":
            raise ValueError("Memory is missing the system message")

        return conversations

    except FileNotFoundError:
        return [
                {
                "role": "system",
                "content": ("You are Athena, a helpful research assistant. "
                "Answer the user's questions clearly and accurately.")
                },
            ]

def save_memory(conversations):
    with open(MEMORY_FILE, "w", encoding="utf-8") as file:
        json.dump(conversations, file, indent=4, ensure_ascii=False)

# Search web tool for Athena (Return result of searches, not webpages)
def research_web(queries, max_results=10, results_per_query=5):

    found = {}

    with DDGS(timeout=10) as ddgs:
        for query in queries:
            try: 
                results = ddgs.text(
                    query,
                    region="my-en",
                    safe_search="moderate",
                    max_results=max_results
                )

                for result in results:
                    url = result.get("href","")
                    title = result.get("title","")

                    if not url.startswith("https://"):
                        continue

                    if not title:
                        continue

                    found[url] = result

            except Exception as e:
                print(f"Search failed for {query}: {e}")

    return list(found.values())[:max_results]

# Read page tool for Athena
def read_webpage(url):
    try:
        with DDGS(timeout=15) as ddgs:
            page = ddgs.extract(url)

        if not isinstance(page, dict):
            return {
                "url":url,
                "title":"",
                "content":"",
                "error":"Unexpected response format."
            }

        return {
            "url":page.get("url",url),
            "title":page.get("title", ""),
            "content":page.get("content",""),
            "error":None
        }

    except Exception as e:
        return {
            "url": url,
            "title": "",
            "content": "",
            "error": str(e),
        }

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
        try:
            result = json.loads(response.read().decode("utf-8"))

        except json.JSONDecodeError as e:
            raise ValueError("Ollama returned invalid JSON.") from e

    try:
        answer = result["message"]["content"]

    except (KeyError, TypeError):
        raise ValueError("Ollama returned an unexpected response format.")
    
    if not isinstance(answer, str):
        raise ValueError("Ollama returned a non-text response.")

    return answer

if __name__ == "__main__":
    print("Loading Athena memory...")
    conversations = load_memory()
    print("Memory loaded successfully.")

    queries = [
    '"AI intern" Klang Valley Malaysia March 2027',
    '"machine learning intern" Malaysia',
    '"data analyst intern" Kuala Lumpur Selangor',
    'site:linkedin.com/jobs/view "Data Analyst Intern" Malaysia',
    'site:my.jobstreet.com "Machine Learning Intern"',
    ]

    results = research_web(queries, max_results=10)

    if results:
        page = read_webpage(results[0]["href"])

        print("\n--- WEBPAGE TEST ---")
        print("URL:", page["url"])
        print("Title:", page["title"])

        if page["error"]:
            print("Error:", page["error"])
        else:
            print("Content:")
            print(page["content"][:3000])

    while True:
        query = input("\n> ")
        
        if query.strip().lower() == "/bye":
            print("Goodbye!")
            break

        # Append user's query to memory for context
        conversations.append({"role": "user", "content": query})

        try:
            answer = ask_athena(conversations)

        except urllib.error.HTTPError as e:
            conversations.pop()
            print(f"Athena: Ollama returned an HTTP error: {e.code}")

        except urllib.error.URLError as e:
            conversations.pop()
            print(f"Athena: Could not connect to Ollama: {e.reason}")

        except TimeoutError:
            conversations.pop()
            print("Athena: The request timed out. Please try again.")

        except ValueError as e:
            conversations.pop()
            print(f"Athena: Invalid response from Ollama: {e}")

        else:
            # Also append model's answer to memory for context
            conversations.append({"role": "assistant", "content": answer})

            try:
                # Saving to memory
                save_memory(conversations)
                print("\nAthena:",answer)

            except OSError as e:
                print(f"I couldn't save our conversations to the memory: {e}")
                print("\nAthena:",answer)
            
