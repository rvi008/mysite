from django.test import TestCase
from django.conf import settings
import redis
from portfolio.mappings import *
from portfolio.controllers import *
import yfinance as yf
from portfolio.models import Stocks
from decimal import Decimal
import logging

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
        stock_name, stock_price, stock_currency, stock_type = retrieve_yf("AAPL", self.redis_instance)
        self.assertEqual(stock_name,"Apple Inc.") #First Run yfinance
        self.assertNotEqual(stock_price,0)
        self.assertEqual(stock_currency,"usd")
        stock_name, stock_price, stock_currency, stock_type = retrieve_yf("AAPL", self.redis_instance)
        self.assertEqual(stock_name,"Apple Inc.") #Second Run redis
        self.assertNotEqual(stock_price,0)
        self.assertEqual(stock_currency,"usd")
    
    def test_retrieve_mslqd(self):
        stock_name, stock_price, stock_currency, stock_type = retrieve_mslqd(self.redis_instance) #First Run Scrapping
        self.assertEqual(stock_name,"MS US Dollar Liquidity Fund") 
        self.assertNotEqual(stock_price,0)
        self.assertEqual(stock_currency,"usd")
        stock_name, stock_price, stock_currency, stock_type = retrieve_mslqd(self.redis_instance) #Second Run redis /!\ TTL 28800
        self.assertEqual(stock_name,"MS US Dollar Liquidity Fund") 
        self.assertNotEqual(stock_price,0)
        self.assertEqual(stock_currency,"usd")

    def test_retrieve_bgf(self):
        stock_name, stock_price, stock_currency, stock_type = retrieve_bgf("LU0122376428", self.redis_instance) #First Run Scrapping
        self.assertEqual(stock_name,"BGF World Energy Fund") 
        self.assertNotEqual(stock_price,0)
        self.assertEqual(stock_currency,"sgd")
        self.assertEqual(stock_type, "equity")
        stock_name, stock_price, stock_currency, stock_type = retrieve_bgf("LU0122376428", self.redis_instance) #Second Run redis /!\ TTL 28800
        self.assertEqual(stock_name,"BGF World Energy Fund") 
        self.assertNotEqual(stock_price,0)
        self.assertEqual(stock_currency,"sgd")
        self.assertEqual(stock_type, "equity")

    def test_retrieve_silver(self):
        stock_name, stock_price, stock_currency, stock_type = retrieve_silver("AG1F", self.redis_instance) #First Run Scrapping
        self.assertEqual(stock_name,"1 Franc Semeuse 1898 - 1920") 
        self.assertNotEqual(stock_price,0)
        self.assertEqual(stock_currency,"eur")
        self.assertEqual(stock_type, "metal")
        stock_name, stock_price, stock_currency, stock_type = retrieve_bgf("AG1F", self.redis_instance) #Second Run redis /!\ TTL 28800
        self.assertEqual(stock_name,"1 Franc Semeuse 1898 - 1920") 
        self.assertNotEqual(stock_price,0)
        self.assertEqual(stock_currency,"eur")
        self.assertEqual(stock_type, "metal")

    def test_retrieve_gold(self):
        stock_name, stock_price, stock_currency, stock_type = retrieve_gold("OR10FR", self.redis_instance) #First Run Scrapping
        self.assertEqual(stock_name,"French/Swiss/Hungarian/Italian 10 Francs") 
        self.assertNotEqual(stock_price,0)
        self.assertEqual(stock_currency,"sgd")
        stock_name, stock_price, stock_currency, stock_type = retrieve_gold("OR10FR", self.redis_instance) #Second Run redis /!\ TTL 28800
        self.assertEqual(stock_name,"French/Swiss/Hungarian/Italian 10 Francs") 
        self.assertNotEqual(stock_price,0)
        self.assertEqual(stock_currency,"sgd")

    def test_retrieve_cl(self):
        stock_name, stock_price, stock_currency, stock_type = retrieve_cl("OCTOBER", self.redis_instance) #First Run Scrapping
        self.assertEqual(stock_name,"OCTOBER") 
        self.assertNotEqual(stock_price,0)
        self.assertEqual(stock_currency,"eur")
        stock_name, stock_price, stock_currency, stock_type = retrieve_gold("OCTOBER", self.redis_instance) #Second Run redis /!\ TTL 28800
        self.assertEqual(stock_name,"OCTOBER") 
        self.assertNotEqual(stock_price,0)
        self.assertEqual(stock_currency,"eur")


# Create your tests here.
class StockTestCase(TestCase):
    def setUp(self):
        Stocks.objects.create(symbol="TEST", name="Test Case", price=100, stocks_owned=10,
        buying_price=Decimal(100), balance=2, valuation=1000, asset_type="equity")

    def test_stocks_values(self):
        logging.info("Testing stock creation")
        stock_test = Stocks.objects.get(symbol="TEST")
        self.assertEqual(stock_test.symbol, "TEST")
        self.assertEqual(stock_test.name, "Test Case")
        self.assertEqual(stock_test.price, Decimal(100))
        self.assertEqual(stock_test.stocks_owned, Decimal(10))
        self.assertEqual(stock_test.buying_price, Decimal(100))
        self.assertEqual(stock_test.balance, Decimal(2))
        self.assertEqual(stock_test.valuation, Decimal(1000))
        self.assertEqual(stock_test.asset_type, "equity")
        stock_test.price = Decimal(101.0000)
        stock_test.save(update_fields=["price"])
        stock_test = Stocks.objects.get(symbol="TEST")
        self.assertEqual(stock_test.price, Decimal(101.0000))
        self.assertEqual(stock_test.delete()[0],1)
