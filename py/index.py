import asyncio
import json
import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# You'll need to implement these functions or replace them with appropriate Python equivalents
from request import open_browser,get_group_list,close_browser,get_browser_list
from utils import get_date, get_json_file_info, write_json_to_file, get_json_from_excel, get_json_obj_file_info
from register import login_to_gv
from sendmsg import send_message

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

def update_local_info(cur_group_window_info_list, cur_group_window_list_file):
    write_json_to_file(cur_group_window_list_file, cur_group_window_info_list)

async def main1(group_name, f_path):

    config_file_name = group_name
    setting_info = get_send_msg_config_info(config_file_name)
    if not setting_info or not setting_info.get('groupName') or not setting_info.get('messageFileName'):
        print(f"Failed to read the send message configuration file, please check if the configuration file ./file/setting/{config_file_name}.json is configured correctly, groupName should be configured as the account group name, messageFileName should be configured as the message file name")
        return

    message_file_name = f_path
    file_path = os.path.join(os.path.dirname(__file__), message_file_name)
    if not os.path.exists(file_path):
        print(f"Message data file {message_file_name} does not exist, please add the message data file first")
        return

    group_name = setting_info['groupName']
    group_id = check_group_exist(group_name)
    if not group_id:
        print(f"Group does not exist, please check if the groupName in the configuration file ./file/setting/{config_file_name}.json is correct")
        return

    cur_group_window_list_file = f"./file/window_info/{group_name}.json"
    
    browser_list_resp = get_browser_list({"page":0, "pageSize":100, "groupId":group_id})
    print(f"browser_list_resp:{browser_list_resp}")
    if browser_list_resp and browser_list_resp['success']:
        print(f"Successfully obtained {group_name} group window information, there are {browser_list_resp['data']['totalNum']} windows in total")
        window_list = browser_list_resp['data']['list']
        if window_list and len(window_list) > 0:
            cur_group_window_info_list = get_json_file_info(cur_group_window_list_file)
            for cur_window in window_list:
                if not any(item['id'] == cur_window['id'] for item in cur_group_window_info_list):
                    print(f"Window {cur_window['seq']} does not exist in the local file record (this situation occurs when adding directly in the bit browser rather than through the script), adding this window to the local file record")
                    cur_group_window_info_list.append(cur_window)
            
            write_json_to_file(cur_group_window_list_file, cur_group_window_info_list)

            message_list = get_json_from_excel(message_file_name)
            if len(message_list) > 0:
                message_index = 0
                send_times = 1
                message_record = read_message_record(group_name)
                if message_record.get('messageIndex', None):
                    message_index = message_record['messageIndex']
                
                print(f"Starting the {send_times}th round of sending, starting from the {message_index}th message")
                send_result = start_send_message(config_file_name, group_name, cur_group_window_info_list, message_index, message_list)
                update_local_info(cur_group_window_info_list, cur_group_window_list_file)
                print(f"The {send_times}th round of sending is completed, a total of {len(cur_group_window_info_list)} windows were operated, of which {send_result['openFailedCount']} failed to open, {send_result['loginFailedCount']} failed to log in, and {send_result['sendMsgFailedCount']} failed to send")
                if len(send_result['unreadMsgWindowId']) > 0:
                    print(f"Windows {send_result['unreadMsgWindowId']} have unread messages, please check them in time!!!!!!")
                
                while send_result['status'] != 'hasNoMoreMsg':
                    is_running = check_is_running(config_file_name)
                    if not is_running or stop_event.is_set():
                        print("User stopped the program")
                        break
                    asyncio.sleep(300)
                    is_running = check_is_running(config_file_name)
                    if not is_running or stop_event.is_set():
                        print("User stopped the program")
                        break
                    send_times += 1
                    message_index = send_result['messageIndex'] + 1
                    print(f"Starting the {send_times}th round of sending, starting from the {message_index}th message")
                    send_result = start_send_message(config_file_name, group_name, cur_group_window_info_list, message_index, message_list)
                    print(f"The {send_times}th round of sending is completed, a total of {len(cur_group_window_info_list)} windows were operated, of which {send_result['openFailedCount']} failed to open, {send_result['loginFailedCount']} failed to log in, and {send_result['sendMsgFailedCount']} failed to send")
                    if len(send_result['unreadMsgWindowId']) > 0:
                        print(f"Windows {send_result['unreadMsgWindowId']} have unread messages, please check them in time!!!!!!")
                    print()
                
                update_local_info(cur_group_window_info_list, cur_group_window_list_file)
            else:
                print('No message list data obtained')
        else:
            print(f"There are no added windows under the {group_name} group, please add windows and register first")
    else:
        print(f"Failed to get {group_name} group window information, exit!!")
        return

async def close_service():
    try:
        # In Python, we don't need to explicitly close the ChromeDriver service
        pass
    except Exception as e:
        print(e)

