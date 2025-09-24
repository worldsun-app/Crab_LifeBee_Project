import json, time, traceback
import requests
from apscheduler.schedulers.blocking import BlockingScheduler
from crab_driver import get_chrome_driver
from crab_new_case import get_new_case_driver
from dotenv import load_dotenv
import os
import threading

load_dotenv(override=True)
bot_token = os.getenv("Bot_token")
API_URL = "https://api.lifebee.tech/app/v3/message/center"
prev_map = None
def load_ids(env_key: str):
    raw = os.getenv(env_key, "").strip()
    if not raw:
        return []
    try:
        val = json.loads(raw)
    except json.JSONDecodeError:
        val = [x.strip() for x in raw.split(",") if x.strip()]
    if isinstance(val, (str, int)):
        val = [val]
    return [str(x) for x in val]
chat_id = load_ids("chat_id")

def send_telegram(msg: str, chat_ids=None):
    ids = chat_ids or chat_id
    if isinstance(ids, (str, int)):
        ids = [str(ids)]
    for cid in ids:
        try:
            requests.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={"chat_id": cid, "text": msg},
                timeout=10
            ).raise_for_status()
        except Exception as e:
            print(f"[TG Error] {cid}: {e}")

def get_content_map(api_json):
    data = api_json.get('data', [])
    if not data:
        return {}
    first = data[0]
    if 'type' in first and 'content' in first:
        return { item['type']: item.get('content') for item in data }
    if 'id' in first and 'remark' in first:
        return {
            str(item['id']): item.get('remark')
            for item in data
        }
    return {
        json.dumps(item, sort_keys=True): json.dumps(item, ensure_ascii=False)
        for item in data
    }

class Monitor:
    def __init__(self, account_config, interval_minutes=10):
        self.account = account_config['account']
        self.password = account_config['password']
        self.instance_code = account_config['instance_code'] 
        self.name = account_config.get('name', self.account) # Use name for logging
        self.interval = interval_minutes * 60
        self.prev_map = None # Each instance has its own prev_map

    def fetch_and_compare(self, api_json):
        new_map = get_content_map(api_json)
        if self.prev_map is None:
            self.prev_map = new_map
            print(f"[{self.name}] 第一次抓取完成，暫存結果。")
            return

        changes = {}
        for t, new_c in new_map.items():
            old_c = self.prev_map.get(t)
            if old_c != new_c:
                changes[t] = {"old": old_c, "new": new_c}
        removed = set(self.prev_map) - set(new_map)
        for t in removed:
            changes[t] = {"old": self.prev_map[t], "new": None}

        if changes:
            lines = []
            for t, v in changes.items():
                old = v["old"] or "<無>"
                new = v["new"] or "<無>"
                lines.append(f"{t}：\n  舊內容：{old}\n  新內容：{new}")
            text = f"🔔 [{self.account}] 發現變動：\n" + "\n\n".join(lines)
            print(text)
            send_telegram(text)
            self.prev_map = new_map
        else:
            print(f"[{self.name}] content 無任何變動。")

    def job_all(self):
        print(f"=== [{self.name}] 開始新一輪監控 ===")
        HEADERS, driver = get_chrome_driver(self.account, self.password, self.instance_code)
        try:
            print(f"▶ [{self.name}] 執行 message_center 檢查")
            resp = requests.get(API_URL, headers=HEADERS)
            resp.raise_for_status()
            self.fetch_and_compare(resp.json())

            print(f"▶ [{self.name}] 執行 pending-list 檢查")
            # We need to pass 'self' to the function to use the correct 'fetch_and_compare'
            get_new_case_driver(driver, self)
        finally:
            print(f"▶ [{self.name}] 本輪結束，關閉瀏覽器")
            # Note: get_new_case_driver already quits the driver, so we check if it's still alive
            try:
                driver.quit()
            except Exception:
                pass 

    def safe_job_all_loop(self):
        while True:
            attempt = 0
            while True:
                attempt += 1
                try:
                    if attempt > 1:
                        print(f"🔄 [{self.name}] 重試第 {attempt} 次 job_all()")
                    self.job_all()
                    break
                except Exception:
                    err = traceback.format_exc()
                    print(f"❌ [{self.name}] job_all() 第 {attempt} 次失敗，原因：\n{err}")
                    time.sleep(5)
            
            print(f">>> [{self.name}] 本輪監控完成，將於 {self.interval / 60} 分鐘後再次執行。")
            time.sleep(self.interval)


if __name__ == "__main__":
    accounts_json = os.getenv("ACCOUNTS")
    if not accounts_json:
        raise ValueError("環境變數 ACCOUNTS 未設定或為空！") 
    try:
        accounts = json.loads(accounts_json)
    except json.JSONDecodeError:
        raise ValueError("ACCOUNTS 的 JSON 格式不正確！")
    threads = []
    for acc_config in accounts:
        monitor = Monitor(acc_config)
        thread = threading.Thread(target=monitor.safe_job_all_loop, daemon=True)
        threads.append(thread)
        thread.start()
        time.sleep(10) #  staggered start

    print(f">>> 所有 {len(threads)} 個帳號監控已啟動，程式將在背景執行。")
    
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        print(">>> 收到停止訊號，程式即將關閉。")