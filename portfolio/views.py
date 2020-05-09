from django.shortcuts import render
import time
import decimal
import logging
from .models import Stocks, Portfolio
from datetime import date, timedelta
from .forms import AddStockForm
from portfolio.controllers import *
import json
from django.conf import settings
import redis
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.response import Response
import pickle
import numpy as np
from django.contrib.auth.decorators import login_required
from django_pandas.io import read_frame
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import io
import urllib, base64

mpl.use('agg')

redis_instance = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0, decode_responses=True)

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

@login_required
def update_stock_table(request):
    """
    function, that allows to add or remove stock options and displays them in portfolio
    
    Another possibility: https://query.yahooapis.com/v1/public/yql?q=select%20Ask%20from%20yahoo.finance.quotes%20where%20symbol%20in%20(%22GOOGL%22)&format=json&env=store%3A%2F%2Fdatatables.org%2Falltableswithkeys&callback=
    
    :param request: POST request that defines weather to add or remove stock options to portfolio
    :return: stocks.html with context dictionary that has all the stock options that you have added to portfolio
    """

    stock_list = Stocks.objects.order_by('symbol')[:30]
    today_date = time.strftime("%d.%m.%Y %H:%M")

    if 'add_stock' in request.POST:

            form = AddStockForm(request.POST)

            if form.is_valid():  # form validation
                new_stock = request.POST.get("add_stock", "")

                if not Stocks.objects.filter(symbol=new_stock.upper()):  # stock not already in portfolio

                    logger.info('Adding ' + new_stock.upper() + ' to portfolio')

                    try:  # try to add stock to portfolio

                        if "LU0904783114" in new_stock:
                            new_stock_name, new_stock_price, currency, stock_type = retrieve_mslqd(redis_instance)

                        elif "LU0" in new_stock:
                            new_stock_name, new_stock_price, currency, stock_type  = retrieve_bgf(new_stock, redis_instance)

                        elif "CASH" in new_stock:
                            new_stock_name = new_stock
                            new_stock_price = form.cleaned_data['buying_price']
                            stocks_owned = 1
                            currency = new_stock[-3:].lower()
                            stock_type = "cash"

                        elif "OR" in new_stock:
                            new_stock_name, new_stock_price, currency, stock_type = retrieve_gold(new_stock, redis_instance)

                        elif "AG" in new_stock:
                            new_stock_name, new_stock_price, currency, stock_type  = retrieve_silver(new_stock, redis_instance)

                        elif "CL" in new_stock:
                            new_stock_name, new_stock_price, currency, stock_type  = retrieve_cl(new_stock.replace("CL",""), redis_instance)

                        else:
                            new_stock_name, new_stock_price, currency, stock_type  = retrieve_yf(new_stock, redis_instance)
                            
                        stocks_owned = form.cleaned_data['stocks_bought']
                        buying_price = form.cleaned_data['buying_price']

                        stock_to_db = Stocks(symbol=new_stock.upper(),
                                             name=new_stock_name,
                                             price=new_stock_price,
                                             stocks_owned=stocks_owned,
                                             buying_price=buying_price,
                                             balance=0,
                                             valuation=new_stock_price*stocks_owned,
                                             currency = currency,
                                             asset_type = stock_type
                                             )
                        stock_to_db.save()

                        add_success_message = "Stock successfully added to portfolio!"

                        stock = Stocks.objects.get(symbol=new_stock)
                        stocks = stock.stocks_owned
                        bprice = stock.buying_price
                        price = stock.price
                        valuation = stock.valuation

                        if currency != 'eur':
                            balance = decimal.Decimal(((stocks * price) - (stocks * bprice))) * decimal.Decimal(convert_currency(currency, redis_instance))
                            valuation = valuation * decimal.Decimal(convert_currency(currency, redis_instance))
                        else:
                            balance = (stocks * price) - (stocks * bprice)
                        stock.balance = balance
                        stock.valuation = valuation
                        stock.save()

                        total_balance, total_valuation = np.sum([s.balance for s in stock_list]), np.sum([s.valuation for s in stock_list])

                        context = {
                            'stock_list': stock_list,
                            'total_balance': total_balance,
                            'total_valuation': total_valuation,
                            'today_date': today_date,
                            'add_success_message': add_success_message,
                        }
                        return render(request, 'stockInformation/stocks.html', context)

                    except Exception as e:  # if symbol is not correct
                        pass
                        error_message = "Error in the creation process"
                        logging.error("Exception %s" % str(e))

                        context = {
                            'stock_list': stock_list,
                            'today_date': today_date,
                            'error_message': error_message,
                        }
                        return render(request, 'stockInformation/stocks.html', context)

                else:  # if symbol is already in your portfolio
                    if 'CASH' in new_stock:
                        logging.info("Updating a current account")
                        update_cash_accounts(new_stock, form)
                        stock_list = Stocks.objects.order_by('symbol')[:30]

                    context = {
                        'stock_list': stock_list,
                        'today_date': today_date,
                    }
                    return render(request, 'stockInformation/stocks.html', context)

            else:  # if form was incorrectly filled in
                error_message = "Invalid form!"

                context = {
                    'stock_list': stock_list,
                    'today_date': today_date,
                    'error_message': error_message,
                }
                return render(request, 'stockInformation/stocks.html', context)

    elif 'remove_stock' in request.POST:  # if user was trying to remove stock from portfolio

        symbol = str(request.POST.get('stock_symbol'))

        if Stocks.objects.filter(symbol=symbol).count() > 0:  # if inserted stock is in portfolio

            logger.info('Removing ' + symbol + ' from stock portfolio')

            Stocks.objects.filter(symbol=symbol).delete()
            stock_list = Stocks.objects.order_by('symbol')[:30]

            delete_success_message = "Stock successfully removed from portfolio!"
            total_balance, total_valuation = np.sum([s.balance for s in stock_list]), np.sum([s.valuation for s in stock_list])

            context = {
                'stock_list': stock_list,
                'total_balance': total_balance,
                'total_valuation': total_valuation,
                'today_date': today_date,
                'delete_success_message': delete_success_message,
            }

            return render(request, 'stockInformation/stocks.html', context)

    else:  # if there was no POST request - the whole portfolio should be updated

        stocks = Stocks.objects.all().order_by('symbol')[:30]  # This returns queryset
        pf, created = Portfolio.objects.get_or_create(date=date.today())

        for stock in stocks:
            try:
            
                if "LU0904783114" in stock.symbol:
                    _, stock.price, currency, t = retrieve_mslqd(redis_instance)
                elif "LU0" in stock.symbol:
                    _, stock.price, currency, t = retrieve_bgf(stock.symbol, redis_instance)
                elif "CASH" in stock.symbol:
                    currency, t = stock.symbol[-3:].lower(), "cash"
                elif "OR" in stock.symbol:
                    _, stock.price, currency, t = retrieve_gold(stock.symbol, redis_instance)
                elif "AG" in stock.symbol:
                    _, stock.price, currency, t = retrieve_silver(stock.symbol, redis_instance)
                elif "CL" in stock.symbol:
                    _, stock.price, currency, t = retrieve_cl(stock.symbol.replace("CL",""), redis_instance)
                elif "CRYPTO" in stock.symbol:
                    _, stock.price, currency, t = retrieve_crypto(redis_instance)
                else:
                    _, stock.price, currency, t = retrieve_yf(stock.symbol, redis_instance)
                if currency != 'eur':
                    balance_before = (stock.stocks_owned * decimal.Decimal(stock.price)) - (decimal.Decimal(stock.stocks_owned) * decimal.Decimal(stock.buying_price))
                    rate = convert_currency(currency, redis_instance) 
                    balance = balance_before * decimal.Decimal(rate)
                    valuation = decimal.Decimal(stock.price) * decimal.Decimal(stock.stocks_owned)  * decimal.Decimal(rate)
                else:
                    balance = (float(stock.stocks_owned) * float(stock.price)) - (float(stock.stocks_owned) * float(stock.buying_price))
                    valuation = decimal.Decimal(stock.price) * decimal.Decimal(stock.stocks_owned)
    
                stock.balance = balance
                stock.valuation = valuation
                stock.currency = currency
                stock.save(update_fields=['price', 'balance', 'valuation', 'currency'])  # do not create new object in db,
                # update current lines
                total_balance, total_valuation = np.sum([s.balance for s in stock_list]), np.sum([s.valuation for s in stock_list])
                pf.valuation = total_valuation
                pf.save(update_fields=['valuation'])

                context = {
                'stock_list': stock_list,
                'total_balance': total_balance,
                'total_valuation': total_valuation,
                'today_date': today_date
                    }      
                logger.info('Refreshing stock list')
            except  Exception as es: #If one update fails, abort the update process and retrieve from DB
                logger.info('Update Failed for %s cause %s' % (str(stock.symbol), str(es)))
                
        return render(request, 'stockInformation/stocks.html', context)


