import requests

def secure_get(url):
    try:
        response = requests.get(url)
    except Exception as e:
        print(f"Exception occured during call : {e}")
        return None
    return response