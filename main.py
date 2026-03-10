import os
import requests
import json
import time  
import config
from metrics import run_all_metrics
import urllib3
from dotenv import load_dotenv

load_dotenv

# Suppress insecure request warnings if using self-signed certs over Tailscale
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def main():
    print("🚀 Script started successfully!")

    # 1. Setup metadata & Environment Variables
    builder_github_username = os.getenv("GITHUB_ACTOR", "Unknown_Builder")
    user_id = config.USER_MAP.get(builder_github_username, config.DEVOPS_ROLE_ID)
    role_id = config.DEVOPS_ROLE_ID 

    # Pull Webhook URLs from GitHub Secrets (Environment), fallback to config.py if local
    NOTIFICATION_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", config.N8N_WEBHOOK_URL)
    
    # You will need to add this new secret to your GitHub Actions and config.py
    AGENT_WEBHOOK_URL = os.getenv("N8N_AGENT_WEBHOOK_URL")

    workflow_path = "workflows/ai_agent_workflow.json"
    if not os.path.exists(workflow_path):
        print(f"❌ ERROR: Cannot find {workflow_path}.")
        return

    try:
        # 2. Load the Workflow structure
        with open(workflow_path, 'r', encoding="utf-8") as f:
            workflow_data = json.load(f)
        
       # 3. Define the test case parameters for Badminton
        user_test_input = "What happens if the shuttlecock lands outside the boundary lines?"
        expected_qa_answer = "If the shuttlecock lands outside the boundary lines, it is a 'fault.' The opponent wins the rally and earns a point."
        
        print(f"🤖 Pinging AI Agent at {AGENT_WEBHOOK_URL}...")
        
        # 4. Trigger the n8n AI Agent and get the real response
        agent_start_time = time.time()
        agent_response = requests.post(
            AGENT_WEBHOOK_URL, 
            json={"prompt": user_test_input}, 
            timeout=60, # LLMs can take a moment, giving it 60 seconds
            verify=False
        )
        agent_response.raise_for_status() # Raise an error for bad status codes
        
        # Assuming your n8n Respond to Webhook node returns JSON like {"output": "..."}
        response_data = agent_response.json()

        if isinstance(response_data, list):
            response_data = response_data[0]
        
        # This safely checks for 'output' but falls back to 'text' just in case
        actual_agent_response = response_data.get("output") or response_data.get("text")
        
        print(f"🤖 AI Answer: {actual_agent_response}")

        if not actual_agent_response:
            print("⚠️ WARNING: The AI Agent returned an empty response! Check n8n logs.")
            actual_agent_response = "No response received from Agent."
        
        agent_end_time = time.time()
        print(f"✅ AI Agent responded in {round(agent_end_time - agent_start_time, 2)}s")

        # 5. Run DeepEval Metrics
        print("⚖️ Running DeepEval metrics...")
        start_time = time.time()
        passed, details = run_all_metrics(workflow_data, actual_agent_response, expected_qa_answer)
        end_time = time.time()
        
        execution_duration = round(end_time - start_time, 2)

        if execution_duration > 10.0:
            details += f"\n⚠️ **Warning**: High evaluation latency ({execution_duration}s)"

        print(f"📊 Metrics completed in {execution_duration}s. Result: {'PASS' if passed else 'FAIL'}")
        
        
    except Exception as e:
        passed = False
        execution_duration = 0
        details = f"**System Error**: {str(e)}"
        print(f"❌ Error during metrics: {e}")

    # 6. Notifications
    mention_target = f"<@&{role_id}>" if passed else f"<@{user_id}>"

    # Payload with Performance Data
    payload = {
        "status": "pass" if passed else "fail",
        "builder_name": builder_github_username,
        "mention_target": mention_target,
        "test_results": details,
        "execution_time": f"{execution_duration}s" 
    }

    print(f"📡 Sending results to Notification Webhook: {NOTIFICATION_WEBHOOK_URL}")

    try:
        response = requests.post(NOTIFICATION_WEBHOOK_URL, json=payload, timeout=30, verify=False)
        print(f"✅ Notification Webhook Response: {response.status_code}")
    except Exception as e:
        print(f"❌ Network Error sending notification: {e}")

if __name__ == "__main__":
    main()
