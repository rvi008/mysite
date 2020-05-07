from bs4 import BeautifulSoup  
import requests
import yfinance as yf
import logging
from selenium import webdriver
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
        return data["name"], data["price"], data["currency"]
    else:
        logger.info("Retrieving %s's price from Yahoo Finance" % str(stock_symbol))
        stock_object = yf.Ticker(stock_symbol)
        stock_name = stock_object.info['shortName']
        stock_price = stock_object.history(period='1d')['Close'].values.tolist()[-1]
        stock_currency = stock_object.info["currency"].lower()
        redis_instance.hset(stock_symbol, "name", stock_name, {"price":stock_price, "currency":stock_currency})
        redis_instance.expire(stock_symbol, 15)
    return stock_name, stock_price, stock_currency

def retrieve_mslqd(redis_instance):
    logger.info("Retrieving data for LU0904783114")

    if redis_instance.exists("LU0904783114"):
        data = redis_instance.hgetall("LU0904783114")
        logger.info("Retrieving %s's price from redis" % "LU0904783114")
        return data["name"], data["price"], data["currency"]
    else:
        logger.info("Retrieving %s's price from Morgan Stanley" % "LU0904783114")
        soup = BeautifulSoup(requests.get(MSLQD_URL).text, 'html.parser')
        stock_name = "MS US Dollar Liquidity Fund"
        extract = soup.find_all('div', {"class": "stickyBoxBody"})[0].find_all('td')[9]
        stock_price = float(extract.text.strip().split(" ")[0])
        stock_currency = extract.text.strip().split(" ")[2].lower()
        redis_instance.hset("LU0904783114", "name", stock_name, {"price":stock_price, "currency":stock_currency})
        redis_instance.expire("LU0904783114", 28800)
    return stock_name, stock_price, stock_currency

def retrieve_bgf(isin, redis_instance):
    logger.info("Retrieving data for %s" % str(isin))

    if redis_instance.exists(isin):
        data = redis_instance.hgetall(isin)
        logger.info("Retrieving %s's price from redis" % isin)
        return data["name"], data["price"], data["currency"]

    else:
        driver = webdriver.Firefox(executable_path=os.getcwd()+"/geckodriver")
        driver.get(BGF[isin])
        stock_name = driver.find_element_by_xpath("//div[contains(@class, 'has-share-class-selector')]").text
        results = driver.find_elements_by_xpath("//*[@class='header-nav-data']")[0].text.split(" ")
        driver.quit()
        stock_price, stock_currency = results[1], results[0].lower()
        redis_instance.hset(isin, "name", stock_name, {"price":stock_price, "currency":stock_currency})
        redis_instance.expire(isin, 28800)
    return stock_name, stock_price, stock_currency

def retrieve_silver(coin, redis_instance):
    logger.info("Retrieving data for silver coin prices")
    if redis_instance.exists(coin):   
        data = redis_instance.hgetall(coin)
        logger.info("Retrieving %s's price from redis" % coin)
        return data["name"], data["price"], data["currency"]
    
    else:
        driver = webdriver.Firefox(executable_path=os.getcwd()+'/geckodriver')
        logger.info("Retrieving %s's price from website" % coin)
        url = SILVER_URL[coin]
        driver.get(url)
        driver.execute_script("window.scrollTo(0, 500)")  
        results = driver.find_element_by_xpath("//html").text
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
                        redis_instance.hset(coin, "name", stock_name, {"price":stock_price, "currency":stock_currency})
                        redis_instance.expire(stock_name, 28800)
                        break
            driver.quit()
        return stock_name, stock_price, stock_currency

def retrieve_gold(coin, redis_instance):

    logger.info("Retrieving data for %s gold coin prices"  % coin)
    if redis_instance.exists(coin):   
        data = redis_instance.hgetall(coin)
        logger.info("Retrieving %s's price from redis" % coin)
        return data["name"], data["price"], data["currency"]
    else:
        logger.info("Retrieving %s's price from Website" % coin)
        driver = webdriver.Firefox(executable_path=os.getcwd()+'/geckodriver')
        driver.get(GOLD_URL)
        driver.execute_script("window.scrollTo(0, 1000)")
        driver.find_element_by_xpath("//tr[@class='category']").click()
        driver.execute_script("window.scrollTo(0, 1500)")
        driver.find_element_by_xpath("//tr[@class='see-more']").click()
        driver.execute_script("window.scrollTo(0, 2000)")
        results = driver.find_element_by_xpath("//tbody").text
        driver.quit()

        for r in results.split("\n"):
            if GOLD_COINS[coin] in r:
                stock_name, stock_price, stock_currency = GOLD_COINS[coin], float(r.split(" ")[-1].replace(',','')), r.split(" ")[-2].lower()
                redis_instance.hset(coin, "name", stock_name, {"price":stock_price, "currency":stock_currency})
                redis_instance.expire(stock_name, 28800)
        return stock_name, stock_price, stock_currency

def retrieve_cl(platform, redis_instance):
    logger.info("Retrieving data for Crowdlending")

    if redis_instance.exists(platform):   
        data = redis_instance.hgetall(platform)
        logger.info("Retrieving %s's price from redis" % platform)
        return data["name"], data["price"], data["currency"]

    else:
        logger.info("Retrieving %s's price from website" % platform)
        driver = webdriver.Firefox(executable_path=os.getcwd()+'/geckodriver')
        url= CL_URLS[platform]
        navigation = CL_NAVIGATION[platform]
        driver.get(url)
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
        time.sleep(6)
        raw = [e.text for e in driver.find_elements_by_xpath(navigation["extract"]["desc_values"][0])][navigation["extract"]["item_num"]]
        time.sleep(5)
        driver.quit()
        stock_name, stock_price, stock_currency = platform, float(raw.split(" ")[0].replace(",",".")), raw.split(" ")[1].replace("€","eur")
        redis_instance.hset(platform, "name", stock_name, {"price":stock_price, "currency":stock_currency})
        redis_instance.expire(stock_name, 28800)
        return stock_name, stock_price, stock_currency

def retrieve_crypto(redis_instance):
    logger.info("Retrieving data for Cryptos")

    if redis_instance.exists("CRYPTO"):   
        data = redis_instance.hgetall("CRYPTO")
        logger.info("Retrieving %s's price from redis" % "Crypto")
        return data["name"], data["price"], data["currency"]
    else:
        logger.info("Retrieving %s's price from website" % "Crypto")
        driver = webdriver.Firefox(executable_path=os.getcwd()+'/geckodriver')
        driver.get(CRYPTO_URL)

        for nav in CRYPTO_NAVIGATION:
            if nav["descriptor"] == "class": nav_func = driver.find_elements_by_class_name
            else: nav_func = driver.find_elements_by_xpath
            if nav["action"] == "input_username": nav_func(nav["value"])[nav["item_num"]].send_keys(username)
            elif nav["action"] == "input_password": nav_func(nav["value"])[nav["item_num"]].send_keys(password)
            elif nav["action"] == "click": nav_func(nav["value"])[nav["item_num"]].click()
            else: res = [e for e in nav_func(nav["value"])[nav["item_num"]].text.split("\n") if "$" in e][nav["item_num"]]
            time.sleep(4)
    
        driver.quit()
        stock_name, stock_price, stock_currency = "Cryptomonnaies", float(res[1:]), res[0].replace("$", "usd")
        redis_instance.hset("CRYPTO", "name", stock_name, {"price":stock_price, "currency":stock_currency})
        redis_instance.expire(stock_name, 6000)
        return stock_name, stock_price, stock_currency
