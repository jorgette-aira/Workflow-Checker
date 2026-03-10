import os
import requests
import json
import time  
import config
from metrics import run_all_metrics
import urllib3
from dotenv import load_dotenv

# 1. Load the .env file correctly
load_dotenv() 

# Suppress insecure request warnings if using self-signed certs over Tailscale
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def main():
    print("🚀 Script started successfully!")

    # Setup Environment Variables
    builder_github_username = os.getenv("GITHUB_ACTOR", "Unknown_Builder")
    user_id = config.USER_MAP.get(builder_github_username, config.DEVOPS_ROLE_ID)
    role_id = config.DEVOPS_ROLE_ID 

    NOTIFICATION_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", config.N8N_WEBHOOK_URL)
    AGENT_WEBHOOK_URL = os.getenv("N8N_AGENT_WEBHOOK_URL")

    workflow_path = "workflows/ai_agent_workflow.json"
    test_suite_path = "test_suite.json" # <--- Path to your new file

    if not os.path.exists(workflow_path) or not os.path.exists(test_suite_path):
        print(f"❌ ERROR: Missing workflow or test_suite file.")
        return

    # 2. Load the Workflow structure and Test Suite
    with open(workflow_path, 'r', encoding="utf-8") as f:
        workflow_data = json.load(f)
    
    with open(test_suite_path, 'r', encoding="utf-8") as f:
        test_cases = json.load(f)

    all_test_details = []
    overall_passed = True

    # 3. Loop through all test cases
    for index, case in enumerate(test_cases):
        user_input = case["input"]
        expected_qa = case["expected_output"]
        time.sleep(2)
        
        print(f"🧪 Testing: {user_test_input}")
        
        try:
            # Trigger n8n Agent
            agent_response = requests.post(
                AGENT_WEBHOOK_URL, 
                json={"prompt": user_input}, 
                timeout=60, 
                verify=False
            )
            agent_response.raise_for_status()
            
            response_data = agent_response.json()
            if isinstance(response_data, list):
                response_data = response_data[0]
            
            actual_answer = response_data.get("output") or response_data.get("text") or "No response"
            print(f"🤖 AI Answer: {actual_answer}")
            
            # Run Metrics for this specific case
            passed, details = run_all_metrics(workflow_data, actual_answer, expected_qa)
            
            if not passed:
                overall_passed = False
            
            all_test_details.append(f"**Test {index+1}:** {'✅' if passed else '❌'}\n{details}")

        except Exception as e:
            overall_passed = False
            error_msg = f"❌ Test {index+1} Failed: {str(e)}"
            all_test_details.append(error_msg)
            print(error_msg)

    # 4. Final Notification
    mention_target = f"<@&{role_id}>" if overall_passed else f"<@{user_id}>"
    full_report = "\n\n".join(all_test_details)

    payload = {
        "status": "pass" if overall_passed else "fail",
        "builder_name": builder_github_username,
        "mention_target": mention_target,
        "test_results": f"### Batch Results Summary:\n{full_report}",
        "execution_time": "N/A (Batch)" 
    }

    print(f"📡 Sending final results to Discord...")
    requests.post(NOTIFICATION_WEBHOOK_URL, json=payload, timeout=30, verify=False)

if __name__ == "__main__":
    main()
