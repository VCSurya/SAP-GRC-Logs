from datetime import datetime
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
        SAP_PASSWORD = "Tgpl@7890"

        print(SAP_USERNAME)
        print(SAP_PASSWORD)


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
        SAP_PASSWORD = "Tgpl@7890"

        print(SAP_USERNAME)
        print(SAP_PASSWORD)

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
        "ID": "WDF7",
        "SUBJECT": "EAM Audit review required for Pavan Jangam using FF1_DEV335 on S4P_SU01",
        "STATUS": "Decision pending",
        "WIGROUP": "000000426228",
        "OBJECTID": "",
        "WORKITEMID": "426228",
        "CREATEDON": "20260422",
        "DUEDATE": "",
        "CREATEDBY": "GRC_ADMIN",
        "URL": "https://tgps4hdevapp.torrentgas.com:8240/sap/bc/webdynpro/sap/grac_ui_spm_audit_wf?APPLID=GRFN_INBOX&ENTITY_ID=FFLOG&MODE=E&OBJECT_ID=FFLOG%2f0AD0B3FBF09B1FD18FC74D8B1E55C000&POWL_QUERY=0AD0B3FBF09B1FD18FC577D3E77AA000&REQNO=&VARIANT=DEFAULT&WI_GROUP_OWNE=EAM_CONTRL&WORKITEM_ID=000000426228&sap-client=336&sap-language=EN#",
        "RISKLEVEL": "HIGH",
        "EXPLANATION": "The log contains risky transactions such as PFCG (Role Maintenance) and SU10 (User Mass Maintenance) which involve change-capable activities. These transactions require manual approval due to their potential impact on security and user roles. Several columns like Table Name and Activity had no populated values but this does not affect the risk evaluation since critical transactions are present.",
        "APPROVAL_MODE": "MANUAL_APPROVAL",
        "DATE_TIME": "23-04-2026 10:32:10"
    },
    {
        "ID": "WD0104",
        "SUBJECT": "EAM Audit review required for Pavan Jangam using FF_ID_BASIS1 on S4P_SU01",
        "STATUS": "Decision pending",
        "WIGROUP": "000000426237",
        "OBJECTID": "",
        "WORKITEMID": "426237",
        "CREATEDON": "20260422",
        "DUEDATE": "",
        "CREATEDBY": "GRC_ADMIN",
        "URL": "https://tgps4hdevapp.torrentgas.com:8240/sap/bc/webdynpro/sap/grac_ui_spm_audit_wf?APPLID=GRFN_INBOX&ENTITY_ID=FFLOG&MODE=E&OBJECT_ID=FFLOG%2f0AD0B3FBF09B1FD18FC74D8B1E574000&POWL_QUERY=0AD0B3FBF09B1FD18FC577D3E77AA000&REQNO=&VARIANT=DEFAULT&WI_GROUP_OWNE=EAM_CONTRL&WORKITEM_ID=000000426237&sap-client=336&sap-language=EN#",
        "RISKLEVEL": "MEDIUM",
        "EXPLANATION": "The log contains change-capable transactions such as SU01 (User Maintenance) and SCC1 (Client Copy), which are sensitive and potentially impactful. Although no direct table or command execution data is present, these transactions require manual approval due to their nature. Several columns like Table Name were empty and ignored during analysis.",
        "APPROVAL_MODE": "MANUAL_APPROVAL",
        "DATE_TIME": "23-04-2026 10:32:44"
    },
    {
        "ID": "WD0111",
        "SUBJECT": "EAM Audit review required for Pavan Jangam using FF_ID_BASIS2 on S4P_SU01",
        "STATUS": "Decision pending",
        "WIGROUP": "000000426238",
        "OBJECTID": "",
        "WORKITEMID": "426238",
        "CREATEDON": "20260422",
        "DUEDATE": "",
        "CREATEDBY": "GRC_ADMIN",
        "URL": "https://tgps4hdevapp.torrentgas.com:8240/sap/bc/webdynpro/sap/grac_ui_spm_audit_wf?APPLID=GRFN_INBOX&ENTITY_ID=FFLOG&MODE=E&OBJECT_ID=FFLOG%2f0AD0B3FBF09B1FD18FC74D8B1E586000&POWL_QUERY=0AD0B3FBF09B1FD18FC577D3E77AA000&REQNO=&VARIANT=DEFAULT&WI_GROUP_OWNE=EAM_CONTRL&WORKITEM_ID=000000426238&sap-client=336&sap-language=EN#",
        "RISKLEVEL": "HIGH",
        "EXPLANATION": "The log contains high-risk transactions such as PFCG (Role Maintenance) and SU01 (User Maintenance), which involve changes to roles and users. These are sensitive change-capable activities requiring manual approval. Although some columns like Table Name are empty, the presence of these risky transactions alone justifies a high risk and manual approval.",
        "APPROVAL_MODE": "MANUAL_APPROVAL",
        "DATE_TIME": "23-04-2026 10:33:18"
    }
]      

# print(verify_data_from_sap("426161"))

# for i in x:
#     print(send_data_to_sap(i))    



