from django.shortcuts import render
import time
import decimal
import logging
from .models import Stocks
from .forms import AddStockForm
from .controllers import retrieve_mslqd, retrieve_yf, retrieve_bgf, convert_currency


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


def update_stock_table(request):
    """
    function, that allows to add or remove stock options and displays them in portfolio
    
    Another possibility: https://query.yahooapis.com/v1/public/yql?q=select%20Ask%20from%20yahoo.finance.quotes%20where%20symbol%20in%20(%22GOOGL%22)&format=json&env=store%3A%2F%2Fdatatables.org%2Falltableswithkeys&callback=
    
    :param request: POST request that defines weather to add or remove stock options to portfolio
    :return: stocks.html with context dictionary that has all the stock options that you have added to portfolio
    """

    stock_list = Stocks.objects.order_by('price')[:30]
    today_date = time.strftime("%d.%m.%Y %H:%M")

    if 'add_stock' in request.POST:

            form = AddStockForm(request.POST)

            if form.is_valid():  # form validation
                new_stock = request.POST.get("add_stock", "")

                if not Stocks.objects.filter(symbol=new_stock.upper()):  # stock not already in portfolio

                    logger.info('Adding ' + new_stock.upper() + ' to stock portfolio')

                    try:  # try to add stock to portfolio

                        if "LU0904783114" in new_stock:
                            new_stock_name, new_stock_price, currency = retrieve_mslqd()

                        elif "LU0" in new_stock:
                            new_stock_name, new_stock_price, currency = retrieve_bgf(new_stock)

                        elif "CASH" in new_stock:
                            new_stock_name = new_stock
                            new_stock_price = form.cleaned_data['buying_price']
                            stocks_owned = 1
                            currency = new_stock[-3:].lower()
                        else:
                            new_stock_name, new_stock_price, currency = retrieve_yf(new_stock)
                        
                        stocks_owned = form.cleaned_data['stocks_bought']
                        buying_price = form.cleaned_data['buying_price']

                        stock_to_db = Stocks(symbol=new_stock.upper(),
                                             name=new_stock_name,
                                             price=new_stock_price,
                                             stocks_owned=stocks_owned,
                                             buying_price=buying_price,
                                             balance=0,
                                             valuation=new_stock_price*stocks_owned
                                             )
                        stock_to_db.save()

                        add_success_message = "Stock successfully added to portfolio!"

                        stock = Stocks.objects.get(symbol=new_stock)
                        stocks = stock.stocks_owned
                        bprice = stock.buying_price
                        price = stock.price
                        valuation = stock.valuation
                        if currency != 'eur':
                            balance = decimal.Decimal(((stocks * price) - (stocks * bprice))) * decimal.Decimal(convert_currency(currency))
                            valuation = valuation * decimal.Decimal(convert_currency(currency))
                        else:
                            balance = (stocks * price) - (stocks * bprice)
                        stock.balance = balance
                        stock.valuation = valuation
                        stock.save()

                        context = {
                            'stock_list': stock_list,
                            'today_date': today_date,
                            'add_success_message': add_success_message,
                        }
                        return render(request, 'stockInformation/stocks.html', context)

                    except Exception as e:  # if symbol is not correct
                        pass
                        error_message = "Insert correct symbol!"
                        logging.error("Exception %s" % str(e))

                        context = {
                            'stock_list': stock_list,
                            'today_date': today_date,
                            'error_message': error_message,
                        }
                        return render(request, 'stockInformation/stocks.html', context)

                else:  # if symbol is already in your portfolio
                    stock_exists_message = "Stock is already in your portfolio!"

                    context = {
                        'stock_list': stock_list,
                        'today_date': today_date,
                        'stock_exists_message': stock_exists_message,
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

            context = {
                'stock_list': stock_list,
                'today_date': today_date,
                'delete_success_message': delete_success_message,
            }
            return render(request, 'stockInformation/stocks.html', context)

    else:  # if there was no POST request - the whole portfolio should be updated

        stocks = Stocks.objects.all()  # This returns queryset

        for stock in stocks:

            if "LU0904783114" in stock.symbol:
                _, stock.price, currency = retrieve_mslqd()
            elif "LU0" in stock.symbol:
                _, stock.price, currency = retrieve_bgf(stock.symbol)
            elif "CASH" in stock.symbol:
                currency = stock.symbol[-3:].lower()
            else:
                _, stock.price, currency = retrieve_yf(stock.symbol)

            if currency != 'eur':
                balance_before = (stock.stocks_owned * decimal.Decimal(stock.price)) - (decimal.Decimal(stock.stocks_owned) * decimal.Decimal(stock.buying_price))
                rate = convert_currency(currency) 
                balance = balance_before * decimal.Decimal(rate)
                valuation = decimal.Decimal(stock.price) * decimal.Decimal(stock.stocks_owned)  * decimal.Decimal(rate)
            else:
                balance = (float(stock.stocks_owned) * float(stock.price)) - (float(stock.stocks_owned) * float(stock.buying_price))
                valuation = decimal.Decimal(stock.price) * decimal.Decimal(stock.stocks_owned)

            stock.balance = balance
            stock.valuation = valuation
            stock.save(update_fields=['price', 'balance', 'valuation'])  # do not create new object in db,
            # update current lines

        context = {
            'stock_list': stock_list,
            'today_date': today_date
        }

        logger.info('Refreshing stock list')

        return render(request, 'stockInformation/stocks.html', context)


def crowdfunding(request):
    context = {
    }

    return render(request, 'stockInformation/crowdfunding.html', context)