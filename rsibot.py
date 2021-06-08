import robin_stocks.robinhood as rs
import tulipy as ti
import numpy as np
from time import sleep
from plyer import notification
import matplotlib.pyplot as plt
import seaborn
import threading
import os
import pickle
import psutil, gc, sys

# variables
ctr = 0
rsi_period = 14
n_prices = 100
triggered = False
over_70_line = False
btc_prices = []
startup_time = 5
kill_time = 350 # 400 max
savefile = 'save.pkl'
initial_acct_value = 0

rsi_top = 69
rsi_bottom = 31

delay_time = 2
amount_per_trade_usd = 5.00

# for calculating percents


def get_change(current, previous):
    if current == previous:
        return 0
    try:
        return (abs(current - previous) / previous) * 100.0
    except ZeroDivisionError:
        return float('inf')

# for the "loop"


def set_interval(func, sec):
    def func_wrapper():
        set_interval(func, sec)
        func()
    t = threading.Timer(sec, func_wrapper)
    t.start()
    return t

# buy and sell functions


def buy():
    global ctr, startup_time, amount_per_trade_usd, fig
    if ctr < startup_time:
        print("not buying - bot started too recently")
        return
    plt.text(45, 90, "BUY!")

    crypto_buying_power = float(
        rs.profiles.load_account_profile(info='crypto_buying_power'))
    if crypto_buying_power < amount_per_trade_usd + 1:
        print("not enough buying power to place trade!")
        return
    # print("Placing trade....")
    # rs.orders.order_buy_crypto_by_price('BTC', amount_per_trade_usd, timeInForce='gtc')
    # print("done!!!")


def sell():
    global ctr, startup_time, amount_per_trade_usd, fig
    if ctr < startup_time:
        print("not selling - bot started too recently")
        return
    plt.text(45, 90, "SELL!")

    last_price = float(rs.crypto.get_crypto_quote('BTC', info='mark_price'))
    held_btc = float([item for item in rs.crypto.get_crypto_positions(
        info=None) if item['currency']['code'] == 'BTC'][0]['quantity_available'])
    if held_btc*last_price < amount_per_trade_usd + 1:
        print("not enough bitcoin to place trade!")
        return
    # print("Placing trade....")
    # rs.orders.order_sell_crypto_by_price('BTC', amount_per_trade_usd, timeInForce='gtc')
    # print("done!!!")


# for aesthetic
def hide_lines(ax):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    # ax.get_xaxis().set_ticks([])
    # ax.get_yaxis().set_ticks([])

# for debugging memory
def actual_size(input_obj):
    memory_size = 0
    ids = set()
    objects = [input_obj]
    while objects:
        new = []
        for obj in objects:
            if id(obj) not in ids:
                ids.add(id(obj))
                memory_size += sys.getsizeof(obj)
                new.append(obj)
        objects = gc.get_referents(*new)
    return memory_size

# entry point


def start():
    print('starting...')
    global ctr, rsi_period, n_prices, delay_time, triggered, over_70_line, btc_prices, initial_acct_value

    # log in to robinhood
    rs.login(username="benjamincooley81@gmail.com",
             password="",
             expiresIn=86400,
             by_sms=True)
    print('logged in')

    # data stuff
    last_price = float(rs.crypto.get_crypto_quote('BTC', info='mark_price'))
    held_btc = float([item for item in rs.crypto.get_crypto_positions(
        info=None) if item['currency']['code'] == 'BTC'][0]['quantity_available'])
    crypto_buying_power = float(
        rs.profiles.load_account_profile(info='crypto_buying_power'))
    initial_acct_value = held_btc * last_price + crypto_buying_power

    # get initial history
    if os.path.exists(savefile):
        with open(savefile, 'rb') as f:
            print('Loading data from pickle...')
            btc_prices = pickle.load(f)
    else:
        # NOTE: The first few iterations will suck ass because this data is WRONG
        # it will be replaced as the bot runs
        print('Making up garbage initial data...')
        rh_btc_history = rs.crypto.get_crypto_historicals(
            'BTC', interval='15second', span='hour', bounds='24_7', info=None)
        btc_prices = np.array(
            [last_price for item in rh_btc_history])
        
    # set up plots
    global fig, ax1, ax2
    fig, ax1 = plt.subplots()
    ax2 = ax1.twinx()

