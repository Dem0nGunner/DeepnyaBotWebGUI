from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

#____Interface____
def OPEN(port):
    driver = start_chrome(port)
    driver.get("https://vk.ru/im/convo/-219688902?entrypoint=list_all")
    return driver
def PRINT_MESSAGE(driver,message):
    text_enter(driver, "span[contenteditable='true'][data-placeholder='Сообщение']",By.CSS_SELECTOR,message)
    but_click(driver, "[aria-label='Отправить сообщение']", By.CSS_SELECTOR)
def CLOSE(driver):
    close_chrome(driver)
def REPEAT_GENERATION(driver):
    if last_but_click(driver,By.XPATH,'//button[contains(@title, "Повторить")]'):
        return True
    else:
        return False
def UPGRADE_GENERATION(driver):
    if last_but_click(driver,By.XPATH, '//button[contains(@title, "Улучшить")]'):
        return True
    else:
        return False
def CHECK(driver):
    if (driver.current_url == "https://vk.ru/im/convo/-219688902?entrypoint=list_all") or(driver.current_url == "https://vk.ru/im/convo/-219688902?entrypoint=vkcom_right_column_menu"):
        print("Проверка (в чате)")
        return
    else:
        driver.get("https://vk.ru/im/convo/-219688902?entrypoint=list_all")
        print("Проверка (не в чате)")
def GET_LAST_MESSAGE(driver):
    return get_last_message_itemkey(driver)
def WAITER_NEXT_MESSAGE(driver,imessage):
    return wait_for_next_message(driver,imessage)
def FIND_CONTENT(driver,mod,key):
    return find_answer(driver, mod, key)
def CHAT_SCROLL_DOWN(driver,message_ind):
    chat_slider(driver,message_ind)
def REFRESH(driver):
    driver.refresh()
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((
            By.CSS_SELECTOR,
            'div.VirtualScrollItem[data-itemkey]'
        )))
    return True


def GENERATE_AND_WAIT(driver, action_func, last_message):
    """
    Выполняет действие и ждёт результат генерации.
    Возвращает URL картинки или None.
    """
    # Выполняем действие (отправка/повтор/улучшение)
    action_func(driver)

    # Ждём "Генерирую..."
    print("Пиздец")
    key1 = wait_for_next_message(driver, last_message)
    print(key1)
    chat_slider(driver,last_message)
    git = find_answer(driver, 1, key1)
    print(git)
    if str(git) != "Генерирую...":
        print("ХехT")
        return None

    # Ждём "Готово" с картинкой
    print("СКА")
    key2 = wait_for_next_message(driver, int(key1))
    print(key2)
    url = find_answer(driver, 2, int(key2))
    print("ОГО")

    return url
#____Const____
DEBUG_PORT = 9222
#____Open_Chrome____
def start_chrome(port):
    options = Options()
    options.add_argument(f"--remote-debugging-port={port}")
    options.add_argument("--user-data-dir=C:/temp/chrome-automation")
    #options.add_argument("--headless")
    return webdriver.Chrome(options=options)
#____Close_Chrome____
def close_chrome(driver):
    driver.quit()
#____Waiter____
def wait_a_min(driver, BY, search):
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((BY, search)))
    print("New_check")

#____Text_Edit____
def text_enter(driver, search,BY,text):
    wait_a_min(driver, BY, search)
    input_field = driver.find_element(BY, search)
    input_field.clear()
    input_field.send_keys(text)
#____Button_Click____
def but_click(driver,search,BY):
    wait_a_min(driver, BY, search)
    print(driver.find_element(BY, search).get_attribute("title"))
    driver.find_element(BY, search).click()
#____Last_Button_Click____
def last_but_click(driver,BY,search):
    print("New_check")
    driver.refresh()
    wait_a_min(driver, BY, search)
    all_buttons = driver.find_elements(BY,search)
    print(all_buttons)
    if all_buttons:
        last_btn = all_buttons[-1]
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", last_btn)
        #but_click(driver, search, BY)
        driver.execute_script("arguments[0].click();", last_btn)
        return True
    else:
        print(f"Кнопки '{search}' не найдены")
        return False
