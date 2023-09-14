import logging
import boto3
from botocore.exceptions import ClientError
import os
from PIL import Image

def main():
    """Reterive .png file from S3 bucket add watermark and return to bucket"""
    bucket_name = "cluut-aws-developer-kurs-lindsay-mcleod-14032023"
    file_name = "programming_coffee.png"
    key = "raw/programming_coffee.png"
    s3 = boto3.client('s3')
    s3.download_file(bucket_name, key, file_name)
    outfile = file_name.replace(".png", "_final.png")                                       #added during solution
    add_watermark(file_name, outfile, 'watermark.png')
    upload_file(outfile, bucket_name, "final/"+outfile)
 
def add_watermark(input_image_path, outfile, watermark_image_path):
    """Takes .png file and adds it to reterived file as a watermark"""
    base_image = Image.open(input_image_path)
    watermark = Image.open(watermark_image_path)
    width, height = base_image.size
    position = (base_image.size[0] - watermark.size[0], base_image.size[1] - watermark.size[1])   # """This is for position calculation from bottom right corner"""
    transparent = Image.new('RGBA', (width, height), (0,0,0,0))
    transparent.paste(base_image, (0,0))
    transparent.paste(watermark, position, mask=watermark)
    transparent.show()
    transparent.save(outfile)

def upload_file(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True

if __name__ == "__main__":
    try:
        main()
        # img = "programming_coffee.png"
        # add_watermark(img, 'watermarked_programming_coffee.png', 'watermark.png', position=(0,0))
    except Exception as e:
         print(e)