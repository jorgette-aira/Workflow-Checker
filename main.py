import os
import requests
import json
import config
from metrics import run_all_metrics

def main():
    # TEST 1: Check if script starts
    print("🚀 Script started successfully!")

    builder_github_username = os.getenv("GITHUB_ACTOR", "Unknown_Builder")
    repo_name = os.getenv("GITHUB_REPOSITORY", "Unknown_Repo")
    
    # 1. Fetch the relevant IDs from your config
    user_id = config.USER_MAP.get(builder_github_username, config.DEVOPS_ROLE_ID)
    role_id = config.DEVOPS_ROLE_ID 

    # TEST 2: Check if file exists
    workflow_path = "workflows/ai_agent_workflow.json"
    if not os.path.exists(workflow_path):
        print(f"❌ ERROR: Cannot find {workflow_path}. Make sure the folder and file exist!")
        return

    try:
        with open(workflow_path, 'r') as f:
            workflow_data = json.load(f)
        
        actual_agent_response = "Hello! I am your assistant from Batangas." 
        expected_qa_answer = "assistant Batangas" 

        passed, details = run_all_metrics(workflow_data, actual_agent_response, expected_qa_answer)
        print(f"📊 Metrics completed. Result: {'PASS' if passed else 'FAIL'}")
        
    except Exception as e:
        passed = False
        details = f"System Error: {str(e)}"
        print(f"❌ Error during metrics: {e}")

    # 2. Logic: Create the Mention String
    # If passed: Mention the Role (<@&ID>)
    # If failed: Mention the Builder (<@ID>)
    if passed:
        mention_target = f"<@&{role_id}>"
    else:
        mention_target = f"<@{user_id}>"

    # 3. Send to n8n Webhook
    payload = {
        "status": "pass" if passed else "fail",
        "builder_name": builder_github_username,
        "mention_target": mention_target,
        "test_results": details
    }

    print(f"📡 Attempting to trigger n8n at: {config.N8N_WEBHOOK_URL}")

    try:
        response = requests.post(config.N8N_WEBHOOK_URL, json=payload, timeout=10)
        print(f"✅ n8n Response: {response.status_code}")
        if response.status_code != 200:
            print(f"⚠️ Server Message: {response.text}")
    except Exception as e:
        print(f"❌ Network Error: {e}")

if __name__ == "__main__":
    main()
