import asyncio
import aiohttp
import time
import json
import random
import string
import statistics
import psutil
import platform
import cpuinfo

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

def generate_random_reference():
    length = random.randint(5, 20)
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

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

async def insert_logs(session, url, num_logs):
    tasks = []
    for _ in range(num_logs):
        reference = generate_random_reference()
        data = {
            "action": "insert",
            "reference": reference,
            "metadata": {
                "event": f"test_event_{reference}",
                "details": f"This is test log entry {reference}"
            }
        }
        tasks.append(send_request(session, url, data, f"insert_{reference}"))
    return await asyncio.gather(*tasks)

async def fetch_all_logs(session, url):
    data = {
        "action": "query_all"
    }
    return await send_request(session, url, data, "fetch_all")

async def run_test(num_logs, batch_size, max_concurrent):
    url = 'http://localhost:54321'
    
    system_info = get_system_info()
    print("System Information:")
    for key, value in system_info.items():
        print(f"{key}: {value}")
    print("\n" + "="*50 + "\n")

    async with aiohttp.ClientSession() as session:
        # Insert logs
        insert_start_time = time.time()
        successful_inserts = 0
        total_latency = 0
        latencies = []

        for batch_start in range(0, num_logs, batch_size):
            batch_end = min(batch_start + batch_size, num_logs)
            print(f"Inserting logs {batch_start} to {batch_end}...")
            
            tasks = []
            for i in range(0, batch_size, max_concurrent):
                end = min(i + max_concurrent, batch_size)
                tasks.append(insert_logs(session, url, end - i))

            batch_results = await asyncio.gather(*tasks)
            batch_results = [item for sublist in batch_results for item in sublist]  # Flatten results
            
            for response, latency in batch_results:
                if response is not None and response.get('success', False):
                    successful_inserts += 1
                    total_latency += latency
                    latencies.append(latency)

        insert_end_time = time.time()
        insert_total_time = insert_end_time - insert_start_time
        
        print(f"\nInsert Test Results:")
        print(f"Total time: {insert_total_time:.2f} seconds")
        print(f"Successful inserts: {successful_inserts}/{num_logs}")
        print(f"Inserts per second: {num_logs / insert_total_time:.2f}")

        # Fetch all logs
        print("\nFetching all logs...")
        fetch_start_time = time.time()
        fetch_response, fetch_latency = await fetch_all_logs(session, url)
        fetch_end_time = time.time()

        fetch_total_time = fetch_end_time - fetch_start_time
        fetched_logs_count = len(fetch_response.get('logs', [])) if fetch_response else 0

        print(f"\nFetch All Logs Test Results:")
        print(f"Total time: {fetch_total_time:.2f} seconds")
        print(f"Fetched logs count: {fetched_logs_count}")
        print(f"Fetch latency: {fetch_latency:.4f} seconds")

    # Insert latency statistics
    if latencies:
        print(f"\nInsert Latency Statistics (seconds):")
        print(f"Min: {min(latencies):.4f}")
        print(f"Max: {max(latencies):.4f}")
        print(f"Mean: {statistics.mean(latencies):.4f}")
        print(f"Median: {statistics.median(latencies):.4f}")
        print(f"95th percentile: {sorted(latencies)[int(len(latencies)*0.95)]:.4f}")
        print(f"99th percentile: {sorted(latencies)[int(len(latencies)*0.99)]:.4f}")

    # Error rate for inserts
    error_rate = (num_logs - successful_inserts) / num_logs * 100
    print(f"\nInsert Error rate: {error_rate:.2f}%")

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
    num_logs = 1_000_000  # 1 million logs to insert
    batch_size = 10_000  # Insert in batches of 10,000
    max_concurrent = 2000  # Maximum concurrent connections
    asyncio.run(run_test(num_logs, batch_size, max_concurrent))