
import asyncio
import websockets
import json
import sys

async def test_connection():
    uri = "ws://localhost:8766"
    print(f"Connecting to {uri}...")
    try:
        async with websockets.connect(uri) as websocket:
            print("[SUCCESS] Connected to WebSocket server")
            
            # Wait for initial account info
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                print(f"[RX] Received: {data.get('type')}")
                if data.get('type') == 'account_info':
                     print("   -> Account Info Verified")
            except asyncio.TimeoutError:
                print("[WARN] No initial account info received within 5s")
            
            # Send Ping
            await websocket.send(json.dumps({"action": "ping"}))
            print("[TX] Sent PING")
            
            # Expect Pong
            try:
                pong = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"[RX] Received: {json.loads(pong)}")
                print("[TEST PASSED] Server is responsive")
            except asyncio.TimeoutError:
                print("[FAIL] No PONG received")
                
    except Exception as e:
        print(f"[FAIL] Connection failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_connection())
