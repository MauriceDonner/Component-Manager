import subprocess
import platform
import concurrent.futures

def ping(ip):
    param = "-n" if platform.system().lower() == "windows" else "-c"
    command = ["ping", param, "1", "-w", "500", ip]  # 500ms timeout
    result = subprocess.run(command, stdout=subprocess.DEVNULL)
    return ip if result.returncode == 0 else None

def ping_sweep(subnet="127.0.0.", start=1, end=3):
    ips = [f"{subnet}{i}" for i in range(start, end + 1)]
    alive = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        results = executor.map(ping, ips)
        for result in results:
            if result:
                alive.append(result)
    return alive

# Example:
print("Online:", ping_sweep())