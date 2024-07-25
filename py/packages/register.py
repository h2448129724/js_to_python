from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from utils import delayed
from request import open_browser
from sms_request import request_phone_num, get_code

async def login_to_gv(driver, user_name, password, recovery_email):
    is_success = False
    try:
        element_info = await wait_until_get_one_element(driver, [
            (By.XPATH, '//*[@id="gvPageRoot"]/div[2]/gv-side-panel/mat-sidenav-container/mat-sidenav-content/div/div[2]/gv-side-nav'),
            (By.ID, 'getVoiceToggle'),
            (By.ID, 'searchAccountPhoneDropDown'),
            (By.XPATH, '//h2[contains(text(),"A free phone number to take control of your communication")]'),
            (By.XPATH, '//h1[contains(text(),"Unable to access a Google product")]')
        ], 30000)

        if element_info:
            index = element_info['index']
            element = element_info['element']
            if index == 0:
                print('已经注册成功')
                is_success = True
            elif index == 1:
                print('没有登录过gmail')
                await element.click()
                await get_visible_element(driver, By.CLASS_NAME, 'getGoogleVoiceOptions')
                web_btn = await get_visible_element(driver, By.CLASS_NAME, 'webButton')
                web_btn.click()
                user_name_input = await get_visible_element(driver, By.CSS_SELECTOR, 'input#identifierId')
                await user_name_input.send_keys(user_name)
                next_btn = await get_visible_element(driver, By.ID, 'identifierNext')
                next_btn.click()
                pwd_input = await get_visible_element(driver, By.NAME, 'Passwd')
                await pwd_input.send_keys(password)
                pwd_next_btn = await get_visible_element(driver, By.ID, 'passwordNext')
                pwd_next_btn.click()
                element_info2 = await wait_until_get_one_element(driver, [
                    (By.ID, 'searchAccountPhoneDropDown'),
                    (By.XPATH, '//span[text()="Not now"]/parent::button'),
                    (By.XPATH, '//div[text()="Confirm your recovery email"]'),
                    (By.XPATH, '//h1[contains(text(),"Unable to access a Google product")]'),
                    (By.XPATH, '//h2[contains(text(),"A free phone number to take control of your communication")]')
                ], 30000)

                if element_info2:
                    index2 = element_info2['index']
                    element2 = element_info2['element']
                    if index2 == 3:
                        print('google账号可能被封无法使用,注册失败')
                        return False
                    if index2 == 1:
                        await element2.click()
                    elif index2 == 2:
                        await handle_recovery_email(driver, recovery_email)
                    elif index2 == 4:
                        continue_btn = await get_visible_element(driver, By.XPATH, '//button[@aria-label="Continue"]')
                        if continue_btn:
                            continue_btn.click()
                    await get_phone_code(driver)
                    is_success = await is_register_success(driver)
                else:
                    is_success = await is_register_success(driver)
            elif index == 2:
                await get_phone_code(driver)
                is_success = await is_register_success(driver)
            elif index == 3:
                continue_btn = await get_visible_element(driver, By.XPATH, '//button[@aria-label="Continue"]')
                if continue_btn:
                    continue_btn.click()
                await get_phone_code(driver)
                is_success = await is_register_success(driver)
            elif index == 4:
                print('账号被封')
                is_success = False
    except Exception as e:
        print('catch', e)
        is_success = await is_register_success(driver)
    return is_success

