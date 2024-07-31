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
from request import open_browser, get_group_list, close_browser, get_browser_list
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


async def main1(group_name, f_path, stop_event, file):

    if stop_event.is_set():
        print(f"用户手动停止程序,分组名称为: {group_name}", file=file)
        return

    message_file_name = f_path

    group_id = check_group_exist(group_name)
    if not group_id:
        print(f"分组{group_name}不存在，请检查分组输入是否正确")
        return

    cur_group_window_list_file = f"./file/window_info/{group_name}.json"

    browser_list_resp = get_browser_list({"page": 0, "pageSize": 100, "groupId": group_id})
    print(f"browser_list_resp:{browser_list_resp}")
    if browser_list_resp and browser_list_resp['success']:
        print(f"成功获取 {group_name} 分组窗口信息，共有 {browser_list_resp['data']['totalNum']} 个窗口")
        window_list = browser_list_resp['data']['list']
        if window_list and len(window_list) > 0:
            cur_group_window_info_list = get_json_file_info(cur_group_window_list_file)
            for cur_window in window_list:
                if not any(item['id'] == cur_window['id'] for item in cur_group_window_info_list):
                    print(
                        f"窗口 {cur_window['seq']} 不存在于本地文件记录中（这种情况发生在直接在 bit browser 添加而不是通过脚本），将该窗口添加到本地文件记录中")
                    cur_group_window_info_list.append(cur_window)

            write_json_to_file(cur_group_window_list_file, cur_group_window_info_list)

            message_list = get_json_from_excel(message_file_name)
            if len(message_list) > 0:
                message_index = 0
                send_times = 1
                message_record = read_message_record(group_name)
                if message_record.get('messageIndex', None):
                    message_index = message_record['messageIndex']

                print(f"开始第 {send_times} 轮发送，从第 {message_index} 条消息开始")
                send_result = start_send_message(stop_event, group_name, cur_group_window_info_list, message_index,
                                                 message_list, file=file)
                update_local_info(cur_group_window_info_list, cur_group_window_list_file)
                print(
                    f"第 {send_times} 轮发送完成，共操作 {len(cur_group_window_info_list)} 个窗口，其中打开失败 {send_result['openFailedCount']} 个，登录失败 {send_result['loginFailedCount']} 个，发送失败 {send_result['sendMsgFailedCount']} 个")
                if len(send_result['unreadMsgWindowId']) > 0:
                    print(f"窗口 {send_result['unreadMsgWindowId']} 有未读消息，请及时处理！")

                while send_result['status'] != 'hasNoMoreMsg':
                    if stop_event.is_set():
                        print("用户停止程序", file=file)
                        break

                    asyncio.sleep(300)

                    if stop_event.is_set():
                        print("用户停止程序", file=file)
                        break
                    send_times += 1
                    message_index = send_result['messageIndex'] + 1
                    print(f"开始第 {send_times} 轮发送，从第 {message_index} 条消息开始")
                    send_result = start_send_message(stop_event, group_name, cur_group_window_info_list, message_index,
                                                     message_list)
                    print(
                        f"第 {send_times} 轮发送完成，共操作 {len(cur_group_window_info_list)} 个窗口，其中打开失败 {send_result['openFailedCount']} 个，登录失败 {send_result['loginFailedCount']} 个，发送失败 {send_result['sendMsgFailedCount']} 个")
                    if len(send_result['unreadMsgWindowId']) > 0:
                        print(f"窗口 {send_result['unreadMsgWindowId']} 有未读消息，请及时处理！")
                    print()

                update_local_info(cur_group_window_info_list, cur_group_window_list_file)
            else:
                print('未获取到消息列表数据')
        else:
            print(f"{group_name} 分组下未添加任何窗口，请先添加窗口并注册")
    else:
        print(f"获取 {group_name} 分组窗口信息失败，退出！")
        return


async def close_service():
    try:
        # In Python, we don't need to explicitly close the ChromeDriver service
        pass
    except Exception as e:
        print(e)


def start_send_message(stop_event, group_name, windows_list, message_index, message_list, file):
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
        if stop_event.is_set():
            print("用户停止程序", file=file)
            return send_result

        if 'failedInfo' not in current_window:
            current_window['failedInfo'] = []

        today_failed_info = next((item for item in current_window['failedInfo'] if item['date'] == date_str), None)
        if today_failed_info and today_failed_info['count'] > 3:
            print(f"今日失败超过 3 次，不再操作窗口 {current_window['seq']}")
            continue

        print(f"开始操作窗口 {current_window['seq']}，窗口信息: {current_window}")
        if current_window.get('isRegisterSuccess') == False:
            print('该窗口注册 GV 失败，跳过发送消息')
            continue

        open_res = open_window(current_window['id'])
        if open_res['success']:
            print('成功打开窗口')
            current_window['isOpenSuccess'] = True
            driver = get_driver(open_res)

            is_success = False
            try:
                if current_window.get('isRegisterSuccess') == True:
                    print('该窗口已成功注册 GV，直接发送消息')
                    driver.get('https://voice.google.com/')
                    is_success = True
                else:
                    print('该窗口尚未注册 GV，正在注册 GV 并发送消息')
                    driver.get('https://voice.google.com/')
                    is_success = login_to_gv(driver, current_window['userName'], current_window['password'],
                                             current_window['remark'])
            except Exception as e:
                print('打开 GV 页面失败，检查代理是否配置正确')
            if is_success:
                print(f"GV 注册成功，窗口 id: {current_window['seq']}")
                current_window['isRegisterSuccess'] = True
                if len(message_list) > message_index:
                    cur_message = message_list[message_index]
                    print('开始发送消息', cur_message)
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
                    print('所有消息已发送完毕！')
                    send_result['status'] = 'hasNoMoreMsg'
            else:
                print(f"GV 注册失败，窗口 id: {current_window['seq']}")
                current_window['isRegisterSuccess'] = False
                send_result['loginFailedCount'] += 1

            if not current_window.get('hasUnreadMsg'):
                asyncio.sleep(2)
                close_all_tab(driver)
                close_browser(current_window['id'])
        else:
            print('打开窗口失败')
            current_window['isOpenSuccess'] = False
            send_result['openFailedCount'] += 1

        send_result['window'] = current_window
        close_service()
        if stop_event.is_set():
            print('用户停止程序', file=file)
            return send_result

    return send_result


async def close_all_tab(driver):
    print('关闭所有标签页')
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
            print("分组已存在")
            return group_item['id']
        else:
            print("分组不存在")
    else:
        print("获取分组列表失败", group_list_resp)
    return None


def record_message_info(date_str, message_info):
    message_record_file_path = f"./file/message_info/{date_str}.json"
    write_json_to_file(message_record_file_path, message_info)


def read_message_record(group_name):
    message_record_file_path = f"./file/message_info/{group_name}.json"
    return get_json_obj_file_info(message_record_file_path)


if __name__ == "__main__":
    asyncio.run(main1())
