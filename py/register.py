from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time

# Assuming these are custom modules that need to be implemented separately
from sms_request import request_phone_num, get_code

def login_to_gv(driver, user_name, password, recovery_email):
    is_success = False
    try:
        element_info = wait_until_get_one_element(driver, [
            (By.XPATH, '//*[@id="gvPageRoot"]/div[2]/gv-side-panel/mat-sidenav-container/mat-sidenav-content/div/div[2]/gv-side-nav'),
            (By.ID, 'getVoiceToggle'),
            (By.ID, 'searchAccountPhoneDropDown'),
            (By.XPATH, '//h2[contains(text(),"A free phone number to take control of your communication")]'),
            (By.XPATH, '//h1[contains(text(),"Unable to access a Google product")]')
        ], 30000)

        if element_info:
            index, element = element_info
            if index == 0:
                print('Already registered successfully')
                is_success = True
            elif index == 1:
                print('Not logged into Gmail')
                element.click()
                get_visible_element(driver, By.CLASS_NAME, 'getGoogleVoiceOptions')
                web_btn = get_visible_element(driver, By.CLASS_NAME, 'webButton')
                web_btn.click()
                time.sleep(2)

                element_info3 = wait_until_get_one_element(driver, [
                    (By.XPATH, '//h1[contains(text(),"Unable to access a Google product")]'),
                    (By.CSS_SELECTOR, 'input#identifierId')
                ], 30000)

                if element_info3:
                    if element_info3[0] == 0:
                        is_success = False
                        print('Google account might be banned, registration failed')
                        return is_success

                user_name_input = get_visible_element(driver, By.CSS_SELECTOR, 'input#identifierId')
                user_name_input.click()
                time.sleep(1)
                user_name_input.clear()
                time.sleep(1)
                user_name_input.send_keys(user_name)
                time.sleep(1)

                next_btn = get_visible_element(driver, By.ID, 'identifierNext')
                next_btn.click()

                pwd_input = get_visible_element(driver, By.NAME, 'Passwd')
                time.sleep(1)
                pwd_input.click()
                time.sleep(1)
                pwd_input.clear()
                time.sleep(1)
                pwd_input.send_keys(password)
                time.sleep(1)

                pwd_next_btn = get_visible_element(driver, By.ID, 'passwordNext')
                pwd_next_btn.click()

                element_info2 = wait_until_get_one_element(driver, [
                    (By.ID, 'searchAccountPhoneDropDown'),
                    (By.XPATH, '//span[text()="Not now"]/parent::button'),
                    (By.XPATH, '//div[text()="Confirm your recovery email"]'),
                    (By.XPATH, '//h1[contains(text(),"Unable to access a Google product")]'),
                    (By.XPATH, '//h2[contains(text(),"A free phone number to take control of your communication")]')
                ], 30000)

                if element_info2:
                    index2, element2 = element_info2
                    if index2 == 3:
                        is_success = False
                        print('Google account might be banned, registration failed')
                        return is_success
                    if index2 == 1:
                        print('Not now page appeared, clicking not now button')
                        element2.click()
                    elif index2 == 2:
                        handle_recovery_email(driver, recovery_email)
                    elif index2 == 4:
                        element = get_visible_element(driver, By.XPATH, '//button[@aria-label="Continue"]')
                        if element:
                            element.click()
                    get_phone_code(driver)
                    is_success = is_register_success(driver)
                else:
                    is_success = is_register_success(driver)
            elif index == 2:
                print('Logged into Gmail, but not registered for GV, area selection box appeared')
                get_phone_code(driver)
                is_success = is_register_success(driver)
            elif index == 3:
                print('Logged into Gmail, but not registered for GV, agreement page appeared')
                element = get_visible_element(driver, By.XPATH, '//button[@aria-label="Continue"]')
                if element:
                    element.click()
                get_phone_code(driver)
                is_success = is_register_success(driver)
            elif index == 4:
                print('Account banned')
                is_success = False
            else:
                print('Element not found')
                is_success = False
    except Exception as e:
        print('catch', e)
        is_success = is_register_success(driver)
    return is_success

