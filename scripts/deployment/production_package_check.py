import os
import sys

def check_production_size():
    # Example logic to check context size or venv exclusion
    print("Checking production package size and docker context...")
    if os.path.exists(".venv") and not os.path.exists(".dockerignore"):
        print("ERROR: .venv exists but no .dockerignore. Production context will be massive.")
        sys.exit(1)
    print("SUCCESS: Production package checks passed.")

if __name__ == "__main__":
    check_production_size()
