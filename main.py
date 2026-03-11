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

    # 1. Setup Environment & URLs
    AGENT_WEBHOOK_URL = os.getenv("N8N_AGENT_WEBHOOK_URL")
    NOTIFICATION_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", config.N8N_WEBHOOK_URL)
    platform = os.getenv("PLATFORM_TYPE", "telegram") 
    
    builder_github_username = os.getenv("GITHUB_ACTOR", "Unknown_Builder")
    user_id = config.USER_MAP.get(builder_github_username, config.DEVOPS_ROLE_ID)
    role_id = config.DEVOPS_ROLE_ID 

    if not AGENT_WEBHOOK_URL:
        print("❌ ERROR: N8N_AGENT_WEBHOOK_URL is not set.")
        return

    # 2. Define Test Inputs & Expected Answer
    user_test_input = "What happens if the shuttlecock lands outside the boundary lines?"
    expected_qa_answer = "If the shuttlecock lands outside the boundary lines, it is a 'fault.' The opponent wins the rally and earns a point."

    # 3. Build Platform-Specific Payload
    if platform == "telegram":
        payload = {"message": {"text": user_test_input}, "from": {"id": 12345}}
    elif platform == "messenger" or platform == "instagram":
        payload = {"entry": [{"messaging": [{"message": {"text": user_test_input}}]}]}
    else:
        payload = {"prompt": user_test_input}

    # 4. Execute the Test
    try:
        workflow_path = "workflows/ai_agent_workflow.json"
        if not os.path.exists(workflow_path):
            print(f"❌ ERROR: Cannot find {workflow_path}.")
            return

        with open(workflow_path, 'r', encoding="utf-8") as f:
            workflow_data = json.load(f)

        print(f"🤖 Pinging AI Agent ({platform}) at {AGENT_WEBHOOK_URL}...")
        
        agent_start_time = time.time()
        agent_response = requests.post(
            AGENT_WEBHOOK_URL, 
            json=payload, 
            timeout=60, 
            verify=False
        )
        agent_response.raise_for_status() 
        
        response_data = agent_response.json()
        if isinstance(response_data, list):
            response_data = response_data[0]
        
        actual_agent_response = response_data.get("output") or response_data.get("text")
        
        print(f"🤖 AI Answer: {actual_agent_response}")

        if not actual_agent_response:
            actual_agent_response = "No response received from Agent."
        
        agent_end_time = time.time()
        print(f"✅ AI Agent responded in {round(agent_end_time - agent_start_time, 2)}s")

        # 5. Run Metrics
        print("⚖️ Running DeepEval metrics...")
        metric_start_time = time.time()

        passed, details = run_all_metrics(
            workflow_data, 
            actual_agent_response, 
            expected_qa_answer, 
            user_test_input
        )
        
        metric_end_time = time.time()
        execution_duration = round(metric_end_time - metric_start_time, 2)

        print(f"📊 Metrics completed in {execution_duration}s. Result: {'PASS' if passed else 'FAIL'}")
        
    except Exception as e:
        passed = False
        execution_duration = 0
        details = f"**System Error**: {str(e)}"
        print(f"❌ Error: {e}")

    # 6. Send Final Notification
    mention_target = f"<@&{role_id}>" if passed else f"<@{user_id}>"
    payload_discord = {
        "status": "pass" if passed else "fail",
        "builder_name": builder_github_username,
        "mention_target": mention_target,
        "test_results": details,
        "execution_time": f"{execution_duration}s" 
    }

    print(f"📡 Sending results to Discord...")
    try:
        if NOTIFICATION_WEBHOOK_URL:
            requests.post(NOTIFICATION_WEBHOOK_URL, json=payload_discord, timeout=30, verify=False)
        else:
            print("❌ Error: NOTIFICATION_WEBHOOK_URL is missing.")
    except Exception as e:
        print(f"❌ Notification failed: {e}")

if __name__ == "__main__":
    main()
