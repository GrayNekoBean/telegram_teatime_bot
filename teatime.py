'''
By @GrayNekoBean

Telegram bot: https://t.me/threeOclock_teatime_bot
Add this to your groups to notice everyone for the Teatime!

Feel free to modify and deploy this code on your own bot.
'''

import os
import time
import random
import json
import logging
import datetime
import threading

from telegram import Update, Video, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.error import TelegramError
from telegram.ext import Updater, Dispatcher, CallbackContext, CommandHandler, ConversationHandler, dispatcher
from telegram.ext.filters import Filters
from telegram.ext.messagehandler import MessageHandler

token_file = open('TOKEN', 'r')
TOKEN = token_file.read().strip()
token_file.close()

if os.path.exists('Chat_IDs.txt'):
    chatID_file = open('Chat_IDs.txt', 'r')
else:
    chatID_file = open('Chat_IDs.txt', 'w+')

chatIDs = {}
timezones = []
for line in chatID_file.readlines():
    if line == '' or line == '\n':
        continue
    dat = line.strip().split(',')
    cid = int(dat[0])
    tz = int(dat[1])
    chatIDs[cid] = tz
    if not tz in timezones:
        timezones.append(tz)
chatID_file.close()

def serialize_chatIDs() -> str:
    global chatIDs
    dat = ''
    for id in chatIDs:
        tz = chatIDs[id]
        dat += f'{id},{tz}\n'
    return dat

def add_chatID(chat_id: int, tz: int = 8):
    global chatIDs
    global timezones
    if not chat_id in chatIDs:
        chatIDs[chat_id] = tz
        if not tz in timezones:
            timezones.append(tz)
        chatID_file = open('Chat_IDs.txt', 'a+')
        chatID_file.write(f'{chat_id},{tz}\n')
        chatID_file.close()
    else:
        print(f"The chat_id: {chat_id} to add already exists in the chatID list")

def update_chatID_timezone(chat_id: int, tz: int):
    global chatIDs
    global timezones
    if chat_id in chatIDs:
        chatIDs[chat_id] = tz
        if not tz in timezones:
            timezones.append(tz)
        chatID_file = open('Chat_IDs.txt', 'w')
        chatID_file.write(serialize_chatIDs())
        chatID_file.close()
    else:
        print(f"The chat_id: {chat_id} to update isn't exist in the chatID list")

def addHour(a, b):
    sum = a+b
    if sum < 24:
        return sum
    else:
        return sum - 24
    

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)

tg_updater: Updater = Updater(token=TOKEN, use_context=True)
tg_dispatcher: Dispatcher = tg_updater.dispatcher

teatime_video_path = 'video/teatime.mp4'
teatime_video: Video = None

if os.path.exists('teatime_video_obj.json'):
    teatime_video_obj = open('teatime_video_obj.json', 'r')
    teatime_video = Video.de_json(json.load(teatime_video_obj), tg_dispatcher.bot)
    teatime_video_obj.close()

STOP = False

teatime_noticed = False

TEA_HOUR=15
TEA_MINUTE=15

SETTING_TZ = 0
SETTING_TZ_RETRY = 1

def start(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="我是群饮茶小助手，希望大家每天三点看到消息可以立刻停止做工，开始**饮茶**\n输入 /help 查看帮助")
    add_chatID(update.effective_chat.id)

def printHelp(update: Update, context: CallbackContext):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='我是@GrayNekoBean编写的饮茶提醒bot. \n使用 /start 命令来初始化，\n使用 /help 命令来显示该帮助信息，\n使用 /settimezone 命令来设置时区。\n项目地址: https://github.com/bioBean/telegram_teatime_bot'
    )
    
def RedTeaOnly(update: Update, context: CallbackContext):
    if random.randint(114, 514) < 314:
        context.bot.send_message(chat_id=update.effective_chat.id, text="アイスティーしかなかったけどいいかな？")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="只有冰红茶可以吗？")

