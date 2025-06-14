#shadowrecon main

import os
import json
import argparse
from pygments.styles.dracula import green
from rich.console import Console
from rich.panel import Panel
from rich import box
from modules.maigret import run_maigret
from input_handler import get_target_info
from modules.bing import bing
from modules.filter_links import refine_targets
from modules.insta_extractor import run_instagram_extraction

console = Console()


def banner():
    console.print(Panel("""[green]
    
    
   _____ _               _               _____                      
  / ____| |             | |             |  __ \                     
 | (___ | |__   __ _  __| | _____      _| |__) |___  ___ ___  _ __  
  \___ \| '_ \ / _` |/ _` |/ _ \ \ /\ / /  _  // _ \/ __/ _ \| '_ \ 
  ____) | | | | (_| | (_| | (_) \ V  V /| | \ \  __/ (_| (_) | | | |
 |_____/|_| |_|\__,_|\__,_|\___/ \_/\_/ |_|  \_\___|\___\___/|_| |_|
 
                                     [green][developed by Ordinary0x]
        """, box=box.DOUBLE, title="[bold red]ShadowRecon", subtitle="[green]People OSINT Phase 1"))



def main():
    banner()

    praser=argparse.ArgumentParser(description="ShadowRecon - OSINT Recon Framework")
    praser.add_argument("--target",help="Target name ",required=True)
    praser.add_argument("--username",help="Target Any Web Site Username(optional)",required=False)
    praser.add_argument("--email",help="Target Email(optional)",required=False)
    praser.add_argument("--phone",help="Target Phone number(optional)",required=False)
    praser.add_argument("--image",help="Target Image Path(optional)",required=False)
    praser.add_argument("--info", help="Optional known info about target (bio keywords, workplace, etc.)",required=False)

    args = praser.parse_args()
    args.target = args.target.strip()

    target_info=get_target_info(args)
    console.print("[bold cyan]\n[1] Running Maigret...\n")
    maigret = run_maigret(args.target)
    # maigret=run_maigret(args.username)
    console.print("[bold cyan]\n[1] Running Bing Search ...\n")
    bing(args.target,args.username,args.info)

    refine_targets(
        f"output/{args.target}/report_{args.target}_ndjson.json",
        f"output/{args.target}/bing_result.json",
        f"output/{args.target}/refined_targets.json"
    )
    run_instagram_extraction(
        f"output/{args.target}/refined_targets.json",
        args.target,
        f"output/{args.target}/{args.target}_instagram.json"
    )







if __name__ == "__main__":
    main()