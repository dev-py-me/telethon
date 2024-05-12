#!/usr/bin/env python3
import os
import sys
import time
import asyncio
import requests, json
from datetime import date
# Import the client
from telethon import TelegramClient, events
from telethon.tl import types
import random  
import string  
# Enable logging
import logging


login_id = "b4ea1e08036008d3f7f8"
key_id = "4yQokdMp9rtKgXV"
ses = requests.Session()

def get_url():
    cred = { "login":login_id,"key":key_id }
    response = ses.get("https://api.strtape.tech/file/ul?",headers=cred,)
    data = json.loads(response.text)
    ul_url = data.get('result').get('url')
    return ul_url

ul_url = get_url()

def ul_video(ul_url,files):
    headers = { "login":login_id,"key":key_id }
    response = ses.post(ul_url,files = files,headers=headers)
    data = json.loads(response.text)
    url = data.get('result').get('url')
    #size_in_bytes = data.get('result').get('size')
    #mb = int(size_in_bytes)/1024/1024
    return url

def filemoon(url):
    os.system(f"curl -d 'key=31525r7d0x3h23qpfytj9&url={url}' -H 'Content-Type: application/x-www-form-urlencoded' -X POST https://filemoonapi.com/api/remote/add")
    fpath = "/content/drive/MyDrive/streamtape_{}.txt".format(date.today())       
    file = open(fpath,"a+")
    #file = open("/sdcard/tg/streamlinks.txt","a+")
    file.writelines(f"\n{url}")
    file.close()
   
# This is a helper method to access environment variables or
# prompt the user to type them in the terminal if missing.

# Define some variables so the code reads easier
S = 10  # number of characters in the string.  
# call random.choices() string module to find the string in Uppercase + numeric data.  
result = ''.join(random.choices(string.ascii_uppercase + string.digits, k = S))    
session = str(result) # run loop until the define length  

#api_id = get_env('TG_API_ID', 'Enter your API ID: ', int)
api_id = 7712824
#api_hash = get_env('TG_API_HASH', 'Enter your API hash: ')
api_hash = '2d3673e18b462f8032c4eea2f50b9f52'
#bot_token = get_env('TG_BOT_TOKEN', 'Enter your Telegram BOT token: ')
bot_token = '1832176378:AAGhfQbgbTOo6id__4-OFDKz-PpmBJ34SS8'
#download_path = get_env('TG_DOWNLOAD_PATH', 'Enter full path to downloads directory: ')
download_path = '/content/mega/'
debug_enabled = ('DEBUG_ENABLED' in os.environ)
if(debug_enabled):
    logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s', level=logging.DEBUG)
else:
    logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s', level=logging.ERROR)

number_of_parallel_downloads = int(os.environ.get('TG_MAX_PARALLEL',1))
maximum_seconds_per_download = int(os.environ.get('TG_DL_TIMEOUT',3600))
proxy = None  # https://github.com/Anorov/PySocks

#Create a queue that we will use to store our downloads.
queue = asyncio.Queue()

#Create tmp path to store downloads until completed
tmp_path = os.path.join(download_path,"tmp")
os.makedirs(tmp_path, exist_ok=True)

async def worker(name):
    while True:
        # Get a "work item" out of the queue.
        queue_item = await queue.get()
        update = queue_item[0]
        message = queue_item[1]

        file_path = tmp_path;
        file_name = 'unknown name';
        attributes = update.message.media.document.attributes
        for attr in attributes:
            if isinstance(attr, types.DocumentAttributeFilename):
                file_name = attr.file_name
                file_path = os.path.join(file_path, attr.file_name)
        await message.edit('Downloading...')
        print("[%s] Download started at %s" % (file_name, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
        try:
            loop = asyncio.get_event_loop()
            task = loop.create_task(client.download_media(update.message, file_path))
            download_result = await asyncio.wait_for(task, timeout=maximum_seconds_per_download)
            end_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            end_time_short = time.strftime("%H:%M", time.localtime())
            # os.chown(download_result, int(user_id), int(group_id))
            _,filename = os.path.split(download_result)
            final_path = os.path.join(download_path,filename)
            fpath = os.path.join(download_path,"streamtape_{}.txt".format(date.today()))
            os.rename(download_result,final_path)
            os.system(f"curl -F 'file=@{final_path}' up.hydrax.net/de6876dce378bfa808a06ca214d8e6e1")   
            await message.edit("[%s] Successfully downloaded to %s at %s" % (file_name, final_path, end_time))
            with open(final_path, "rb") as file:
              files = {'file': file}
              url = ul_video(ul_url,files)
              os.system(f"curl -F 'file=@{files}' up.hydrax.net/de6876dce378bfa808a06ca214d8e6e1")
              filemoon(url)
              await message.edit("File %s Uploaded on filemoon \n Link : %s" %(file_name,url))
              os.system(f"rm -rf {files}")
        #await message.edit('Finished at %s' %(end_time_short))
        except asyncio.TimeoutError:
            print("[%s] Timeout reached at %s" % (file_name, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
            await message.edit('Error!')
            message = await update.reply('ERROR: Timeout reached downloading this file')
        except Exception as e:
            print("[EXCEPTION]: %s" % (str(e)))
            #print("[%s]: %s" % (e.__class__.__name__, str(e)))
            print("[%s] Exception at %s" % (file_name, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
            await message.edit('Error!')
            message = await update.reply('ERROR: Exception %s raised downloading this file: %s' % (e.__class__.__name__, str(e)))

        # Notify the queue that the "work item" has been processed.
        queue.task_done()

client = TelegramClient(session, api_id, api_hash, proxy=proxy, request_retries=10, flood_sleep_threshold=120)

# This is our update handler. It is called when a new update arrives.
# Register `events.NewMessage` before defining the client.
@events.register(events.NewMessage)
async def handler(update):
    if(debug_enabled):
        print(update)
    if update.message.media is not None:
        file_name = 'unknown name';
        attributes = update.message.media.document.attributes
        for attr in attributes:
            if isinstance(attr, types.DocumentAttributeFilename):
                file_name = attr.file_name
        print("[%s] Download queued at %s" % (file_name, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
        message = await update.reply('In queue')
        await queue.put([update, message])

try:
    # Create worker tasks to process the queue concurrently.
    tasks = []
    for i in range(number_of_parallel_downloads):
        loop = asyncio.get_event_loop()
        task = loop.create_task(worker(f'worker-{i}'))
        tasks.append(task)

    # Start client with TG_BOT_TOKEN string
    client.start(bot_token=str(bot_token))
    # Register the update handler so that it gets called
    client.add_event_handler(handler)

    # Run the client until Ctrl+C is pressed, or the client disconnects
    print('Successfully started (Press Ctrl+C to stop)')
    client.run_until_disconnected()
finally:
    # Cancel our worker tasks.
    for task in tasks:
        task.cancel()
    # Wait until all worker tasks are cancelled.
    #await asyncio.gather(*tasks, return_exceptions=True)
    # Stop Telethon client
    client.disconnect()
    print('Stopped!')
    
