
import os
import json
from urllib.parse import urlparse
from rich.console import Console

console = Console()

PRIMARY_DOMAINS = {
    "instagram.com": "Instagram",
    "twitter.com": "Twitter",
    "linkedin.com": "LinkedIn",
    "facebook.com": "Facebook",
    "github.com": "GitHub",
    "youtube.com": "Youtube"
}

BLOCKED_DOMAINS = [
    "op.gg", "fanlore.org", "fandom.com", "speedrun.com",
    "roblox.com", "https://www.op.gg/","https://3ddd.ru","https://diary.ru",
    "scratch.mit.edu", "twitchtracker.com", "socialblade.com","https://opensea.io"
]

def load_json(path: str) -> list | dict:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return [json.loads(line) for line in content.splitlines() if line.strip()]
    except Exception as e:
        console.print(f"[red]Failed to load {path}: {e}[/]")
        return []

def is_blocked(url:str) -> bool:
    domain = urlparse(url).netloc.replace("www.", "")
    return any(blocked in domain for blocked in BLOCKED_DOMAINS)

def extract_from_maigret(data: list | dict) -> list[dict]:
    """Extract found sites with details from Maigret output."""
    results = []
    if isinstance(data, list):
        for entry in data:
            site = entry.get("site", {})
            status = entry.get("status", {})
            url = status.get("url")
            if status.get("status") == "Claimed" and url and not is_blocked(url):
                results.append({
                    'platform': PRIMARY_DOMAINS.get(urlparse(url).netloc, status.get("site_name", "Unknown")),
                    'url': url,
                    'info': entry,
                    'score': 0.8
                })
    elif isinstance(data, dict):
        sites = data.get('sites', {})
        for site, info in sites.items():
            if info.get('status') == 'found':
                url = info.get('url')
                if url and not is_blocked(url):
                    results.append({
                        'platform': PRIMARY_DOMAINS.get(urlparse(url).netloc, site),
                        'url': url,
                        'info': info,
                        'score': 0.8
                    })

    else:
        console.print("[red]Invalid data format for maigret.json[/]")
    return results



def extract_from_bing(data: list) -> list[dict]:
    results = []
    for entry in data:
        url = entry.get('url', '')
        title = entry.get('title', '')
        snippet = entry.get('snippet', '')
        if not url or is_blocked(url):
            continue
        domain = urlparse(url).netloc.replace('www.', '')
        platform = PRIMARY_DOMAINS.get(domain, 'Other')
        results.append({
            'platform': platform,
            'url': url,
            'title': title,
            'snippet': snippet,
            'score': 0.9,
            'source': 'bing'
        })
    return results

def refine_targets(maigret_path: str, bing_path: str, output_path: str):
    maigret_data = load_json(maigret_path)
    bing_data = load_json(bing_path)

    console.print("[bold cyan]Extracting Maigret links...[/]")
    maigret_results = extract_from_maigret(maigret_data)

    console.print("[bold cyan]Extracting Bing links...[/]")
    bing_results = extract_from_bing(bing_data)

    combined = maigret_results + bing_results
    unique = {entry['url']: entry for entry in combined}.values()
    sorted_links = sorted(unique, key=lambda x: x.get('score', 0), reverse=True)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(list(sorted_links), f, indent=4)

    console.print(f"[bold green]Refined targets saved to {output_path}[/]")