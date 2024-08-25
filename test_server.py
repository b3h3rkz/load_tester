import asyncio
import aiohttp
import time
import json

async def send_request(session, url, data):
    try:
        async with session.post(url, json=data) as response:
            return await response.json()
    except Exception as e:
        print(f"Error in request: {str(e)}")
        return None

async def query_all_logs(session, url):
    data = {
        "action": "query_all"
    }
    return await send_request(session, url, data)

async def run_test():
    url = 'http://localhost:54321'
    
    async with aiohttp.ClientSession() as session:
        print("Querying all logs...")
        query_start_time = time.time()
        
        query_result = await query_all_logs(session, url)
        
        query_end_time = time.time()
        query_total_time = query_end_time - query_start_time
        
        if query_result and 'logs' in query_result:
            fetched_logs_count = len(query_result['logs'])
            print(f"\nQuery All Logs Test Results:")
            print(f"Total time: {query_total_time:.4f} seconds")
            print(f"Fetched logs count: {fetched_logs_count}")
            print(f"Logs fetched per second: {fetched_logs_count / query_total_time:.2f}")
        else:
            print("Error: Failed to fetch logs or no logs returned")
            if query_result:
                print(f"Server response: {json.dumps(query_result, indent=2)}")

if __name__ == "__main__":
    asyncio.run(run_test())