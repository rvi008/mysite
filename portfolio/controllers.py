from bs4 import BeautifulSoup  
import requests
import yfinance as yf
import logging
from selenium import webdriver
from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as expected
from selenium.webdriver.support.wait import WebDriverWait
import os
import time
from portfolio.mappings import *
import decimal
import json
import re
from portfolio.credentials import *


# CREATING LOGGER
logger = logging.getLogger('LOG')
logger.setLevel(logging.INFO)

options = Options()
options.add_argument('-headless')

def convert_currency(currency, redis_instance):
    if redis_instance.exists(currency):
        data = redis_instance.hgetall(currency)
        logger.info("Retrieving %s's price from redis" % currency)
        return float(data["rate"])
    else:
        logger.info("Retrieving %s's price from Yahoo Finance" % currency)
        currency_object = yf.Ticker(CURRENCIES_TICKERS[currency])
        rate = float(currency_object.history(period='1d')['Close'].values.tolist()[-1])
        redis_instance.hset(currency, "rate", rate)
        redis_instance.expire(currency, 15)
        return rate

def retrieve_yf(stock_symbol, redis_instance):
    if redis_instance.exists(stock_symbol):
        data = redis_instance.hgetall(stock_symbol)
        logger.info("Retrieving %s's price from redis" % str(stock_symbol))
        return data["name"], data["price"], data["currency"], data["type"]
    else:
        logger.info("Retrieving %s's price from Yahoo Finance" % str(stock_symbol))
        stock_object = yf.Ticker(stock_symbol)
        stock_name = stock_object.info['shortName']
        stock_price = stock_object.history(period='1d')['Close'].values.tolist()[-1]
        stock_currency = stock_object.info["currency"].lower()
        stock_type = stock_object.info["quoteType"].lower()
        redis_instance.hset(stock_symbol, "name", stock_name, {"price":stock_price, "currency":stock_currency, "type":stock_type})
        redis_instance.expire(stock_symbol, 15)
    return stock_name, decimal.Decimal(stock_price)	, stock_currency, stock_type.replace("etf","equity")

def retrieve_mslqd(redis_instance):
    logger.info("Retrieving data for LU0904783114")

    if redis_instance.exists("LU0904783114"):
        data = redis_instance.hgetall("LU0904783114")
        logger.info("Retrieving %s's price from redis" % "LU0904783114")
        return data["name"], data["price"], data["currency"], data["type"]
    else:
        logger.info("Retrieving %s's price from Morgan Stanley" % "LU0904783114")
        soup = BeautifulSoup(requests.get(MSLQD_URL).text, 'html.parser')
        stock_name = "MS US Dollar Liquidity Fund"
        extract = soup.find_all('div', {"class": "stickyBoxBody"})[0].find_all('td')[9]
        stock_price = float(extract.text.strip().split(" ")[0])
        stock_currency = extract.text.strip().split(" ")[2].lower()
        stock_type = "bond"
        redis_instance.hset("LU0904783114", "name", stock_name, {"price":stock_price, "currency":stock_currency, "type":stock_type})
        redis_instance.expire("LU0904783114", 28800)
    return stock_name, stock_price, stock_currency, stock_type

def retrieve_bgf(isin, redis_instance):
    logger.info("Retrieving data for %s" % str(isin))

    if redis_instance.exists(isin):
        data = redis_instance.hgetall(isin)
        logger.info("Retrieving %s's price from redis" % isin)
        return data["name"], data["price"], data["currency"], data["type"]

    else:
        driver = webdriver.Firefox(executable_path=os.getcwd()+"/geckodriver", options=options)
        driver.get(BGF[isin])
        WebDriverWait(driver, 2)
        stock_name = driver.find_element_by_xpath("//div[contains(@class, 'has-share-class-selector')]").text
        WebDriverWait(driver, 2)
        results = driver.find_elements_by_xpath("//*[@class='header-nav-data']")[0].text.split(" ")
        WebDriverWait(driver, 2)
        driver.quit()
        stock_price, stock_currency, stock_type = results[1], results[0].lower(), "equity"
        redis_instance.hset(isin, "name", stock_name, {"price":stock_price, "currency":stock_currency, "type":stock_type})
        redis_instance.expire(isin, 28800)
    return stock_name, stock_price, stock_currency, stock_type

