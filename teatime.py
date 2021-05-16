'''
By @GrayNekoBean

Telegram bot: https://t.me/threeOclock_teatime_bot
Add this to your groups to notice everyone for the Teatime!

Feel free to modify and deploy this code on your own bot.
'''

import os
import time
import logging
import datetime
import threading

from telegram import Update, Video
from telegram.error import TelegramError
from telegram.ext import Updater, Dispatcher, CallbackContext, CommandHandler

token_file = open('TOKEN', 'r')
TOKEN = token_file.read().strip()
token_file.close()

if os.path.exists('Chat_IDs.txt'):
    chatID_file = open('Chat_IDs.txt', 'r')
else:
    chatID_file = open('Chat_IDs.txt', 'w+')
chatIDs = [int(cid) for cid in chatID_file.readlines()]
chatID_file.close()

def add_chatID(chat_id: int):
    if not chat_id in chatIDs:
        chatIDs.append(chat_id)
        chatID_file = open('Chat_IDs.txt', 'a+')
        chatID_file.write(str(chat_id))
        chatID_file.close()

teatime_video_path = 'video/teatime.mp4'
teatime_video: Video = None

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)

tg_updater: Updater = Updater(token=TOKEN, use_context=True)
tg_dispatcher: Dispatcher = tg_updater.dispatcher

STOP = False

teatime_noticed = False

TEA_HOUR=15
TEA_MINUTE=15

def start(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="我是群飲茶小助手，希望大家每天三點看到消息可以立刻停止做工，開始**飲茶**")
    add_chatID(update.effective_chat.id)
    
def teatime_alarm(chatID: int, video_file):
    global tg_dispatcher
    global teatime_video_path
    global teatime_video
    try:
        if teatime_video == None:
            msg = tg_dispatcher.bot.send_video(chat_id=chatID, video=video_file, timeout=1000)
            if msg != None:
                teatime_video = msg.video
            else:
                print("Error: send video failed.")
        else:
            tg_dispatcher.bot.send_video(chat_id=chatID, video=teatime_video)
    except TelegramError as err:
        print(err.message)
        
def loop():
    global teatime_noticed
    global chatIDs
    global TEA_HOUR
    global TEA_MINUTE
    now = datetime.datetime.now()
    if not teatime_noticed:
        if now.hour == TEA_HOUR and now.minute == TEA_MINUTE:
            teatime_video_file = open(teatime_video_path, 'rb')
            for id in chatIDs:
                teatime_alarm(id, teatime_video_file)
            teatime_video_file.close()
            teatime_noticed = True
    else:
        if now.hour == TEA_HOUR and now.minute == TEA_MINUTE+1:
            teatime_noticed = False
    pass

def cmd_loop():
    global STOP
    global TEA_HOUR
    global TEA_MINUTE
    while True:
        try:
            cmd = input("teatime_bot> ")
            cmd = cmd.split(' ')
            if len(cmd) == 1:
                if cmd[0] == 'stop':
                    STOP = True
                    print('Stopping bot...')
                    break
            elif len(cmd) == 3:
                if (cmd[0] == 'set'):
                    if cmd[1] == 'TEATIME':
                        inputTime = cmd[2].split(':')
                        h = int(inputTime[0])
                        m = int(inputTime[1])
                        if 0 <= h <= 23 and 0 <= m <= 59:
                            TEA_HOUR = h
                            TEA_MINUTE = m
                            print('Teatime setted to: ' + cmd[2])
                        else:
                            print('Invalid time.')
        except IndexError as err:
            print('\nInvalid Input.')
            print('\n' + err)
            continue
        time.sleep(0.1)

def main_loop():
    global STOP
    global tg_updater
    while not STOP:
        loop()
        time.sleep(0.3)
    tg_updater.stop()

def init():
    global tg_updater
    global tg_dispatcher
    
    timer_thread = threading.Thread(target=main_loop)
    timer_thread.start()
    
    cmd_thread = threading.Thread(target=cmd_loop)
    cmd_thread.start()
    
    start_handler = CommandHandler('start', start)
    tg_dispatcher.add_handler(start_handler)
    tg_updater.start_polling()
    pass

init()