async def get_phone_code(driver):
    element = await get_visible_element(driver, By.ID, 'searchAccountPhoneDropDown')
    if not element:
        return
    city_code_element = await get_visible_element(driver, By.ID, 'citycodesuggestionid-0')
    if not city_code_element:
        return
    await city_code_element.click()
    phone_num_element = await get_visible_element(driver, By.ID, 'phonenumberresultid-0')
    if not phone_num_element:
        return
    select_btn = await phone_num_element.find_element(By.CLASS_NAME, "gmat-button")
    if not select_btn:
        return
    await select_btn.click()
    verify_btn = await get_visible_element(driver, By.XPATH, '//button[@aria-label="Verify"]', 10000)
    if not verify_btn:
        return
    await verify_btn.click()
    phone_num_input = await get_visible_element(driver, By.CLASS_NAME, 'gvAddLinkedNumber-numberInput')
    if not phone_num_input:
        return
    resp = await request_phone_num()
    if resp and len(resp) == 3:
        phone_num = resp[2]
        await phone_num_input.send_keys(phone_num)
        add_link_element = await get_visible_element(driver, By.CLASS_NAME, 'gvAddLinkedNumber-actions')
        button_list = await add_link_element.find_elements(By.TAG_NAME, "button")
        if len(button_list) > 1:
            ok_btn = button_list[1]
            await ok_btn.click()
        id = resp[1]
        phone_code = await get_code_from_remote(id, driver)
        if phone_code:
            code_input_elements = await get_visible_elements(driver, By.NAME, 'verify-code')
            if code_input_elements and len(code_input_elements) == 6:
                for i, code_input in enumerate(code_input_elements):
                    await code_input.send_keys(phone_code[i])
            add_link_element2 = await get_visible_element(driver, By.CLASS_NAME, 'gvAddLinkedNumber-actions')
            button_list2 = await add_link_element2.find_elements(By.TAG_NAME, "button")
            if len(button_list2) > 1:
                verify_btn = button_list2[1]
                await verify_btn.click()
            finish_btn = await get_visible_element(driver, By.XPATH, '//button[@aria-label="Finish"]')
            await finish_btn.click()
            finish_btn2 = await get_visible_element(driver, By.XPATH, '//button[@aria-label="Finish"]')
            await finish_btn2.click()
        else:
            print('接码平台获取验证码失败')
    else:
        print('接码平台获取号码失败')

async def get_code_from_remote(id, driver):
    cur_time = time.time() * 1000
    phone_code = await get_code(id, cur_time)
    if phone_code == -1:
        resend_btn = await get_visible_element(driver, By.XPATH, '//*[@id="dialogContent_0"]/div/gv-stroked-button/span/button')
        if resend_btn:
            await resend_btn.click()
            new_cur_time = time.time() * 1000
            phone_code = await get_code(id, new_cur_time)
            if phone_code and phone_code != -1:
                return phone_code
    return phone_code

async def is_in_conversation_page(driver, wait_time):
    try:
        element = await get_visible_element(driver, By.ID, 'messaging-view', wait_time)
        return element
    except Exception as e:
        print('isInConversationPage', e)
        return None

async def is_register_success(driver):
    is_in_page = await is_in_conversation_page(driver, 30000)
    if is_in_page:
        element = await wait_until_get_one_element(driver, [
            (By.XPATH, '//*[local-name()="gv-conversation-list"]'),
            (By.CLASS_NAME, 'phone-number-details')
        ], 30000)
        if not element:
            print('注册成功但不可用')
        else:
            print('注册成功')
            return True
    return False

async def get_visible_element(driver, by, value, wait_time=30000):
    try:
        element = WebDriverWait(driver, wait_time).until(
            EC.visibility_of_element_located((by, value))
        )
        return element
    except Exception as e:
        print(f'获取元素失败: {value}', e)
        return None

async def wait_until_get_one_element(driver, identities, timeout):
    cur_date_timestamp = time.time() * 1000
    while time.time() * 1000 - cur_date_timestamp < timeout:
        for i, identity in enumerate(identities):
            element = await get_visible_element(driver, *identity, 1000)
            if element:
                return {"element": element, "index": i}
    return None

async def get_visible_elements(driver, by, value, wait_time=30000):
    try:
        elements = WebDriverWait(driver, wait_time).until(
            EC.visibility_of_any_elements_located((by, value))
        )
        return elements
    except Exception as e:
        print(f'获取元素失败: {value}', e)
        return []

async def handle_recovery_email(driver, email):
    try:
        element = await get_visible_element(driver, By.XPATH, '//div[text()="Confirm your recovery email"]')
        if element:
            await element.click()
            email_input = await get_visible_element(driver, By.NAME, 'knowledgePreregisteredEmailResponse')
            if email_input:
                await email_input.send_keys(email)
                next_btn = await get_visible_element(driver, By.XPATH, '//span[text()="Next"]')
                await next_btn.click()
    except Exception as e:
        print('获取辅助邮箱页面失败', e)

