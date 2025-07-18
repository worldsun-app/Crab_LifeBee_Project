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

    # 等一下讓網頁載入、JS 執行
    time.sleep(3)
    wait = WebDriverWait(driver, 10)
    actions = ActionChains(driver)

    # 等 tbody 本身出現
    tbody = wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, ".ant-table-tbody.ng-star-inserted")
    ))

    # 找出裡面所有的 row（tr）或你定義的 case 元素
    cases = tbody.find_elements(By.CSS_SELECTOR, "tr")  # 或者更精準的 class: ".ant-table-row"

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
        time.sleep(random.uniform(2, 4))
        api_request = None
        for req in driver.requests:
            if req.url.startswith("https://api.lifebee.tech/app/v3/underwriting/pending-list"):
                api_request = req
                break
            else:
                continue

        raw_body = api_request.response.body
        text     = raw_body.decode('utf-8')
        api_json = json.loads(text)
        fetch_and_compare(api_json)
        close_button = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR,'.anticon.anticon-close.ng-star-inserted')
            ))
        close_button.click()
        time.sleep(random.uniform(2, 4))
    driver.quit()






