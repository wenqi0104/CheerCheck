from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time

# 初始化浏览器驱动
driver = webdriver.Chrome()  # 确保 ChromeDriver 在 PATH 中

# 打开亚马逊登录页面
driver.get('https://www.amazon.co.uk/ap/signin?openid.pape.max_auth_age=0&openid.return_to=https%3A%2F%2Fwww.amazon.co.uk%2Fref%3Dnav_signin&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.assoc_handle=gbflex&openid.mode=checkid_setup&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0')


# 等待页面加载
# time.sleep(100)  # 增加延迟以确保页面加载完成
# 找到用户名和密码输入框并输入信息
driver.find_element(By.ID, 'ap_email').send_keys('1299226721@qq.com')  # 替换为你的邮箱
# 提交登录表单
driver.find_element(By.ID, 'continue').click()

driver.find_element(By.ID, 'ap_password').send_keys('WR11wr11')  # 替换为你的密码
driver.find_element(By.ID, 'signInSubmit').click()

# 暂停脚本，等待手动完成验证码
print("请手动完成验证码验证，完成后按回车继续...")
input()  # 等待用户输入（按回车继续）
 
# 获取手动验证后的 Cookies
cookies = driver.get_cookies()

# 可以保存 Cookies 供后续使用
with open("cookies.txt", "w") as f:
    import json
    json.dump(cookies, f)

 


# -----------------------------


# 等待登录完成并重定向
WebDriverWait(driver, 10).until(EC.url_contains('https://www.amazon.co.uk/ref=nav_logo'))

# 打开评论页面
driver.get('https://www.amazon.co.uk/product-reviews/B0CFM8CMZS/ref=cm_cr_getr_d_paging_btm_next_9?ie=UTF8&reviewerType=all_reviews&pageNumber=9')

# 等待页面加载
time.sleep(5)  # 增加延迟以确保页面加载完成



# 关闭浏览器
driver.quit()