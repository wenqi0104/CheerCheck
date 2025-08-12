from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time

# 初始化浏览器驱动
driver = webdriver.Chrome()

# 加载保存的 Cookies
with open("cookies.txt", "r") as f:
    cookies = json.load(f)

# 访问亚马逊首页以加载 Cookies
driver.get("https://www.amazon.co.uk/")

# 打印当前 Cookies（调试用）
print("Initial Cookies:", driver.get_cookies())

# 添加 Cookies 到当前会话
for cookie in cookies:
    driver.add_cookie({
        'name': cookie['name'],
        'value': cookie['value'],
        'domain': cookie.get('domain', '.amazon.co.uk'),  # 确保域名正确
        'path': cookie.get('path', '/'),
        'expiry': cookie.get('expiry'),
        'secure': cookie.get('secure', False),
        'httpOnly': cookie.get('httpOnly', False),
        'sameSite': cookie.get('sameSite', 'Lax')
    })

# 刷新页面以应用 Cookies
driver.refresh()

# 打印刷新后的 Cookies（调试用）
print("After Refresh Cookies:", driver.get_cookies())

# 打开评论页面
driver.get("https://www.amazon.co.uk/product-reviews/B0CFM8CMZS/ref=cm_cr_getr_d_paging_btm_next_9?ie=UTF8&reviewerType=all_reviews&pageNumber=9")

# 等待评论加载（使用显式等待）
try:
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '.a-size-base.review-text'))
    )
except Exception as e:
    print("页面加载超时或元素未找到:", e)

# 提取评论数据
comments = driver.find_elements(By.CSS_SELECTOR, '.a-size-base.review-text')
comments_data = [comment.text for comment in comments]

# 输出评论数据
for comment in comments_data:
    print(comment)

# 关闭浏览器
driver.quit()