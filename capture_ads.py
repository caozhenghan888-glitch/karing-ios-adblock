#!/usr/bin/env python3
"""
Karing 实时连接监听与广告源定位脚本
使用方式：
    python3 capture_ads.py --port 3057 --secret YOUR_SECRET
"""

import sys
import json
import asyncio
import argparse

try:
    import websockets
except ImportError:
    print("提示：需要 websockets 库 (pip install websockets 或 apk add py3-websockets)")
    sys.exit(1)

AD_KEYWORDS = [
    "ad", "track", "log", "stat", "pangolin", "toutiao", 
    "yfanads", "baertt", "jpush", "umeng", "gdt", "kuaishou"
]

async def monitor_logs(port, secret):
    url = f"ws://127.0.0.1:{port}/logs?level=info&token={secret}"
    print("[*] 请在手机上划掉 App 并重新打开，等待捕获广告域名...\n" + "="*50)

    # 自动重连：Karing 重启、内核切换或网络抖动断线时不退出，3 秒后接回
    attempt = 0
    while True:
        try:
            print(f"[*] 正在连接 Karing 日志流: ws://127.0.0.1:{port}")
            async with websockets.connect(url) as ws:
                attempt = 0
                print("[*] 已连接，监听中...（Ctrl+C 退出）")
                while True:
                    msg = await ws.recv()
                    try:
                        data = json.loads(msg)
                        payload = data.get("payload", "")
                        # 匹配外发出站或进站连接
                        if "inbound connection to" in payload or "outbound connection to" in payload:
                            target = payload.split("connection to ")[-1].strip()
                            # 高亮展示疑似广告域名
                            is_suspicious = any(k in target.lower() for k in AD_KEYWORDS)
                            prefix = "[🚨 疑似广告源]" if is_suspicious else "[直连/放行]"
                            print(f"{prefix} {target}")
                    except Exception:
                        pass
        except asyncio.CancelledError:
            raise
        except Exception as e:
            attempt += 1
            print(f"[!] 连接断开: {e}，3 秒后自动重连（第 {attempt} 次）")
            await asyncio.sleep(3)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Karing 广告嗅探工具")
    parser.add_argument("--port", type=int, default=3057, help="Karing 内核 API 端口")
    parser.add_argument("--secret", type=str, required=True, help="Karing API Secret")
    args = parser.parse_args()

    try:
        asyncio.run(monitor_logs(args.port, args.secret))
    except KeyboardInterrupt:
        print("\n[*] 已退出监听")
