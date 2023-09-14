import requests
import json

my_data = json.dumps({"postID": "5", "text": "New blog text"})
headers = {'Content-Type': 'application/json'}
postID = "123"
def put():
    r = requests.put('https://81e04wxlze.execute-api.eu-central-1.amazonaws.com/posts', data=my_data, headers=headers)
    print(r.json())

def post():
    r = requests.post('https://81e04wxlze.execute-api.eu-central-1.amazonaws.com/posts', data=my_data, headers=headers)
    print(r.json())

def get():
    r = requests.get(f'https://81e04wxlze.execute-api.eu-central-1.amazonaws.com/posts/{postID}')
    print(r.json())

def delete():
    r = requests.delete(f'https://81e04wxlze.execute-api.eu-central-1.amazonaws.com/posts/{postID}')
    print(r.json())

if __name__ == "__main__":
    put()