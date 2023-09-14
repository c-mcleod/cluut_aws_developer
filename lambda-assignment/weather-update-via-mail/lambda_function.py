import json
import requests
import boto3
import os

def get_weather_now(location):
    """Returns for my location current weather"""
    try:
        l_url = f"https://geocoding-api.open-meteo.com/v1/search?name={location}&language=de"
        r_l = requests.get(l_url)
        r_l_dict = r_l.json()
        url = f"https://api.open-meteo.com/v1/forecast?latitude={r_l_dict['results'][0]['latitude']}&longitude={r_l_dict['results'][0]['longitude']}&current_weather=true&forecast_days=1&timezone=Europe%2FBerlin"
        weather_info = requests.get(url)
        return weather_info.json()
    
    except Exception as e:
        print("An error occured when trying to get weather adta for your location")
        return e
    
def weather_dict(weather_info):
    """Create Email body"""
    try:
        date_time = weather_info['current_weather']['time']
        temperature = weather_info['current_weather']['temperature']
        wind = weather_info['current_weather']['windspeed']
        wind_direction = weather_info['current_weather']['winddirection']
        weather_dict = {
            "time_stamp": date_time,
            "current_temp": temperature,
            "current_wind": wind,
            "current_wind_direction": wind_direction
        }
        return weather_dict#f"The weather in your set location for {date_time} is {temperature}°C with a wind of {wind}km/h and direction of {wind_direction}deg. "
    
    except:
        print("An error occured while trying to create your weather dictionary")
        return{}

def lambda_handler(event, context):
    """Sends Email to set address"""
    location = os.environ['MY_LOCATION']
    sns_topic =os.environ['SNS_TOPIC']
    print("Your requested location is " + location)
    
    weather_data = get_weather_now(location)
    weather_email = weather_dict(weather_data)
    
    if weather_email:
        try:
            sns = boto3.client('sns')
            response = sns.publish(
                TargetArn=sns_topic,
                Message=json.dumps({'default': json.dumps(weather_email)}),
                MessageStructure='json'
            )
            return{
                "status": "Success",
                "date": json.dumps(weather_email)
            }
        except Exception:
            print("Error in sending message to SNS")
            raise Exception
    
    else:
        print("An Error has occured in retrieving weather infromation. No message pushed to SNS.")
        return{
            "status": "Failed",
            "data": json.dumps({})
        }
if __name__ == "__main__":
    location = "Eitorf"
    
    weather_data = get_weather_now(location)
    print(weather_data)
    weather_email = weather_dict(weather_data)
    print(weather_email)