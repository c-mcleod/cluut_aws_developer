import datetime
from pytz import timezone
import requests
import boto3
import csv
import os
from botocore.exceptions import ClientError
from s3_uploader import upload_file
from bitcoin_price_graph import daily_price_graph
import sys


current_date = datetime.datetime.now().strftime('%d-%m-%Y')
current_time = datetime.datetime.now().astimezone(timezone('Europe/Berlin')).strftime('%H:%M:%S')
bit_url = 'https://api.coindesk.com/v1/bpi/currentprice.json'
bit_dict = requests.get(bit_url).json()
bitcoin_price = bit_dict['bpi']['USD']['rate']
s3 = boto3.client('s3')
field_names = ['current_date', 'current_time', 'bitcoin_price']
bucket_name = "cluut-aws-developer-kurs-lindsay-mcleod-14032023"
file_name = "bitcoin_prices.csv"
key = "trading/bitcoin_prices.csv"
new_line = current_date, current_time, bitcoin_price

try:
    s3.download_file(bucket_name, key, file_name)
        
except ClientError as e:
    if e.response['Error']['Code'] == "404":
        print('File does not exist, creating a new file...')
        with open(file_name, 'w') as csv_file:
            writer = csv.writer(csv_file, field_names, delimiter=';')
            writer.writerow(field_names)
    else:
        raise e
        # sys.exit()  #added during solution

finally:
    with open(file_name, 'a') as csv_file:
        updated_csv = csv.writer(csv_file, field_names, delimiter= ';')
        updated_csv.writerow(new_line)
    upload_file(file_name, bucket_name, key)
daily_price_graph(file_name, current_date)
new_plot = f'bitcoin_prices_{current_date}.png'
upload_file(new_plot, bucket_name, 'trading/plots/'+new_plot)

try:
    os.remove(file_name)
    os.remove(new_plot)
except OSError as e:
    # If it fails, inform the user.
    print("Error: %s - %s." % (e.filename, e.strerror))

if __name__ == "__main__":
    
    print(current_time)
    # print(prices_today.tail())