def start_send_message(config_file_name, group_name, windows_list, message_index, message_list):
    send_result = {
        'message': {},
        'messageIndex': message_index,
        'status': '',
        'window': {},
        'openFailedCount': 0,
        'loginFailedCount': 0,
        'sendMsgFailedCount': 0,
        'unreadMsgWindowId': []
    }
    date_str = get_date()
    for current_window in windows_list:
        is_running = check_is_running(config_file_name)
        if not is_running or stop_event.is_set():
            print("User stopped the program")
            return send_result
        
        if 'failedInfo' not in current_window:
            current_window['failedInfo'] = []
        
        today_failed_info = next((item for item in current_window['failedInfo'] if item['date'] == date_str), None)
        if today_failed_info and today_failed_info['count'] > 3:
            print(f"Failed more than 3 times today, no longer operating window {current_window['seq']}")
            continue
        
        print(f"Start operating window {current_window['seq']}, window information: {current_window}")
        if current_window.get('isRegisterSuccess') == False:
            print('This window failed to register GV, skipping sending messages')
            continue
        
        open_res = open_window(current_window['id'])
        if open_res['success']:
            print('Successfully opened the window')
            current_window['isOpenSuccess'] = True
            driver = get_driver(open_res)

            is_success = False
            try:
                if current_window.get('isRegisterSuccess') == True:
                    print('This window has successfully registered GV, sending messages directly')
                    driver.get('https://voice.google.com/')
                    is_success = True
                else:
                    print('This window has not registered GV yet, registering GV and sending messages')
                    driver.get('https://voice.google.com/')
                    is_success = login_to_gv(driver, current_window['userName'], current_window['password'], current_window['remark'])
            except Exception as e:
                print('打开gv页面失败，检查代理是否配置正确')    
            if is_success:
                print(f"GV registration successful, window id: {current_window['seq']}")
                current_window['isRegisterSuccess'] = True
                if len(message_list) > message_index:
                    cur_message = message_list[message_index]
                    print('Start sending message', cur_message)
                    record_msg = {
                        'messageIndex': message_index,
                        'message': cur_message
                    }
                    record_message_info(group_name, record_msg)
                    send_status = send_message(driver, cur_message)
                    if send_status == 'hadUnreadMsg':
                        current_window['hasUnreadMsg'] = True
                        current_window['sendSuccess'] = False
                        send_result['unreadMsgWindowId'].append(current_window['seq'])
                    elif send_status == 'sendSuccess':
                        current_window['sendSuccess'] = True
                        current_window['hasUnreadMsg'] = False
                        send_result['message'] = cur_message
                        send_result['messageIndex'] = message_index
                        message_index += 1
                        if len(message_list) > message_index:
                            record_msg = {
                                'messageIndex': message_index,
                                'message': message_list[message_index]
                            }
                        else:
                            record_msg = {
                                'messageIndex': 0,
                                'message': message_list[0]
                            }
                        record_message_info(group_name, record_msg)
                    else:
                        current_window['sendSuccess'] = False
                        current_window['hasUnreadMsg'] = False
                        if today_failed_info:
                            today_failed_info['count'] += 1
                        else:
                            current_window['failedInfo'].append({
                                'date': date_str,
                                'count': 1
                            })
                        send_result['sendMsgFailedCount'] += 1
                else:
                    print('All messages have been sent!!!!')
                    send_result['status'] = 'hasNoMoreMsg'
            else:
                print(f"GV registration failed, window id: {current_window['seq']}")
                current_window['isRegisterSuccess'] = False
                send_result['loginFailedCount'] += 1
            
            if not current_window.get('hasUnreadMsg'):
                asyncio.sleep(2)
                close_all_tab(driver)
                close_browser(current_window['id'])
        else:
            print('Failed to open the window')
            current_window['isOpenSuccess'] = False
            send_result['openFailedCount'] += 1
        
        send_result['window'] = current_window
        close_service()
        is_running = check_is_running(config_file_name)
        if not is_running or stop_event.is_set():
            print('User stopped the program')
            return send_result
    
    return send_result

def get_send_msg_config_info(config_file_name):
    gv_setting_file_name = f"./file/setting/{config_file_name}.json"
    return get_json_obj_file_info(gv_setting_file_name)

async def close_all_tab(driver):
    print('Closing all tabs')
    all_handles = driver.window_handles
    for handle in reversed(all_handles[1:]):
        driver.switch_to.window(handle)
        asyncio.sleep(1)
        driver.close()
    driver.switch_to.window(all_handles[0])

def check_group_exist(group_name):
    group_list_resp = get_group_list(0, 1000)
    if group_list_resp['success']:
        group_item = next((item for item in group_list_resp['data']['list'] if item['groupName'] == group_name), None)
        if group_item:
            print("Group already exists")
            return group_item['id']
        else:
            print("Group does not exist")
    else:
        print("Failed to get group list", group_list_resp)
    return None

def check_is_running(config_file_name):
    gv_setting_file_name = f"./file/setting/{config_file_name}.json"
    json_info = get_json_obj_file_info(gv_setting_file_name)
    return json_info.get('isRunning', False)

def record_message_info(date_str, message_info):
    message_record_file_path = f"./file/message_info/{date_str}.json"
    write_json_to_file(message_record_file_path, message_info)

def read_message_record(group_name):
    message_record_file_path = f"./file/message_info/{group_name}.json"
    return get_json_obj_file_info(message_record_file_path)

if __name__ == "__main__":
    asyncio.run(main1())