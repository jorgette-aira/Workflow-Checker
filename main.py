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

def get_execution_result(execution_id, headers):
    N8N_BASE_URL = "https://jorgette.tail3679cb.ts.net/api/v1"
    url = f"{N8N_BASE_URL}/executions/{execution_id}"
    
    time.sleep(8) 
    
    try:
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        data = response.json()
        
        result_data = data.get("data", {}).get("resultData", {}).get("runData", {})
        
        for node_name, runs in result_data.items():
            if "Agent" in node_name or "Reply" in node_name:
                return runs[0].get("data", {}).get("main", [{}])[0][0].get("json", {}).get("output")
    except Exception as e:
        print(f"⚠️ Could not fetch execution history: {e}")
    return None

def main():
    print("🚀 Script started successfully!")

    N8N_API_KEY = os.getenv("N8N_API_KEY")
    WORKFLOW_ID = os.getenv("N8N_WORKFLOW_ID")
    WEBHOOK_URL = os.getenv("N8N_AGENT_WEBHOOK_URL")
    NOTIFICATION_URL = os.getenv("N8N_WEBHOOK_URL", config.N8N_WEBHOOK_URL)
    
    platform = os.getenv("PLATFORM_TYPE", "telegram") 
    builder_name = os.getenv("GITHUB_ACTOR", "Unknown_Builder")
    
    user_test_input = "What happens if the shuttlecock lands outside the boundary lines?"
    expected_answer = "If the shuttlecock lands outside the boundary lines, it is a 'fault.' The opponent wins the rally and earns a point."

    if platform == "telegram":
        payload = {
            "message": {
                "text": user_test_input,
                "from": {"id": 12345, "first_name": "Tester", "is_bot": False},
                "chat": {"id": 12345},
                "date": int(time.time()),
                "message_id": 999
            }
        }
    elif platform in ["messenger", "instagram"]:
        payload = {"entry": [{"messaging": [{"message": {"text": user_test_input}}]}]}
    else:
        payload = {"prompt": user_test_input}

    try:
        workflow_path = "workflows/ai_agent_workflow.json"
        with open(workflow_path, 'r', encoding="utf-8") as f:
            workflow_data = json.load(f)

        agent_start_time = time.time()
        headers = {"X-N8N-API-KEY": N8N_API_KEY, "Content-Type": "application/json"}

        if N8N_API_KEY and WORKFLOW_ID:
            print(f"📡 Method: n8n API Mimic (Workflow #{WORKFLOW_ID})")
            api_url = f"https://jorgette.tail3679cb.ts.net/api/v1/workflows/{WORKFLOW_ID}/run"
            
            response = requests.post(api_url, json={"data": payload}, headers=headers, timeout=60, verify=False)
            response.raise_for_status()
            result = response.json()
            
            actual_response = result.get("data", {}).get("output") or result.get("data", {}).get("text")
            
            if not actual_response and "id" in result:
                print(f"⏳ Waiting for AI Agent to finish (Execution ID: {result['id']})...")
                actual_response = get_execution_result(result["id"], headers)

        elif WEBHOOK_URL:
            print(f"📡 Method: Webhook Trigger ({WEBHOOK_URL})")
            response = requests.post(WEBHOOK_URL, json=payload, timeout=60, verify=False)
            response.raise_for_status()
            result = response.json()
            if isinstance(result, list): result = result[0]
            actual_response = result.get("output") or result.get("text")

        else:
            print("❌ ERROR: Required Environment Variables are missing.")
            return

        if not actual_response:
            actual_response = "No response received from Agent."

        print(f"🤖 AI Answer: {actual_response}")
        agent_duration = round(time.time() - agent_start_time, 2)

        print(f"⚖️ Running metrics (Total time: {agent_duration}s)...")
        passed, details = run_all_metrics(workflow_data, actual_response, expected_answer, user_test_input)

    except Exception as e:
        passed, details = False, f"**System Error**: {str(e)}"
        print(f"❌ Error: {e}")

    user_id = config.USER_MAP.get(builder_name, config.DEVOPS_ROLE_ID)
    payload_discord = {
        "status": "pass" if passed else "fail",
        "mention_target": f"<@&{config.DEVOPS_ROLE_ID}>" if passed else f"<@{user_id}>",
        "test_results": details,
        "builder_name": builder_name
    }

    if NOTIFICATION_URL:
        requests.post(NOTIFICATION_URL, json=payload_discord, timeout=10, verify=False)
        print("✅ Notification sent.")

if __name__ == "__main__":
    main()
