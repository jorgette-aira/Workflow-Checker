import os
import requests
import json
import time  # New import for timing
import config
from metrics import run_all_metrics

def main():
    print("🚀 Script started successfully!")

    # 1. Setup metadata
    builder_github_username = os.getenv("GITHUB_ACTOR", "Unknown_Builder")
    user_id = config.USER_MAP.get(builder_github_username, config.DEVOPS_ROLE_ID)
    role_id = config.DEVOPS_ROLE_ID 

    workflow_path = "workflows/ai_agent_workflow.json"
    if not os.path.exists(workflow_path):
        print(f"❌ ERROR: Cannot find {workflow_path}.")
        return

    try:
        with open(workflow_path, 'r') as f:
            workflow_data = json.load(f)
        
        actual_agent_response = "Hello!"
        expected_qa_answer = "assistant Batangas" 

        # --- Performance Tracking Start ---
        start_time = time.time()
        passed, details = run_all_metrics(workflow_data, actual_agent_response, expected_qa_answer)
        end_time = time.time()
        
        execution_duration = round(end_time - start_time, 2)
        # ----------------------------------

        # Check if response time is too slow (e.g., > 10 seconds)
        if execution_duration > 10.0:
            details += f"\n⚠️ Warning: High latency ({execution_duration}s)"

        print(f"📊 Metrics completed in {execution_duration}s. Result: {'PASS' if passed else 'FAIL'}")
        
    except Exception as e:
        passed = False
        execution_duration = 0
        details = f"System Error: {str(e)}"
        print(f"❌ Error during metrics: {e}")

    # 2. Mentions
    mention_target = f"<@&{role_id}>" if passed else f"<@{user_id}>"

    # 3. Payload with Performance Data
    payload = {
        "status": "pass" if passed else "fail",
        "builder_name": builder_github_username,
        "mention_target": mention_target,
        "test_results": details,
        "execution_time": f"{execution_duration}s" # New field for n8n/Discord
    }

    print(f"📡 Triggering n8n: {config.N8N_WEBHOOK_URL}")

    try:
        response = requests.post(config.N8N_WEBHOOK_URL, json=payload, timeout=10)
        print(f"✅ n8n Response: {response.status_code}")
    except Exception as e:
        print(f"❌ Network Error: {e}")

if __name__ == "__main__":
    main()
