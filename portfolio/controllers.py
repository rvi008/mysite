from bs4 import BeautifulSoup  
import requests
import yfinance as yf
import logging
from selenium import webdriver
import os
import time


MSLQD_URL='https://www.morganstanley.com/im/en-nl/liquidity-investor/product-and-performance/morgan-stanley-liquidity-funds/us-dollar-liquidity-fund.shareClass.QU.html'
BGF = {"LU0122376428":"https://www.blackrock.com/sg/en/terms-and-conditions?targetUrl=%2Fsg%2Fen%2Fproducts%2F229927%2Fbgf-world-energy-fund-a2-sgd-hedged&action=ACCEPT",
"LU0368265764":"https://www.blackrock.com/sg/en/terms-and-conditions?targetUrl=%2Fsg%2Fen%2Fproducts%2F229951%2Fbgf-world-gold-fund-a2-sgd-hedged&action=ACCEPT"}
CURRENCIES_TICKERS = {"usd":"EUR=X", "sgd":"SGDEUR=X", "gbp":"GBPEUR=X"}
GOLD_URL="https://www.bullionstar.com/sell/"



# CREATING LOGGER
logger = logging.getLogger('LOG')
logger.setLevel(logging.INFO)

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
        logging.error(e)
    return title, results[1], results[0].lower()

def retrieve_gold_prices():
    logger.info("Retrieving data for gold coin prices")
    driver = webdriver.Firefox(executable_path='./geckodriver')
    driver.get(url)
    driver.execute_script("window.scrollTo(0, 1000)")
    driver.find_element_by_xpath("//tr[@class='category']").click()
    driver.execute_script("window.scrollTo(0, 1500)")
    driver.find_element_by_xpath("//tr[@class='see-more']").click()
    driver.execute_script("window.scrollTo(0, 2000)")
    result = driver.find_element_by_xpath("//tbody").text

    with open("gold_prices_"+time.strftime("%Y%m%d")) as file:
    	logger.info("Writing today's prices to disk")
        file.write(result)



