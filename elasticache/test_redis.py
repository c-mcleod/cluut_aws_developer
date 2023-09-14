import redis

# Connect to Redis
redis_client = redis.Redis(host='gameanalytics-cache.qh7wu0.ng.0001.euc1.cache.amazonaws.com', port=6379, db=0)

# Ping Redis
response = redis_client.ping()
if response:
    print("Redis is running and responsive")
else:
    print("Redis is not responsive")

# Close the Redis connection (optional)
redis_client.close()