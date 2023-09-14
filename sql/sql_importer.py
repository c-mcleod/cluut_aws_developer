import logging
import boto3
from botocore.exceptions import ClientError
import os

def file_importer(bucket, key, file_name):
    """
    Import a file from an S3 bucket

    :param bucket: Bucket to download from
    :param key: S3 object name.
    :param file_name: File to download to
    :return: True if file was downloaded, else False
    """

    # Download the file
    s3_client = boto3.client('s3')
    try:
        s3_client.download_file(bucket, key, file_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True
    
    
bucket = "cluut-aws-developer-kurs-lindsay-mcleod-14032023"
file_name = "mysqlsampledb.sql"
key = "raw/mysqlsampledb.sql"
file_importer(bucket, key, file_name)
print('Done')