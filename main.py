import json
import urllib.request
import urllib.error
from ddgs import DDGS
import time
import re
from urllib.parse import urljoin

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen3:4b-instruct-2507-q4_K_M"
MEMORY_FILE = "memory.json"

# --- MEMORY FUNCTIONS ---
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
# ------------------------

# --- WEB SEARCH FUNCTIONS --- 
# Search web tool for Athena (Return result of searches, not webpages)
def research_web(queries, max_results=10, results_per_query=5):

    found = {}

    with DDGS(timeout=10) as ddgs:
        for query in queries:
            query_count = 0
            try: 
                results = ddgs.text(
                    query,
                    region="my-en",
                    safesearch="moderate",
                    max_results=results_per_query
                )

                for result in results:
                    url = result.get("href","")
                    title = result.get("title","")

                    if not url.startswith("https://") or not title:
                        continue

                    if url not in found:
                        found[url] = result

                    query_count += 1

                print(f"Search completed: {query}")
                print(f"Results returned: {query_count}")

            except Exception as e:
                if "no results found" in str(e).lower():
                    print(f"No matches returned: {query}")
                else:
                    print(f"Search error for {query}: {e}")

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
        # Return a dict
        return {
            "url": url,
            "title": "",
            "content": "",
            "error": str(e),
        }



#  Extract structured data when Athena already browse a page
def extract_structured_data(page, fields):
    if page["error"]:
        return {
            "source_url":page["url"],
            "error":page["error"]
        }

    content = page.get("content","")
    print(page["url"])

    # Calls extractor to get the link reference
    link_references = extract_markdown_link_references(
        content, page["url"]
    )

    # Records contain the raw text file
    records = split_markdown_listings(content)

    # parse_job_record then takes the raw text returned by 
    # split_markdown_listings (records) and convert it to structured dict
    jobs = [parse_job_record(record, link_references) for record in records]

    print("Records found:", len(jobs))

    return jobs

# Main function call to chat with Athena
def ask_athena(conversation, json_mode=False):
    start = time.time()
    payload = {
        "model": MODEL,
        "messages": conversation,
        "think": False,
        "stream": False,
    }

    if json_mode:
        payload["format"] = "json"

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        OLLAMA_URL,
        data = data,
        headers = {"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(request, timeout=300) as response:
        try:
            result = json.loads(response.read().decode("utf-8"))

        except json.JSONDecodeError as e:
            raise ValueError("Ollama returned invalid JSON.") from e

    try:
        answer = result["message"]["content"]
        print(f"Response time: {time.time() - start:.2f} seconds")

    except (KeyError, TypeError):
        raise ValueError("Ollama returned an unexpected response format.")
    
    if not isinstance(answer, str):
        raise ValueError("Ollama returned a non-text response.")

    return answer

def research_pipeline(queries, fields, max_results=10, pages_to_read=5):
    # 1. Search the web
    # 2. Select candidate URLs
    # 3. Read the pages
    # 4. Extract structured data from readable pages
    # 5. Preserve errors and source URLs
    # 6. Return research records
    pass

if __name__ == "__main__":

    # 1. Load the Memory
    print("Loading Athena memory...")
    conversations = load_memory()
    print("Memory loaded successfully.")

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
            