#____Get_Message_Count____
def get_last_message_itemkey(driver):
    items = driver.find_elements(
        By.CLASS_NAME,
        'VirtualScrollItem'
    )
    if not items:
        raise Exception("Сообщения не найдены")
    last_item = items[-1]
    itemkey = last_item.get_attribute('data-itemkey')
    print(itemkey)
    return itemkey
#____Result_Waiter____
def wait_for_next_message(driver, current_itemkey, timeout=120):
    try:
        expected_key = int(current_itemkey) + 1
    except (ValueError, TypeError) as e:
        raise ValueError(f"Не удалось преобразовать current_itemkey '{current_itemkey}' в int: {e}")

    selector = f'div.VirtualScrollItem[data-itemkey="{expected_key}"]'

    wait = WebDriverWait(driver, timeout)
    message = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, selector)),
        message=f"Сообщение с data-itemkey='{expected_key}' не появилось за {timeout} секунд"
    )
    print(message)
    return str(expected_key)
#____Find_Answer_Gen____
def find_answer(driver, mod, key):
    if mod==1:
        print("Вход")
        item = driver.find_element(By.CSS_SELECTOR, f'div.VirtualScrollItem[data-itemkey="{key}"]')
        print(item.get_attribute('data-itemkey'))
        chat_slider(driver, key)
        wait = WebDriverWait(driver, 10)
        span_item = wait.until(EC.presence_of_all_elements_located((By.XPATH, './/span[@class="MessageText ConvoMessage__text"]')))
        # Получаем чистый текст через JavaScript, игнорируя вложенные <img>
        import time
        time.sleep(5)
        try:
            huinya = span_item[-1].text.strip()
            print(huinya)
        except:
            print("Хуйня не нахуярилась")
        return huinya
    elif mod==2:
        wait = WebDriverWait(driver, 120)
        item = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, f'div.VirtualScrollItem[data-itemkey="{key}"]')))
        if item.find_element(By.CSS_SELECTOR, 'img'):
            src = item.find_element(By.CSS_SELECTOR, 'img')
            return (src.get_attribute('src'))
        else:
            return None
    #else:
        #raise ValueError("Не верно введён мод")
        # Ищем именно картинку сообщения, а не эмодзи
        #imgs = item.find_elements(By.CSS_SELECTOR, 'img.PhotoItem__img')
        #if imgs:
        #    return imgs[0].get_attribute('src')
        #return None
    else:
        raise ValueError("Не верно введён мод")
#____Slide_Down____
def chat_slider(driver,message_ind):
    try:
        selector = f'div.VirtualScrollItem[data-itemkey="{message_ind}"]'
        wait = WebDriverWait(driver, 10)
        next_message = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector)),
            message=f"Сообщение с data-itemkey='{message_ind}' не появилось за {10} секунд"
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_message)
    except Exception as e:
        print(e)

#____Main_Process_(For_Tests)____
if __name__ == "__main__":
    driver = start_chrome(DEBUG_PORT)
    driver.get("https://vk.ru/im/convo/-219688902?entrypoint=list_all")
    text_enter(driver, "span[contenteditable='true'][data-placeholder='Сообщение']",By.CSS_SELECTOR,"gen (@laliberte:1.3), katarina \(League of Legends\), battle pose, red lipstick, Irish, gold eyes, long red hair, leather armor /(katarina/), high collar, shoulder pads, small broad swords, reverse grip, left eyes scar, skin blush, left side tattoo, abs, wide chest, sweat, bite lips, (freckles:1.2), wet spots, halfside shot")
    but_click(driver,"[aria-label='Отправить сообщение']",By.CSS_SELECTOR)
    input("Нажмите Enter, чтобы закрыть Chrome...")
    close_chrome(driver)