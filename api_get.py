import json, hashlib, time
import requests
from deepdiff import DeepDiff
from apscheduler.schedulers.blocking import BlockingScheduler
from crab_driver import get_chrome_driver
from crab_new_case import get_new_case_driver
from dotenv import load_dotenv
import os

load_dotenv()
bot_token = os.getenv("Bot_token")
chat_id = os.getenv("chat_id")


API_URL = "https://api.lifebee.tech/app/v3/message/center"
prev_map = None

def send_telegram(msg: str):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": msg}
    requests.post(url, json=payload).raise_for_status()

def get_content_map(api_json):
    
    data = api_json.get('data', [])
    if not data:
        return {}

    first = data[0]
    # message-center 格式
    if 'type' in first and 'content' in first:
        return { item['type']: item.get('content') for item in data }

    # pending-list 格式
    if 'id' in first and 'remark' in first:
        return {
            # 这里用 id 当 key，也可以用 underwritingNo, pendingNo 等字段
            str(item['id']): item.get('remark')
            for item in data
        }

    return {
        json.dumps(item, sort_keys=True): json.dumps(item, ensure_ascii=False)
        for item in data
    }
    

def fetch_and_compare(api_json):
    global prev_map
    # 1. 呼叫 API

    new_map = get_content_map(api_json)

    # 2. 第一次只存不比對
    if prev_map is None:
        prev_map = new_map
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



def job_all():
    """
    每次完整流程：
     1) get_chrome_driver -> (HEADERS, driver)
     2) message_center 比對
     3) pending_list 比對
     4) driver.quit()
    """
    print("=== 開始新一輪監控 ===")
    HEADERS, driver = get_chrome_driver()
    try:
        # 2) 處理 message_center
        print("▶ 執行 message_center 檢查")
        resp = requests.get(API_URL, headers=HEADERS)
        resp.raise_for_status()
        fetch_and_compare(resp.json())  

        # 3) 處理 pending-list
        print("▶ 執行 pending-list 檢查")
        get_new_case_driver(driver)
    finally:
        print("▶ 本輪結束，關閉瀏覽器")
        driver.quit()


if __name__ == "__main__":

    job_all()

    # 排程：之後每 5 分鐘執行一次
    scheduler = BlockingScheduler()
    scheduler.add_job(job_all, 'interval', minutes=5)
    print(">>> 排程啟動，每 5 分鐘執行一次，按 Ctrl+C 停止")
    scheduler.start()