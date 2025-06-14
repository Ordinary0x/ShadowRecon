# modules/ai_correlator.py
"""
AI Correlator Module for ShadowRecon

- Reads maigret.json and bing_scraper.json
- Extracts and scores social profile URLs (Instagram, Twitter, LinkedIn, Facebook, GitHub)
- Uses Hugging Face transformers ([facebook/bart-large-mnli]) for zero-shot classification
- Builds a refined list of target URLs with related info for downstream scrapers
- Saves output to refined_targets.json

Model Explanation:
- facebook/bart-large: A large sequence-to-sequence model good for summarization.
- facebook/bart-large-mnli: A fine-tuned BART model for multi-label Natural Language Inference (zero-shot classification).
  We use bart-large-mnli to classify whether a snippet/title corresponds to a social media profile.
"""
import os
import json
from urllib.parse import urlparse
from rich.console import Console
from transformers import pipeline

console = Console()

# Define primary social domains
PRIMARY_DOMAINS = {
    "instagram.com": "Instagram",
    "twitter.com": "Twitter",
    "linkedin.com": "LinkedIn",
    "facebook.com": "Facebook",
    "github.com": "GitHub",
    "youtube.com":"Youtube"
}

# Initialize zero-shot classifier
classifier = pipeline(
    "zero-shot-classification",
    model="facebook/bart-large-mnli"
)


def load_json(path: str) -> list | dict:
    """Load JSON or NDJSON from file correctly."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        # Try to parse full JSON
        try:
            data = json.loads(content)
            return data
        except json.JSONDecodeError:
            # Fallback to NDJSON
            results = []
            for line in content.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    results.append(json.loads(line))
                except json.JSONDecodeError:
                    console.print(f"[red]Invalid NDJSON line, skipping: {line}[/]")
            return results
    except Exception as e:
        console.print(f"[bold red]Failed to load {path}:[/] {e}")
        return []


def is_social_profile(url: str, title: str, snippet: str) -> bool:
    """Use zero-shot classification to check if a link corresponds to a social profile."""
    labels = ["social media profile", "news article", "company website", "blog post"]
    text = f"Title: {title}. Snippet: {snippet}"
    result = classifier(text, candidate_labels=labels, multi_label=False)
    top_label = result['labels'][0]
    score = result['scores'][0]
    return top_label == "social media profile" and score > 0.8


def extract_from_maigret(data: list | dict) -> list[dict]:
    """Extract found sites with details from Maigret output."""
    results = []
    if isinstance(data, list):
        for entry in data:
            site = entry.get("site", {})
            status = entry.get("status", {})
            url = status.get("url")
            if status.get("status") == "Claimed" and url:
                # important_keys = ['url', 'username', 'site_name', 'ids', 'tags']
                # info_fields = sum(1 for k in important_keys if info.get(k))

                # info_fields = sum(1 for v in entry.values() if v)
                results.append({
                    'platform': PRIMARY_DOMAINS.get(urlparse(url).netloc, status.get("site_name", "Unknown")),
                    'url': url,
                    'info': entry,
                    'score': 0.8
                })
            # if is_social_profile(url, site, status):
            #     results.append({
            #         'platform': PRIMARY_DOMAINS.get(urlparse(url).netloc, status.get("site_name", "Unknown")),
            #         'url': url,
            #         'info': entry,
            #         'score': 0.8
            #     })
    elif isinstance(data, dict):
        sites = data.get('sites', {})
        for site, info in sites.items():
            if info.get('status') == 'found':
                url = info.get('url')
                # important_keys = ['url', 'username', 'site_name', 'ids', 'tags']
                # info_fields = sum(1 for k in important_keys if info.get(k))
                info_fields = sum(1 for v in info.values() if v)
                results.append({
                    'platform': PRIMARY_DOMAINS.get(urlparse(url).netloc, site),
                    'url': url,
                    'info': info,
                    'score': 0.8
                })
                # if is_social_profile(url, site, status):
                #     results.append({
                #         'platform': PRIMARY_DOMAINS.get(urlparse(url).netloc, status.get("site_name", "Unknown")),
                #         'url': url,
                #         'info': entry,
                #         'score': 0.8
                #     })
    else:
        console.print("[red]Invalid data format for maigret.json[/]")
    return results




def extract_from_bing(results: list) -> list[dict]:
    """Extract and classify URLs from Bing search results."""
    extracted = []
    for item in results:
        url = item.get('url', '')
        title = item.get('title', '')
        snippet = item.get('snippet', '')
        domain = urlparse(url).netloc.replace('www.', '')
        platform = PRIMARY_DOMAINS.get(domain)
        if platform:
            extracted.append({
                'platform': platform,
                'url': url,
                'title': title,
                'snippet': snippet,
                'score': 1.0  # default high for known domains
            })
        else:
            # classify unknown domains
            if is_social_profile(url, title, snippet):
                extracted.append({
                    'platform': 'Other',
                    'url': url,
                    'title': title,
                    'snippet': snippet,
                    'score': 0.9
                })
    return extracted


def refine_targets(maigret_path: str, bing_path: str, output_path: str):
    """Main entry: load JSONs, extract, merge, dedupe, and save refined targets."""
    maigret_data = load_json(maigret_path)
    bing_data = load_json(bing_path)

    console.print("[bold cyan]Extracting from Maigret...[/]")
    maigret_results = extract_from_maigret(maigret_data)

    console.print("[bold cyan]Extracting from Bing...[/]")
    bing_results = extract_from_bing(bing_data)

    # merge and dedupe by URL
    merged = {item['url']: item for item in maigret_results + bing_results}
    refined = list(merged.values())

    # sort by score descending
    refined.sort(key=lambda x: x.get('score', 0), reverse=True)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(refined, f, indent=4)

    console.print(f"[bold green]Refined targets saved to {output_path}[/]")


