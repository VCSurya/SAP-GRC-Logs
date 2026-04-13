from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import os
from datetime import datetime
from glob import glob
import pandas as pd, json
import httpx
import traceback
from dotenv import load_dotenv
from openai import AzureOpenAI
import requests
load_dotenv()


# MAKE CONNECTION FOR TLS handshake
timeout = httpx.Timeout(connect=45.0, read=30.0,write=30.0, pool=30.0)

http_client = httpx.Client(
    timeout=timeout,
    limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
    trust_env=True,   # safe even if you think no proxy
)

aoai_client = AzureOpenAI(
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key = os.getenv("AZURE_OPENAI_KEY") ,
    api_version="2024-02-01",
    http_client=http_client,
    timeout=30.0,
    max_retries=1
)

def verify_data_from_sap(OBJECTID,WORKITEMID):

    try:

        session = requests.Session()
        POST_URL = f"{os.getenv("Z_URL")}?$filter=OBJECTID eq '{OBJECTID}' and WORKITEMID eq '{WORKITEMID}'&$format=json"
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

        # --- Step 3: Handle Response ---
        if response.status_code in [200, 201]:
            
            if len(res.get('d',False).get('results',False)) != 0:
                return True
            
            else:
                return False
            
        else:
            return False

    except Exception as e :

        return False

def append_to_json_file(json_file_path, new_data):
    """
    Appends new_data (dict) to a JSON file.
    If file does not exist, it creates one.
    JSON file structure is a list of objects.
    """
    # If file exists, load existing data
    if os.path.exists(json_file_path):
        with open(json_file_path, "r", encoding="utf-8") as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                data = []
    else:
        data = []

    # Ensure JSON root is a list
    if not isinstance(data, list):
        raise ValueError("JSON file content must be a list")

    # Append new data
    data.append(new_data)

    # Write back to file
    with open(json_file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)

def read_excel(file_path):
    df = pd.read_excel(file_path, engine="openpyxl", dtype=str)

    # Normalize column names
    df.columns = [str(col).strip() for col in df.columns]

    # Replace NaN with empty string
    df = df.fillna("")

    # Parse Date/Time safely
    if "Date/Time" not in df.columns:
        raise ValueError("Column 'Date/Time' not found in Excel file")

    df["DateParsed"] = pd.to_datetime(
        df["Date/Time"],
        format="%d.%m.%Y %H:%M:%S",
        errors="coerce"
    )

    # Fallback parsing if some rows fail
    if df["DateParsed"].isna().any():
        fallback_mask = df["DateParsed"].isna()
        df.loc[fallback_mask, "DateParsed"] = pd.to_datetime(
            df.loc[fallback_mask, "Date/Time"],
            errors="coerce",
            dayfirst=True
        )

    # Sort by parsed date
    df = df.sort_values("DateParsed", na_position="last")

    lines = ["Transactions:","-"*85,"Date/Time | Transaction | Transaction Description | Program | Table Name | Activity","-"*85]
    
    for _, r in df.iterrows():
        time_str = (
            r["DateParsed"].strftime("%H:%M:%S")
            if pd.notna(r["DateParsed"])
            else str(r.get("Date/Time", "")).strip()
        )

        transaction = str(r.get("Transaction", "")).strip()
        program = str(r.get("Program", "")).strip()
        table_name = str(r.get("Table Name", "")).strip()
        transaction_desc = str(r.get("Transaction Description", "")).strip()


        line = f"{time_str} | {transaction} | {transaction_desc} | {program} | {table_name} | "

        # Add optional useful fields only if they have data
        extra_parts = []

        activity_desc = str(r.get("Activity Description", "")).strip()
        if activity_desc:
            extra_parts.append(activity_desc)

        old_value = str(r.get("Old Value", "")).strip()
        new_value = str(r.get("New Value", "")).strip()
        if old_value or new_value:
            extra_parts.append(f"Old Value: {old_value} -> New Value: {new_value}")

        if extra_parts:
            line += " ; ".join(extra_parts)

        lines.append(line)

    return "\n".join(lines)

