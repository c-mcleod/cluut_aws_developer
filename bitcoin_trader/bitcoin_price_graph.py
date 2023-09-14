import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt



def daily_price_graph(file_name, current_date):
    """
    Takes data into dataframe then produces line graph for current day
    
    :param file_name: File to upload
    :param current_date: needs to be created in calling code
    """
    bitcoin_price = pd.read_csv(file_name, sep= ";", thousands= ",")
    prices_today = bitcoin_price[bitcoin_price["current_date"] == current_date]
    sns.set_theme()
    sns.set_context("paper")
    sns_prices_today = sns.lineplot(data = prices_today, x = 'current_time', y = "bitcoin_price", errorbar=None)
    sns_prices_today.set_title(f"The Bitcoin prices for {current_date}.")
    sns_prices_today.set_xlabel(f"Time")
    sns_prices_today.set_ylabel("Bitcoin Price $USD")
    plt.xticks(rotation = 45, ha = 'right')
    sns_prices_today.get_figure().savefig(f'bitcoin_prices_{current_date}.png', bbox_inches = 'tight')
    sns_prices_today.figure.clf()