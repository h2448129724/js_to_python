import asyncio
from request import open_browser, close_browser, create_browser, get_group_list, add_group
from utils import get_date, get_json_file_info, write_json_to_file, get_json_from_excel, get_json_obj_file_info
from register import login_to_gv, get_visible_element
from sendmsg import send_message
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import sys
async def main():
    if len(sys.argv) != 3:
        print('运行脚本失败，未指定配置文件')
        return

    config_file_name = sys.argv[2]

    setting_info = await get_register_gv_setting_info(config_file_name)
    if not setting_info or not setting_info.get('groupName') or not setting_info.get('accountFileName'):
        print('注册账号配置文件读取失败，请检查配置文件./file/setting/register.json是否配置正确,groupName应该配置为账号分组名称,accountFileName应该配置为含有账号信息的excel文件名称')
        return

    group_name = setting_info['groupName']
    group_id = await get_group_id_by_name(group_name)
    if not group_id:
        return

    today_account_list_file = f"./file/account_info/{group_name}.json"
    today_account_list = await get_json_file_info(today_account_list_file)

    today_new_account_excel_file = f"./file/excel_info/{setting_info['accountFileName']}.xlsx"
    today_new_account_list = get_json_from_excel(today_new_account_excel_file)

    for account in today_new_account_list:
        if not any(item['userName'] == account['userName'] for item in today_account_list):
            today_account_list.append(account)
    await write_json_to_file(today_account_list_file, today_account_list)

    today_window_list_file = f"./file/window_info/{group_name}.json"
    today_window_info_list = await get_json_file_info(today_window_list_file)

    if today_new_account_list:
        for i, account_info in enumerate(today_new_account_list):
            if not any(item['userName'] == account_info['userName'] and item['password'] == account_info['password'] for item in today_window_info_list):
                window_info_params = generate_window_info(
                    group_id, "https://accounts.google.com/", "gmail", f"{group_name}-{i}", account_info['userName'],
                    account_info['password'], account_info['remark'], 2, "socks5", account_info['host'],
                    account_info['port'], account_info['proxyUserName'], account_info['proxyPassword']
                )
                res = await create_browser(window_info_params)
                if res['success']:
                    today_window_info_list.append(res['data'])
                else:
                    print("添加窗口失败！", window_info_params['userName'])

        await write_json_to_file(today_window_list_file, today_window_info_list)

    for current_window in today_window_info_list:
        if not current_window.get('registerFailedInfo'):
            current_window['registerFailedInfo'] = []
        today_failed_info = next((item for item in current_window['registerFailedInfo'] if item['date'] == get_date()), None)
        if today_failed_info and today_failed_info['count'] > 3:
            continue
        open_res = await open_window(current_window['id'])
        if open_res['success']:
            current_window['isOpenSuccess'] = True
            driver = get_driver(open_res)
            driver.get('https://voice.google.com/')
            is_success = await login_to_gv(driver, current_window['userName'], current_window['password'], current_window['remark'])
            if is_success:
                current_window['isRegisterSuccess'] = True
            else:
                current_window['isRegisterSuccess'] = False
                if today_failed_info:
                    today_failed_info['count'] += 1
                else:
                    current_window['registerFailedInfo'].append({'date': get_date(), 'count': 1})
            await close_all_tabs(driver)
        else:
            current_window['isOpenSuccess'] = False
            if today_failed_info:
                today_failed_info['count'] += 1
            else:
                current_window['registerFailedInfo'].append({'date': get_date(), 'count': 1})
        await write_json_to_file(today_window_list_file, today_window_info_list)
        await asyncio.sleep(2)
        service = ChromeService(ChromeDriverManager().install())
        service.kill()
        await asyncio.sleep(2)
        if not current_window.get('hasUnreadMsg'):
            await close_browser(current_window['id'])

async def get_register_gv_setting_info(config_file_name):
    gv_setting_file_name = f"./file/setting/{config_file_name}.json"
    return await get_json_obj_file_info(gv_setting_file_name)

async def close_all_tabs(driver):
    all_handles = await driver.window_handles
    for handle in all_handles:
        driver.switch_to.window(handle)
        await asyncio.sleep(1)
        driver.close()

async def get_group_id_by_name(group_name):
    group_list_resp = await get_group_list(0, 100)
    if group_list_resp['success']:
        group_item = next((item for item in group_list_resp['data']['list'] if item['groupName'] == group_name), None)
        if group_item:
            return group_item['id']
        else:
            add_group_resp = await add_group(group_name, 0)
            if add_group_resp['success']:
                return add_group_resp['data']['id']

def generate_window_info(group_id, platform, platform_icon, name, user_name, password, remark, proxy_method, proxy_type, host, port, proxy_user_name, proxy_password):
    return {
        "groupId": group_id,
        "platform": platform,
        "platformIcon": platform_icon,
        "name": name,
        "userName": user_name,
        "password": password,
        "remark": remark,
        "proxyMethod": proxy_method,
        "proxyType": proxy_type,
        "host": host,
        "port": port,
        "proxyUserName": proxy_user_name,
        "proxyPassword": proxy_password,
        "browserFingerPrint": {"os": "MacIntel"},
    }

async def open_window(window_id):
    return await open_browser({"id": window_id, "args": [], "loadExtensions": False, "extractIp": False})

def get_driver(window_info):
    options = webdriver.ChromeOptions()
    options.add_experimental_option("debuggerAddress", window_info['data']['http'])
    service = ChromeService(executable_path=ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def check_is_running(config_file_name):
    gv_setting_file_name = f"./file/setting/{config_file_name}.json"
    json_info = get_json_obj_file_info(gv_setting_file_name)
    return json_info.get('isRunning', False)
