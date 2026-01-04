"""
Test WebSocket connection to backend server
"""
import asyncio
import websockets
import json

async def test_connection():
    uri = "ws://localhost:8766"
    
    print("=" * 60)
    print("Testing WebSocket Connection to Backend")
    print("=" * 60)
    print(f"\nConnecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("[OK] Connected successfully!")
            
            # Test 1: Get account data
            print("\nTest 1: Requesting account data...")
            await websocket.send(json.dumps({
                "type": "get_account"
            }))
            
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(response)
            
            if data.get("type") == "account_data":
                print("[OK] Account data received")
                print(f"     Account: {data.get('account', {}).get('login', 'N/A')}")
                print(f"     Balance: ${data.get('account', {}).get('balance', 0):.2f}")
                print(f"     Server: {data.get('account', {}).get('server', 'N/A')}")
            else:
                print(f"[INFO] Response type: {data.get('type')}")
            
            # Test 2: Get positions
            print("\nTest 2: Requesting positions...")
            await websocket.send(json.dumps({
                "type": "get_positions"
            }))
            
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(response)
            
            if data.get("type") == "positions":
                positions = data.get("positions", [])
                print(f"[OK] Positions received: {len(positions)} open positions")
            else:
                print(f"[INFO] Response type: {data.get('type')}")
            
            print("\n" + "=" * 60)
            print("SUCCESS: Backend is working correctly!")
            print("=" * 60)
            
    except asyncio.TimeoutError:
        print("[FAIL] Timeout waiting for response")
        print("       Backend may be stuck or not processing messages")
        
    except websockets.exceptions.ConnectionRefused:
        print("[FAIL] Connection refused")
        print("       Backend server is not running on port 8766")
        
    except Exception as e:
        print(f"[FAIL] Error: {type(e).__name__}: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_connection())
