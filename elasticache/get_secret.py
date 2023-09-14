import boto3
from botocore.exceptions import ClientError
import json


secret_name = "videogames_db_pw_manager"
region_name = "eu-central-1"

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
        raise e

    # Decrypts secret using the associated KMS key.
    secret = get_secret_value_response['SecretString']
    secret_dict = json.loads(secret)
    password = secret_dict['password']
    return password

# MySQL connection parameters
host = 'videogames.culkhipx22mw.eu-central-1.rds.amazonaws.com'
user = 'admin'
password = get_secret(secret_name, region_name)  # Retrieve password from Secrets Manager
database = 'videogames'

if __name__ == "__main__":
    print (password)
    
    # {"username":"admin","password":"*******","engine":"mysql","host":"videogames.culkhipx22mw.eu-central-1.rds.amazonaws.com","port":3306,"dbInstanceIdentifier":"videogames"}