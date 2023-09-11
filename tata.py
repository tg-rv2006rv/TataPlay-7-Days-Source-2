import time
import json

from datetime import datetime

from pytz import timezone


from config import DL_DONE_MSG, SIMPLE_CAPTION

from urllib.request import urlopen, Request

from utils import get_slug, calculateTime, subtractTime, get_sec, get_tplay_past_details

from utils import get_group_tag, mpd_download, decrypt, mux_video, tg_upload_to_sudo_users



IST = timezone('Asia/Kolkata')

def tataplay_text_handler(app, message, data_json):
    if "coming-soon" in message.text:
        message.reply_text(f"<b>Can't DL something which has not aired yet\nCheck URL and try again...</b>")
        return
    if "watch.tataplay.com" in message.text:
        download_catchup(message.text , data_json, app, message)


def download_tata_past_catchup(data_json, app, message):
    
    #cmd = /past SonyYay 04/02/2023+19:20:00-04/02/2023+22:15:00 | Obbochama

    if len(message.text.split()) < 3:
            message.reply_text("<b>Syntax: </b>`/past [channelName] [dd/mm/yyyy+hh:mm:ss-dd/mm/yyyy+hh:mm:ss] | [filename]`")
            return
    
    cmd = message.text
    if not "|" in cmd:
      message.reply_text(f"<b>No Title Found, Add one...</b>\n<b>Syntax: </b>`/past [channelName] [dd/mm/yyyy+hh:mm:ss-dd/mm/yyyy+hh:mm:ss] | [filename]`\n<b>Example: </b>`/past SONYYAY 04/02/2023+19:20:00-04/02/2023+22:15:00 | Obbochama`")
      return

    cmd = message.text.split("|")
    print(cmd)


    title = cmd[-1].strip()
    tg_cmd, channel, complete_date_data = cmd[0].strip().split(" ")

    begin, end, date_of, time_data = get_tplay_past_details(complete_date_data)


    if channel not in data_json:
        message.reply_text(f"<b>Channel Not in DB</b>")
        return

    
    msg = message.reply_text(f"<b>Processing...</b>")

    final_file_name = "{}.{}.{}.TATAPLAY.WEB-DL.AAC2.0.{}.H264-{}.mkv".format(title, time_data, data_json[channel][0]['quality'], "-".join(data_json[channel][0]['audio']) , get_group_tag(message.from_user.id)).replace(" - " , "-").replace(" " , ".")

    

    
    # /past SonyYay 04/02/2023+19:20:00-04/02/2023+22:15:00

    channel_name = data_json[channel][0]['title']
    
    stream = data_json[channel][0]['link'].replace("linear" , "catchup") + "?begin=" + str(begin) + "&end=" + str(end)
    print(stream)

    process_start_time = time.time()

    msg.edit(f'''<b>Downloading...</b>\n<code>{final_file_name}</code>
  ''')
    end_code = mpd_download(stream  , data_json[channel][0]['audio_id'] , data_json[channel][0]['video_id'], msg)


    msg.edit(f"<b>Decrypting...</b>")
    dec = decrypt(data_json[channel][0]['audio_id'] , data_json[channel][0]['video_id'] , data_json[channel][0]['k'] , end_code, msg)


    

    msg.edit(f"<b>Muxing...</b>")
    filename = mux_video(data_json[channel][0]['audio_id'], data_json[channel][0]['video_id'], end_code, final_file_name, get_group_tag(message.from_user.id), msg)
    
    
    tg_upload_to_sudo_users(filename, app, msg)



    msg.delete()




def ind_time():
    return datetime.now(IST).strftime('[%H:%M].[%d-%m-%Y]')






