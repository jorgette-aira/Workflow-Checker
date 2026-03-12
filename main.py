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

API_ID = int(os.getenv("TELEGRAM_API_ID", 0))
API_HASH = os.getenv("TELEGRAM_API_HASH")
BOT_USERNAME = os.getenv("TELEGRAM_BOT_USERNAME")
SESSION_STRING = os.getenv("TELEGRAM_SESSION", "")
NOTIFICATION_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", config.N8N_WEBHOOK_URL)

builder_github_username = os.getenv("GITHUB_ACTOR", "Unknown_Builder")
user_id = config.USER_MAP.get(builder_github_username, config.DEVOPS_ROLE_ID)
role_id = config.DEVOPS_ROLE_ID 

async def run_single_telegram_test(user_input):
    print("🚀 Starting Telegram Test...")

    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    await client.start()
    
    print(f"✅ Sending message to {BOT_USERNAME}...")
    start_time = time.time()
    
    async with client.conversation(BOT_USERNAME, timeout=60.0) as conv:
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

        actual_answer, agent_duration = asyncio.run(run_single_telegram_test(user_input))

        print("⚖️ Running DeepEval metrics...")

        try:
            with open("workflows/ai_agent_workflow.json", 'r', encoding="utf-8") as f:
                workflow_data = json.load(f)
        except Exception:
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
