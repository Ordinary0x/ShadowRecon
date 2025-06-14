# modules/insta_extractor.py
"""
Instaloader Extractor Module for ShadowRecon

- Prompts optional login for private/data extraction
- Reads `refined_targets.json` to find Instagram username in URL, title, or snippet
- Requires login (and follow) to extract posts, stories, highlights, tagged posts
- Downloads and saves:
  * Profile picture
  * Posts metadata + media (login only)
  * Story highlights media (login only)
  * Stories media (login only)
  * Tagged posts media (login only)
- Sleeps between requests to avoid rate limits
- Saves all data and file paths to JSON
"""
import os
import re
import json
import time
from getpass import getpass
from urllib.parse import urlparse
import requests
import instaloader
from IPython.utils.timing import timings_out
from rich.prompt import Prompt
from rich.console import Console
import random



console = Console()
L = instaloader.Instaloader(sleep=True)


def login_prompt():
    choice = Prompt.ask("[cyan]Login to Instagram for private/highlight/tagged data? (Y/n)[/]", default="n")
    if choice.lower() == 'y':
        user = Prompt.ask("Enter your IG login username")
        pwd = getpass("Enter your IG password: ")
        try:
            L.login(user, pwd)
            console.print("[green]Logged in successfully.[/]")
        except Exception as e:
            console.print(f"[red]Login failed: {e}[/]")
            exit(1)


def load_refined_targets(path: str) -> dict:
    """Load refined_targets and attempt to extract Instagram username."""
    pattern = re.compile(r'@([A-Za-z0-9_.]+)')
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for entry in data:
            # Check URL
            url = entry.get('url','')
            if 'instagram.com' in urlparse(url).netloc:
                parts = url.strip('/').split('/')
                if parts[-1] and parts[-1] != 'p':
                    return {'username': parts[-1].lstrip('@')}
            # Check title/snippet for @username
            for key in ('title','snippet'):
                text = entry.get(key,'')
                match = pattern.search(text)
                if match:
                    return {'username': match.group(1)}
    except Exception:
        pass
    return {}


def download_url(url: str, dest_folder: str) -> str:
    """Download a media URL to dest_folder and return file path."""
    try:
        os.makedirs(dest_folder, exist_ok=True)
        resp = requests.get(url, stream=True)
        if resp.status_code == 200:
            filename = os.path.join(dest_folder, os.path.basename(urlparse(url).path))
            with open(filename, 'wb') as f:
                for chunk in resp.iter_content(1024):
                    f.write(chunk)
            return filename
        else:
            console.print(f"[yellow]Warning: {resp.status_code} downloading {url}[/]")
    except Exception as e:
        console.print(f"[red]Failed to download {url}: {e}[/]")
    return ''


def extract_instagram_data(target_username: str, output_file: str):

    try:
        profile = instaloader.Profile.from_username(L.context, target_username)
    except Exception:
        console.print(f"[red]Profile '{target_username}' not found or inaccessible.[/]")
        return

    console.print(f"[bold cyan]Extracting Instagram data for {target_username}[/]")
    data = {
        'username': profile.username,
        'full_name': profile.full_name,
        'bio': profile.biography,
        'followers': profile.followers,
        'followees': profile.followees,
        'posts_count': profile.mediacount,
        'external_url': profile.external_url,
        'is_private': profile.is_private,
        'is_verified': profile.is_verified,
        'profile_pic_url': profile.profile_pic_url,
        'profile_pic_path': '',
        'posts': [],
        'stories': [],
        'highlights': [],
        'tagged_posts': []
    }

    # Download profile pic
    data['profile_pic_path'] = download_url(profile.profile_pic_url,
                                         f"output/insta/{target_username}/profile_pic")
    if profile.is_private:
        if not L.context.is_logged_in:
            console.print("[red]Error: Login required to extract Instagram posts and media. Aborting.[/]")
            save_data(data, output_file)
            return

    # Posts metadata + media
    try:
        console.print("[yellow]Fetching posts...[/]")
        for post in profile.get_posts():
            entry = {'url': f"https://www.instagram.com/p/{post.shortcode}/",
                     'timestamp': str(post.date_utc),
                     'media_path': ''}
            # Download media
            media_url = getattr(post, 'url', None) or getattr(post, 'pic_url', None)
            if media_url:
                entry['media_path'] = download_url(media_url,
                                                   f"output/insta/{target_username}/posts")
            data['posts'].append(entry)
            time.sleep(random.uniform(5, 15))
    except Exception as e:
        console.print(f"[red]Failed to fetch posts: {e}[/]")

    # Stories
    try:
        console.print("[yellow]Fetching stories...[/]")
        for story in L.get_stories(userids=[profile.userid]):
            for item in story.get_items():
                path = download_url(item.url,
                                    f"output/insta/{target_username}/stories")
                data['stories'].append({'url': item.url,
                                         'timestamp': str(item.date_utc),
                                         'media_path': path})
                time.sleep(random.uniform(5, 15))
    except Exception as e:
        console.print(f"[red]Failed to fetch stories: {e}[/]")

    # Highlights
    try:
        console.print("[yellow]Fetching highlights...[/]")
        for hl in profile.get_highlights():
            hl_entry = {'title': hl.title, 'items': []}
            for item in hl.get_items():
                path = download_url(item.url,
                                    f"output/insta/{target_username}/highlights/{hl.title}")
                hl_entry['items'].append({'url': item.url,
                                          'timestamp': str(item.date_utc),
                                          'media_path': path})
                time.sleep(random.uniform(5, 15))
            data['highlights'].append(hl_entry)
    except Exception as e:
        console.print(f"[red]Failed to fetch Highlights: {e}[/]")

    # Tagged posts
    try:
        console.print("[yellow]Fetching tagged posts...[/]")
        for tagged in profile.get_tagged_posts():
            post_url = f"https://www.instagram.com/p/{tagged.shortcode}/"
            path = download_url(tagged.url,
                                f"output/insta/{target_username}/tagged_posts")
            data['tagged_posts'].append({'url': post_url,
                                          'timestamp': str(tagged.date_utc),
                                          'media_path': path})
            time.sleep(random.uniform(5, 15))
        save_data(data,output_file)
    except Exception as e:
        console.print(f"[red]Failed to fetch Tagged posts: {e}[/]")

    # Save to JSON
def save_data(data,output_file:str):
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
    console.print(f"[green]Saved Instagram data and media paths to {output_file}[/]")


def run_instagram_extraction(refined_json='output/target/refined_targets.json', username=None, output_file=None):
    login_prompt()
    refined = load_refined_targets(refined_json)
    target =  refined.get('username') or  username or Prompt.ask("Instagram username (fallback to target)")
    out_file = output_file or f"output/insta/{target}_insta.json"
    extract_instagram_data(target, out_file)

# CLI mode
if __name__ == '__main__':
    run_instagram_extraction()
