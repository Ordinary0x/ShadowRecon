import os
import json
from rich.console import Console

console = Console()

def get_target_info(args):
    target_info = {
        "target": args.target,
        "phone": args.phone if args.phone else None,
        "email": args.email if args.email else None,
        "username": args.username if args.username else None,
        "info": args.info if args.info else None,
        "image_path": args.image if args.image else None
    }

    #Validating name
    if not target_info["target"]:
        console.print("[bold red]Invalid Target Name")
        raise ValueError("Target name is required")
    #validating image path
    if target_info["image_path"] and not os.path.exists(target_info["image_path"]):
        console.print("f[bold red]Warning: Image file '{target_info['image_path']}' does not exist. Skipping image analysis.")
        target_info["image_path"] = None

    os.makedirs(f'input/target_info["target"]', exist_ok=True)
    with open(f"input/{target_info["target"]}", "w") as f:
        json.dump(target_info, f, indent=4)

    return target_info

