'''
By @GrayNekoBean

Telegram bot: https://t.me/threeOclock_teatime_bot
Add this to your groups to notice everyone for the Teatime!

Feel free to modify and deploy this code on your own bot.
'''

from operator import truediv
import os
import time
import random
import json
import logging
import datetime
import threading

from telegram import Update, Video, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.error import TelegramError
from telegram.ext import Updater, Dispatcher, CallbackContext, CommandHandler, ConversationHandler
from telegram.ext.filters import Filters
from telegram.ext.messagehandler import MessageHandler


# logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#                      level=logging.INFO)

logging.basicConfig(
     format='%(asctime)s %(levelname)-8s %(message)s',
     level=logging.INFO,
     datefmt='%Y-%m-%d %H:%M:%S')

token_file = open('TOKEN', 'r')
TOKEN = token_file.read().strip()
token_file.close()

chat_id_file_path = 'Chat_IDs.txt'
stopped_id_file_path = 'stopped_IDs.txt'

if os.path.exists(chat_id_file_path):
    chatID_file = open(chat_id_file_path, 'r')
else:
    chatID_file = open(chat_id_file_path, 'w+')

if os.path.exists(stopped_id_file_path):
    stoppedID_file = open(stopped_id_file_path, 'r')
else:
    stoppedID_file = open(stopped_id_file_path, 'w+')

chatIDs = {}
stoppedIDs = []
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

for line in stoppedID_file.readlines():
    if line == '' or line == '\n':
        continue
    cid = int(line)
    stoppedIDs.append(cid)
stoppedID_file.close()


def serialize_chatIDs() -> str:
    global chatIDs
    dat = ''
    for id in chatIDs:
        tz = chatIDs[id]
        dat += f'{id},{tz}\n'
    return dat

def serialize_stopIDs() -> str:
    dat = ''
    for id in stoppedIDs:
        dat += f'{id}\n'
    return dat

def add_chatID(chat_id: int, tz: int = 8):
    global chatIDs
    global timezones
    if not chat_id in chatIDs:
        chatIDs[chat_id] = tz
        if not tz in timezones:
            timezones.append(tz)
        chatID_file = open(chat_id_file_path, 'a+')
        chatID_file.write(f'{chat_id},{tz}\n')
        chatID_file.close()
    else:
        logging.warning(f"The chat_id: {chat_id} to add already exists in the chatID list")

def add_stoppedID(chat_id: int):
    global stoppedIDs
    if not chat_id in stoppedIDs:
        stoppedIDs.append(chat_id)
        stoppedID_file = open(stopped_id_file_path, 'a+')
        stoppedID_file.write(f'{chat_id}\n')
        stoppedID_file.close()
        return True
    else:
        logging.warning(f"The chat_id: {chat_id} to add already exists in the stoppedID list")
        return False

def remove_stoppedID(chat_id: int):
    global stoppedIDs
    if chat_id in stoppedIDs:
        stoppedIDs.remove(chat_id)
        stoppedID_file = open(stopped_id_file_path, 'w')
        stoppedID_file.write(serialize_stopIDs())
        stoppedID_file.close()
        return True
    else:
        logging.warning(f"The chat_id: {chat_id} to remove not exists in the stoppedID list")
        return False

def update_chatID_timezone(chat_id: int, tz: int):
    global chatIDs
    global timezones
    if chat_id in chatIDs:
        chatIDs[chat_id] = tz
        if not tz in timezones:
            timezones.append(tz)
        chatID_file = open(chat_id_file_path, 'w')
        chatID_file.write(serialize_chatIDs())
        chatID_file.close()
    else:
        logging.warning(f"The chat_id: {chat_id} to update isn't exist in the chatID list")

def addHour(a, b):
    sum = a+b
    if sum < 24:
        return sum
    else:
        return sum - 24

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
    context.bot.send_message(chat_id=update.effective_chat.id, text="????????????????????????????????????????????????????????????????????????????????????????????????**??????**\n?????? /help ????????????")
    add_chatID(update.effective_chat.id)

def printHelp(update: Update, context: CallbackContext):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='??????@GrayNekoBean?????????????????????bot. \n?????? /start ?????????????????????\n?????? /help ?????????????????????????????????\n?????? /settimezone ????????????????????????\n?????? /stop ?????????????????????????????? /resume ????????????????????????\n----------------\n16.Nov.21??????????????????????????????bot?????????\n????????????: https://github.com/GrayNekoBean/telegram_teatime_bot'
    )
    
def RedTeaOnly(update: Update, context: CallbackContext):
    if random.randint(114, 514) < 314:
        context.bot.send_message(chat_id=update.effective_chat.id, text="?????????????????????????????????????????????????????????")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="???????????????????????????")

def stopNotice(update: Update, context: CallbackContext):
    global stoppedIDs
    cid = update.effective_chat.id
    if add_stoppedID(cid):
        context.bot.send_message(chat_id=cid, text="????????????????????????????????????????????????????????????")
    else:
        context.bot.send_message(chat_id=cid, text="?????????????????????????????????")

def resumeNotice(update: Update, context: CallbackContext):
    global stoppedIDs
    cid = update.effective_chat.id
    if remove_stoppedID(cid):
        context.bot.send_message(chat_id=cid, text="?????????????????????????????????????????????????????????pong??????????????????")
    else:
        context.bot.send_message(chat_id=cid, text="?????????????????????????????????")

