from django.test import TestCase
from portfolio.models import Stocks
from decimal import Decimal

# Create your tests here.
class StockTestCase(TestCase):
	def setUp(self):
		Stocks.objects.create(symbol="TEST", name="Test Case", price=100, stocks_owned=10,
		buying_price=Decimal(100), balance=2, valuation=1000)

	def test_stocks_values(self):
		stock_test = Stocks.objects.get(symbol="TEST")
		self.assertEqual(stock_test.symbol, "TEST")
		self.assertEqual(stock_test.name, "Test Case")
		self.assertEqual(stock_test.price, Decimal(100))
		self.assertEqual(stock_test.stocks_owned, Decimal(10))
		self.assertEqual(stock_test.buying_price, Decimal(100))
		self.assertEqual(stock_test.balance, Decimal(2))
		self.assertEqual(stock_test.valuation, Decimal(1000))
		stock_test.price = Decimal(101.0000)
		stock_test.save(update_fields=["price"])
		stock_test = Stocks.objects.get(symbol="TEST")
		self.assertEqual(stock_test.price, Decimal(101.0000))
		self.assertEqual(stock_test.delete()[0],1)
