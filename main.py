import os
import requests
import json
import time  
import config
from metrics import run_all_metrics

def main():
    print("🚀 Script started successfully!")

    builder_github_username = os.getenv("GITHUB_ACTOR", "Unknown_Builder")
    user_id = config.USER_MAP.get(builder_github_username, config.DEVOPS_ROLE_ID)
    role_id = config.DEVOPS_ROLE_ID 

    workflow_path = "workflows/ai_agent_workflow.json"
    if not os.path.exists(workflow_path):
        print(f"❌ ERROR: Cannot find {workflow_path}.")
        return

    passed = False
    details = ""
    execution_duration = 0

    try:
        with open(workflow_path, 'r', encoding="utf-8") as f:
            workflow_data = json.load(f)
        
        payload = {"query": "Explain the system purpose."}
        response = requests.post(config.N8N_WEBHOOK_URL, json=payload)

        if response.status_code == 200:
            actual_agent_response = response.json().get("output", "No response")
            expected_qa_answer = (
                "This system serves as a multi-functional tool that uses specific "
                "functions and tools to perform various tasks. It allows simultaneous "
                "operation of different tools and functions that are designed to work in parallel."
            )

            start_time = time.time()
            passed, details = run_all_metrics(workflow_data, actual_agent_response, expected_qa_answer)
            end_time = time.time()
            
            execution_duration = round(end_time - start_time, 2)

            if execution_duration > 10.0:
                details += f"\n⚠️ **Warning**: High latency ({execution_duration}s)"

            print(f"📊 Metrics completed in {execution_duration}s. Result: {'PASS' if passed else 'FAIL'}")
        else:
            print(f"❌ n8n Trigger Failed: {response.status_code}")
            passed = False
            details = f"n8n Trigger Failed with status: {response.status_code}"

    except Exception as e:
        passed = False
        details = f"System Error: {str(e)}"
        print(f"❌ Error during metrics: {e}")

    # 2. Mentions
    mention_target = f"<@&{role_id}>" if passed else f"<@{user_id}>"

    # 3. Final Payload
    final_payload = {
        "status": "pass" if passed else "fail",
        "builder_name": builder_github_username,
        "mention_target": mention_target,
        "test_results": details,
        "execution_time": f"{execution_duration}s" 
    }

    print(f"📡 Sending Results to Discord via n8n...")
    
    

    try:
        final_response = requests.post(config.N8N_WEBHOOK_URL, json=final_payload, timeout=30)
        print(f"✅ Final Result Sent: {final_response.status_code}")
        
        if not passed:
            exit(1)
            
    except Exception as e:
        print(f"❌ Network Error sending final result: {e}")
        exit(1)

if __name__ == "__main__":
    main()