def set_timezone(update: Update, context: CallbackContext) -> int:
    global chatIDs
    if update.effective_chat.id not in chatIDs:
        update.message.reply_text('?????????????????? \start ??????????????????')
        return ConversationHandler.END
    
    current_tz = chatIDs[update.effective_chat.id]
    current_tz_str = ('+' if current_tz >= 0 else '') + str(current_tz) + ':00'
    reply_keys = [[
        '+8:00(??????????????????)',
        '+9:00(??????/????????????)',
        '+7:00(??????/????????????????????????)',
    ],
    [
        '-4:00(??????/????????????????????????)',
        '+1:00(???????????????)',
        '/cancel'
    ]]
    update.message.reply_text(
        '????????????????????????(??????UTC)????????????????????????**??????**???\n???????????????UTC' + current_tz_str + ', ???????????????????????????(UTC+8:00), ???????????????????????????????????????????????????(+/-)hh:00?????????????????????',
        reply_markup=ReplyKeyboardMarkup(reply_keys, one_time_keyboard=True)
    )
    return SETTING_TZ
    
def set_timezone_done(update: Update, context: CallbackContext) -> int:
    tz_ = update.message.text.split(':')[0]
    tz = int(tz_)
    if tz < -12 or tz > 12:
        reply_keys = [['????????????', '/cancel']]
        update.message.reply_text('??????????????????', reply_markup=ReplyKeyboardMarkup(reply_keys, one_time_keyboard=True))
        return SETTING_TZ_RETRY
    update_chatID_timezone(update.effective_chat.id, tz)
    update.message.reply_text(
        '???????????????????????????UTC' + tz_ + ':00, ??????????????????????????????',
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

def set_timezone_wrong_format(update: Update, context: CallbackContext) -> int:
    reply_keys = [['????????????', '/cancel']]
    update.message.reply_text(
        '?????????+/-hh:00???????????????????????????????????????UTC/GMT???????????????????????????????????????????????????????????????+8:00????????????+???-???????????????',
        reply_markup=ReplyKeyboardMarkup(reply_keys, one_time_keyboard=True)
    )
    return SETTING_TZ_RETRY

def cancel_set_timezone(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('??????????????????????????????????????????????????????????????????', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def teatime_alarm(chatID: int):
    global tg_dispatcher
    global teatime_video_path
    global teatime_video
    try:
        if teatime_video == None:
            teatime_video_file = open(teatime_video_path, 'rb') 
            msg = tg_dispatcher.bot.send_video(chat_id=chatID, video=teatime_video_file, timeout=1000)
            teatime_video_file.close()
            if msg != None:
                teatime_video = msg.video
                video_obj = open('teatime_video_obj.json', 'w')
                video_obj.write(teatime_video.to_json())
                video_obj.close()
            else:
                logging.error("Error: send video failed.")
                return False
        else:
            tg_dispatcher.bot.send_video(chat_id=chatID, video=teatime_video)
        return True
    except TelegramError as err:
        print(err.message)
        return False

def loop():
    global teatime_noticed
    global chatIDs
    global timezones
    global TEA_HOUR
    global TEA_MINUTE
    now = datetime.datetime.now(datetime.timezone.utc)
    minute = now.minute
    for tz in timezones:
        if addHour(now.hour, tz) == TEA_HOUR and (minute == TEA_MINUTE or minute == TEA_MINUTE + 1):
           break
    else:
        return 
    if not teatime_noticed:
        noticed_count = 0
        success_count= 0
        failed_count = 0
        for id in chatIDs:
            localized_hour = addHour(now.hour, chatIDs[id])
            if localized_hour == TEA_HOUR and minute == TEA_MINUTE:
                noticed_count += 1
                if not id in stoppedIDs:
                    if teatime_alarm(id):
                        success_count += 1
                    else:
                        failed_count += 1
                    teatime_noticed = True
        if noticed_count > 0:
            logging.info(f'The bot just noticed {noticed_count} telegram users for the teatime, with {success_count} successed and {failed_count} failed.')
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
                if (cmd[0].lower() == 'set'):
                    if cmd[1].upper() == 'TEATIME':
                        inputTime = cmd[2].split(':')
                        h = int(inputTime[0])
                        m = int(inputTime[1])
                        if 0 <= h <= 23 and 0 <= m <= 59:
                            TEA_HOUR = h
                            TEA_MINUTE = m
                            print('Teatime setted to: ' + cmd[2])
                        else:
                            print('Invalid time.')
            elif len(cmd) == 2:
                if cmd[0].lower() == 'get':
                    if cmd[1].upper() == 'USER_COUNT':
                        all_users = chatIDs.keys()
                        personals = list(filter(lambda id: id > 0, all_users))
                        print('Current number of user: ' + str(len(all_users)))
                        print(f'include {len(personals)} of personal users, and {len(all_users) - len(personals)} of groups.')
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

    stop_handler = CommandHandler('stop', stopNotice)
    tg_dispatcher.add_handler(stop_handler)

    resume_handler = CommandHandler('resume', resumeNotice)
    tg_dispatcher.add_handler(resume_handler)

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