def retrieve_silver(coin, redis_instance):
    logger.info("Retrieving data for silver coin prices")
    if redis_instance.exists(coin):   
        data = redis_instance.hgetall(coin)
        logger.info("Retrieving %s's price from redis" % coin)
        return data["name"], data["price"], data["currency"], data["type"]
    
    else:
        driver = webdriver.Firefox(executable_path=os.getcwd()+'/geckodriver', options=options)
        logger.info("Retrieving %s's price from website" % coin)
        url = SILVER_URL[coin]
        driver.get(url)
        WebDriverWait(driver, 2)
        driver.execute_script("window.scrollTo(0, 500)")
        WebDriverWait(driver, 2)
        results = driver.find_element_by_xpath("//html").text
        WebDriverWait(driver, 2)
        splitted = results.split("\n")
        temp_dict = {}
        for i,r  in enumerate(splitted):
            if SILVER_COINS[coin] in r:
                logger.info("Coin Found %s" % splitted[i])
                for j in range(10):
                    if "VENTE" in splitted[i+j]:
                        vente = splitted[i+j]
                        logger.info("Prix de vente trouvé %s" % str(splitted[i+j]))
                        temp_dict[coin] = splitted[i+j].replace("VENTE","").replace("€","eur").strip()
                        parsed = temp_dict[coin].split(" ")
                        stock_name, stock_price, stock_currency = SILVER_COINS[coin], float(parsed[0]), parsed[1]
                        stock_type = "metal"
                        redis_instance.hset(coin, "name", stock_name, {"price":stock_price, "currency":stock_currency, "type":stock_type})
                        redis_instance.expire(coin, 10000)
                        break
            driver.quit()
        return stock_name, stock_price, stock_currency, stock_type

def retrieve_gold(coin, redis_instance):

    logger.info("Retrieving data for %s gold coin prices"  % coin)
    if redis_instance.exists(coin):   
        data = redis_instance.hgetall(coin)
        logger.info("Retrieving %s's price from redis" % coin)
        return data["name"], data["price"], data["currency"], data["type"]
    else:
        logger.info("Retrieving %s's price from Website" % coin)
        driver = webdriver.Firefox(executable_path=os.getcwd()+'/geckodriver', options=options)
        driver.get(GOLD_URL)
        WebDriverWait(driver, 2)
        driver.execute_script("window.scrollTo(0, 1000)")
        WebDriverWait(driver, 2)
        driver.find_element_by_xpath("//tr[@class='category']").click()
        WebDriverWait(driver, 2)
        driver.execute_script("window.scrollTo(0, 1500)")
        WebDriverWait(driver, 2)
        driver.find_element_by_xpath("//tr[@class='see-more']").click()
        WebDriverWait(driver, 2)
        driver.execute_script("window.scrollTo(0, 2000)")
        WebDriverWait(driver, 2)
        results = driver.find_element_by_xpath("//tbody").text
        WebDriverWait(driver, 2)
        driver.quit()

        for r in results.split("\n"):
            if GOLD_COINS[coin] in r:
                stock_name, stock_price, stock_currency = GOLD_COINS[coin], float(r.split(" ")[-1].replace(',','')), r.split(" ")[-2].lower()
                redis_instance.hset(coin, "name", stock_name, {"price":stock_price, "currency":stock_currency, "type":"metal"})
                redis_instance.expire(coin, 10000)
        return stock_name, stock_price, stock_currency, "metal"

def retrieve_cl(platform, redis_instance):
    logger.info("Retrieving data for Crowdlending")

    if redis_instance.exists(platform):   
        data = redis_instance.hgetall(platform)
        logger.info("Retrieving %s's price from redis" % platform)
        return data["name"], data["price"], data["currency"], data["type"]

    else:
        logger.info("Retrieving %s's price from website" % platform)
        driver = webdriver.Firefox(executable_path=os.getcwd()+'/geckodriver', options=options)
        url= CL_URLS[platform]
        navigation = CL_NAVIGATION[platform]
        driver.get(url)
        driver.find_element_by_id(navigation["login"]["desc_values"][0]).send_keys(username)
        driver.find_element_by_id(navigation["login"]["desc_values"][1]).send_keys(password)
        driver.find_element_by_id(navigation["login"]["desc_values"][2]).click()
        WebDriverWait(driver, 2)

        if navigation["home"]["descriptor"] == "id":
            nav_func = driver.find_element_by_id
        else:
            nav_func = driver.find_element_by_class_name
        for i in range(5):
            try:
                nav_func(navigation["home"]["desc_values"][0]).click()
            except:
                driver.refresh()
                WebDriverWait(driver, 2)
                continue
        WebDriverWait(driver, 2)
        raw = [e.text for e in driver.find_elements_by_xpath(navigation["extract"]["desc_values"][0])][navigation["extract"]["item_num"]]
        WebDriverWait(driver, 2)
        driver.quit()
        stock_type = "bond"
        stock_name, stock_price, stock_currency = platform, float(raw.split(" ")[0].replace(",",".")), raw.split(" ")[1].replace("€","eur")
        redis_instance.hset(platform, "name", stock_name, {"price":stock_price, "currency":stock_currency, "type":stock_type})
        redis_instance.expire(stock_name, 300000)
        return stock_name, stock_price, stock_currency, stock_type