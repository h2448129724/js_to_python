import json
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time

# These functions would need to be implemented based on your specific requirements
from utils import get_date, get_json_file_info, write_json_to_file, get_json_from_excel, get_json_obj_file_info
from register import login_to_gv
from request import open_browser, close_browser, create_browser, get_group_list, add_group

def open_window(window_id):
    open_res = open_browser({
        'id': window_id,
        'args': [],
        'loadExtensions': False,
        'extractIp': False
    })
    return open_res

def get_driver(window_info):
    driver_path = window_info['data']['driver']
    debuggerAddress = window_info['data']['http']
     # selenium 连接代码
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option("debuggerAddress", debuggerAddress)

    service = Service(driver_path)

    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def main(group_name, f_path):
    config_file_name = group_name
    date_str = get_date()
    setting_info = get_register_gv_setting_info(config_file_name)
    print(f'setting_info:{setting_info}')
    if not setting_info or 'groupName' not in setting_info or 'accountFileName' not in setting_info:
        print(f'注册账号配置文件读取失败，请检查配置文件./file/setting/{group_name}.json是否配置正确')
        return

    group_name = setting_info['groupName']
    print(f'groupName:{group_name}')
    group_id = get_group_id_by_name(group_name)
    if not group_id:
        return

    today_account_list_file = f'./file/account_info/{group_name}.json'
    today_account_list = get_json_file_info(today_account_list_file)

    today_new_account_excel_file = f_path
    today_new_account_list = get_json_from_excel(today_new_account_excel_file)

    for account in today_new_account_list:
        if not any(item['userName'] == account['userName'] for item in today_account_list):
            today_account_list.append(account)

    write_json_to_file(today_account_list_file, today_account_list)

    today_window_list_file = f'./file/window_info/{group_name}.json'
    today_window_info_list = get_json_file_info(today_window_list_file)

    print(f'today_window_info_list:{today_new_account_list.count}')

    if today_new_account_list:
        for i, account_info in enumerate(today_new_account_list):
            print(f'index:{i}')
            if not any(item['userName'] == account_info['userName'] and item['password'] == account_info['password'] for item in today_window_info_list):
                window_info_params = generate_window_info(group_id, "https://accounts.google.com/", "gmail", f"{group_name}-{i}", 
                                                          account_info['userName'], account_info['password'], account_info['remark'], 
                                                          2, "socks5", account_info['host'], account_info['port'], 
                                                          account_info['proxyUserName'], account_info['proxyPassword'])
                res = create_browser(window_info_params)
                if res['success']:
                    print(f"添加窗口成功！{window_info_params['userName']}")
                    window_info = {
                        'id': res['data']['id'],
                        'seq': res['data']['seq'],
                        'code': res['data']['code'],
                        'groupId': res['data']['groupId'],
                        'platform': res['data']['platform'],
                        'platformIcon': res['data']['platformIcon'],
                        'name': res['data']['name'],
                        'userName': res['data']['userName'],
                        'password': res['data']['password'],
                        'proxyMethod': res['data']['proxyMethod'],
                        'proxyType': res['data']['proxyType'],
                        'host': res['data']['host'],
                        'port': res['data']['port'],
                        'proxyUserName': res['data']['proxyUserName'],
                        'proxyPassword': res['data']['proxyPassword'],
                        'remark': res['data']['remark']
                    }
                    today_window_info_list.append(window_info)
                else:
                    print(f"添加窗口失败！{window_info_params['userName']}", res)

        write_json_to_file(today_window_list_file, today_window_info_list)

    date = get_date()

    for current_window in today_window_info_list:
        is_running = check_is_running(config_file_name)
        if not is_running:
            print("用户停止程序")
            return

        if 'registerFailedInfo' not in current_window:
            current_window['registerFailedInfo'] = []

        today_failed_info = next((item for item in current_window['registerFailedInfo'] if item['date'] == date_str), None)
        if today_failed_info and today_failed_info['count'] > 3:
            print(f"今日注册失败次数超过3次,不再操作窗口{current_window['seq']}")
            continue

        print(f"开始操作窗口{current_window['seq']}")
        open_res = open_window(current_window['id'])
        if open_res['success']:
            print('打开窗口成功')
            current_window['isOpenSuccess'] = True
            try:
                driver = get_driver(open_res)
                driver.get('https://voice.google.com/')
                is_success = login_to_gv(driver, current_window['userName'], current_window['password'], current_window['remark'])
                if is_success:
                    print(f"gv注册成功,窗口id: {current_window['seq']}")
                    current_window['isRegisterSuccess'] = True
                else:
                    print(f"gv注册失败,窗口id: {current_window['seq']}")
                    current_window['isRegisterSuccess'] = False
                    if today_failed_info:
                        today_failed_info['count'] += 1
                    else:
                        current_window['registerFailedInfo'].append({'date': date, 'count': 1})
                close_all_tabs(driver)
            except Exception as e:
                print('打开gv页面失败，检查代理是否配置正确')
                if today_failed_info:
                    today_failed_info['count'] += 1
                else:
                    current_window['registerFailedInfo'].append({'date': date, 'count': 1})
        else:
            print('打开窗口失败')
            current_window['isOpenSuccess'] = False
            if today_failed_info:
                today_failed_info['count'] += 1
            else:
                current_window['registerFailedInfo'].append({'date': date, 'count': 1})

        write_json_to_file(today_window_list_file, today_window_info_list)
        time.sleep(2)

        try:
            driver.quit()
            time.sleep(2)
            if not current_window.get('hasUnreadMsg'):
                close_browser(current_window['id'])
        except Exception as e:
            print('关闭窗口失败', e)

        is_running = check_is_running(config_file_name)
        if not is_running:
            print("用户停止程序")
            return

def get_register_gv_setting_info(config_file_name):
    gv_setting_file_name = f'./file/setting/{config_file_name}.json'
    return get_json_obj_file_info(gv_setting_file_name)

def close_all_tabs(driver):
    all_handles = driver.window_handles
    for handle in all_handles:
        driver.switch_to.window(handle)
        time.sleep(1)
        driver.close()

def get_group_id_by_name(group_name):
    group_list_resp = get_group_list(0, 100)
    if group_list_resp['success']:
        group_item = next((item for item in group_list_resp['data']['list'] if item['groupName'] == group_name), None)
        if group_item:
            print("已存在分组")
            return group_item['id']
        else:
            print(f'开始添加分组,分组名称为: {group_name}')
            add_group_resp = add_group(group_name, 0)
            if add_group_resp['success']:
                print("添加分组成功", add_group_resp['data'])
                return add_group_resp['data']['id']
            else:
                print("添加分组失败", add_group_resp)
    else:
        print("获取分组列表失败", group_list_resp)

def generate_window_info(group_id, platform, platform_icon, name, user_name, password, remark, proxy_method, proxy_type, host, port, proxy_user_name, proxy_password):
    return {
        'groupId': group_id,
        'platform': platform,
        'platformIcon': platform_icon,
        'name': name,
        'userName': user_name,
        'password': password,
        'remark': remark,
        'proxyMethod': proxy_method,
        'proxyType': proxy_type,
        'host': host,
        'port': port,
        'proxyUserName': proxy_user_name,
        'proxyPassword': proxy_password,
        'browserFingerPrint': {
            'os': "MacIntel",
        },
    }

def check_is_running(config_file_name):
    gv_setting_file_name = f'./file/setting/{config_file_name}.json'
    json_info = get_json_obj_file_info(gv_setting_file_name)
    return json_info['isRunning']

if __name__ == "__main__":
    main()