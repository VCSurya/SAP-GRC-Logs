import os
import platform
import urllib.request
import zipfile
import subprocess
import re

def get_edge_version():
    system = platform.system()

    if system == "Windows":
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Edge\BLBeacon"
            )
            version, _ = winreg.QueryValueEx(key, "version")
            return version
        except Exception:
            return "Microsoft Edge not found on Windows"

    elif system == "Linux":
        try:
            result = subprocess.run(
                ["microsoft-edge", "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            # Output example: "Microsoft Edge 123.0.2420.97"
            return result.stdout.strip()
        except Exception:
            return "Microsoft Edge not found on Linux"

    else:
        return "Unsupported OS"


def parse_version(version_output):
    match = re.search(r"\d+\.\d+\.\d+\.\d+", version_output)
    return match.group(0) if match else None

def get_edgedriver_version(driver_path):
    """
    Returns EdgeDriver version string.
    Example output:
    'Microsoft Edge WebDriver 123.0.2420.97'
    """
    if not os.path.exists(driver_path):
        raise FileNotFoundError("EdgeDriver executable not found")

    try:
        result = subprocess.run(
            [driver_path, "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except Exception as e:
        raise RuntimeError(f"Failed to get EdgeDriver version: {e}")


def get_driver_filename():
    system = platform.system().lower()
    if system == "windows":
        return "edgedriver_win64.zip"
    elif system == "linux":
        return "edgedriver_linux64.zip"
    else:
        raise OSError("Unsupported OS")


def get_driver_exe_name():
    return "msedgedriver.exe" if platform.system() == "Windows" else "msedgedriver"


def download_and_extract_edgedriver():
    try:
        edge_version = get_edge_version()
        if not edge_version:
            raise RuntimeError("Microsoft Edge not found")

        zip_name = get_driver_filename()
        exe_name = get_driver_exe_name()

        download_dir = os.path.join(os.getcwd(), "edgedriver")
        os.makedirs(download_dir, exist_ok=True)

        zip_path = os.path.join(download_dir, zip_name)

        url = f"https://msedgedriver.microsoft.com/{edge_version}/{zip_name}"

        # print("Downloading:", url)
        urllib.request.urlretrieve(url, zip_path)

        # print("Extracting:", zip_path)
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(download_dir)

        driver_path = os.path.join(download_dir, exe_name)

        if not os.path.exists(driver_path):
            raise FileNotFoundError("EdgeDriver executable not found after extraction")

        # print("✅ EdgeDriver path:", driver_path)
        return {"success":True,"path":driver_path}
    
    except Exception as e:
    
        return {"success":False,"error":str(e)}

def validate_version():

    try:

        exe_name = "msedgedriver.exe" if platform.system() == "Windows" else "msedgedriver"

        path = os.path.join(os.getcwd(), "edgedriver", exe_name)

        if os.path.isfile(path):

            current_edge_version = get_edge_version()

            version = get_edgedriver_version(path)
            current_edge_driver_version = parse_version(version)   

            if current_edge_driver_version == current_edge_version:
                return {"success":True,"path":path}

            else:
                response = download_and_extract_edgedriver()
            
                if response.get("success",False):
                    return {"success":True,"path":response.get("path",False)}
                else:
                    return {"success":False,"path":response.get("error",False)}
        else:
        
            response = download_and_extract_edgedriver()
            
            if response.get("success",False):
                return {"success":True,"path":response.get("path",False)}
            else:
                return {"success":False,"path":response.get("error",False)}

    except Exception as e:
            return {"success":False,"error":str(e)}


# if __name__ == "__main__":
    # driver_path = download_and_extract_edgedriver()
    # version = get_edgedriver_version(driver_path)
    # numeric_version = parse_version(version)    
    # print("✅ Downloaded EdgeDriver version:", numeric_version)
    # current_edge_version = get_edge_version()
    # print(current_edge_version)
    # C:\Users\111439\OneDrive - Torrent Gas Ltd\Desktop\GRC Logs\edgedriver\msedgedriver.exe