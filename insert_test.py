import asyncio
import aiohttp
import time
import json
import random
import string

async def send_request(session, url, data):
    try:
        async with session.post(url, json=data) as response:
            return await response.json()
    except Exception as e:
        print(f"Error in request: {str(e)}")
        return None

def generate_random_reference():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

async def insert_log(session, url):
    reference = generate_random_reference()
    data = {
        "action": "insert",
        "reference": reference,
        "metadata": {
            "event": f"test_event_{reference}",
            "details": f"This is test log entry {reference}"
        }
    }
    return await send_request(session, url, data)

async def run_test(num_logs):
    url = 'http://localhost:54321'
    
    async with aiohttp.ClientSession() as session:
        print(f"Inserting {num_logs} logs...")
        start_time = time.time()
        
        tasks = [insert_log(session, url) for _ in range(num_logs)]
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        successful_inserts = sum(1 for r in results if r and r.get('success', False))
        
        print(f"\nTest Results:")
        print(f"Total time: {total_time:.2f} seconds")
        print(f"Successful inserts: {successful_inserts}/{num_logs}")
        print(f"Inserts per second: {num_logs / total_time:.2f}")
        
        if successful_inserts < num_logs:
            print(f"Failed inserts: {num_logs - successful_inserts}")

if __name__ == "__main__":
    num_logs = 100000  # Number of logs to insert
    asyncio.run(run_test(num_logs))