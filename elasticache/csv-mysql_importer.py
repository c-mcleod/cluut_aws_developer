import pandas as pd
import pymysql
import boto3
import json
from botocore.exceptions import ClientError


# Use this code snippet in your app.
# If you need more information about configurations
# or implementing the sample code, visit the AWS docs:
# https://aws.amazon.com/developer/language/python/


def get_secret():
    # Create a Secrets Manager client
    secret_name = "videogames_db_pw_manager"
    region_name = "eu-central-1"

    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    # Decrypts secret using the associated KMS key.
    secret = get_secret_value_response['SecretString']
    secret_dict = json.loads(secret)
    password = secret_dict['password']
    return password

    # Your code goes here.
# MySQL connection parameters
host = 'videogames.culkhipx22mw.eu-central-1.rds.amazonaws.com'
user = 'admin'
password = get_secret()  # Retrieve password from Secrets Manager
database = 'videogames'

# CSV file path
csv_file = 'imdb-ratings.csv'

# Read the CSV file using pandas, skipping the first line
data = pd.read_csv(csv_file, skiprows=1, names=['title', 'year', 'genre', 'rating', 'votes', 'directors', 'plot'])

# Remove commas from the 'votes' column and convert to integer
data['votes'] = data['votes'].str.replace(',', '').astype(int)

# Establish a connection to the MySQL database
connection = pymysql.connect(host=host, user=user, password=password, database=database)

try:
    # Create a cursor object
    cursor = connection.cursor()

    # Iterate over each row in the CSV data
    for _, row in data.iterrows():
        # Extract the values from the row
        title = row['title']
        year = row['year']
        genre = row['genre']
        rating = row['rating']
        votes = row['votes']
        directors = row['directors']
        plot = row['plot']

        # SQL query to insert the values into the database using positional parameters
        sql = "INSERT INTO ratings (title, year, genre, rating, votes, directors, plot) " \
              "VALUES (%s, %s, %s, %s, %s, %s, %s)"

        # Execute the SQL query with the values as a tuple
        cursor.execute(sql, (title, year, genre, rating, votes, directors, plot))

    # Commit the changes to the database
    connection.commit()

    print('Data imported successfully')

except pymysql.Error as e:
    print(f'Error: {e}')

finally:
    # Close the cursor and connection
    cursor.close()
    connection.close()
    print("DONE!")