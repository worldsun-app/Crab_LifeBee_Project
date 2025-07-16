from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time
import random
import tempfile
import shutil

def get_chrome_driver():
    temp_profile = tempfile.mkdtemp(prefix="selenium-profile-")
    options = webdriver.ChromeOptions()
    for arg in [
        "--headless",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--disable-extensions",
        "--disable-infobars",
        "--disable-software-rasterizer",
        "--disable-accelerated-2d-canvas"
    ]:
        options.add_argument(arg)
    options.add_argument(f"--user-data-dir={temp_profile}")
    # 如果想讓視窗保持打開，別用 headless；也可加 detach 讓程式結束後不關瀏覽器
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    service = Service(executable_path="/usr/bin/chromedriver")

    driver = webdriver.Chrome(service=Service(), options=options)
    driver.get("https://user.lifebee.tech/#/auth/instance-code")

    # 等一下讓網頁載入、JS 執行
    time.sleep(3)
    wait = WebDriverWait(driver, 10)
    actions = ActionChains(driver)

    # 等元素可輸入後再找
    input_el = wait.until(
    EC.element_to_be_clickable((By.CSS_SELECTOR,
        ".input-group.ant-input-affix-wrapper > input"))
    )
    input_el.clear()
    for ch in "The1Advisor":
        input_el.send_keys(ch)
        time.sleep(random.uniform(0.1, 0.3))  # 隨機延遲，像人在打字


    enter_btn = wait.until(
    EC.element_to_be_clickable((By.CSS_SELECTOR,
        "button.ant-btn.ant-btn-circle.ant-btn-icon-only"))
    )
    actions.move_to_element(enter_btn) \
        .pause(random.uniform(0.2, 0.5)) \
        .click() \
        .perform()


    time.sleep(random.uniform(2, 4))
    login_btn = wait.until(
    EC.element_to_be_clickable((By.CSS_SELECTOR,
        "button.ant-btn.ant-btn-round"))
    )
    actions.move_to_element(login_btn) \
        .pause(random.uniform(0.2, 0.5)) \
        .click() \
        .perform()


    time.sleep(random.uniform(2, 4))
    for field_id, value in [("account", "A2077"), ("password", "A001491")]:
        el = wait.until(EC.element_to_be_clickable((By.ID, field_id)))
        el.clear()
        for ch in value:
            el.send_keys(ch)
            time.sleep(random.uniform(0.1, 0.3))


    agree = wait.until(EC.element_to_be_clickable((By.ID, "checkedDisclaimer")))
    actions.move_to_element(agree).pause(random.uniform(0.2, 0.5)).click().perform()


    time.sleep(random.uniform(1, 2))
    buttons = driver.find_elements(By.CSS_SELECTOR, "button.ant-btn.ant-btn-circle.ant-btn-icon-only")

    enter_btn2 = buttons[1]
    actions.move_to_element(enter_btn2).pause(random.uniform(0.2, 0.5)).click().perform()

    time.sleep(random.uniform(2, 4))

    driver.get("https://user.lifebee.tech/#/user/message/message-main")

    time.sleep(random.uniform(2, 4))

    for req in driver.requests:
        if req.url.endswith("/app/v3/message/center") and req.response:
            api_request = req
            break
    else:
        print("未找到 API 請求")
        return
    
    headers = dict(api_request.headers)

    driver.quit()
    return headers