def download_playback_catchup(channel, title, recordingDuration, data_json, app, message):
  msg = message.reply_text(f"<b>Processing...</b>")

  time_data = ind_time()
  
  final_file_name = "{}.{}.{}.TATAPLAY.WEB-DL.AAC2.0.{}.H264-{}.mkv".format(title, time_data, data_json[channel][0]['quality'], "-".join(data_json[channel][0]['audio']) , get_group_tag(message.from_user.id)).replace(" " , ".")

  process_start_time = time.time()
        
  catchup = data_json[channel][0]['catchup']
  startTime = subtractTime(catchup , recordingDuration)
  endTime = catchup

  msg.edit(f'''<b>Recording...</b>\n<code>{final_file_name}</code>
  ''')


  time.sleep(get_sec(recordingDuration))

  end_code = mpd_download(data_json[channel][0]['link'], data_json[channel][0]['audio_id'], data_json[channel][0]['video_id'], msg)

  msg.edit(f'''<b>Decrypting...</b>\n<code>{final_file_name}</code>
        ''')

  # Decrypting
  dec = decrypt(data_json[channel][0]['audio_id'], data_json[channel][0]['video_id'], data_json[channel][0]['k'], end_code, msg)
  msg.edit(f'''<b>Muxing...</b>\n<code>{final_file_name}</code>
        ''')
  
  


  # Muxing
  filename = mux_video(data_json[channel][0]['audio_id'], data_json[channel][0]['video_id'], end_code, final_file_name, get_group_tag(message.from_user.id), msg, startTime=startTime, endTime=endTime)

  tg_upload_to_sudo_users(filename, app, msg)

          
  msg.delete()

 


def download_catchup(catchup_url, data_json, app, message):
    '''
    Parameters:
    catchup_url (str): URLs of TataPlay seperated by +, also can add |CUSTOM Title for Custom Title
    data_json (json): json containing all the info


    Example:
    (More than one url and with Custom Title)

    
    
    (More than one url and with No Custom Title i.e Title from tataplay side)

    '''
    catchup_urls = catchup_url.split("+")
    for m in catchup_urls:
        if "|" in m:
            catchup_id, title = m.split("|")[0].split("/")[-1], m.split("|")[1].strip().replace(" ", ".")
        else:
            catchup_id = m.split("/")[-1]
            title = "NO CUSTOM"


        tResponse = urlopen(trequest)
        tplay_catchup_data = json.loads(tResponse.read())
        channel_tplay_catchup = tplay_catchup_data['data']['meta'][0]['channelName']

        channel = get_slug(channel_tplay_catchup, data_json)
        

        if channel is None:
           msg.edit(f'''<b>Error...</b>\n<code>Channel Not Available to RIP</code>
        ''')
           return

        # Custom Title or TPlay Provided Title
        if title == "NO CUSTOM":
            title = tplay_catchup_data['data']['meta'][0]['title'].replace("Movie - ", "")
        else:
            title == title


        

        
        final_file_name = "{}.{}.{}.TATAPLAY.WEB-DL.AAC2.0.{}.H264-{}.mkv".format(title, time_data, data_json[channel][0]['quality'], "-".join(data_json[channel][0]['audio']) , get_group_tag(message.from_user.id)).replace(" " , ".")

        
        
        
        print("________________________")
        print(f"Catchup ID : [{catchup_id.split('?')[0]}]")
        
        

        print(title)
        print(time_data)
        # Downloading

        process_start_time = time.time()
        

        msg.edit(f'''<b>Downloading...</b>\n<code>{final_file_name}</code>
        ''')


        end_code = mpd_download(tplay_catchup_data['data']['detail']['dashWidewinePlayUrl'], data_json[channel][0]['audio_id'], data_json[channel][0]['video_id'], msg)

        msg.edit(f'''<b>Decrypting...</b>\n<code>{final_file_name}</code>
        ''')

        # Decrypting
        dec = decrypt(data_json[channel][0]['audio_id'], data_json[channel][0]['video_id'], data_json[channel][0]['k'], end_code, msg)
        msg.edit(f'''<b>Muxing...</b>\n<code>{final_file_name}</code>
        ''')

        # Muxing
        filename = mux_video(data_json[channel][0]['audio_id'], data_json[channel][0]['video_id'], end_code, final_file_name, get_group_tag(message.from_user.id), msg)


        tg_upload_to_sudo_users(filename, app, msg)
  

        msg.delete()
