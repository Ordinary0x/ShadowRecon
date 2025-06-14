

import os
import subprocess
import json
from rich.console import Console

console = Console()

def run_maigret(username):
    os.makedirs(f"output/{username}", exist_ok=True)


    console.print(f"[yellow]Running Maigret for username: [bold]{username}[/bold]...\n")

    try:
        result=subprocess.run([
            "maigret",username,"-J","ndjson","-fo",f"output/{username}","--timeout","20"
        ],capture_output=True,text=True)

        if result.returncode != 0:
            console.print(f"[bold red]Maigret failed:[/bold red] {result.stderr}")
            return {}



        # return maigret_data

    except FileNotFoundError:
        console.print("[bold red]Error: Maigret is not installed or not in PATH.[/bold red]")
        return {}
    except json.decoder.JSONDecodeError:
        console.print("[bold red]Error: Failed to decode Maigret JSON output.[/bold red]")
        return {}



