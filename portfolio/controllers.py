from bs4 import BeautifulSoup  
import requests
import yfinance as yf
import logging
from selenium import webdriver
import os
import time
from .mappings import MSLQD_URL, BGF, CURRENCIES_TICKERS, GOLD_URL, GOLD_COINS, SILVER_COINS, SILVER_URL, CL_URLS, CL_NAVIGATION, CRYPTO_URL, CRYPTO_NAVIGATION
import decimal
import json
import re
from .credentials import username, password


# CREATING LOGGER
logger = logging.getLogger('LOG')
logger.setLevel(logging.ERROR)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)


def convert_currency(currency):
    currency_object = yf.Ticker(CURRENCIES_TICKERS[currency])
    rate = float(currency_object.history(period='1d')['Close'].values.tolist()[-1])	
    return rate

def retrieve_yf(stock_symbol):
    stock_object = yf.Ticker(stock_symbol)
    stock_name = stock_object.info['shortName']
    stock_price = stock_object.history(period='1d')['Close'].values.tolist()[-1]
    stock_currency = stock_object.info["currency"].lower()
    return stock_name, stock_price, stock_currency

def retrieve_mslqd():
    logger.info("Retrieving data for LU0904783114")
    soup = BeautifulSoup(requests.get(MSLQD_URL).text, 'html.parser')
    extract = soup.find_all('div', {"class": "stickyBoxBody"})[0].find_all('td')[9]
    stock_price = float(extract.text.strip().split(" ")[0])
    currency = extract.text.strip().split(" ")[2].lower()
    return "MS US Dollar Liquidity Fund", stock_price, currency

def retrieve_bgf(isin):
    logger.info("Retrieving data for %s" % str(isin))
    driver = webdriver.Firefox(executable_path=os.getcwd()+"/geckodriver")
    try:
        driver.get(BGF[isin])
        title = driver.find_element_by_xpath("//div[contains(@class, 'has-share-class-selector')]").text
        results = driver.find_elements_by_xpath("//*[@class='header-nav-data']")[0].text.split(" ")
        driver.quit()
    except Exception as e:
        logger.error(e)
    return title, results[1], results[0].lower()

def retrieve_silver(coin):
    if not os.path.exists(os.getcwd()+"/silver_prices_"+time.strftime("%Y%m%d")+".txt"):
        logger.info("Retrieving data for silver coin prices")
        driver = webdriver.Firefox(executable_path=os.getcwd()+'/geckodriver')
        output = {}

        for url in SILVER_URL:
            driver.get(url)
            driver.execute_script("window.scrollTo(0, 500)")  
            results = driver.find_element_by_xpath("//html").text

            splitted = results.split("\n")
            for name in SILVER_COINS.values():
                for i,r  in enumerate(splitted):
                    if name in r:
                        logger.info("Coin Found %s" % splitted[i])

                        for j in range(10):
                            if "VENTE" in splitted[i+j]:
                                vente = splitted[i+j]
                                logger.info("Prix de vente trouvé %s" % str(splitted[i+j]))
                                output[name] = splitted[i+j].replace("VENTE","").replace("€","eur").strip()
                                break


        with open(os.getcwd()+"/silver_prices_"+time.strftime("%Y%m%d")+".txt","w") as file:
            logger.info("Writing today's prices to disk")
            json.dump(output, file) 

        driver.quit()

    with open(os.getcwd()+"/silver_prices_"+time.strftime("%Y%m%d")+".txt","r") as file:
        logger.info("Reading silver prices from disk")
        prices = json.load(file)
        parsed = prices[SILVER_COINS[coin]].split(" ")
        return SILVER_COINS[coin], decimal.Decimal(parsed[0]), parsed[1]

def retrieve_gold(coin):

    if not os.path.exists(os.getcwd()+"/gold_prices_"+time.strftime("%Y%m%d")+".txt"):
        logger.info("Retrieving data for gold coin prices")
        driver = webdriver.Firefox(executable_path=os.getcwd()+'/geckodriver')
        driver.get(GOLD_URL)
        driver.execute_script("window.scrollTo(0, 1000)")
        driver.find_element_by_xpath("//tr[@class='category']").click()
        driver.execute_script("window.scrollTo(0, 1500)")
        driver.find_element_by_xpath("//tr[@class='see-more']").click()
        driver.execute_script("window.scrollTo(0, 2000)")
        result = driver.find_element_by_xpath("//tbody").text
        driver.quit()

        with open(os.getcwd()+"/gold_prices_"+time.strftime("%Y%m%d")+".txt","w") as file:
            logger.info("Writing today's prices to disk")
            file.write(result)

    with open(os.getcwd()+"/gold_prices_"+time.strftime("%Y%m%d")+".txt","r") as file:
        logger.info("Reading gold prices from disk")
        results = file.read().split("\n")

        for r in results:
            if GOLD_COINS[coin] in r:
                return GOLD_COINS[coin], decimal.Decimal(r.split(" ")[-1].replace(',','')), r.split(" ")[-2].lower()

def retrieve_cl(platform):
    logger.info("Retrieving data for crowdlending")
    driver = webdriver.Firefox(executable_path=os.getcwd()+'/geckodriver')
    url= CL_URLS[platform]
    navigation = CL_NAVIGATION[platform]
    res = driver.get(url)
    driver.find_element_by_id(navigation["login"]["desc_values"][0]).send_keys(username)
    driver.find_element_by_id(navigation["login"]["desc_values"][1]).send_keys(password)
    driver.find_element_by_id(navigation["login"]["desc_values"][2]).click()
    time.sleep(5)

    if navigation["home"]["descriptor"] == "id":
        nav_func = driver.find_element_by_id
    else:
    	nav_func = driver.find_element_by_class_name
    try:
        nav_func(navigation["home"]["desc_values"][0]).click()
    except:
        for i in range(5):
            time.sleep(10)
            nav_func(navigation["home"]["desc_values"][0]).click()
    time.sleep(5)
    raw = [e.text for e in driver.find_elements_by_xpath(navigation["extract"]["desc_values"][0])][navigation["extract"]["item_num"]]
    time.sleep(5)
    driver.quit()
    return platform, decimal.Decimal(raw.split(" ")[0].replace(",",".")), raw.split(" ")[1].replace("€","eur")

def retrieve_crypto():

    driver = webdriver.Firefox(executable_path=os.getcwd()+'/geckodriver')
    driver.get(CRYPTO_URL)

    for nav in CRYPTO_NAVIGATION:
        if nav["descriptor"] == "class": nav_func = driver.find_elements_by_class_name
        else: nav_func = driver.find_elements_by_xpath
        if nav["action"] == "input_username": nav_func(nav["value"])[nav["item_num"]].send_keys(username)
        elif nav["action"] == "input_password": nav_func(nav["value"])[nav["item_num"]].send_keys(password)
        elif nav["action"] == "click": nav_func(nav["value"])[nav["item_num"]].click()
        else: res = [e for e in nav_func(nav["value"])[nav["item_num"]].text.split("\n") if "$" in e][nav["item_num"]]
        time.sleep(3)
    driver.quit()
    
    currency, price = res[0].replace("$", "usd"), decimal.Decimal(res[1:])
    return "Cryptomonnaies", price, currency