def update_cash_accounts(symbol, form):
    stock = Stocks.objects.get(symbol=symbol)
    stock.price = form.cleaned_data['buying_price']
    stock.buying_price = stock.price
    stock.save(update_fields=["price", "buying_price"])

@api_view(['GET', 'POST'])
def manage_items(request, *args, **kwargs):
    if request.method == 'GET':
        items = {}
        count = 0
        for key in redis_instance.keys("*"):
            items[key] = redis_instance.hgetall(key)
            count += 1
        response = {
            'count': count,
            'msg': f"Found {count} items.",
            'items': items
        }
        return Response(response, status=200)
    elif request.method == 'POST':
        item = json.loads(request.body)
        key = list(item.keys())[0]
        value = item[key]
        #redis_instance.set(key, value)
        redis_instance.hset(name, key, value, mapping)
        response = {
            'msg': f"{key} successfully set to {value}"
        }
        return Response(response, 201)


@api_view(['GET', 'PUT', 'DELETE'])
def manage_item(request, *args, **kwargs):
    if request.method == 'GET':
        if kwargs['key']:
            value = redis_instance.hgetall(kwargs['key'])
            if value:
                response = {
                    'key': kwargs['key'],
                    'value': value,
                    'msg': 'success'
                }
                return Response(response, status=200)
            else:
                response = {
                    'key': kwargs['key'],
                    'value': None,
                    'msg': 'Not found'
                }
                return Response(response, status=404)
    elif request.method == 'PUT':
        if kwargs['key']:
            request_data = json.loads(request.body)
            new_value = request_data['new_value']
            value = redis_instance.get(kwargs['key'])
            if value:
                redis_instance.set(kwargs['key'], new_value)
                response = {
                    'key': kwargs['key'],
                    'value': value,
                    'msg': f"Successfully updated {kwargs['key']}"
                }
                return Response(response, status=200)
            else:
                response = {
                    'key': kwargs['key'],
                    'value': None,
                    'msg': 'Not found'
                }
                return Response(response, status=404)

    elif request.method == 'DELETE':
        if kwargs['key']:
            result = redis_instance.delete(kwargs['key'])
            if result == 1:
                response = {
                    'msg': f"{kwargs['key']} successfully deleted"
                }
                return Response(response, status=404)
            else:
                response = {
                    'key': kwargs['key'],
                    'value': None,
                    'msg': 'Not found'
                }
                return Response(response, status=404)

