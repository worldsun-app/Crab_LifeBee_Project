import json, hashlib, time
import requests
from deepdiff import DeepDiff
from apscheduler.schedulers.blocking import BlockingScheduler
from crab_driver import get_chrome_driver
from dotenv import load_dotenv
import os

load_dotenv()
bot_token = os.getenv("Bot_token")
chat_id = os.getenv("chat_id")

def send_telegram(msg: str):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": msg}
    requests.post(url, json=payload).raise_for_status()


HEADERS = get_chrome_driver()
API_URL = "https://api.lifebee.tech/app/v3/message/center"

prev_data = None

def fetch_and_compare():
    global prev_data
    # 1. 呼叫 API
    resp = requests.get(API_URL, headers=HEADERS)
    resp.raise_for_status()
    new_data = resp.json()

    print("API 回應:", json.dumps(new_data, indent=2, ensure_ascii=False))

    # 2. 第一次只存不比對
    if prev_data is None:
        prev_data = new_data
        print("第一次抓取完成，暫存結果。")
        return

    # 3. 用 DeepDiff 精確找差異
    diff = DeepDiff(prev_data, new_data, ignore_order=True, include_paths=["root['data'][*]['content']"])
    if diff:
        print("偵測到差異：", diff)
        send_telegram(f"🔔 有更新！差異內容：\n```json\n{json.dumps(diff, indent=2, ensure_ascii=False)}```")
        prev_data = new_data
    else:
        print("API 無變動。")
        # send_telegram("✅ API 無變動。")

if __name__ == "__main__":
    # 啟動時立刻執行一次
    fetch_and_compare()

    # 每 5 分鐘執行一次
    scheduler = BlockingScheduler()
    scheduler.add_job(fetch_and_compare, 'interval', minutes=0.5)
    scheduler.start()