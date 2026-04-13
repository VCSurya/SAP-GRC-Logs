from flask import Flask,render_template,redirect,url_for,jsonify,request
from flask_cors import CORS
import ssl
import json
from datetime import datetime
import multiprocessing
import os
import asyncio
import main
from apscheduler.schedulers.background import BackgroundScheduler


app = Flask(__name__)
CORS(app)

process_ref = shared_data = manager =None

scheduler= BackgroundScheduler()
scheduler.start()

def update_json_file(file_path: str, data: dict) -> bool:
    
    try:
        
        with open(file_path, "w") as file:
            json.dump(data, file, indent=4)

        return True
    
    except Exception as e:
        return False

def load_schedule_config():
    try:
        with open("bot/scheduler.json", 'r') as f:
            return json.load(f)
    except Exception:
        return {"enable": False, "interval_minutes": 5}

def get_bot_status():
    
    with open('bot/bot_status.json' , "r") as file:
        data = json.load(file)

    return data

def run_async_target(shared_data):
    try:

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        # Run async function
        loop.run_until_complete(main.start(shared_data))
        loop.close()
        # Process finished successfully
        os._exit(0)
    except Exception as e:
        shared_data["status"].append(f"Fatal error in process: {e}")
        os._exit(1)  # Only set 1 if a real exception occurs

def start_process():

    """Start an async function in a separate process."""
    global process_ref,shared_data
    
    if process_ref and process_ref.is_alive():
        # print("[+] Process already running.")
        return

    manager = multiprocessing.Manager()
    shared_data  = manager.dict()
    shared_data["proceed_emails"] = manager.dict()
    shared_data["status"] = manager.list(["1. Process initializing"])
    process_ref = multiprocessing.Process(target=run_async_target,args=(shared_data,))
    process_ref.start()
    shared_data["status"].append(f"2. Started process PID: {process_ref.pid}")


def scheduled_bot_run():
    status = get_bot_status()
    if not status["run"]:
        global process_ref,shared_data,manager

        # print('[Scheduler] Triggering bot run (bot was not running)')
        
        bot_data = {
            "run":True,
            "start_bot_date_time":f"{datetime.now()}"
        }

        
        start_process()
        process_ref.join()
        
        if process_ref.exitcode == 0:
            shared_data["status"].append(f"-> Process completed normally")
            bot_data['Process completed normally'] = True
            
        else:
            shared_data["status"].append(f"-> Process not completed normally its terminate")
            bot_data['Process completed normally'] = False

        bot_data['run'] = False
        bot_data['end_bot_date_time'] = f"{datetime.now()}"
        
        job = scheduler.get_job('bot_schedule')
        
        with open("bot/scheduler.json","r") as file:
            data = json.load(file)

        if job:
            # Return the next run time
            bot_data['Next run time'] = job.next_run_time.strftime('%Y-%m-%d %H:%M:%S')
            data["Next run time"] = job.next_run_time.strftime('%Y-%m-%d %H:%M:%S')
    

        with open("bot/scheduler.json","w") as file:
            json.dump(data, file, indent=2)

        return {'status':True,"msg":""}

    else:
        return {'status':False,"msg":"Bot already running"}
 

def stop_process():
    """Stop the running process cleanly."""
    
    try:
        global process_ref,shared_data

        if process_ref and process_ref.is_alive():

            shared_data["status"].append(f"Terminating process PID: {process_ref.pid}...")

            # print(f"[Main] Terminating process PID: {process_ref.pid}...")
            
            process_ref.terminate()
            process_ref.join()
            shared_data["status"].append(f"Process terminated successfully.")
            
            return {"status":True,"msg":"Process terminated successfully."}

            # print("[Main] Process terminated successfully.")
        else:
            # print("[Main] No process running.")
            return {"status":False,"error":"No process running."}

    except Exception as e:
        return {"status":False,"error":str(e)}

def update_scheduler():
    try:
        config = load_schedule_config()
        stop_process()
        scheduler.remove_all_jobs()

        if config.get('enable'):
            job = scheduler.add_job(scheduled_bot_run, 'interval', minutes=int(config.get('interval_minutes', 5)), id='bot_schedule', replace_existing=True)
            return {'status':True,"next_run_time":job.next_run_time.strftime('%Y-%m-%d %H:%M:%S')}
        return {'status':True}
    
    except Exception as e:
        return {'status':False,"error":str(e)}


def default():  # start point 
    global scheduler,shared_data
    shared_data = None
    scheduler.remove_all_jobs()
    stop_process()
    update_scheduler()



# -------------------------------------------------------------

