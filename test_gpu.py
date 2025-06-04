"""
集成显卡很难测试
"""

import torch


def burn_gpu(duration=10):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    x = torch.rand((4096, 4096), device=device)
    end_time = torch.cuda.Event(enable_timing=True)
    start_time = torch.cuda.Event(enable_timing=True)
    start_time.record()
    while True:
        y = torch.mm(x, x)
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        end_time.record()
        if start_time.elapsed_time(end_time) > duration * 1000:
            break


if __name__ == "__main__":
    print("开始让GPU高负载运算...")
    burn_gpu(duration=10)
    print("结束。")