def call_model(prompt):
    try:
        return aoai_client.chat.completions.create(
            model= os.getenv("AZURE_OPENAI_DEPLOYMENT"),
                response_format={"type": "json_object"},  # 👈 Force valid JSON
                messages=[
                    {
                        "role": "system",
                        "content": "You are an SAP GRC Firefighter ID (FFID) log reviewer"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=1200,
                temperature=0.2,
                top_p = 1,
                frequency_penalty = 0,
                presence_penalty = 0,
        )
    except:
        print(f"132 {traceback.print_exc()}")
        return {}

def get_latest_excel_file(directory_name):
    """
    Returns the full path of the latest (most recently modified)
    Excel file in the given directory.
    """
    excel_files = glob(os.path.join(os.getcwd(),directory_name, "*.xlsx")) + \
                  glob(os.path.join(os.getcwd(),directory_name, "*.xls"))

    if not excel_files:
        return None

    return max(excel_files, key=os.path.getmtime)

download_dir = os.path.join(os.getcwd(),os.getenv("DOWNLOAD_DIR"))   # folder path
os.makedirs(download_dir, exist_ok=True)

edge_options = Options()

prefs = {
    "download.default_directory": download_dir,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
}

edge_options.add_experimental_option("prefs", prefs)
edge_options.add_argument("--start-maximized")
edge_options.add_argument("--headless")
edge_options.add_argument("--disable-gpu")
edge_options.add_argument("--window-size=1920,1080")

service = Service(r"C:\Users\111439\Downloads\edgedriver_win64 (1)\msedgedriver.exe")

driver = webdriver.Edge(service=service, options=edge_options)

wait = WebDriverWait(driver, 20)

driver.get(
    "https://tgps4hdevapp.torrentgas.com:8240/sap/bc/webdynpro/sap/grfn_powl_inbox/?sap-client=335&sap-user=200142&sap-language=EN#"
    #   "https://tgps4hqaapp.torrentgas.com:8220/sap/bc/webdynpro/sap/grfn_powl_inbox/?sap-client=333&sap-user=200142&sap-language=EN#"
)

# Store main window handle
main_window = driver.current_window_handle

password_input = wait.until(
    EC.visibility_of_element_located((By.NAME, "sap-password"))
)

password_input.clear()
password_input.send_keys("Dev*2d7g")
# password_input.send_keys("Hello@7890")

driver.switch_to.active_element.send_keys(Keys.CONTROL, Keys.ENTER)

time.sleep(5)

try:
    if "Logon Status Check" in driver.title:
        driver.switch_to.active_element.send_keys(Keys.ENTER)
except Exception:
    pass

time.sleep(10)

setting_btn = driver.find_element(By.XPATH, "//div[@title='Open Settings']")
driver.execute_script("arguments[0].click();", setting_btn)

time.sleep(2)

# Get all div elements with the given class
tabs = driver.find_elements(
    By.XPATH, "//div[@class='lsTabStrip--item-title']"
)

for tab in tabs:
    if tab.text.strip() == "Display":

        # Get the ID of the matched div
        tab_id = tab.get_attribute("id")

        # Click using the ID
        driver.find_element(By.ID, tab_id).click()
        break

time.sleep(2)

driver.switch_to.active_element.send_keys(Keys.TAB)

time.sleep(1)

driver.switch_to.active_element.send_keys("50", Keys.TAB)

time.sleep(1)

driver.switch_to.active_element.send_keys(Keys.CONTROL,Keys.ENTER)

time.sleep(20)

tbody = wait.until(
    EC.presence_of_element_located(
        (By.CSS_SELECTOR, "[id$='-contentTBody']")
    )
)

rows = tbody.find_elements(By.TAG_NAME, "tr")

table_data = []

for row in rows:
    row_data = []

    cells = row.find_elements(By.TAG_NAME, "td")

    for cell in cells:
        # Try to find span inside td
        spans = cell.find_elements(By.TAG_NAME, "span")

        if spans:
            span = spans[0]               # usually one span per cell
            text = span.text.strip()
            span_id = span.get_attribute("id")

            row_data.append({
                "text": text,
                "span_id": span_id
            })
        else:
            # Fallback if no span exists
            row_data.append({
                "text": cell.text.strip(),
                "span_id": ""
            })

    table_data.append(row_data)

data = []
for i in table_data:
    if len(i) == 6:

        row_data = {}

        if i[1]["span_id"] != "" and i[1]['text'] != "" and i[2]['text'] != "" and  i[3]['text'] != "" :
            row_data['ID'] = i[1]["span_id"].split("-")[0]
            row_data['SUBJECT'] = i[1]['text']
            row_data['STATUS'] = i[2]['text']
            
            dt = datetime.strptime(i[3]['text'], '%d.%m.%Y %H:%M:%S')
            row_data['CREATEDON'] = dt.strftime('%Y%m%d')

            row_data['DUEDATE'] = "" # i[4]['text']
            row_data['CREATEDBY'] = i[5]['text']
            data.append(row_data)

for row in data:

    driver.find_element(By.ID,row['ID']).click()

    WebDriverWait(driver, 10).until(
        lambda d: len(d.window_handles) > 1
    )

    #  Switch to new tab

    for window in driver.window_handles:
        if window != main_window:
            driver.switch_to.window(window)
            break

    # ✅ Maximize new tab
    driver.maximize_window()

    current_url = driver.current_url

    row['URL'] = current_url
    
    for i in current_url.split('&'):
    
        if 'OBJECT_ID' in i:
            row['OBJECTID'] = i.split('=')[1].split('%2f')[1]

        elif 'WORKITEM_ID' in i:
            row['WORKITEMID'] = i.split('=')[1]
    

    if verify_data_from_sap(row['OBJECTID'],row['WORKITEMID']):
        driver.close()
        time.sleep(2)
        driver.switch_to.window(main_window)
        continue

    time.sleep(5)
    
    setting_btn = driver.find_element(By.XPATH, "//div[@title='Open Settings']")
    driver.execute_script("arguments[0].click();", setting_btn)

    time.sleep(1)

    hidden_btn = driver.find_element(By.XPATH, "//span[@title='Hidden Columns Available for Selection']")
    driver.execute_script("arguments[0].click();", hidden_btn)

    time.sleep(1)

    driver.switch_to.active_element.send_keys(Keys.LEFT_SHIFT,Keys.TAB)
    driver.switch_to.active_element.send_keys(Keys.SPACE)

    time.sleep(2)

    for i in range(0,10):
        driver.switch_to.active_element.send_keys(Keys.TAB)

    time.sleep(1)

    driver.switch_to.active_element.send_keys(Keys.SPACE)

    time.sleep(2)


    driver.switch_to.active_element.send_keys(Keys.CONTROL, Keys.ENTER)

    time.sleep(10)

    export_div = driver.find_element(By.XPATH, "//div[@title='Export']")
    driver.execute_script("arguments[0].click();", export_div)

    time.sleep(2)

    driver.switch_to.active_element.send_keys(Keys.ENTER)

    time.sleep(2)
    
    excel_file = get_latest_excel_file(os.getenv('DOWNLOAD_DIR'))


    transactions = read_excel(excel_file)

    with open("prompt.txt","r") as file:
        prompt = file.read()

    result = call_model(prompt+transactions)

    llm_response = result.choices[0].message.content

    parsed_data = json.loads(llm_response)

    row['RISKLEVEL'] = parsed_data.get('RISK_LEVEL','')
    row['EXPLANATION'] = parsed_data.get('Explanation','')
    row['APPROVAL_MODE'] = parsed_data.get('APPROVAL_MODE','')

    append_to_json_file("logs.json", row)

    if os.path.exists(excel_file):
        os.remove(excel_file)
        print("File deleted successfully")
    
    else:
        print("File not found")

    driver.close()
    time.sleep(2)
    driver.switch_to.window(main_window)

    
driver.close()
driver.close()

