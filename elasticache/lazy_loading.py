import hashlib
import json
import mysql.connector
from sqlalchemy import create_engine
import redis
import boto3
from botocore.exceptions import ClientError
from decimal import Decimal

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return str(o)
        return super().default(o)

def get_secret(secret_name, region_name):
    """
    Returns password from secret manager given
    #Param secret_name
    #Param region_name
    """

    # Create a Secrets Manager client
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
    responce = json.loads(secret)
    return responce

# Retrieve password from Secrets Manager
secret_name = "videogames_db_pw_manager"
region_name = "eu-central-1"
responce = get_secret(secret_name, region_name)
password = responce['password']
print('Got secret')
# MySQL connection parameters
host = responce['host']
user = responce['username']
database = responce['dbInstanceIdentifier']

# Initialize Redis and MySQL connections
redis_client = redis.Redis(host='gameanalytics-cache.qh7wu0.ng.0001.euc1.cache.amazonaws.com', port=6379, db=0)
print('Connected to Redis')
mysql_engine = create_engine(f"mysql+mysqlconnector://{user}:{password}@{host}/{database}")
# mysql_engine = mysql.connector.connect(
#     host=host,
#     user=user,
#     password=password,
#     database=database
# )
print('Connected to DB')

# Lazy loading function
def lazy_loading(sql_query):
    # Generate MD5 hash of the query for Redis key
    query_hash = hashlib.md5(sql_query.encode()).hexdigest()

    # Check if the result is cached in Redis
    result = redis_client.get(query_hash)

    if result:
        # If cached, return the result from Redis
        result = json.loads(result)
        print('Result fetched from cache.')
    else:
        # If not cached, execute the query in MySQL
        # cursor = mysql_engine.cursor() 
        # cursor.execute(sql_query)
        # result = cursor.fetchall()

        with mysql_engine.connect() as connection:
            rows = connection.execute(sql_query).fetchall()
            result = [dict(row) for row in rows]

        # Cache the result in Redis with a TTL of 2 minutes
        redis_client.setex(query_hash, 120, json.dumps(result, cls=DecimalEncoder))
        print('Result fetched from DB.')
    return result

# Testing the lazy_loading function
if __name__ == '__main__':
    # Example SQL queries
    query1 = "SELECT title, year, genre, rating, votes FROM ratings WHERE votes >= 100 ORDER BY rating DESC LIMIT 10;"
    query2 = "SELECT title, year, genre, rating, votes FROM ratings WHERE votes >= 100 ORDER BY rating ASC LIMIT 10;"
    query3 = "SELECT genre, COUNT(*) AS game_count FROM ratings GROUP BY genre ORDER BY game_count DESC;"
    query4 = "SELECT year, COUNT(*) AS game_count FROM ratings GROUP BY year ORDER BY year DESC;"


    # # Testing query1
    result1 = lazy_loading(query1)
    print("Result 1:", result1)
    print()
    
    # # Testing query2
    result2 = lazy_loading(query2)
    print("Result 2:", result2)
    print()
    
    #  # Testing query2
    result3 = lazy_loading(query3)
    print("Result 3:", result3)
    print()
    
    #  # Testing query2
    result4 = lazy_loading(query4)
    print("Result 4:", result4)
    
    # Close the Redis connection (optional)
    redis_client.close()