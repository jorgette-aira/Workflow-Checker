from telethon.sync import TelegramClient
from telethon.sessions import StringSession

API_ID = 36900497 
API_HASH = '53febe3927a475639c9ac9646a51a984'

print("Initializing StringSession...")

with TelegramClient(StringSession(), API_ID, API_HASH) as client:
    print("\n✅ Login successful! Here is your StringSession token:\n")
    print(client.session.save())
    print("\n⚠️ COPY the string above. Treat it like a password and DO NOT share it!")
