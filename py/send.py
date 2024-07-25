# send.py
import os
from packages.utils import get_json_from_excel, get_json_file_info, write_json_to_file, delayed
from packages.sendmsg import send_message
from packages.request import open_browser, close_browser, get_browser_list, get_group_list, add_group
from packages.index import get_json_obj_file_info,get_date
import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

async def send_messages_from_excel(config_file_name):
    setting_info = await get_send_msg_config_info(config_file_name)
    if not setting_info or not setting_info.get('groupName') or not setting_info.get('messageFileName'):
        print(f"发送消息配置文件读取失败，请检查配置文件./file/setting/{config_file_name}.json是否配置正确,groupName应该配置为账号分组名称,messageFileName应该配置为消息文件名称")
        return

    message_file_name = f"./file/message_excel_info/{setting_info['messageFileName']}.xlsx"
    if not os.path.exists(message_file_name):
        print(f"消息数据文件{message_file_name}不存在，请先添加消息数据文件")
        return

    group_name = setting_info['groupName']
    group_id = await check_group_exist(group_name)
    if not group_id:
        print(f"分组不存在,请检查配置文件./file/setting/{config_file_name}.json中的groupName是否正确")
        return

    cur_group_window_list_file = f"./file/window_info/{group_name}.json"
    browser_list_resp = await get_browser_list({"page": 0, "pageSize": 100, "groupId": group_id})
    if browser_list_resp and browser_list_resp['success']:
        window_list = browser_list_resp['data']['list']
        if window_list:
            cur_group_window_info_list = await get_json_file_info(cur_group_window_list_file)
            for cur_window in window_list:
                if not any(item['id'] == cur_window['id'] for item in cur_group_window_info_list):
                    cur_group_window_info_list.append(cur_window)
            await write_json_to_file(cur_group_window_list_file, cur_group_window_info_list)

            message_list = get_json_from_excel(message_file_name)
            if message_list:
                message_index = 0
                send_times = 1
                message_record = await read_message_record(group_name)
                if message_record.get('messageIndex'):
                    message_index = message_record['messageIndex']
                print(f"开始第{send_times}轮发送,从{message_index}条消息开始发送")
                send_result = await start_send_message(config_file_name, group_name, cur_group_window_info_list, message_index, message_list)
                await update_local_info(cur_group_window_info_list, cur_group_window_list_file)
                print(f"第{send_times}轮发送完成,共操作{len(cur_group_window_info_list)}个窗口,其中打开失败{send_result['openFailedCount']}个,登录失败{send_result['loginFailedCount']}个,发送失败{send_result['sendMsgFailedCount']}个")
                if send_result['unreadMsgWindowId']:
                    print(f"窗口{send_result['unreadMsgWindowId']}有未读消息未查看，请及时查看！！！！！！！！！")
                while send_result['status'] != 'hasNoMoreMsg':
                    is_running = await check_is_running(config_file_name)
                    if not is_running:
                        print("用户停止程序")
                        break
                    await delayed(300)
                    send_times += 1
                    message_index = send_result['messageIndex'] + 1
                    print(f"开始第{send_times}轮发送,从{message_index}条消息开始发送")
                    send_result = await start_send_message(config_file_name, group_name, cur_group_window_info_list, message_index, message_list)
                    print(f"第{send_times}轮发送完成,共操作{len(cur_group_window_info_list)}个窗口,其中打开失败{send_result['openFailedCount']}个,登录失败{send_result['loginFailedCount']}个,发送失败{send_result['sendMsgFailedCount']}个")
                    if send_result['unreadMsgWindowId']:
                        print(f"窗口{send_result['unreadMsgWindowId']}有未读消息未查看，请及时查看！！！！！！！！！")
                await update_local_info(cur_group_window_info_list, cur_group_window_list_file)
            else:
                print('没有获取到消息列表数据')
        else:
            print(f"{group_name}分组下没有已添加的窗口，请先添加窗口并注册")
    else:
        print(f"获取{group_name}分组窗口信息失败，退出！！")

async def start_send_message(config_file_name, group_name, windows_list, message_index, message_list):
    send_result = {
        "message": {},
        "messageIndex": message_index,
        "status": '',
        "window": {},
        "openFailedCount": 0,
        "loginFailedCount": 0,
        "sendMsgFailedCount": 0,
        "unreadMsgWindowId": []
    }
    date_str = get_date()
    for current_window in windows_list:
        is_running = await check_is_running(config_file_name)
        if not is_running:
            print("用户停止程序")
            return send_result
        if current_window.get('failedInfo') and any(item['date'] == date_str and item['count'] > 3 for item in current_window['failedInfo']):
            print(f"今日失败次数超过3次,不再操作窗口{current_window['seq']}")
            continue
        print(f"开始操作窗口{current_window['seq']},窗口信息:{current_window}")
        if current_window.get('isRegisterSuccess') is False:
            print('该窗口注册GV失败,跳过发送短信')
            continue
        open_res = await open_window(current_window['id'])
        if open_res['success']:
            print('打开窗口成功')
            current_window['isOpenSuccess'] = True
            driver = get_driver(open_res)
            if await send_message(driver, message_list[message_index]) == 'sendSuccess':
                send_result['messageIndex'] = message_index
                send_result['status'] = 'hasNoMoreMsg' if message_index == len(message_list) - 1 else 'hasMoreMsg'
                message_index += 1
            else:
                send_result['sendMsgFailedCount'] += 1
        else:
            send_result['openFailedCount'] += 1
    return send_result

def get_driver(window_info):
    options = webdriver.ChromeOptions()
    options.add_experimental_option("debuggerAddress", window_info['data']['http'])
    service = ChromeService(executable_path=ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

async def check_is_running(config_file_name):
    gv_setting_file_name = f"./file/setting/{config_file_name}.json"
    json_info = await get_json_obj_file_info(gv_setting_file_name)
    return json_info.get('isRunning', False)

async def get_send_msg_config_info(config_file_name):
    gv_setting_file_name = f"./file/setting/{config_file_name}.json"
    return await get_json_obj_file_info(gv_setting_file_name)

async def check_group_exist(group_name):
    group_list_resp = await get_group_list(0, 100)
    if group_list_resp['success']:
        group_item = next((item for item in group_list_resp['data']['list'] if item['groupName'] == group_name), None)
        if group_item:
            return group_item['id']
        else:
            add_group_resp = await add_group(group_name, 0)
            if add_group_resp['success']:
                return add_group_resp['data']['id']
    return None

async def update_local_info(cur_group_window_info_list, cur_group_window_list_file):
    await write_json_to_file(cur_group_window_list_file, cur_group_window_info_list)

async def read_message_record(group_name):
    message_record_file = f"./file/message_record/{group_name}.json"
    return await get_json_file_info(message_record_file)

async def open_window(window_id):
    return await open_browser({"id": window_id, "args": [], "loadExtensions": False, "extractIp": False})
