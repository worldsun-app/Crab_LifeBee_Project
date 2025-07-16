# Lifebee 訊息監控小爬蟲

## 專案介紹  
本專案透過 Selenium 自動化操作瀏覽器，模擬使用者登入 Lifebee 平台，取得內部 API 權杖後，定時呼叫訊息中心 API (`/app/v3/message/center`)，並使用 DeepDiff 比對前後回傳資料內容差異，當偵測到更新時立即透過 Telegram Bot 推播通知，讓您不用手動刷頁面，即可掌握最新消息。

---

## 功能特色  
- 🔑 **自動登入**：透過 `crab_driver.py` 自動完成帳號／密碼輸入、按鈕點擊、同意條款等所有步驟。  
- 📡 **定時抓取**：使用 APScheduler 每 30 秒（`minutes=0.5`）呼叫一次 API，並在程式啟動後立即執行第一次抓取。  
- 🔍 **精確比對**：利用 dict的方式，辨識content內容的變化。 
- 📲 **即時推播**：當有更新或無更新時，都會自動發送 Telegram 訊息到指定 Chat ID。  

---

## 環境需求  
- Python 版本：3.8 以上  
- Google Chrome 瀏覽器（對應版本的 ChromeDriver）  
- Linux / macOS / Windows 均可  

## 安裝與設定  

1. **Clone 專案**  
   ```bash
   git clone https://github.com/你的帳號/你的專案.git
   cd 你的專案

2. **建立虛擬環境**  
   ```bash
    python -m venv venv
    source venv/bin/activate      # macOS / Linux
    .\venv\Scripts\activate       # Windows PowerShell

3. **安裝套件**  
   ```bash
   pip install -r requirements.txt  

可依照.toml去安裝相依套件

## 執行方式
    python api_get.py

## 專案結構
```plaintext
.
├── api_get.py          # 主程式：呼叫 API、差異比對、Telegram 通知
├── crab_driver.py      # 瀏覽器自動化：登入並擷取 API 權杖
├── requirements.txt    # Python 相依套件清單
└── .env                # 環境變數：Bot token、Chat ID