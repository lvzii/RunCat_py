import time
import multiprocessing
import os

def burn():
    while True:
        pass

def burn_cpu(target_util=80, duration=10):
    cpu_count = os.cpu_count()
    burn_count = int(cpu_count * target_util / 100)
    procs = []
    for _ in range(burn_count):
        p = multiprocessing.Process(target=burn)
        p.start()
        procs.append(p)
    print(f"已启动 {burn_count} 个进程，占用率约 {target_util}%")
    time.sleep(duration)
    for p in procs:
        p.terminate()
    print("结束。")

if __name__ == "__main__":
    print("开始占用CPU 10秒...")
    burn_cpu(target_util=80, duration=10)