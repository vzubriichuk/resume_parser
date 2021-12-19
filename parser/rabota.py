#!/usr/bin/env python
# coding:utf-8
"""
Author : Vitaliy Zubriichuk
Contact : v@zubr.kiev.ua
Time    : 14.12.2021 9:44
"""
import os
import threading
import json
import time
import pandas as pd
import config

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException
from datetime import datetime
from icecream import ic

from logger import logger


logger = logger('Rabota')

def time_format():
    return f'{datetime.now()}|> '

"""
Инициализация класса + функция авторизации
"""


class Rabota(threading.Thread):
    def __init__(self, headless=False, download_path=os.getcwd() + '\\download'):
        super().__init__()
        self.chrome_options = webdriver.ChromeOptions()
        prefs = {'profile.default_content_settings.popups': 0,
                 "download.prompt_for_download": False,
                 'download.default_directory': download_path}
        service = Service(os.getcwd() + '\\chromedriver.exe')
        self.chrome_options.add_argument('--disable-download-notification')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36')
        self.chrome_options.add_experimental_option('prefs', prefs)
        self.chrome_options.headless = headless
        try:
            self.driver = webdriver.Chrome(options=self.chrome_options,
                                           service=service)
        except Exception as error:
            chromedriver_downoad = 'https://chromedriver.chromium.org/downloads'
            logger.info(f'Необходимо обновить Chromedriver, загрузив подходящую версию по адресу {chromedriver_downoad}')
            logger.critical(error, exc_info=True)

    def authorisation(self, login, password):
        logger.info(f'{time_format()} Авторизация')
        url = 'https://rabota.ua/employer/login'
        self.driver.get(url)
        self.driver.set_page_load_timeout(45)
        if self.driver.execute_script('return document.readyState;') == 'complete':
            login_xpath = '//*[@id="ctl00_content_ZoneLogin_txLogin"]'
            try:
                WebDriverWait(self.driver, 40).until(
                    lambda d: self.driver.find_element(By.XPATH, login_xpath))
            except Exception as error:
                logger.critical(error, exc_info=True)
                return False
            self.driver.find_element(By.XPATH, login_xpath).send_keys(login)

            password_xpath = '//*[@id="ctl00_content_ZoneLogin_txPassword"]'
            self.driver.find_element(By.XPATH, password_xpath).send_keys(password)

            entrance = '//*[@id="ctl00_content_ZoneLogin_btnLogin"]'
            self.driver.find_element(By.XPATH, entrance).click()
            try:
                assert 'Неправильный логин или пароль' not in self.driver.page_source
                return True
            except AssertionError as error:
                logger.exception(error)
                return False

    def end(self):
        self.driver.quit()

    def test(self):
        self.driver.execute_script("window.open('');")
        self.driver.switch_to.window(self.driver.window_handles[-1])


"""
Парсит резюме по поисковому запросу
"""