@login_required
def analytics(request):
    stock_list = Stocks.objects.all().order_by('symbol')[:50]

    df = read_frame(stock_list)[["currency","valuation"]]
    gp = df.groupby("currency").agg({"valuation":"sum"})
    names = gp.index.tolist()
    gpp = gp['valuation'] / gp['valuation'].sum()
    new = pd.DataFrame()
    new["valuation"], new.index  = gpp.astype(float), names
    explode = [0 for i in range(len(names))]
    explode[0] = 0.1
    plot = new.plot.pie(y="valuation", use_index=False,xticks=None, figsize=(11,5), explode=explode, shadow=True, radius=1.2, autopct="%1.1f")
    plt.legend(bbox_to_anchor=(1, 1),
           bbox_transform=plt.gcf().transFigure)
    plt.axis('off')
    plt.close()

    buf = io.BytesIO()
    plot.figure.savefig(buf, format='png')
    buf.seek(0)
    string = base64.b64encode(buf.read())
    uri1 = 'data:image/png;base64,' + urllib.parse.quote(string)

    df = read_frame(stock_list)[["asset_type","valuation"]]
    gp = df.groupby("asset_type").agg({"valuation":"sum"})
    names = gp.index.tolist()
    gpp = gp['valuation'] / gp['valuation'].sum()
    new = pd.DataFrame()
    new["valuation"], new.index  = gpp.astype(float), names
    explode = [0 for i in range(len(names))]
    explode[3] = 0.1
    plot = new.plot.pie(y="valuation", use_index=False,xticks=None, figsize=(11,5), explode=explode, shadow=True, radius=1.2, autopct="%1.1f")
    plt.legend(bbox_to_anchor=(1, 1),
           bbox_transform=plt.gcf().transFigure)
    plt.axis('off')
    plt.close()

    buf1 = io.BytesIO()
    plot.figure.savefig(buf1, format='png')
    buf1.seek(0)
    string = base64.b64encode(buf1.read())
    uri2 = 'data:image/png;base64,' + urllib.parse.quote(string)


    portfolios = Portfolio.objects.all()
    pf = read_frame(portfolios)
    pf.index = pf["date"]
    pf['valuation'] = pf['valuation'].astype(float)
    pf["ma"] = pf['valuation'].ewm(com=0.3).mean()
    plot = pf['valuation'].plot.line(figsize=(11,5), grid=True)
    plot = pf['ma'].plot.line(linestyle='dashed', marker='x', color='red')
    plt.legend(bbox_to_anchor=(1, 1),
       bbox_transform=plt.gcf().transFigure)
    plt.xticks(rotation=70)
    plt.gcf().subplots_adjust(bottom=0.15)
    plt.close()

    buf2 = io.BytesIO()
    plot.figure.savefig(buf2, format='png')
    buf2.seek(0)
    string = base64.b64encode(buf2.read())
    uri3 = 'data:image/png;base64,' + urllib.parse.quote(string)

    return render(request, 'stockInformation/analyses.html', {'image1':uri1, 'image2':uri2, 'image3':uri3})









