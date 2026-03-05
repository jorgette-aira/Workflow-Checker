import os
import requests
import json
import time  
import config
from metrics import run_all_metrics

def main():
    print("🚀 Script started successfully!")

    # 1. Setup metadata
    builder_github_username = os.getenv("GITHUB_ACTOR", "Unknown_Builder")
    user_id = config.USER_MAP.get(builder_github_username, config.DEVOPS_ROLE_ID)
    role_id = config.DEVOPS_ROLE_ID 

    # Correcting the path to match your GitHub folder structure
    workflow_path = "workflows/ai_agent_workflow.json"
    if not os.path.exists(workflow_path):
        print(f"❌ ERROR: Cannot find {workflow_path}.")
        return

    try:
        with open(workflow_path, 'r', encoding="utf-8") as f:
            workflow_data = json.load(f)
        
        # FIX: Added 's' to requests and used the URL from config
        payload = {"query": "Explain the system purpose."}
        response = requests.post(config.N8N_WEBHOOK_URL, json=payload)

        if response.status_code == 200:
            # FIX: Ensure variable names match the run_all_metrics signature
            actual_agent_response = response.json().get("output", "No response from agent")
            expected_qa_answer = (
                "This system serves as a multi-functional tool that uses specific "
                "functions and tools to perform various tasks. It allows simultaneous "
                "operation of different tools and functions that are designed to work in parallel."
            )

            start_time = time.time()
            # FIX: Variables passed here must match the names defined above
            passed, details = run_all_metrics(workflow_data, actual_agent_response, expected_qa_answer)
            end_time = time.time()
            
            execution_duration = round(end_time - start_time, 2)

            if execution_duration > 10.0:
                details += f"\n⚠️ **Warning**: High latency ({execution_duration}s)"

            print(f"📊 Metrics completed in {execution_duration}s. Result: {'PASS' if passed else 'FAIL'}")
        else:
            print(f"❌ n8n Trigger Failed: {response.status_code}")
            return # Exit if we can't get an answer to test
            
    except Exception as e:
        passed = False
        execution_duration = 0
        details = f"System Error: {str(e)}"
        print(f"❌ Error during metrics: {e}")

    # 2. Mentions
    mention_target = f"<@&{role_id}>" if passed else f"<@{user_id}>"

    # 3. Payload for Discord via n8n
    final_payload = {
        "status": "pass" if passed else "fail",
        "builder_name": builder_github_username,
        "mention_target": mention_target,
        "test_results": details,
        "execution_time": f"{execution_duration}s" 
    }

    print(f"📡 Sending Results to Discord via n8n...")

    try:
        # Using a timeout to prevent the Action from hanging forever
        final_response = requests.post(config.N8N_WEBHOOK_URL, json=final_payload, timeout=30)
        print(f"✅ Final Result Sent: {final_response.status_code}")
        
        # CRITICAL: Exit with 1 if failed so GitHub Action shows a Red X
        if not passed:
            exit(1)
            
    except Exception as e:
        print(f"❌ Network Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
