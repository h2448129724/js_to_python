import time
import requests

session = requests.Session()
def request_phone_num():
    try:
        resp = session.get("https://daisysms.com/stubs/handler_api.php", params={
            "api_key": "rOsdxGL7ZD6h9l0SnZHekvDBD9o8kK",
            "action": "getNumber",
            "service": "gf",
            "max_price": "5.5"
        })
        print('requestPhoneNum', resp.text)
        if resp.text:
            if 'ACCESS_NUMBER' in resp.text:
                return resp.text.split(':')
    except Exception as e:
        print('Exception occurred while getting phone number from the platform', e)

def get_code(id, start_time):
    resp = session.get("https://daisysms.com/stubs/handler_api.php", params={
        "api_key": "rOsdxGL7ZD6h9l0SnZHekvDBD9o8kK",
        "action": "getStatus",
        "id": id
    })
    print('getCode', resp.text)
    if resp.text:
        if 'STATUS_OK' in resp.text:
            return resp.text.split(':')[1]
        else:
            cur_time = time.time() * 1000
            if cur_time - start_time > 30000:
                return -1
            else:
                print('SMS not received yet, retrying in 5 seconds')
                time.sleep(5)
                return get_code(id, start_time)

