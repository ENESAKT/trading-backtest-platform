#!/usr/bin/env python
import os

def check_borfin_integration():
    print("--- BORFIN INTEGRATION CHECK ---")
    
    # 1. Klasörler
    print("\nChecking artifacts/ folder:")
    if os.path.exists("artifacts"):
        for d in os.listdir("artifacts"):
            if "borfin" in d.lower():
                print(f"  [INFO] Found Borfin artifact: artifacts/{d}")
    else:
        print("  [OK] No artifacts folder found.")

    # 2. Kod içi referanslar
    print("\nChecking code for 'borfin' references...")
    cmd = "grep -rnwi 'borfin' backend/ quant_engine/ piyasapilot-v2/src/ docs/ 2>/dev/null"
    res = os.popen(cmd).read().strip()
    
    if res:
        print("  [WARN] Found 'borfin' strings in codebase:")
        lines = res.split("\n")
        for line in lines[:10]:
            print(f"    {line}")
        if len(lines) > 10:
            print(f"    ... and {len(lines)-10} more.")
    else:
        print("  [OK] No code references found.")

if __name__ == "__main__":
    check_borfin_integration()
