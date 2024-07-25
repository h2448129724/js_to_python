
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from utils import get_json_from_excel, delayed, get_date
from request import open_browser
from sms_request import request_phone_num, get_code
from register import get_visible_element,get_visible_elements
def send_message(driver, message):
    message_nav = select_message_nav(driver)
    if message_nav:
        had_msg = None
        try:
            had_msg = get_visible_elements(driver, By.XPATH, '//a[contains(@aria-label,"Messages:")]')
        except Exception:
            pass
        if had_msg:
            return 'hadUnreadMsg'
        else:
            try:
                loading_view = driver.find_element(By.CLASS_NAME, 'gvMessagingView-loading')
                WebDriverWait(driver, 30).until(EC.invisibility_of_element(loading_view))
            except Exception as e:
                driver.execute_script("document.querySelector('.gvMessagingView-loading').style.display = 'none';")
                delayed(1000)
            conversation_list = get_visible_element(driver, By.XPATH, '//*[local-name()="gv-conversation-list"]')
            if conversation_list:
                add_message_btn = get_visible_element(driver, By.CLASS_NAME, 'gvMessagingView-actionButton')
                if add_message_btn:
                    delayed(2000)
                    add_message_btn.click()
                    delayed(2000)
                    input_div = get_visible_element(driver, By.CLASS_NAME, 'input-field')
                    if input_div:
                        number_input = input_div.find_element(By.TAG_NAME, 'input')
                        if number_input:
                            delayed(1000)
                            number_input.clear()
                            delayed(2000)
                            number_input.send_keys(message["phone"])
                            number_input.send_keys(',')
                            number_input.send_keys(Keys.ESCAPE)
                            delayed(2000)
                            try:
                                had_msg = get_visible_elements(driver, By.XPATH, '//a[contains(@aria-label,"Messages:")]')
                                if had_msg:
                                    return 'hadUnreadMsg'
                            except Exception:
                                pass
                            delete_icon = get_visible_elements(driver, By.CLASS_NAME, 'mat-mdc-chip-remove')
                            if delete_icon and len(delete_icon) > 0:
                                message_input = get_visible_element(driver, By.CLASS_NAME, 'message-input')
                                if message_input:
                                    message_input.click()
                                    delayed(1000)
                                    message_input.clear()
                                    delayed(1000)
                                    message_input.send_keys(message["message"])
                                    delayed(2000)
                                    send_btn = get_visible_element(driver, By.XPATH, '//button[@aria-label="Send message"]')
                                    if send_btn:
                                        send_btn.click()
                                        delayed(5000)
                                        if is_msg_send_success(driver):
                                            return 'sendSuccess'
                                        else:
                                            return 'sendFailed'
                                    else:
                                        return 'noSendButton'
                else:
                    return 'noAddMessageButton'
    else:
        return 'noMessageNav'

def select_message_nav(driver):
    elements = get_visible_elements(driver, By.XPATH, '//*[@id="gvPageRoot"]/div[2]/gv-side-panel/mat-sidenav-container/mat-sidenav-content/div/div[2]/gv-side-nav/div/div/mat-nav-list/a[2]')
    if elements:
        elements[0].click()
        return elements[0]

def is_msg_send_success(driver):
    elements = get_visible_elements(driver, By.CLASS_NAME, 'status')
    if elements:
        last_element = elements[-1]
        WebDriverWait(driver, 10).until(EC.text_matches(last_element, r'\b\d{1,2}:\d{2}\s+[AP]M\b'))
        return True
    return False
