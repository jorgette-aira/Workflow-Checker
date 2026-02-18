import os
import requests
import json
import config
from metrics import check_workflow_metrics

def main():
    # 1. Capture data from GitHub Environment Variables
    # These are automatically available when run inside a GitHub Action
    builder_github_username = os.getenv("GITHUB_ACTOR", "Unknown_Builder")
    repo_name = os.getenv("GITHUB_REPOSITORY", "Unknown_Repo")
    
    print(f"🚀 Starting automation for {builder_github_username} on {repo_name}...")

    # 2. Get the Builder's Discord ID from your mapping in config.py
    # This ensures the correct person gets pinged on Discord
    discord_id = config.USER_MAP.get(builder_github_username)
    
    if not discord_id:
        print(f"⚠️ Warning: No Discord ID found for {builder_github_username}. Defaulting to devops ping.")
        discord_id = config.DEVOPS_ROLE_ID

    # 3. Fetch the Builder's n8n workflow JSON
    # In a real scenario, you would fetch this via n8n API or read a .json file in the repo
    # For now, let's assume your metrics check a local file in the PR
    workflow_path = "workflows/ai_agent_workflow.json"
    
    try:
        with open(workflow_path, 'r') as f:
            workflow_data = json.load(f)
            
        # 4. Run the Metrics Logic (from your metrics.py)
        # Returns a boolean (passed) and a string (details)
        passed, details = check_workflow_metrics(workflow_data)
        
    except FileNotFoundError:
        passed = False
        details = "Error: Workflow JSON file not found in the repository."
    except Exception as e:
        passed = False
        details = f"System Error: {str(e)}"

    # 5. Send the Results to the n8n Webhook
    payload = {
        "status": "pass" if passed else "fail",
        "builder_name": builder_github_username,
        "discord_id": discord_id,
        "test_results": details,
        "repo": repo_name
    }

    try:
        response = requests.post(
            config.N8N_WEBHOOK_URL, 
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✅ Successfully sent results to n8n.")
        else:
            print(f"❌ Failed to reach n8n. Status Code: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Network Error: {e}")

if __name__ == "__main__":
    main()