# infinite loop


def main():

    # python is weird
    global ctr, rsi_period, n_prices, delay_time, triggered, over_70_line, btc_prices, startup_time

    # get last btc price from robinhood
    last_price = float(rs.crypto.get_crypto_quote('BTC', info='mark_price'))

    # push last price and pop first price
    btc_prices = np.append(btc_prices, last_price)
    btc_prices = np.delete(btc_prices, 0)

    with open(savefile, 'wb') as f:
        print('saving updated data')
        pickle.dump(btc_prices, f, protocol=pickle.HIGHEST_PROTOCOL)

    # crypto_buying_power = float(rs.profiles.load_account_profile(info='crypto_buying_power'))
    # print('crypto buying power: ', str(crypto_buying_power))
    # cbp_in_btc = crypto_buying_power/last_price
    # print('crypto buying power in btc: ' + str(cbp_in_btc))

    # held_btc = float([item for item in rs.crypto.get_crypto_positions(info=None) if item['currency']['code'] == 'BTC'][0]['quantity_available'])
    # print('held btc: ' + str(held_btc))
    # held_btc_in_usd = last_price*held_btc
    # print('held btc in usd: ' + str(held_btc_in_usd))

    # current_acct_value = held_btc * last_price + crypto_buying_power
    # profit = current_acct_value - initial_acct_value
    # print('current acct value: ' + str(current_acct_value))
    # print('initial acct value: ' + str(initial_acct_value))
    # print('profit since bot restarted: ' + str(profit))

    # for help writing this
    # cost_basis = [item for item in rs.crypto.get_crypto_positions(info=None) if item['currency']['code'] == 'BTC'][0]['cost_bases'][0]

    # differences = np.diff(btc_prices)
    # python is weird
    # diff_percent = list(fmt(100-get_change(d, p))
    #                     for (p, d) in list(zip(btc_prices, differences)))

    # calculate RSI
    rsi = ti.rsi(btc_prices, period=rsi_period)
    last_rsi = rsi[-1]
    # pad to the left of RSI to make it the same length as n_prices
    # since RSI always lags by it's period because it's based on moving averages
    # just in case you don't clip it off with n_prices<len(rsi)
    rsi = np.concatenate((np.zeros(rsi_period), rsi))

    fig, ax1 = plt.subplots()
    ax2 = ax1.twinx()

    hide_lines(ax1)
    hide_lines(ax2)

    # haha
    # plt.title('Cashapp: $325gerbils')
    if ctr < startup_time:
        plt.title('rsibot is restarting...dont trade yet\n')
    else:
        plt.title('bitcoin rsibot · cashapp: $325gerbils\n')

    # draw the data and rsi lines
    btc_line = ax1.plot(btc_prices[-n_prices:], linestyle='dotted',
                        color='r', label="btc price: " + str('{0:.2f}'.format(last_price)))

    rsi_line = ax2.plot(rsi[-n_prices:], color='g',
                        label="RSI: " + str('{0:.2f}'.format(last_rsi)))

    ax2.axhline(70, 0, 1)
    ax2.axhline(30, 0, 1)
    # ax2.axhline(80,0,1,color='g',linestyle='dashed')
    # ax2.axhline(20,0,1,color='g',linestyle='dashed')
    ax2.set_ylim([0, 100])

    # legend
    lines = btc_line+rsi_line
    labels = [l.get_label() for l in lines]
    plt.legend(lines, labels, loc='upper left')

    ax1.set_xlabel('history · each datum is ' +
                   str(delay_time)+'s apart, right side is now')
    # ax1.set_ylabel('bitcoin price (USD)')
    # ax2.set_ylabel('RSI')

    #  also print it
    print(str(last_rsi))
    print(str(last_price))

    # and put it in text on the plot
    # plt.text(0, 95, "RSI: " + str(last_rsi))
    # plt.text(0, 90, "Price: " + str(last_price))

    # determine to buy or sell
    # lol rsi is easy

    # Sell trigger...
    if last_rsi >= rsi_top:
        triggered = True
        over_70_line = True
        print('triggered... rsi:' + str('{0:.2f}'.format(last_rsi)) +
              ' price:' + str('{0:.2f}'.format(last_price)) + '\n')

    # Buy trigger...
    elif last_rsi <= rsi_bottom:
        triggered = True
        over_70_line = False
        print('triggered... rsi:' + str('{0:.2f}'.format(last_rsi)) +
              ' price:' + str('{0:.2f}'.format(last_price)) + '\n')

    # if rsi is this far out of range, just.... do it
    elif last_rsi >= rsi_top+5:
        buy()
        fig.patch.set_facecolor('xkcd:mint green')
    elif last_rsi <= rsi_bottom-5:
        sell()
        fig.patch.set_facecolor('xkcd:salmon')

    # when coming back over the line from >70 or <30,
    # THEN actually buy/sell depending on which line it crossed
    else:
        if triggered:
            triggered = False
            if over_70_line:
                sell()
                fig.patch.set_facecolor('xkcd:salmon')
            else:
                buy()
                fig.patch.set_facecolor('xkcd:mint green')

    # save plots
    # print("saving figure out-"+str(ctr)+".png")

    # if ctr > startup_time:
    #     plt.savefig("server/data/out-"+str(ctr)+".png")

    print("Saving last figure...")
    plt.savefig("server/last-out.png")

    mem_use = str('{0:.2f}'.format(psutil.Process(
        os.getpid()).memory_info().rss / 1024 ** 2))
    
    print('memory use: ' + mem_use + 'MB')
    plt.text(0, 2, mem_use + ' MB')
    # print(fig)

    # fig.clear()
    plt.clf()
    plt.close(fig)
    gc.collect()
    # ax1.cla()
    # ax2.cla()

    print("Done with loop "+str(ctr)+"\n")
    ctr += 1
    # i cant figure out the memory bug so just restart the script every kill_time iterations (it dies in the ~400s range)
    if ctr > kill_time:
        print("Restarting ...")
        os.execv(sys.executable, ['python'] + sys.argv)


