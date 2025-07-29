from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

import time
import random
import json

def get_new_case_driver(driver):
    from api_get import fetch_and_compare
    driver.get("https://user.lifebee.tech/#/user/underwriting/underwriting-main")
    results = []

    # 等一下讓網頁載入、JS 執行
    time.sleep(3)
    wait = WebDriverWait(driver, 10)
    actions = ActionChains(driver)

    try:
        # 等待 tbody 元素出現
        tbody = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, ".ant-table-tbody.ng-star-inserted")
        ))
        # 找出 tbody 內所有的 row (tr)
        cases = tbody.find_elements(By.CSS_SELECTOR, "tr")

    except Exception as e:
        # 如果 tbody 沒有出現，記錄為沒有案例資料
        print(f"錯誤：未能找到 tbody 元素或 tbody 為空。錯誤訊息: {e}")
        results.append({
            'status': 'no_cases',
            'data': '未能找到案例列表的 tbody 元素或 tbody 為空。'
        })
        driver.quit()
        return results

    count = len(cases)

    # 逐一點擊
    for idx in range(count):
        driver.requests.clear()
        # 等 tbody 本身出現
        tbody = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, ".ant-table-tbody.ng-star-inserted")
        ))
        cases = tbody.find_elements(By.CSS_SELECTOR, "tr")

        # 找出裡面所有的 row（tr）或你定義的 case 元素
        case = cases[idx]
        # 滑鼠移到元素上再點
        actions.move_to_element(case) \
            .pause(random.uniform(0.1, 0.3)) \
            .click() \
            .perform()
        time.sleep(random.uniform(5, 10))
        api_request = None
        for req in driver.requests:
            if req.url.startswith("https://api.lifebee.tech/app/v3/underwriting/pending-list"):
                api_request = req
                break
            else:
                continue

        # raw_body = api_request.response.body
        # text     = raw_body.decode('utf-8')
        # api_json = json.loads(text)
        # fetch_and_compare(api_json)
        if api_request and api_request.response:
            try:
                raw_body = api_request.response.body
                text = raw_body.decode('utf-8')
                api_json = json.loads(text)
                fetch_and_compare(api_json) # 調用外部函數處理 API 資料
            except Exception as e:
                # 如果解碼或解析 JSON 失敗
                print(f"錯誤：解碼或解析 API 響應失敗。錯誤訊息: {e}")
        else:
            # 如果沒有捕獲到目標 API 請求，記錄為 nonetype
            print(f"無個案例的目標 API 請求。")

        try:
            close_button = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR,'.anticon.anticon-close.ng-star-inserted')
            ))
            close_button.click()
            time.sleep(random.uniform(2, 4))
        except Exception as e:
            print(f"無點擊關閉按鈕。元素不存在。")
    driver.quit()






