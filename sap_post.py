import requests
from utils import decrypt_password
from dotenv import load_dotenv
import os
load_dotenv()

def send_data_to_sap(SAP_JSON):

    try:

        SAP_JSON.pop('ID')
        SAP_JSON.pop('APPROVAL_MODE')
        SAP_JSON.pop('DATE_TIME')
        session = requests.Session()
        POST_URL = os.getenv("Z_URL")
        SAP_USERNAME =  os.getenv("Z_SAP_USER")
        SAP_PASSWORD = decrypt_password(os.getenv("Z_SAP_PASS")).replace('"','').replace("'",'')

        # --- Step 1: Fetch CSRF Token ---
        token_response = session.get(
            POST_URL,
            auth=(SAP_USERNAME, SAP_PASSWORD),
            headers={"x-csrf-token": "Fetch","sap-client": os.getenv("Z_SAP_CLIENT")},
            verify=False
        )

        if token_response.status_code != 200:
            return {'status':False ,'error': 'In SAP API CSRF Token Not Found!'}

        csrf_token = token_response.headers.get("x-csrf-token")
        cookies = token_response.cookies

        # --- Step 2: Send POST request with CSRF token ---
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "x-csrf-token": csrf_token
        }

        response = session.post(
            POST_URL,
            json=SAP_JSON,
            headers=headers,
            auth=(SAP_USERNAME, SAP_PASSWORD),
            cookies=cookies,
            verify=False
        )

        # --- Step 3: Handle Response ---
        if response.status_code in [200, 201]:
            
            if response.json().get('d','').get('__metadata',''):
                return {'status':True}
                
            return {'status':False,'error':"Somthing Went Wrong!" }

        else:
            return {'status':False ,'error': response.json().get("error","").get("message","").get("value","")}

    except Exception as e:
        import traceback
        print(traceback.print_exc())
        return {'status':False ,'error': str(e)}

def verify_data_from_sap(WORKITEMID):

    try:

        session = requests.Session()
        POST_URL = f"{os.getenv("Z_URL")}?$filter= WORKITEMID eq '{WORKITEMID}'&$format=json"
    
        SAP_USERNAME =  os.getenv("Z_SAP_USER")
        SAP_PASSWORD = decrypt_password(os.getenv("Z_SAP_PASS")).replace('"','').replace("'",'')

        # --- Step 1: Fetch CSRF Token ---
        token_response = session.get(
            POST_URL,
            auth=(SAP_USERNAME, SAP_PASSWORD),
            headers={"x-csrf-token": "Fetch","sap-client": os.getenv("Z_SAP_CLIENT")},
            verify=False
        )

        if token_response.status_code != 200:
            return False    

        csrf_token = token_response.headers.get("x-csrf-token")
        cookies = token_response.cookies

        # --- Step 2: Send POST request with CSRF token ---
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "x-csrf-token": csrf_token
        }

        response = session.get(
            POST_URL,
            headers=headers,
            auth=(SAP_USERNAME, SAP_PASSWORD),
            cookies=cookies,
            verify=False
        )
        res = response.json()

        # --- Step 3: Handle Response ---
        if response.status_code in [200, 201]:
            
            if len(res.get('d').get('results')) != 0:
                return True
            
            else:
                return False
            
        else:
            return False

    except Exception as e :
        print(e)
        return False
  



