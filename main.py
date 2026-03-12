import os
import time
import asyncio
import json
import random
import traceback 
import config
import requests
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession
from metrics import run_all_metrics

load_dotenv()

# Core Configuration
API_ID = int(os.getenv("TELEGRAM_API_ID", 0))
API_HASH = os.getenv("TELEGRAM_API_HASH")
SESSION_STRING = os.getenv("TELEGRAM_SESSION", "")
NOTIFICATION_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", config.N8N_WEBHOOK_URL)

builder_github_username = os.getenv("GITHUB_ACTOR", "Unknown_Builder")
user_id = config.USER_MAP.get(builder_github_username, config.DEVOPS_ROLE_ID)
role_id = config.DEVOPS_ROLE_ID 

# 👇 NEW: Dynamic GitHub Action Inputs (with safe local fallbacks)
TRIGGER_TYPE = os.getenv("DYNAMIC_TRIGGER_TYPE", "Telegram")
TARGET_ENDPOINT = os.getenv("DYNAMIC_TARGET_ENDPOINT", os.getenv("TELEGRAM_BOT_USERNAME"))
WORKFLOW_PATH = os.getenv("DYNAMIC_WORKFLOW_FILE", "workflows/ai_agent_workflow.json")


# ---------------------------------------------------------
# 1. TELEGRAM TEST FUNCTION
# ---------------------------------------------------------
async def run_single_telegram_test(user_input, target_bot):
    print(f"🚀 Starting Telegram Test targeting {target_bot}...")

    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    await client.start()
    
    print(f"✅ Sending message to {target_bot}...")
    start_time = time.time()
    
    async with client.conversation(target_bot, timeout=60.0) as conv:
        await conv.send_message(user_input)
        try:
            response = await conv.get_response()
            actual_answer = response.text
        except asyncio.TimeoutError:
            actual_answer = "Timeout: No response from Agent within 60 seconds."
            
    duration = round(time.time() - start_time, 2)
    print(f"🤖 Bot Reply ({duration}s): {actual_answer}\n")
    
    await client.disconnect()
    return actual_answer, duration


# ---------------------------------------------------------
# 2. WEBHOOK TEST FUNCTION (NEW)
# ---------------------------------------------------------
def run_single_webhook_test(user_input, webhook_url):
    print(f"🚀 Sending POST request to Webhook: {webhook_url}")
    start_time = time.time()
    
    try:
        # NOTE: If your n8n workflow expects a different JSON key instead of "chatInput", change it here!
        payload = {"chatInput": user_input} 
        response = requests.post(webhook_url, json=payload, timeout=60)
        response.raise_for_status()
        
        try:
            response_data = response.json()
            # Try to grab "output", but fall back to the raw text if n8n returns a different format
            actual_answer = response_data.get("output", response.text) 
        except ValueError:
            actual_answer = response.text
            
    except Exception as e:
        actual_answer = f"Webhook Error: {e}"
        
    duration = round(time.time() - start_time, 2)
    print(f"🤖 Webhook Reply ({duration}s): {actual_answer}\n")
    return actual_answer, duration


# ---------------------------------------------------------
# 3. MAIN CONTROLLER
# ---------------------------------------------------------
def main():
    passed = False
    error_type = "system"
    details = "Unknown system crash."
    agent_duration = 0

    try:
        with open("test_cases.json", "r", encoding="utf-8") as f:
            test_cases = json.load(f)
            
        if not test_cases:
            raise ValueError("test_cases.json is empty.")
            
        selected_test = random.choice(test_cases)
        user_input = selected_test.get("input") 
        expected_answer = selected_test.get("expected_output")
        
        print(f"🎲 Randomly selected question: '{user_input}'")
        print(f"🎯 Target Endpoint: {TARGET_ENDPOINT} ({TRIGGER_TYPE})")
        print(f"📂 Evaluating against: {WORKFLOW_PATH}")

        # 👇 NEW: Router logic to direct traffic based on the UI selection
        
        if TRIGGER_TYPE == "Telegram":
            actual_answer, agent_duration = asyncio.run(run_single_telegram_test(user_input, TARGET_ENDPOINT))
        elif TRIGGER_TYPE == "Webhook":
            actual_answer, agent_duration = run_single_webhook_test(user_input, TARGET_ENDPOINT)
        else:
            raise ValueError(f"Unknown TRIGGER_TYPE selected: {TRIGGER_TYPE}")

        print("⚖️ Running DeepEval metrics...")

        try:
            # 👇 NEW: Loading the dynamic workflow file
            with open(WORKFLOW_PATH, 'r', encoding="utf-8") as f:
                workflow_data = json.load(f)
        except Exception as e:
            print(f"⚠️ Could not load {WORKFLOW_PATH}: {e}")
            workflow_data = {} 

        passed, metric_details = run_all_metrics(
            workflow_data, 
            actual_answer, 
            expected_answer, 
            user_input
        )
        
        details = metric_details

        if passed:
            error_type = "none"
        else:
            error_type = "metric"

    except Exception as e:
        print(f"🚨 SYSTEM CRASH: {e}")
        passed = False
        error_type = "system"
        crash_log = traceback.format_exc()
        details = f"**Fatal System Exception:**\n```python\n{crash_log}\n```"

    finally:
        mention_target = f"<@&{role_id}>" if passed else f"<@{user_id}>"
        
        payload_discord = {
            "status": "pass" if passed else "fail",
            "error_type": error_type,
            "builder_name": builder_github_username,
            "mention_target": mention_target,
            "test_results": details,
            "execution_time": f"{agent_duration}s" 
        }

        print(f"📡 Sending results to Discord...")
        if NOTIFICATION_WEBHOOK_URL:
            try:
                requests.post(NOTIFICATION_WEBHOOK_URL, json=payload_discord, timeout=30, verify=False)
                print("✅ Notification sent successfully to n8n.")
            except Exception as e:
                print(f"❌ Notification failed: {e}")

if __name__ == "__main__":
    main()
