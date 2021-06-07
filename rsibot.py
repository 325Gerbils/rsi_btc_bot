import robin_stocks.robinhood as rs
import tulipy as ti
import numpy as np
from time import sleep
from plyer import notification
import matplotlib.pyplot as plt

# variables
ctr = 0
rsi_period = 14
n_prices = 100
delay_time = 2
triggered = False
over_70_line = False

# pretty-print numbers (fix to 2 decimal places) as string


def fmt(input):
    return str('{0:.2f}'.format(input))

# for calculating percents


def get_change(current, previous):
    if current == previous:
        return 0
    try:
        return (abs(current - previous) / previous) * 100.0
    except ZeroDivisionError:
        return float('inf')

# buy and sell functions


def buy():
    if ctr < 100:
        print("not buying - bot started too recently")
        return
    print("buying")
    fig.patch.set_facecolor('xkcd:mint green')
    plt.text(45, 24, "BUY!")


def sell():
    if ctr < 100:
        print("not selling - bot started too recently")
        return
    print("selling")
    fig.patch.set_facecolor('xkcd:salmon')
    plt.text(45, 74, "SELL!")


# entry point
print('starting...')

# log in to robinhood
rs.login(username="benjamincooley81@gmail.com",
         password="",
         expiresIn=86400,
         by_sms=True)
print('logged in')

# data stuff
crypto_buying_power = float(
    rs.profiles.load_account_profile(info='crypto_buying_power'))
last_price = float(rs.crypto.get_crypto_quote('BTC', info='mark_price'))

# get initial history
# NOTE: The first few iterations will suck ass because this data is WRONG
# it will be replaced as the bot runs
rh_btc_history = rs.crypto.get_crypto_historicals(
    'BTC', interval='15second', span='hour', bounds='24_7', info=None)
btc_prices = np.array(
    [last_price for item in rh_btc_history], dtype=np.float64)

# infinite loop
while True:

    # get last btc price from robinhood
    last_price = float(rs.crypto.get_crypto_quote('BTC', info='mark_price'))

    # push last price and pop first price
    btc_prices = np.append(btc_prices, last_price)
    btc_prices = np.delete(btc_prices, 0)

    differences = np.diff(btc_prices)
    # python is weird
    diff_percent = list(fmt(100-get_change(d, p))
                        for (p, d) in list(zip(btc_prices, differences)))

    # calculate RSI
    rsi = ti.rsi(btc_prices, period=rsi_period)
    last_rsi = rsi[-1]
    # pad to the left of RSI to make it the same length as n_prices
    # since RSI always lags by it's period because it's based on moving averages
    # just in case you don't clip it off with n_prices<len(rsi)
    rsi = np.concatenate((np.zeros(rsi_period), rsi))

    # set up plots
    fig, ax1 = plt.subplots()
    ax2 = ax1.twinx()

    # draw the data and rsi lines
    ax1.plot(btc_prices[-n_prices:], linestyle='dotted', color='r')
    ax2.plot(rsi[-n_prices:], color='g')
    ax2.axhline(70, 0, 1)
    ax2.axhline(30, 0, 1)
    # ax2.axhline(80,0,1,color='g',linewidth=1,linestyle='dashed')
    # ax2.axhline(20,0,1,color='g',linewidth=1,linestyle='dashed')
    ax2.set_ylim([0, 100])

    #  also print it
    print(str(last_rsi))
    print(str(last_price))

    # and put it in text on the plot
    plt.text(0, 95, "RSI: " + str(last_rsi))
    plt.text(0, 90, "Price: " + str(last_price))

    # determine to buy or sell
    # lol rsi is easy

    # Sell trigger...
    if last_rsi > 70:
        triggered = True
        over_70_line = True

        print('triggered... rsi:' + fmt(last_rsi) +
              ' price:' + fmt(last_price) + '\n')

    # Buy trigger...
    elif last_rsi < 30:
        triggered = True
        over_70_line = False

        print('triggered... rsi:' + fmt(last_rsi) +
              ' price:' + fmt(last_price) + '\n')

    # if rsi is this far out of range, just.... do it
    elif last_rsi < 20:
        buy()
    elif last_rsi > 80:
        sell()

    # when coming back over the line from >70 or <30,
    # THEN actually buy/sell depending on which line it crossed
    else:
        if triggered:
            triggered = False
            if over_70_line:
                sell()
            else:
                buy()

    # save plots
    # print("saving figure out-"+str(ctr)+".png")
    # plt.savefig("data/out-"+str(ctr)+".png")
    print("Saving last figure...")
    plt.savefig("../last-out.png")

    # upkeep
    plt.close(fig)
    print("Done with loop "+str(ctr)+"\n")
    ctr += 1

    # wait
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