def get_phone_code(driver):
    print("Getting area code selection box")
    element = get_visible_element(driver, By.ID, 'searchAccountPhoneDropDown')
    if not element:
        return

    print("Getting first area code option")
    city_code_element = get_visible_element(driver, By.ID, 'citycodesuggestionid-0')
    if not city_code_element:
        return
    time.sleep(2)
    print("Clicking area code option")
    city_code_element.click()
    print("Getting phone number selection box")
    get_visible_element(driver, By.ID, 'searchAccountPhoneDropDown')
    print("Getting first phone number")
    phone_num_element = get_visible_element(driver, By.ID, 'phonenumberresultid-0')
    if not phone_num_element:
        return
    print("Getting phone number confirmation button")
    select_btn = phone_num_element.find_element(By.CLASS_NAME, "gmat-button")
    if not select_btn:
        return
    time.sleep(2)
    print("Clicking phone number confirmation button")
    select_btn.click()
    get_visible_element(driver, By.CLASS_NAME, "gvSignupView-innerArea")
    time.sleep(2)
    print("Getting verify button")
    verify_btn = get_visible_element(driver, By.XPATH, '//button[@aria-label="Verify"]', 10000)
    if not verify_btn:
        return
    time.sleep(2)
    print("Clicking verify button")
    verify_btn.click()
    print("Getting phone number input box")
    phone_num_input = get_visible_element(driver, By.CLASS_NAME, 'gvAddLinkedNumber-numberInput')
    if not phone_num_input:
        return
    time.sleep(1)
    phone_num_input.click()
    time.sleep(1)
    phone_num_input.clear()
    time.sleep(1)
    resp = request_phone_num()
    print('resp', resp)
    if resp and len(resp) == 3:
        phone_num = resp[2]
        print("Entering SMS platform number")
        phone_num_input.send_keys(phone_num)
        add_link_element = get_visible_element(driver, By.CLASS_NAME, 'gvAddLinkedNumber-actions')
        button_list = add_link_element.find_elements(By.TAG_NAME, "button")
        if len(button_list) > 1:
            ok_btns = button_list[1]
            time.sleep(2)
            ok_btns.click()

        id = resp[1]
        phone_code = get_code_from_remote(id, driver)
        if phone_code:
            print("SMS platform verification code is", phone_code)
            time.sleep(2)
            print('Getting verification code input box')
            code_input_elements = get_visible_elements(driver, By.NAME, 'verify-code')
            if code_input_elements and len(code_input_elements) == 6:
                for i, code_input in enumerate(code_input_elements):
                    code_input.click()
                    code_input.clear()
                    print('Entering the first digit', phone_code[i])
                    code_input.send_keys(phone_code[i])
                    time.sleep(1)
            print('Getting confirmation button')
            add_link_element2 = get_visible_element(driver, By.CLASS_NAME, 'gvAddLinkedNumber-actions')
            button_list2 = add_link_element2.find_elements(By.TAG_NAME, "button")
            if len(button_list2) > 1:
                verify_btn = button_list2[1]
                time.sleep(2)
                print('Clicking confirmation button')
                verify_btn.click()
            print('Getting Finish button')
            finish_btn = get_visible_element(driver, By.XPATH, '//button[@aria-label="Finish"]')
            time.sleep(1)
            print('Clicking Finish button')
            finish_btn.click()
            print('Getting Finish button again')
            finish_btn2 = get_visible_element(driver, By.XPATH, '//button[@aria-label="Finish"]')
            time.sleep(1)
            print('Clicking Finish button again')
            finish_btn2.click()
        else:
            print('Failed to get verification code from SMS platform')
    else:
        print('Failed to get number from SMS platform')

def get_code_from_remote(id, driver):
    cur_time = int(time.time() * 1000)
    phone_code = get_code(id, cur_time)
    if phone_code:
        if phone_code == -1:
            print('No verification code received within 30 seconds, clicking resend')
            resend_btn = get_visible_element(driver, By.XPATH, '//*[@id="dialogContent_0"]/div/gv-stroked-button/span/button')
            if resend_btn:
                resend_btn.click()
                new_cur_time = int(time.time() * 1000)
                phone_code = get_code(id, new_cur_time)
                if phone_code and phone_code != -1:
                    return phone_code
    return phone_code

def is_in_conversation_page(driver, wait_time):
    try:
        element = get_visible_element(driver, By.ID, 'messaging-view', wait_time)
        if element:
            return element
    except Exception as e:
        print('is_in_conversation_page', e)

def is_register_success(driver):
    is_in_page = is_in_conversation_page(driver, 30000)
    if is_in_page:
        element = wait_until_get_one_element(driver, [
            (By.XPATH, '//*[local-name()="gv-conversation-list"]'),
            (By.CLASS_NAME, 'phone-number-details')
        ], 30000)
        if not element:
            print('Registration successful but not usable')
        else:
            print('Registration successful')
            return True

def get_visible_element(driver, by, value, wait_time=30000):
    try:
        element = WebDriverWait(driver, wait_time/1000).until(
            EC.visibility_of_element_located((by, value))
        )
        return element
    except TimeoutException:
        print('Failed to get element', value)

def wait_until_get_one_element(driver, identities, timeout):
    start_time = time.time()
    while time.time() - start_time < timeout/1000:
        print('Starting a new round of search')
        for i, (by, value) in enumerate(identities):
            try:
                element = get_visible_element(driver, by, value, 1000)
                if element:
                    print('Successfully got element', value)
                    return i, element
            except Exception as e:
                print('Failed to get element', e)

def get_visible_elements(driver, by, value, wait_time=30000):
    try:
        elements = WebDriverWait(driver, wait_time/1000).until(
            EC.visibility_of_all_elements_located((by, value))
        )
        return elements
    except TimeoutException:
        print('Failed to get elements', value)
        return None

def handle_recovery_email(driver, email):
    try:
        element = get_visible_element(driver, By.XPATH, '//div[text()="Confirm your recovery email"]', 2000)
        if element:
            print('Recovery email input page appeared')
            element.click()
            email_input = get_visible_element(driver, By.NAME, 'knowledgePreregisteredEmailResponse')
            if email_input:
                time.sleep(1)
                email_input.click()
                time.sleep(1)
                email_input.clear()
                time.sleep(1)
                print("Entering recovery email")
                email_input.send_keys(email)
                next_btn = get_visible_element(driver, By.XPATH, '//span[text()="Next"]')
                next_btn.click()
    except Exception as e:
        print('Failed to get recovery email page', e)

# The module exports are not needed in Python, as you can import the functions directly