def set_timezone(update: Update, context: CallbackContext) -> int:
    reply_keys = [[
        '+8:00(中国广东时间)',
        '+9:00(日本/韩国时间)',
        '+7:00(越南/泰国等东南亚时间)',
    ],
    [
        '-4:00(美国/加拿大东部夏令时)',
        '+1:00(英国夏令时)',
        '/cancel'
    ]]
    update.message.reply_text(
        '选择您所在的时区(基于UTC)以更准确地提醒您**饮茶**。\n默认时区为广东时间(UTC+8:00), 如果常用选项中没有你所在的时区可按(+/-)hh:00的格式手动回复',
        reply_markup=ReplyKeyboardMarkup(reply_keys, one_time_keyboard=True)
    )
    return SETTING_TZ
    
def set_timezone_done(update: Update, context: CallbackContext) -> int:
    tz_ = update.message.text.split(':')[0]
    tz = int(tz_)
    if tz < -12 or tz > 12:
        reply_keys = [['重新输入', '/cancel']]
        update.message.reply_text('时差太大嘞！', reply_markup=ReplyKeyboardMarkup(reply_keys, one_time_keyboard=True))
        return SETTING_TZ_RETRY
    update_chatID_timezone(update.effective_chat.id, tz)
    update.message.reply_text(
        '已将您的时区设置为UTC' + tz_ + ':00, 今天的工就做到这里了',
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

def set_timezone_wrong_format(update: Update, context: CallbackContext) -> int:
    reply_keys = [['重新输入', '/cancel']]
    update.message.reply_text(
        '请按照+/-hh:00的格式输入时差，该时差是与UTC/GMT标准时间的时差，例如设为国内时间则输入为“+8:00”，注意+或-号是必须的',
        reply_markup=ReplyKeyboardMarkup(reply_keys, one_time_keyboard=True)
    )
    return SETTING_TZ_RETRY

def cancel_set_timezone(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('太棒了，我直接停止做工！请继续保持每日饮茶！', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def teatime_alarm(chatID: int, video_file):
    global tg_dispatcher
    global teatime_video_path
    global teatime_video
    try:
        if teatime_video == None:
            msg = tg_dispatcher.bot.send_video(chat_id=chatID, video=video_file, timeout=1000)
            if msg != None:
                teatime_video = msg.video
                video_obj = open('teatime_video_obj.json', 'w')
                video_obj.write(teatime_video.to_json())
                video_obj.close()
            else:
                print("Error: send video failed.")
        else:
            tg_dispatcher.bot.send_video(chat_id=chatID, video=teatime_video)
    except TelegramError as err:
        print(err.message)
        
def loop():
    global teatime_noticed
    global chatIDs
    global timezones
    global TEA_HOUR
    global TEA_MINUTE
    now = datetime.datetime.now(datetime.timezone.utc)
    for tz in timezones:
        if addHour(now.hour, tz) == TEA_HOUR:
           break
    else:
        return 
    if not teatime_noticed:
        teatime_video_file = open(teatime_video_path, 'rb')
        for id in chatIDs:
            localized_hour = addHour(now.hour, chatIDs[id])
            if localized_hour == TEA_HOUR and now.minute == TEA_MINUTE:
                teatime_alarm(id, teatime_video_file)
        teatime_noticed = True
        teatime_video_file.close()
    else:
        if now.minute == TEA_MINUTE+1:
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
    exit()

def init():
    global tg_updater
    global tg_dispatcher
    
    timer_thread = threading.Thread(target=main_loop)
    timer_thread.start()
    
    cmd_thread = threading.Thread(target=cmd_loop)
    cmd_thread.start()
    
    start_handler = CommandHandler('start', start)
    tg_dispatcher.add_handler(start_handler)

    help_handler = CommandHandler('help', printHelp)
    tg_dispatcher.add_handler(help_handler)

    inm_handler = CommandHandler('114514', RedTeaOnly)
    tg_dispatcher.add_handler(inm_handler)

    set_timezone_handler = ConversationHandler(
        entry_points=[CommandHandler('settimezone', set_timezone)],
        states={
            SETTING_TZ: [MessageHandler(Filters.regex('^[+-][0-9]{1,2}:00.*'), set_timezone_done), MessageHandler(~Filters.command, set_timezone_wrong_format)],
            SETTING_TZ_RETRY: [MessageHandler(~Filters.command, set_timezone)]
        },
        fallbacks=[CommandHandler('cancel', cancel_set_timezone)]
    )
    tg_dispatcher.add_handler(set_timezone_handler)
    tg_updater.start_polling()
    #tg_updater.idle()
    pass

if __name__ == '__main__':
    init()