@app.route("/update_scheduler",methods=["POST","GET"])
def update_scheduler_method():
    
    """
    {
      inputValue: "1"
      isChecked: true
      selectedTime: "minutes"
    }
    """
    try:
        
        if request.method == 'POST':
        
            status = get_bot_status()
            
            if not status["run"]:
            
                data = request.get_json()
                scheduler_data = {}

                if data['isChecked'] and int(data['inputValue']) > 0:
                    
                    if data['selectedTime'] == "minutes":
                        scheduler_data = {
                            "interval_minutes":int(data['inputValue']),
                            "enable":True,
                            "duration":"minutes"
                        }

                    elif data['selectedTime'] == "hours":
                        scheduler_data = {
                            "interval_minutes":int(data['inputValue'])*60,
                            "enable":True,
                            "duration":"hours"

                        }
                    else:
                        return jsonify({"success":False,"error":"Enter Valid Input Try Again!"})

                else:
                    scheduler_data = {
                        "interval_minutes":1,
                        "enable":False,
                        "duration": "minutes"
                    }
                    
                
                scheduler_data["last_updated_scheduler"] = str(datetime.now())

                with open("bot/scheduler.json", "w") as file:
                    json.dump(scheduler_data, file, indent=4)

                res = update_scheduler()

                if res["status"]:

                    if res.get("next_run_time"):
                        scheduler_data["Next run time"] = res["next_run_time"]         
                        
                        bot_data = {
                            "run":False,
                            "Next run time": scheduler_data["Next run time"]
                        }
                        update_json_file("bot/bot_status.json",bot_data)

                        with open("bot/scheduler.json", "w") as file:
                            json.dump(scheduler_data, file, indent=4)

                    return jsonify({"success":True,"msg":"scheduler update successfully"})
                else:
                    return jsonify({"success":True,"msg":"error in updating scheduler try again"})
            else:
                return jsonify({"success":True,"msg":"Bot is running, error in updating scheduler first stop the bot!"})
        else:

            with open("bot/scheduler.json", 'r', encoding='utf-8') as file:
                bot_scheduler = json.load(file)

            if bot_scheduler['duration'] == 'hours':
                bot_scheduler['interval_minutes'] = int(bot_scheduler['interval_minutes']/60); 

            return jsonify({"success":True,"bot_scheduler":bot_scheduler})
            
    except Exception as e:
        return jsonify({"success":False,"error":f"505: {str(e)}"})

@app.route("/logs", methods=['GET'])
async def logs():

    try:
        logs = {}

        with open("bot/bot_status.json", 'r', encoding='utf-8') as file:
            bot_status = json.load(file)
        
        logs["bot_status"] = bot_status
        
        global shared_data
        if shared_data:
            safe_data  = dict(shared_data)
            safe_data['proceed_emails']  = dict(shared_data['proceed_emails'])
            safe_data["status"] = list(shared_data["status"])
            logs["data"] = safe_data
    
        return {"success":True,"logs":logs}

    except Exception as e:
        return {"success":False,"error":str(e)}

@app.route("/reset-bot",methods=["GET"])
def reset_bot():

    try:
        global process_ref
        scheduler.remove_all_jobs()
        stop_process()
        
        scheduler_data = {
            "interval_minutes": 1,
            "enable": False,
            "duration": "minutes",
            "Next run time": ""
        }

        with open("bot/scheduler.json", "w") as file:
            json.dump(scheduler_data, file, indent=4)

        bot_status = {
            "run": False
        }

        with open("bot/bot_status.json", "w") as file:
            json.dump(bot_status, file, indent=4)


        return jsonify({"success":True,"msg":"Bot Reset Sucessfully."})

    except Exception as e:
        return jsonify({"success":False,"error":str(e)})
     

# start the bot immediately
@app.route("/start",methods=["GET"])
def start_bot():
    global scheduler
    try:
        
        data = load_schedule_config()

        if data.get('enable'):
            return {"success":False,"error":"Please First Disable the Scheduler!"}
            
        scheduler.remove_all_jobs()
        stop_process()

        if not data.get('enable'):
            job = scheduler.add_job(scheduled_bot_run, trigger="date", id='bot_schedule', replace_existing=True)
            return {'status':True,"next_run_time":job.next_run_time.strftime('%Y-%m-%d %H:%M:%S')}
        
        return {'status':True}
        
    except Exception as e:
        return {"success":False,"error":f"Error: {str(e)} Durring Bot Start."}

# load dashbored page
@app.route("/apple")
def apple():
        
    return render_template("index.html")

# flask trigger point
@app.route("/")
def home():
    return redirect(url_for("apple"))
    
default()

if __name__ == '__main__':

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile='cert.pem', keyfile='key.pem')
    app.run(host='0.0.0.0', port=5000, ssl_context=context,debug=True)
