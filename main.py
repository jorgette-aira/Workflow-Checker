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

    requests.post(config.N8N_WEBHOOK_URL, json=payload)

if __name__ == "__main__":
    main()