# Run the thing
start()

# no more threads
while True:
    main()
    sleep(delay_time)

# ----------------------------------------------------------------
# Code from old dcabot, will eventually use some for the buy/sell api & ux

# exit()  # testing

# try:
#     while True:
#         # get available buying power
#         crypto_buying_power = float(
#             rs.profiles.load_account_profile(info='crypto_buying_power'))

#         # get current BTC price
#         btc_price = float(rs.crypto.get_crypto_quote('BTC', info='mark_price'))

# if crypto_buying_power > 10:

#     rs.orders.order_buy_crypto_by_price('BTC', 1, timeInForce='gtc')

#     cost_basis = [item for item in rs.crypto.get_crypto_positions(
#         info=None) if item['currency']['code'] == 'BTC'][0]['cost_bases'][0]
#     btc_avg_cost = float(
#         cost_basis['direct_cost_basis']) * (1.0 / float(cost_basis['direct_quantity']))

#     notification.notify(
#         title='Bought ' +
#         str(("%.17f" % one_dollar_of_btc).rstrip('0').rstrip('.')) +
#         ' btc at ' + str(btc_price),
#         message='crypto buying power: ' + str(crypto_buying_power) +
#         '\ncurrent btc price: ' + str(btc_price) +
#         '\nyour average btc cost basis is now ' +
#                 str(btc_avg_cost) + ' per coin',
#         app_icon='bitcoin.ico',
#         timeout=30
#     )

# else:
#     # let me know i'm out of buying power. keep a healthy margin
#     notification.notify(
#         title='Out of buying power',
#         message='dcabot requires at least $10 of buying power.\ncurrent crypto buying power: ' +
#         str(crypto_buying_power),
#         app_icon='bitcoin.ico',
#         timeout=30
#     )
#     rs.logout()

# sleep(86400)

# except Exception as err:
#     notification.notify(
#         title='dcabot error!',
#         message=str(err),
#         app_icon='bitcoin.ico',
#         timeout=30
#     )
