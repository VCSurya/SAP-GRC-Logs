from datetime import datetime
import requests

from dotenv import load_dotenv
import os
load_dotenv()

def send_data_to_sap(SAP_JSON):

    try:

        SAP_JSON.pop('ID')
        SAP_JSON.pop('APPROVAL_MODE')
        session = requests.Session()
        POST_URL = os.getenv("Z_URL")
        SAP_USERNAME =  os.getenv("Z_SAP_USER")
        SAP_PASSWORD = os.getenv("Z_SAP_PASS")
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
        print(response.json())


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
        print(POST_URL)
    
        SAP_USERNAME =  os.getenv("Z_SAP_USER")
        SAP_PASSWORD = os.getenv("Z_SAP_PASS")
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
        print(res)
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


x = [
    {
        "ID": "WDF8",
        "SUBJECT": "EAM Audit review required for Pavan Jangam using FF_ID_BASIS2 on GRC_335",
        "STATUS": "Decision pending",
        "CREATEDON": "20241009",
        "DUEDATE": "",
        "CREATEDBY": "111142",
        "URL": "https://tgps4hdevapp.torrentgas.com:8240/sap/bc/webdynpro/sap/grac_ui_spm_audit_wf?APPLID=GRFN_INBOX&ENTITY_ID=FFLOG&MODE=E&OBJECT_ID=FFLOG%2f294822B0CAF31EDFA1B483E0519249C6&POWL_QUERY=294822B0CAF31EDFA0E6138BCABE1ECF&REQNO=&VARIANT=DEFAULT&WI_GROUP_OWNE=200142&WORKITEM_ID=000000437719&sap-client=335&sap-language=EN#",
        "OBJECTID": "FFLOG%2f294822B0CAF31EDFA1B483E0519249C6",
        "WORKITEMID": "000000437719",
        "RISKLEVEL": "HIGH",
        "EXPLANATION": "The log shows multiple SU01 transactions indicating user maintenance with changes to user data, which is a sensitive and change-capable activity. This requires manual approval due to the high risk of user data modification. Other columns like Program were empty and ignored, but the transaction and activity data clearly indicate risky change activity.",
        "APPROVAL_MODE": "MANUAL_APPROVAL"
    },
    {
        "ID": "WD0105",
        "SUBJECT": "EAM Audit review required for Pavan Jangam using FF_ID_BASIS on GRC_335",
        "STATUS": "Decision pending",
        "CREATEDON": "20241009",
        "DUEDATE": "",
        "CREATEDBY": "GRC_ADMIN",
        "URL": "https://tgps4hdevapp.torrentgas.com:8240/sap/bc/webdynpro/sap/grac_ui_spm_audit_wf?APPLID=GRFN_INBOX&ENTITY_ID=FFLOG&MODE=E&OBJECT_ID=FFLOG%2f294822B0CAF31EDFA1BEE4CD4BBA949F&POWL_QUERY=294822B0CAF31EDFA0E6138BCABE1ECF&REQNO=&VARIANT=DEFAULT&WI_GROUP_OWNE=200142&WORKITEM_ID=000000437743&sap-client=335&sap-language=EN#",
        "OBJECTID": "FFLOG%2f294822B0CAF31EDFA1BEE4CD4BBA949F",
        "WORKITEMID": "000000437743",
        "RISKLEVEL": "HIGH",
        "EXPLANATION": "The log contains multiple user and role maintenance transactions (SU01, SU03, SU10, PFCG) which are sensitive and change-capable activities. These transactions indicate configuration and authorization changes requiring manual approval due to high risk. Other columns like Table Name are empty and ignored for risk evaluation.",
        "APPROVAL_MODE": "MANUAL_APPROVAL"
    }
]      

# print(verify_data_from_sap("426161"))

# for i in x:
#     i.pop('ID')
#     i.pop('APPROVAL_MODE')
#     i['RISKLEVEL'] = "MEDIUM"
#     i['EXPLANATION'] = "XYZ"
#     i['OBJECTID'] = i['OBJECTID'].split('%2f')[1]
#     print(send_data_to_sap(i))    



