import os
import time
import asyncio
import config
import requests
from dotenv import load_dotenv
from telethon import TelegramClient, events
from metrics import run_all_metrics

load_dotenv()

# Environment Variables
API_ID = int(os.getenv("TELEGRAM_API_ID", 0))
API_HASH = os.getenv("TELEGRAM_API_HASH")
BOT_USERNAME = os.getenv("TELEGRAM_BOT_USERNAME")
NOTIFICATION_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", config.N8N_WEBHOOK_URL)

builder_github_username = os.getenv("GITHUB_ACTOR", "Unknown_Builder")
user_id = config.USER_MAP.get(builder_github_username, config.DEVOPS_ROLE_ID)
role_id = config.DEVOPS_ROLE_ID 

# Test Data
USER_TEST_INPUT = "How many players can play in badminton?"
EXPECTED_QA_ANSWER = "If the shuttlecock lands outside the boundary lines, it is a 'fault.' The opponent wins the rally and earns a point."

async def run_telegram_test():
    print("🚀 Starting True End-to-End Telegram Test...")
    
    # Initialize the Telegram Client (saves login to 'qa_session.session')
    client = TelegramClient('qa_session', API_ID, API_HASH)
    await client.start()
    
    print(f"✅ Logged into Telegram successfully. Pinging {BOT_USERNAME}...")
    
    # A Future to hold the bot's response
    bot_response_future = asyncio.Future()

    # Event listener: Watch for a new message from the Bot
    @client.on(events.NewMessage(chats=BOT_USERNAME))
    async def handler(event):
        bot_reply = event.message.text
        bot_response_future.set_result(bot_reply)
        await client.disconnect() # Disconnect once we get the answer

    # Send the test question to the n8n bot
    start_time = time.time()
    await client.send_message(BOT_USERNAME, USER_TEST_INPUT)

    try:
        # Wait up to 60 seconds for n8n/AI to process and reply
        actual_agent_response = await asyncio.wait_for(bot_response_future, timeout=60.0)
    except asyncio.TimeoutError:
        actual_agent_response = "Timeout: No response received from Agent within 60 seconds."
        await client.disconnect()
        
    end_time = time.time()
    agent_duration = round(end_time - start_time, 2)
    print(f"🤖 Bot Answer: {actual_agent_response}")
    print(f"⏱️ Response Time: {agent_duration}s")
    
    return actual_agent_response, agent_duration

def main():
    # 1. Run the async Telegram test
    try:
        actual_agent_response, agent_duration = asyncio.run(run_telegram_test())
    except Exception as e:
        print(f"❌ Telegram Error: {e}")
        return

    # 2. Run Metrics
    print("\n⚖️ Running DeepEval metrics...")
    try:
        import json
        with open("workflows/ai_agent_workflow.json", 'r', encoding="utf-8") as f:
            workflow_data = json.load(f)

        passed, details = run_all_metrics(
            workflow_data, 
            actual_agent_response, 
            EXPECTED_QA_ANSWER, 
            USER_TEST_INPUT
        )
    except Exception as e:
        passed = False
        details = f"**Metrics Error**: {str(e)}"
        print(f"❌ Error: {e}")

    # 3. Send Final Notification
    mention_target = f"<@&{role_id}>" if passed else f"<@{user_id}>"
    payload_discord = {
        "status": "pass" if passed else "fail",
        "builder_name": builder_github_username,
        "mention_target": mention_target,
        "test_results": details,
        "execution_time": f"{agent_duration}s" 
    }

    print(f"\n📡 Sending results to Discord...")
    try:
        if NOTIFICATION_WEBHOOK_URL:
            requests.post(NOTIFICATION_WEBHOOK_URL, json=payload_discord, timeout=30, verify=False)
    except Exception as e:
        print(f"❌ Notification failed: {e}")

if __name__ == "__main__":
    main()
