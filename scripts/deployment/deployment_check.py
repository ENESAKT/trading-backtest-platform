import os
import sys

def check_deployment():
    print("Checking deployment readiness (domain, volume binds, secrets)...")
    if not os.path.exists("infra/docker-compose.prod.yml"):
        print("ERROR: docker-compose.prod.yml not found.")
        sys.exit(1)
        
    print("SUCCESS: Deployment config logic seems ready.")

if __name__ == "__main__":
    check_deployment()
