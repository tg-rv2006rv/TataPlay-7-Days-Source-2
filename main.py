import requests, re
from pyrogram import Client, filters
from utils import get_tplay_data
from config import api_id, api_hash, bot_token, sudo_users, bot_creator_id, HELP_TEXT

from utils import trim_video_handler
from tata import download_playback_catchup, download_tata_past_catchup, tataplay_text_handler



app = Client("AhBokkaleTata_Bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

def edit_message(chat_id, message_id, text):
    app.edit_message_text(chat_id, message_id, text)

data_json = get_tplay_data()



@app.on_message(filters.chat(sudo_users) & filters.incoming & filters.command(['trim']) & filters.text)
def trim_video_cmd_handler(app, message):
    trim_video_handler(app, message)



@app.on_message(filters.incoming & filters.command(['start']) & filters.text)
def start_cmd_handler(app, message):
    message.reply_text(
            f"<b>AhBokkale Bot by - {bot_creator}</b>\n\n`> >`<b> Sachipo {bot_creator_id}</b>"
        )
    

@app.on_message(filters.incoming & filters.command(['help']) & filters.text)
def help_cmd_handler(app, message):
    message.reply_text(HELP_TEXT)
    

@app.on_message(filters.chat(sudo_users) & filters.incoming & filters.command(['past']) & filters.text)
def past_tata_task_cmd_handler(app, message):

    download_tata_past_catchup(data_json, app, message)

    
@app.on_message(filters.chat(sudo_users) & filters.incoming & filters.command(['tata']) & filters.text)
def playback_cmd_handler(app, message):
    
    if len(message.text.split()) < 3:
            message.reply_text("<b>Syntax: </b>`/tata [recordingDuration] [channelName] | [filename]`")
            return
        

    cmd = message.text.split("|")
        
    _, recordingDuration, channel = cmd[0].strip().split(" ")

    if ":" not in str(recordingDuration):
        message.reply_text(f"<b>Invalid Recording Duration</b>")
        return

    if channel not in data_json:
        message.reply_text(f"<b>Channel Not in DB</b>")
        return

    download_playback_catchup(channel, cmd[1].strip() , recordingDuration, data_json, app, message)



@app.on_message(filters.chat(sudo_users) & filters.incoming & filters.text)
def text_handler(app, message):
    
    tataplay_text_handler(app, message, data_json)


if __name__ == '__main__':
    print("Bot Started")
    app.run()
