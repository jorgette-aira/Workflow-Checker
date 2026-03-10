import os
import requests
import json
import time  
import config
from metrics import run_all_metrics
import urllib3
from dotenv import load_dotenv

load_dotenv() 
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
    test_suite_path = "test_suite.json"

    if not os.path.exists(workflow_path) or not os.path.exists(test_suite_path):
        print(f"❌ ERROR: Missing workflow or test_suite file.")
        return

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
        time.sleep(1) # Small cooldown
        
        print(f"🧪 Testing: {user_input}")
        
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
            
            # Run Metrics
            try:
                passed, details = run_all_metrics(workflow_data, actual_answer, expected_qa)
            except Exception as e:
                passed = False
                details = f"Metric Error: {str(e)}"
                print(f"❌ Metric Error: {e}")

            # --- CRITICAL: Add the results to the report list ---
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
    
    # Ensure full_report isn't empty
    full_report = "\n\n".join(all_test_details) if all_test_details else "No tests were executed."

    payload = {
        "status": "pass" if overall_passed else "fail",
        "builder_name": builder_github_username,
        "mention_target": mention_target,
        "test_results": f"### Batch Results Summary:\n{full_report}",
        "execution_time": "N/A" 
    }

    print(f"📡 Sending final results to Discord...")
    
    # Final safety check on the URL before posting
    if NOTIFICATION_WEBHOOK_URL:
        requests.post(NOTIFICATION_WEBHOOK_URL, json=payload, timeout=30, verify=False)
    else:
        print("❌ Error: NOTIFICATION_WEBHOOK_URL is None. Check your .env file!")

if __name__ == "__main__":
    main()
