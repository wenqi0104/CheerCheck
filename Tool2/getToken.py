import requests
import json

def main():
        
    url = "https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=K4w7faNOpXRqKpZezSBx3uok&client_secret=GCbC9ZSltg2SjlNW0XNsqbXzw97GOK8D"
    
    payload = ""
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    response = requests.request("POST", url, headers=headers, data=payload)
    
    print(response.text)
    

if __name__ == '__main__':
    main()