class Parser(Rabota):
    def __init__(self, headless=False, download_path=os.getcwd() + '\\download'):
        super().__init__(headless, download_path)
        self.cv_url_list = []
        self.uid_list = []
        self.candidates = {}
        self.href = str
        self.uid = int
        self.name = str
        self.position = str
        self.phone = ''
        self.city = str
        self.salary = str
        self.age = str
        self.cv_note = ''
        self.download_path = download_path

    def parsing_query(self, query_search=str, query_number=int):
        """
        Парсит список резюме по запросу
        query_search: строка запроса
        query_number: порядковый номер запроса
        """
        logger.info(f'{time_format()} Отправка запроса # {query_number} и получение списка резюме')
        self.driver.get(query_search)
        time.sleep(5)
        temp_uid_list = []
        page = 1
        while True and len(temp_uid_list) <= 20:
            self.driver.refresh()
            try:
                if self.driver.execute_script('return document.readyState;') == 'complete':
                    # print(f'\n{page}\n')
                    cards = '//alliance-employer-cvdb-cv-list-card'
                    WebDriverWait(self.driver, 40).until(lambda d: self.driver.find_element(By.XPATH, cards))
                    elements = self.driver.find_elements(By.XPATH, cards)
                    for element in elements:
                        # if element.is_displayed():
                        #     var = element.location_once_scrolled_into_view
                        # try:
                        #     # если находим уже просмотренное резюме, то пропускаем
                        #     element.find_element(By.CLASS_NAME, 'santa-opacity-50')
                        #     continue
                        # except NoSuchElementException:
                        #     pass
                        a = element.find_element(By.TAG_NAME, 'a')
                        info = [i.text for i in a.find_elements(By.TAG_NAME, 'p')][:-2]
                        self.cv_url_list.append(a.get_attribute('href'))
                        self.href = (a.get_attribute('href'))
                        self.uid = self.href.replace('https://rabota.ua/candidates/', "")
                        temp_uid_list.append(self.uid)
                        self.uid_list.append(self.uid)
                        try:
                            self.cv_note = element.find_element(By.CLASS_NAME, 'santa-bg-yellow-100')
                            info.pop(1)
                        except NoSuchElementException:
                            pass
                        self.position = info[0]
                        self.name = info[1]
                        try:
                            self.city = info[2]
                        except IndexError:
                            self.city = 'Не указан'
                        try:
                            self.age = info[3]
                        except IndexError:
                            self.age = 'Не указан'
                        try:
                            self.salary = info[4]
                        except IndexError:
                            self.salary = 'Не указан'
                        self.candidates[f'{int(self.uid)}'] = {
                            "url": self.href,
                            "name": self.name,
                            "position": self.position,
                            "city": self.city,
                            "age": self.age,
                            "salary": self.salary,
                            "phone": ''
                        }
                    try:
                        if page == 1:
                            button_next = '//div/nav/santa-pagination/div/div[6]'
                        else:
                            button_next = '//div/nav/santa-pagination/div/div[7]'
                        next_page = self.driver.find_element(By.XPATH, button_next)
                        var = next_page.location_once_scrolled_into_view
                        next_page.click()
                    except NoSuchElementException:
                        # print('Страницы закончились')
                        break
            except (StaleElementReferenceException, TimeoutException) as e:
                logger.warning(e)
            page += 1


    def run_parsing_cv(self):
        """
        Проходит по списку uid и url адресов вакансий, передает их по очереди
        в функцию parsing_cv откуда дополнительно парсится телефон
        в конце запускает сохранение словаря с данными
        """
        count_cv = len(self.uid_list)
        logger.info(f'{time_format()} Проход по списку собранных резюме: {count_cv} шт.')
        cv = 1
        for uid in self.uid_list:
            time.sleep(3)
            print('#',cv, self.candidates[f'{uid}']['url'])
            url = self.candidates[f'{uid}']['url']
            self.parsing_cv(uid, url)
            cv += 1
        json_obj = json.dumps(self.candidates, indent=4, ensure_ascii=False)
        # print(json_obj)
        self.save_data_to_excel()
        self.driver.quit()


    def parsing_cv(self, uid, url):
        """
        Парсит по очереди каждое резюме по url, грабит номер телефона
        и добавляет его в словарь
        """
        self.driver.get(url)
        if self.driver.execute_script('return document.readyState;') == 'complete':
            card = '//alliance-employer-cvdb-resume'
            WebDriverWait(self.driver, 40).until(lambda d: self.driver.find_element(By.XPATH, card))
            elements = self.driver.find_elements(By.XPATH, card)
            for element in elements:
                try:
                    open_button = '//santa-button-spinner/div/santa-button/button'
                    self.driver.find_element(By.XPATH, open_button).click()
                    time.sleep(2)
                    continue
                except NoSuchElementException:
                    pass
                try:
                    time.sleep(2)
                    phone_element = '//alliance-shared-ui-copy-to-clipboard/p/a'
                    phone = element.find_element(By.XPATH, phone_element)
                    self.phone = phone.text
                    # print(self.phone)
                    continue
                except NoSuchElementException:
                    pass
            self.candidates[f'{uid}']['phone'] = self.phone


    def save_data_to_excel(self):
        """
        Обрабатывает словарь спарсенных данных и сохраняет в Excel
        """
        logger.info('{time_format()} Сохранение результатов в файл.')
        # вместо зарплаты может спарситься левый текст, проверяем

        for uid in self.uid_list:
            if self.candidates[f'{uid}']['salary'][0].isdigit():
                pass
            else:
                self.candidates[f'{uid}']['salary'] = 'Не указана'
        df = pd.DataFrame.from_dict(self.candidates, orient='index')
        df.to_excel('cv_rabota_response.xlsx')
        # json_obj = json.dumps(self.candidates, indent=4, ensure_ascii=False)


query_list = []

def get_query_list():
    with open('search_query_list.txt', 'r', encoding='utf-8') as f:
        for line in f:
            currentline = line.split(",")
            position = currentline[0].strip()
            city = currentline[1].strip()
            query_list.append(f'https://rabota.ua/candidates/{position}/{city}')


if __name__ == '__main__':
    login = config.LOGIN
    password = config.PASSWORD
    headless = True
    parser = Parser(headless)
    parser.authorisation(login, password)
    get_query_list()

    query_num = 1
    for query in query_list:
        count_query = len(query_list)
        ic(query_num)
        ic(query)
        parser.parsing_query(query, query_num)
        query_num += 1

    parser.run_parsing_cv()



