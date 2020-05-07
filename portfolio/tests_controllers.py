from django.test import TestCase
from django.conf import settings
import redis
from portfolio.mappings import *
from portfolio.controllers import *
import yfinance as yf



class ControllersTestCase(TestCase):
    def setUp(self):
        self.redis_instance = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=1, decode_responses=True)

    def test_currency_extraction_yf(self):
        rate = convert_currency("usd", self.redis_instance)
        self.assertIsInstance(rate, float) #First Run yfinance
        self.assertNotEqual(rate, 0)
        rate = convert_currency("usd", self.redis_instance)        
        self.assertIsInstance(rate, float) #Second Run Redis
        self.assertNotEqual(rate, 0)

    def test_stocks_yf(self):
        stock_name, stock_price, stock_currency = retrieve_yf("AAPL", self.redis_instance)
        self.assertEqual(stock_name,"Apple Inc.") #First Run yfinance
        self.assertNotEqual(stock_price,0)
        self.assertEqual(stock_currency,"usd")
        stock_name, stock_price, stock_currency = retrieve_yf("AAPL", self.redis_instance)
        self.assertEqual(stock_name,"Apple Inc.") #Second Run redis
        self.assertNotEqual(stock_price,0)
        self.assertEqual(stock_currency,"usd")
    
    def test_retrieve_mslqd(self):
        stock_name, stock_price, stock_currency = retrieve_mslqd(self.redis_instance) #First Run Scrapping
        self.assertEqual(stock_name,"MS US Dollar Liquidity Fund") 
        self.assertNotEqual(stock_price,0)
        self.assertEqual(stock_currency,"usd")
        stock_name, stock_price, stock_currency = retrieve_mslqd(self.redis_instance) #Second Run redis /!\ TTL 28800
        self.assertEqual(stock_name,"MS US Dollar Liquidity Fund") 
        self.assertNotEqual(stock_price,0)
        self.assertEqual(stock_currency,"usd")

    def test_retrieve_bgf(self):
        stock_name, stock_price, stock_currency = retrieve_bgf("LU0122376428", self.redis_instance) #First Run Scrapping
        self.assertEqual(stock_name,"BGF World Energy Fund") 
        self.assertNotEqual(stock_price,0)
        self.assertEqual(stock_currency,"sgd")
        stock_name, stock_price, stock_currency = retrieve_bgf("LU0122376428", self.redis_instance) #Second Run redis /!\ TTL 28800
        self.assertEqual(stock_name,"BGF World Energy Fund") 
        self.assertNotEqual(stock_price,0)
        self.assertEqual(stock_currency,"sgd")

    def test_retrieve_silver(self):
        stock_name, stock_price, stock_currency = retrieve_silver("AG1F", self.redis_instance) #First Run Scrapping
        self.assertEqual(stock_name,"1 Franc Semeuse 1898 - 1920") 
        self.assertNotEqual(stock_price,0)
        self.assertEqual(stock_currency,"eur")
        stock_name, stock_price, stock_currency = retrieve_bgf("AG1F", self.redis_instance) #Second Run redis /!\ TTL 28800
        self.assertEqual(stock_name,"1 Franc Semeuse 1898 - 1920") 
        self.assertNotEqual(stock_price,0)
        self.assertEqual(stock_currency,"eur")

    def test_retrieve_gold(self):
        stock_name, stock_price, stock_currency = retrieve_gold("OR10FR", self.redis_instance) #First Run Scrapping
        self.assertEqual(stock_name,"French/Swiss/Hungarian/Italian 10 Francs") 
        self.assertNotEqual(stock_price,0)
        self.assertEqual(stock_currency,"sgd")
        stock_name, stock_price, stock_currency = retrieve_gold("OR10FR", self.redis_instance) #Second Run redis /!\ TTL 28800
        self.assertEqual(stock_name,"French/Swiss/Hungarian/Italian 10 Francs") 
        self.assertNotEqual(stock_price,0)
        self.assertEqual(stock_currency,"sgd")

    def test_retrieve_cl(self):
        stock_name, stock_price, stock_currency = retrieve_cl("OCTOBER", self.redis_instance) #First Run Scrapping
        self.assertEqual(stock_name,"OCTOBER") 
        self.assertNotEqual(stock_price,0)
        self.assertEqual(stock_currency,"eur")
        stock_name, stock_price, stock_currency = retrieve_gold("OCTOBER", self.redis_instance) #Second Run redis /!\ TTL 28800
        self.assertEqual(stock_name,"OCTOBER") 
        self.assertNotEqual(stock_price,0)
        self.assertEqual(stock_currency,"eur")    	

    def test_retrieve_crypto(self):
        stock_name, stock_price, stock_currency = retrieve_crypto(self.redis_instance) #First Run Scrapping
        self.assertEqual(stock_name,"Cryptomonnaies") 
        self.assertNotEqual(stock_price,0)
        self.assertEqual(stock_currency,"usd")
        stock_name, stock_price, stock_currency = retrieve_crypto(self.redis_instance) #Second Run redis 
        self.assertEqual(stock_name,"Cryptomonnaies") 
        self.assertNotEqual(stock_price,0)
        self.assertEqual(stock_currency,"usd")  


