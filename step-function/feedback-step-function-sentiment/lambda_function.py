import boto3
from datetime import datetime

comprehend = boto3.client('comprehend')

def lambda_handler(event, context):
    """
    Lambda function that detects the sentiment of customer feedback using Amazon Comprehend
    and returns a response containing the feedback ID, sentiment, customer name and type, 
    and the date and time the feedback was received.

    Parameters:
    event (dict): A dictionary containing the input values from the API Gateway event.
    context (LambdaContext): An object that provides information about the current execution context.

    Returns:
    dict: A dictionary containing the HTTP status code and the response body.

    Raises:
    Exception: An exception occurred while processing the request.
    """
    try:
        # extract input values from API Gateway event
        customer_name = event["customerName"]
        customer_type = event["customerType"]
        feedback = event["feedback"]
        
        # blank feedback is converted to Neutral to avoid error.
        if feedback == "":
            feedback = "Neutral"
            
        # use Amazon Comprehend to detect sentiment of feedback
        sentiment_response = comprehend.detect_sentiment(Text=feedback, LanguageCode='en')
        sentiment = sentiment_response['Sentiment']
        
        # create feedback ID using customer name and current datetime
        date_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        feedback_id = f"{customer_name}_{date_time}"
        
        # create response body as Python dictionary
        response_body = {
            "feedbackID": feedback_id,
            "sentiment": sentiment,
            "customerName": customer_name,
            "customerType": customer_type,
            "date": date_time.split()[0],
            "time": date_time.split()[1],
            "feedback": feedback
        }
        
        # create response object with success status code and response body
        response = {
            "statusCode": 200,
            "body": response_body
        }
        print(response_body)
        return response
        
    except Exception as e:
        # create error response object with error status code and error message
        response = {
            "statusCode": 400,
            "body": f"Error: {str(e)}"
        }
        
        return response
        
if __name__ == "__main__":
    text = {
      "customerName": "Marlon Fernandez",
      "customerType": "Premium",
      "feedback": "I had a horrible experience. Never again!"
    }

    print(lambda_handler(text))