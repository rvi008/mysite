from __future__ import unicode_literals

from django.db import models


class Stocks(models.Model):
    symbol = models.CharField(max_length=200)
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=4, default=0.0000)
    stocks_owned = models.DecimalField(max_digits=10, decimal_places=4, default=0.0000)
    buying_price = models.DecimalField(max_digits=10, decimal_places=4)
    balance = models.DecimalField(max_digits=10, decimal_places=2)
    valuation = models.DecimalField(max_digits=10, decimal_places=2, default=0.0000)
    currency = models.CharField(max_length=5, default='eur')
    asset_type = models.CharField(max_length=10, default='equity')

    def __str__(self):
        return self.symbol, self.name, self.price, self.change

class Portfolio(models.Model):
    valuation = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    date = models.DateField(auto_now=True)