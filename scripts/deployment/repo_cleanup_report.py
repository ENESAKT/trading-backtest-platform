#!/usr/bin/env python
import os
import sys

def report_cleanup():
    print("--- REPO CLEANUP REPORT ---")
    
    large_files = []
    tracked_artifacts = []
    
    # 1. Büyük Dosya Kontrolü (>10MB)
    for root, dirs, files in os.walk("."):
        if ".git" in root or ".venv" in root or "node_modules" in root:
            continue
        for file in files:
            path = os.path.join(root, file)
            try:
                size = os.path.getsize(path) / (1024 * 1024)
                if size > 10:
                    large_files.append((path, size))
            except Exception:
                pass
                
    # 2. Tracked Artifact Kontrolü
    try:
        tracked = os.popen("git ls-files artifacts").read().strip()
        if tracked:
            tracked_artifacts = tracked.split("\n")
    except Exception:
        pass
        
    print("\nLarge Files (>10MB):")
    if not large_files:
        print("  None found. OK.")
    else:
        for p, s in large_files:
            print(f"  {p} - {s:.1f} MB")
            
    print("\nTracked Artifacts:")
    if not tracked_artifacts:
        print("  None found in git. OK.")
    else:
        for p in tracked_artifacts[:10]:
            print(f"  {p}")
        if len(tracked_artifacts) > 10:
            print(f"  ... and {len(tracked_artifacts)-10} more.")
            
    print("\nAction Needed:")
    if large_files or tracked_artifacts:
        print("  Please untrack artifacts or add them to .gitignore.")
    else:
        print("  Repo is clean.")

if __name__ == "__main__":
    report_cleanup()
