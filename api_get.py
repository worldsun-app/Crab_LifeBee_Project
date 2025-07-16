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


HEADERS = get_chrome_driver()
API_URL = "https://api.lifebee.tech/app/v3/message/center"

prev_map = None

def send_telegram(msg: str):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": msg}
    requests.post(url, json=payload).raise_for_status()

def get_content_map(api_json):
    """
    將原始 JSON 的 data list 轉成 { type: content } 的字典
    """
    return {
        item['type']: item.get('content')
        for item in api_json.get('data', [])
    }

def fetch_and_compare():
    global prev_map
    # 1. 呼叫 API
    resp = requests.get(API_URL, headers=HEADERS)
    resp.raise_for_status()
    new_data = resp.json()

    new_map = get_content_map(new_data)

    # 2. 第一次只存不比對
    if prev_map is None:
        prev_map = new_data
        print("第一次抓取完成，暫存結果。")
        return
    
    changes = {}
    # 檢查新增或變更
    for t, new_c in new_map.items():
        old_c = prev_map.get(t)
        if old_c != new_c:
            changes[t] = {"old": old_c, "new": new_c}
    # 檢查被移除的 type
    removed = set(prev_map) - set(new_map)
    for t in removed:
        changes[t] = {"old": prev_map[t], "new": None}

    if changes:
        # 依序把每個變動的 type 和新舊 content 轉成「Type：old → new」格式
        lines = []
        for t, v in changes.items():
            old = v["old"] or "<無>"
            new = v["new"] or "<無>"
            lines.append(f"{t}：\n  舊內容：{old}\n  新內容：{new}")
        # 最後把所有行合成一個字串
        text = "🔔 發現變動：\n" + "\n\n".join(lines)
        print(text)
        send_telegram(text)
        prev_map = new_map
    else:
        print("content 無任何變動。")


    # 3. 用 DeepDiff 精確找差異
    # diff_full = DeepDiff(prev_data, new_data, ignore_order=True)
    # print("完整 diff：", diff_full)
    # diff = DeepDiff(prev_data, new_data, ignore_order=True, include_paths=["root['data'][*]['content']"])
    # if diff_full:
    #     print("偵測到差異：", diff_full)
    #     send_telegram(f"🔔 有更新！差異內容：\n```json\n{json.dumps(diff_full, indent=2, ensure_ascii=False)}```")
    #     prev_data = new_data
    # else:
    #     print("API 無變動。")
    #     # send_telegram("✅ API 無變動。")

if __name__ == "__main__":
    # 啟動時立刻執行一次
    fetch_and_compare()

    # 每 5 分鐘執行一次
    scheduler = BlockingScheduler()
    scheduler.add_job(fetch_and_compare, 'interval', minutes=10)
    scheduler.start()