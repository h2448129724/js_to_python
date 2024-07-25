import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils import delayed
import time 
baseURL = "https://daisysms.com"

session = requests.Session()
session.headers.update({
    "Content-Type": "application/json"
})

def request(method, url, data=None):
    response = session.request(method, f"{baseURL}{url}", json=data)
    response.raise_for_status()
    return response.json()

def request_phone_num():
    try:
        resp = request("GET", "/stubs/handler_api.php?api_key=rOsdxGL7ZD6h9l0SnZHekvDBD9o8kK&action=getNumber&service=gf&max_price=5.5")
        if resp and 'ACCESS_NUMBER' in resp:
            return resp.split(':')
    except Exception as e:
        print('接码平台获取号码发生异常', e)

def get_code(id, start_time):
    resp = request("GET", f"/stubs/handler_api.php?api_key=rOsdxGL7ZD6h9l0SnZHekvDBD9o8kK&action=getStatus&id={id}")
    if resp:
        if 'STATUS_OK' in resp:
            return resp.split(':')[1]
        else:
            cur_time = time.time() * 1000
            if cur_time - start_time > 30000:
                return -1
            else:
                delayed(5000)
                return get_code(id, start_time)
