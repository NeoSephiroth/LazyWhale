from zebitex import Zebitex, ZebitexError
from decimal import *
from datetime import datetime, date
import time

class zebitexFormatted(object):
    """"Zebittex api formatter to get almost same output as ccxt"""
    getcontext().prec = 8

    def __init__(self, access_key=None, secret_key=None, is_staging=False, ze = None):
        self.access_key = access_key
        self.secret_key = secret_key
        self.is_staging = is_staging
        self.ze = Zebitex("uzpIqy140HN2vhzRcdxcFxojb6K7SvEhjKBPSnpx",
                 "v8tjziNLxSA3mgMH95nMVRbycXY8cKd9fnHmXoa5", True)
        self.fees = Decimal('0.0015')
        self.symbols = self.get_symbols()

    def get_symbols(self):
        tickers = self.load_markets()
        symbols = []
        for item in tickers:
            symbols.append(item)
        return symbols
    
    def fetch_balance(self):
        balance = self.ze.funds()
        fetched_balance = {}
        for key, value in balance.items():
            if value['balance'] == '0.00000000' or value['balance'] == '1E-8':
                value['balance'] = '0.0'
            if value['lockedBalance'] == '0.00000000' or value['lockedBalance'] == '1E-8':
                value['lockedBalance'] = '0.0'
            fetched_balance.update({key: {'free': str(Decimal(value['balance']) - Decimal(value ['lockedBalance'])), 'used': value ['lockedBalance'], 'total': value['balance']}})
        return fetched_balance

    def fetch_open_orders(self, market=None):
        open_orders = self.ze.open_orders('1', '1000')
        fetched_open_order = []
        for item in open_orders['items']:            
            if market:
                if item['pair'] == market:
                    fetched_open_order.append(self.order_formatted(item))
            else:
                fetched_open_order.append(self.order_formatted(item))
        return fetched_open_order


        print(open_orders['items'])

    def order_formatted(self, order):
        return {'info': 
                    {'orderNumber': order['id'],
                     'type': order['ordType'],
                     'rate': order['price'],
                     'startingAmount': order['amount'],
                     'amount': str(Decimal(order['amount']) - Decimal(order['filled'])),
                     'total': order['total'],
                     'date': order['updatedAt'],
                     'margin': 0,
                     'status': order['state'],
                     'side': order['side'],
                     'price': order['price']},
                'id': order['id'],
                'timestamp': self.str_to_epoch(order['updatedAt']), #carefull, it will construct epoch following your personnal timezone
                'datetime': order['updatedAt'],
                'lastTradeTimestamp': None, #Not enough info fro the api to construct it
                'status': order['state'],
                'symbol': order['pair'],
                'type': order['ordType'],
                'side': order['side'],
                'price': float(order['price']),
                'cost': float(self.calculate_filled_cost(order['filled'], order['price'])),
                'amount': float(order['amount']),
                'filled': float(order['filled']),
                'remaining': float(Decimal(order['amount']) - Decimal(order['filled'])),
                'trades': None if float(order['filled']) != 0 else True,
                'fee': float(self.calcultate_paid_fees(order['filled']))
                }

    def load_markets(self):
        tickers = self.ze.tickers()
        fetched_tickers = {}
        for key, ticker in tickers.items():
            fetched_tickers.update({ticker['name']: {
                'fee_loaded': False,
                'percentage': True,
                'maker': ticker['ask_fee'],
                'taker': ticker['bid_fee'],
                'precision': {'amount': 8, 'price': 8},#need to check for eur 
                'limits': {'amount': {'min': 1e-07, ' max': 1000000000},
                           'price': {'min': 1e-08, 'max': 1000000000},
                           'cost': {'min': 0.000001}},
                'id': ticker['base_unit'].upper() + '_' + ticker['quote_unit'].upper(),
                'symbol': ticker['name'],
                'baseId': ticker['base_unit'].upper(),
                'quoteId': ticker['quote_unit'].upper(),
                'active': ticker['isUpTend'],
                'info': {'id': None,
                         'last': ticker['last'],
                         'lowestAsk': ticker['sell'],
                         'highestBid': ticker['buy'],
                         'percentChange': ticker['percent'],
                         'baseVolume': None,
                         'quoteVolume': ticker['volume'],
                         'isFrozen': '0',
                         'high24hr': ticker['high'],
                         'low24hr': ticker['low']
                         }}})
        return fetched_tickers

    def fetch_ticker(self, ticker_name):
        formatted_ticker_name = ticker_name.split('/')
        formatted_ticker_name = (formatted_ticker_name[0] + formatted_ticker_name[1]).lower()
        ticker = self.ze.ticker(formatted_ticker_name)
        return {'symbol': ticker_name, 
                'timestamp': ticker['at'], 
                'datetime': self.epoch_to_str(ticker['at']), 
                'high': float(ticker['high']), 
                'low': float(ticker['low']), 
                'bid': float(ticker['sell']), 
                'bidVolume': None, 
                'ask': float(ticker['buy']), 
                'askVolume': None, 
                'vwap': None, 
                'open': float(ticker['visualOpen']), 
                'close': None,
                'last': float(ticker['last']), 
                'previousClose': None, 
                'change': float(ticker['change']), 
                'percentage': float(ticker['percent']), 
                'average': None, 
                'baseVolume': float(ticker['volume']), 
                'quoteVolume': None, 
                'info': {'id': 229, 
                         'last': ticker['last'], 
                         'lowestAsk': ticker['sell'], 
                         'highestBid': ticker['buy'], 
                         'percentChange': ticker['percent'], 
                         'baseVolume': ticker['volume'], 
                         'quoteVolume': None, 
                         'isFrozen': '0', 
                         'high24hr': None, 
                         'low24hr': None}}

    def fetch_my_trades(self, market=None):
        history = self.ze.trade_history('buy', '2018-04-01', date.today().isoformat(), 1, 1000)
        my_trades = []
        for item in history['items']:
            market_name = item['baseCurrency'] + '/' + item['quoteCurrency']
            if market:
                if market_name == market:
                    my_trades.append(self.trade_formatted(item, market_name))
            else:
                my_trades.append(self.trade_formatted(item, market_name))
        return my_trades

    def trade_formatted(self, trade, market_name):
        return {'info': {'globalTradeID': None,
                         'tradeID': None,
                         'date': trade['createdAt'],
                         'rate': trade['price'],
                         'amount': trade['baseAmount'],
                         'total': trade['quoteAmount'],
                         'fee': '0.00150000',
                         'orderNumber': None,
                         'type': trade['side'],
                         'category': 'exchange'},
                'timestamp': self.str_to_epoch(trade['createdAt']),
                'datetime': trade['createdAt'] + '.000Z',
                'symbol': market_name,
                'id': None,
                'order': None,
                'type': None,
                'side': trade['side'],
                'price': float(trade['price']),
                'amount': float(trade['baseAmount']),
                'cost':  float(trade['quoteAmount']),
                'fee': {'type': None,
                        'rate': 0.0015,
                        'cost': float(self.calcultate_paid_fees(trade['quoteAmount'])),
                        'currency': trade['quoteCurrency']}}

    def create_limit_buy_order(self, symbol, amount, price):
        symbol = symbol.split('/')
        bid = symbol[0].lower()
        ask = symbol[1].lower()
        market = bid + ask
        return self.ze.new_order(bid, ask, 'bid', price, amount, market, 'limit')

    def create_limit_sell_order(self, symbol, amount, price):
        symbol = symbol.split('/')
        bid = symbol[0].lower()
        ask = symbol[1].lower()
        market = bid + ask
        return self.ze.new_order(bid, ask, 'ask', price, amount, market, 'limit')

    def cancel_order(self, order_id):
        return self.ze.cancel_order(int(order_id))

    def str_to_epoch(self, date_string):
        return int(str(time.mktime(datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S').timetuple())).split('.')[0] + '000')

    def epoch_to_str(self, epoch):
        return datetime.fromtimestamp(epoch).isoformat() + '.000Z'

    def calculate_filled_cost(self, amt_filled, price):
        return (Decimal(amt_filled) * Decimal(price) * (Decimal('1') - self.fees).quantize(Decimal('.00000001'), rounding=ROUND_HALF_EVEN))
    
    def calcultate_paid_fees(self, amt_filled):
        return (Decimal(amt_filled) * self.fees).quantize(Decimal('.00000001'), 
                                                          rounding=ROUND_HALF_EVEN)