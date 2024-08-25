import asyncio
import aiohttp
import time
import json
import psutil
import platform
import cpuinfo
from concurrent.futures import ThreadPoolExecutor

def get_system_info():
    try:
        cpu_info = cpuinfo.get_cpu_info()
        cpu_brand = cpu_info['brand_raw']
    except:
        cpu_brand = "Unable to retrieve CPU info"

    return {
        "OS": f"{platform.system()} {platform.release()}",
        "CPU": cpu_brand,
        "CPU Cores": psutil.cpu_count(logical=False),
        "CPU Threads": psutil.cpu_count(logical=True),
        "RAM": f"{psutil.virtual_memory().total / (1024 ** 3):.2f} GB",
        "Python Version": platform.python_version()
    }

async def send_request(session, url, data, request_id):
    start_time = time.time()
    try:
        async with session.post(url, json=data) as response:
            response_text = await response.text()
            end_time = time.time()
            latency = end_time - start_time
            return json.loads(response_text), latency
    except Exception as e:
        print(f"Error in request {request_id}: {str(e)}")
        return None, time.time() - start_time

async def fetch_all_logs(session, url, thread_id):
    data = {
        "action": "query_all"
    }
    return await send_request(session, url, data, f"fetch_all_thread_{thread_id}")

async def run_fetch_test(thread_id):
    url = 'http://localhost:54321'
    async with aiohttp.ClientSession() as session:
        return await fetch_all_logs(session, url, thread_id)

def thread_fetch(thread_id):
    return asyncio.run(run_fetch_test(thread_id))

async def run_test():
    system_info = get_system_info()
    print("System Information:")
    for key, value in system_info.items():
        print(f"{key}: {value}")
    print("\n" + "="*50 + "\n")

    num_threads = 8
    print(f"Fetching all logs using {num_threads} threads...")
    fetch_start_time = time.time()

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        results = list(executor.map(thread_fetch, range(num_threads)))

    fetch_end_time = time.time()
    fetch_total_time = fetch_end_time - fetch_start_time

    total_logs = 0
    total_latency = 0
    successful_fetches = 0

    for result, latency in results:
        if result is not None:
            total_logs += len(result.get('logs', []))
            total_latency += latency
            successful_fetches += 1

    avg_latency = total_latency / successful_fetches if successful_fetches > 0 else 0

    print(f"\nFetch All Logs Test Results:")
    print(f"Total time: {fetch_total_time:.2f} seconds")
    print(f"Total fetched logs count: {total_logs}")
    print(f"Average fetch latency: {avg_latency:.4f} seconds")
    print(f"Successful fetches: {successful_fetches}/{num_threads}")

    # System resource usage
    print("\nSystem Resource Usage:")
    cpu_percent = psutil.cpu_percent()
    memory_info = psutil.virtual_memory()
    print(f"CPU Usage: {cpu_percent}%")
    print(f"Memory Usage: {memory_info.percent}%")
    print(f"Available Memory: {memory_info.available / (1024 * 1024):.2f} MB")

    # Print system information again with the results
    print("\nSystem Information:")
    for key, value in system_info.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    asyncio.run(run_test())