#!/usr/bin/env python3
"""Create a fresh, editable starter; never overwrite an existing project."""
import argparse
import shutil
from pathlib import Path
from prepare_fonts import prepare

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination',type=Path)
    args=parser.parse_args()
    target=args.destination.resolve()
    if target.exists() and any(target.iterdir()):
        parser.exit(1,'Destination is not empty. Use a new directory or edit the existing project explicitly.\n')
    source=Path(__file__).resolve().parents[1]/'assets'/'starter'
    shutil.copytree(source,target,dirs_exist_ok=True)
    try:
        result=prepare(target)
    except (ValueError,RuntimeError,OSError) as exc:
        parser.exit(1,f'Project copied to {target}; font preparation needs attention: {exc}\n')
    print(f'Created {target}/index.html; covered {result["characters"]} characters. Replace sample content before delivery.')

if __name__=='__main__':
    main()
