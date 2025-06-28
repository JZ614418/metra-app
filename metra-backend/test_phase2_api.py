import asyncio
import httpx
import json
import os

# API base URL
BASE_URL = "http://localhost:8000/api/v1"

# Test credentials
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpassword"

async def test_phase2_api():
    async with httpx.AsyncClient() as client:
        print("=== Testing Phase 2 API ===\n")
        
        # 1. Login
        print("1. Testing login...")
        login_response = await client.post(
            f"{BASE_URL}/auth/login",
            data={
                "username": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.text}")
            return
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print(f"✅ Login successful! Token: {token[:20]}...\n")
        
        # 2. Create conversation
        print("2. Creating conversation...")
        conv_response = await client.post(
            f"{BASE_URL}/conversations",
            headers=headers,
            json={"title": "Test Conversation"}
        )
        
        if conv_response.status_code != 200:
            print(f"❌ Create conversation failed: {conv_response.text}")
            return
        
        conversation = conv_response.json()
        conv_id = conversation["id"]
        print(f"✅ Conversation created! ID: {conv_id}\n")
        
        # 3. Send message
        print("3. Sending message...")
        message_content = "I want to build an AI model that can classify customer reviews as positive or negative sentiment."
        
        # Check if OPENAI_API_KEY is set
        if not os.getenv("OPENAI_API_KEY"):
            print("⚠️  OPENAI_API_KEY not set. Skipping message test.")
            print("   Set it with: export OPENAI_API_KEY='your-key-here'")
        else:
            msg_response = await client.post(
                f"{BASE_URL}/conversations/{conv_id}/messages",
                headers=headers,
                json={
                    "content": message_content,
                    "role": "user"
                }
            )
            
            if msg_response.status_code != 200:
                print(f"❌ Send message failed: {msg_response.text}")
            else:
                message = msg_response.json()
                print(f"✅ Message sent and AI replied!")
                print(f"   AI Response: {message['content'][:100]}...\n")
        
        # 4. List conversations
        print("4. Listing conversations...")
        list_response = await client.get(
            f"{BASE_URL}/conversations",
            headers=headers
        )
        
        if list_response.status_code != 200:
            print(f"❌ List conversations failed: {list_response.text}")
            return
        
        conversations = list_response.json()
        print(f"✅ Found {len(conversations)} conversation(s)")
        for conv in conversations[:3]:
            print(f"   - {conv['title'] or 'Untitled'} (ID: {conv['id']}, Messages: {conv['message_count']})")
        
        print("\n=== All tests completed! ===")

if __name__ == "__main__":
    asyncio.run(test_phase2_api()) 