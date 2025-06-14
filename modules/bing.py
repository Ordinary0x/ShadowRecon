import os
import json
import requests
from bs4 import BeautifulSoup
from rich.console import Console
from urllib.parse import quote
import time

console = Console()

HEADERS={
"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/114.0.0.0 Safari/537.36"
}

def bing(name,username=None,info=None,max_results=10):
    query=f'"{name}"'
    if username:
        query += f'"{username} "'
    if info:
        query += f'" {info}"'

    # query += " site:facebook.com OR site:instagram.com OR site:linkedin.com OR site:github.com

    encoded_query=quote(query)
    search_url = f"https://www.bing.com/search?q={encoded_query}&count={max_results}"
    console.print(f"[bold cyan]Bing Search URL:[/] {search_url}")


    try:
        time.sleep(3)
        response = requests.get(search_url, headers=HEADERS,timeout=20)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]Request failed:[/] {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    results = []

    for h2 in soup.find_all("h2"):
        a = h2.find("a")
        if not a or not a.get("href"):
            continue
        title = a.get_text(strip=True)
        url = a["href"].strip()

        # Try to find the next <p> sibling or parent <li> with a <p>
        snippet_tag = h2.find_next("p")
        snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""

        results.append({
            "title": title,
            "url": url,
            "snippet": snippet
        })

    console.print(f"[bold green]Retrieved {len(results)} results from Bing.")

    os.makedirs(f"output/{name}", exist_ok=True)
    bing_output = os.path.join(f"output/{name}/bing_result.json")
    with open(bing_output,"w") as f:
        json.dump(results, f,indent=4)
    console.print(f"[bold yellow]Saved results to:[/] {name}")











