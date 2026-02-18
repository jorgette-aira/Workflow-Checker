import os
import requests
import json
import config
from metrics import run_all_metrics # Ensure this function exists in metrics.py

def main():
    # 1. Capture Environment Data
    builder_github_username = os.getenv("GITHUB_ACTOR", "Unknown_Builder")
    repo_name = os.getenv("GITHUB_REPOSITORY", "Unknown_Repo")
    
    # 2. Get Discord ID from config mapping
    discord_id = config.USER_MAP.get(builder_github_username, config.DEVOPS_ROLE_ID)

    # 3. Load the builder's workflow
    workflow_path = "workflows/ai_agent_workflow.json"
    
    try:
        with open(workflow_path, 'r') as f:
            workflow_data = json.load(f)

        # --- MOCK DATA FOR TESTING ---
        # In a real scenario, these would come from your n8n test results
        actual_agent_response = "Hello! I am your assistant from Batangas." 
        expected_qa_answer = "assistant Batangas" 
        # -----------------------------

        # 4. Run the Metrics (Fixed Syntax)
        passed, details = run_all_metrics(
            workflow_data, 
            actual_agent_response, 
            expected_qa_answer
        )
        
    except FileNotFoundError:
        passed = False
        details = "Error: Workflow JSON file not found."
    except Exception as e:
        passed = False
        details = f"System Error: {str(e)}"

   # 5. Send to n8n Webhook
    payload = {
        "status": "pass" if passed else "fail",
        "builder_name": builder_github_username,
        "discord_id": discord_id,
        "test_results": details
    }

    print(f"📡 Attempting to trigger n8n at: {config.N8N_WEBHOOK_URL}")

    try:
        # We add a timeout so the script doesn't hang forever if ngrok is down
        response = requests.post(config.N8N_WEBHOOK_URL, json=payload, timeout=10)
        
        # This will raise an error if the status is 404, 500, etc.
        response.raise_for_status() 

        print(f"✅ Success! n8n responded with: {response.status_code}")
        
    except requests.exceptions.HTTPError as err:
        print(f"❌ HTTP Error: {err}")
        print(f"Check if your URL is correct: {config.N8N_WEBHOOK_URL}")
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Is your ngrok tunnel running?")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
