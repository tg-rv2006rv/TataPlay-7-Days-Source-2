import os, time, ffmpeg, json, math
import subprocess
import threading
from config import sudo_users, SIMPLE_CAPTION

from datetime import timedelta
from datetime import datetime

import re

from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from tabulate import tabulate


currentFile = __file__
realPath = os.path.realpath(currentFile)
dirPath = os.path.dirname(realPath)
dirName = os.path.basename(dirPath)


if os.name == 'nt': iswin = "1"
else: iswin =  "0"


if iswin == "0":
    aria2c = dirPath + "/binaries/aria2c"
    mp4decrpyt = dirPath + "/binaries/mp4decrypt"
    ytdlp = dirPath + "/binaries/yt-dlp"

    os.system(f"chmod 777 {aria2c} {mp4decrpyt} {ytdlp}")
else:
    aria2c = dirPath + "/binaries/aria2c.exe"
    mp4decrpyt = dirPath + "/binaries/mp4decrypt.exe"
    ytdlp = dirPath + "/binaries/yt-dlp.exe"

def get_tplay_data():

    tplay_data_file_path = dirPath + "/tplay_data.json"
    json_data = open(tplay_data_file_path, "r", encoding="utf8")
    json_data = json.loads(json_data.read())
    return json_data

def download_audio_stream(link, stream_format, filename, msg):
    try:
        cmd = [
        f"{ytdlp}",
        "--geo-bypass-country",
        "IN",
        "-k",
        "--allow-unplayable-formats",
        "--no-check-certificate",
        "-f",
        str(stream_format),
        f"{link}",
        "-o",
        f"{filename}.m4a",
        "--external-downloader",
        f"{aria2c}"
    ]
        subprocess.call(cmd)
    except Exception as e:
       msg.edit('Error Running YT-DLP Command:' , str(e))




def mpd_download(link, audio_data, video_data, msg):
    # audio_data: ["audio_94482_hin=94000","audio_94490_tam=94000","audio_94483_tel=94000","audio_94486_ben=94000"]
    # video_id: "video=1297600"
    end_code = str(time.time()).replace("." , "")

    threads = []
    for i in range(0, len(audio_data)):
        filename = f"enc_{audio_data[i]}_{end_code}"
        thread = threading.Thread(target=download_audio_stream, args=(link, audio_data[i], filename, msg))
        threads.append(thread)
        thread.start()
        print(f"[DL] Audio Stream {i + 1} of {len(audio_data)}")
    try:
        video_cmd = [
            f"{ytdlp}",
            "--geo-bypass-country",
            "IN",
            "-k",
            "--allow-unplayable-formats",
            "--no-check-certificate",
            "-f",
            str(video_data),
            f"{link}",
            "-o",
            f"enc_{video_data}-{end_code}.mp4",
            "--external-downloader",
            f"{aria2c}"
        ]
        print("[DL] Video Stream")
        subprocess.call(video_cmd)
    except Exception as e:
       msg.edit('Error Downloading Video File' , str(e))

    for thread in threads:
        thread.join()

    return end_code

def decrypt(audio_data, video_data, key, end_code, msg):
  for i in range(0 , len(audio_data)):
    enc_dl_audio_file_name = f"enc_{audio_data[i]}_{end_code}.m4a"
    dec_out_audio_file_name = f"dec_{audio_data[i]}_{end_code}.m4a"
    
    
    if isinstance(key, list):
        cmd_audio_decrypt = [
            f"{mp4decrpyt}"]
    
        for k in key:
            cmd_audio_decrypt.append(str("--key"))
            cmd_audio_decrypt.append(str(k))

        cmd_audio_decrypt.append(str(enc_dl_audio_file_name)),
        cmd_audio_decrypt.append(str(dec_out_audio_file_name))
    
    else:
        
        cmd_audio_decrypt = [
            f"{mp4decrpyt}",
            "--key",
            str(key),
            str(enc_dl_audio_file_name),
            str(dec_out_audio_file_name)
            
        ]
        
    decrypt_audio = subprocess.run(cmd_audio_decrypt)
    try:
      os.remove(enc_dl_audio_file_name)
    except:
      pass

  enc_dl_video_file_name = f"enc_{video_data}-{end_code}.mp4"
  dec_out_video_file_name = f"dec_{video_data}-{end_code}.mp4"


  if isinstance(key, list):
        cmd_video_decrypt = [
            f"{mp4decrpyt}"]
    
        for k in key:
            cmd_video_decrypt.append(str("--key"))
            cmd_video_decrypt.append(str(k))

        cmd_video_decrypt.append(str(enc_dl_video_file_name)),
        cmd_video_decrypt.append(str(dec_out_video_file_name))
    
  else:
        cmd_video_decrypt = [
            f"{mp4decrpyt}",
            "--key",
            str(key),
            str(enc_dl_video_file_name),
            str(dec_out_video_file_name)
            
        ]
  try:
    decrypt_video = subprocess.run(cmd_video_decrypt)
  except Exception as e:
    msg.edit(str(e))
     
  try:
    os.remove(enc_dl_video_file_name)
  except:
    pass


  return end_code

def mux_video(audio_data, video_data, end_code, file_name, custom_group_tag, msg, startTime=None, endTime=None):
    
  dec_out_video_file_name = f"dec_{video_data}-{end_code}.mp4"
  audio_files = [f"dec_{audio_data[i]}_{end_code}.m4a" for i in range(len(audio_data))]
  ffmpeg_opts = ["ffmpeg", "-y", "-i", dec_out_video_file_name]

  
  for audio_file in audio_files:
    ffmpeg_opts.extend(["-i", audio_file])


  if startTime and endTime != None:
     ffmpeg_opts.extend(["-ss", f"{startTime}"])  
     ffmpeg_opts.extend(["-to", f"{endTime}"])  
  
  for i in range(len(audio_data)):
    ffmpeg_opts.extend(["-map", f"{i+1}:a:0"])


    
  ffmpeg_opts.extend(["-map", "0:v:0"])
  ffmpeg_opts.extend(["-metadata", f"encoded_by={custom_group_tag}"])
  ffmpeg_opts.extend(["-metadata:s:a", f"title={custom_group_tag}"])
  ffmpeg_opts.extend(["-metadata:s:v", f"title={custom_group_tag}"])
  out_name = f"{end_code}.mkv"

  
  out_file_name = file_name
     
  ffmpeg_opts.extend(["-c", "copy", out_name])

 
  try:
    subprocess.check_call(ffmpeg_opts)
  except subprocess.CalledProcessError as e:
    msg.edit(f"Error: {e}")
    return None

  try:
    os.rename(out_name, out_file_name)
  except OSError as e:
    msg.edit(f"Error: {e}")
    return None

  for audio_file in audio_files:
    try:
      os.remove(audio_file)
    except OSError as e:
      msg.edit(f"Error: {e}")
    
  try:
    os.remove(dec_out_video_file_name)
  except OSError as e:
    msg.edit(f"Error: {e}")

  return out_file_name




def extract_filename(data):
    pattern = r"FileName : (.+)"
    match = re.search(pattern, data)
    if match:
        return match.group(1).strip()
    else:
        return data

import subprocess

def trim_video_ffmpeg(input_file, output_file, start_time, end_time, msg, **kwargs):
    ffmpeg_cmd = ["ffmpeg", "-i", input_file]

    for i, (key, value) in enumerate(kwargs.items()):
        ffmpeg_cmd.extend(["-metadata:s:a:" + str(i), f"title={value}"])
    ffmpeg_cmd.extend(["-metadata:s:v", f"title={value}"])

    ffmpeg_cmd.extend(["-c:v", "copy"])  # Copy video codec

    # Add the "-ss" and "-t" options to specify start and end times for trimming
    ffmpeg_cmd.extend(["-ss", start_time, "-t", end_time])

    ffmpeg_cmd.append(output_file)

    try:
        subprocess.check_call(ffmpeg_cmd)
        return output_file
    except subprocess.CalledProcessError as e:
        msg.edit(f"Error: {e}")
        return None

# Modify the trim_and_merge_video function to handle single or multiple segments
def trim_and_merge_video(trim_segments, filename):
    if len(trim_segments) == 1:
        # Single trim segment
        start_time, end_time = trim_segments[0].split("-")
        start_time = start_time.strip()
        end_time = end_time.strip()

        # Create a unique filename for the trimmed segment
        trimmed_segment_filename = f"{filename}_trimmed.mkv"

        # Trim the video segment
        msg.edit(f"<b>Trimming...</b>")
        filename = trim_video_ffmpeg(filename, trimmed_segment_filename, start_time, end_time, msg, custom_gr_tag=get_group_tag(message.from_user.id))

        if filename:
            # Upload the trimmed file using tg_upload_to_sudo_users
            tg_upload_to_sudo_users(filename, app, msg)

            # Remove temporary files
            try:
                os.remove(filename)
            except Exception as e:
                print(f"Error removing file: {e}")

            msg.delete()

    elif len(trim_segments) > 1:
        # Multiple trim segments
        # Create a list to store the trimmed video segments
        trimmed_segments = []

        for segment in trim_segments:
            # Parse trim segment in the format "start_time-end_time"
            segment_parts = segment.split("-")
            if len(segment_parts) != 2:
                raise ValueError("Invalid trim segment format. Use 'start_time-end_time'.")

            start_time, end_time = segment_parts
            start_time = start_time.strip()
            end_time = end_time.strip()

            # Create a unique filename for each trimmed segment
            trimmed_segment_filename = f"{filename}_segment_{len(trimmed_segments)}.mkv"

            # Trim the video segment
            msg.edit(f"<b>Trimming segment {len(trimmed_segments) + 1}...</b>")
            filename = trim_video_ffmpeg(filename, trimmed_segment_filename, start_time, end_time, msg, custom_gr_tag=get_group_tag(message.from_user.id))

            if filename:
                trimmed_segments.append(filename)

        if trimmed_segments:
            # Merge the trimmed segments into one .mkv file
            msg.edit(f"<b>Merging segments...</b>")
            merged_filename = merge_video_segments(trimmed_segments)

            if merged_filename:
                # Upload the merged file using tg_upload_to_sudo_users
                tg_upload_to_sudo_users(merged_filename, app, msg)

                # Remove temporary files
                for filename in trimmed_segments + [merged_filename]:
                    try:
                        os.remove(filename)
                    except Exception as e:
                        print(f"Error removing file: {e}")

                msg.delete()

# Modify the trim_video_handler function to parse user input correctly

def trim_video_handler(app, message):
    if message.reply_to_message and message.reply_to_message.video:
        command = message.text.split(" | ")
        if len(command) != 2:
            msg = message.reply_text(f"<b>Syntax: </b>`/trim [trim_segments or single_segment] | [Filename]`")
            return

        try:
            trim_segments, filename = command
            trim_segments = trim_segments.strip().split(",")
            filename = filename.strip()

            # Call the trim_and_merge_video function to handle the trimming and merging
            trim_and_merge_video(trim_segments, filename)

        except Exception as e:
            print(f"Error handling trim command: {str(e)}")

    else:
        msg = message.reply_text(f"<b>Syntax: </b>`/trim [trim_segments or single_segment] | [Filename]`")


def merge_video_segments(segment_files, output_file):
    # Create a temporary segment list file
    with open("segment_list.txt", "w") as f:
        for segment_file in segment_files:
            f.write(f"file '{segment_file}'\n")

    # Use ffmpeg to merge the segments
    try:
        ffmpeg_cmd = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", "segment_list.txt",
            "-c:v", "copy",
            "-c:a", "copy",
            output_file
        ]

        process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            error_message = stderr.decode("utf-8")
            print(f"Error merging video segments: {error_message}")
            return None

        return output_file

    except Exception as e:
        print(f"Error merging video segments: {str(e)}")
        return None


def trim_and_merge_video(trim_segments, filename):
    # Trim the video segments
    trimmed_files = trim_video_segments(trim_segments, filename)

    if not trimmed_files:
        return None

    # Merge the trimmed video segments
    merged_file = merge_video_segments(trimmed_files, f"{filename}_merged.mp4")

    # Remove the temporary trimmed files
    for trimmed_file in trimmed_files:
        try:
            subprocess.run(["rm", trimmed_file])
        except Exception as e:
            print(f"Error removing temporary file: {str(e)}")

    return merged_file


def calculateTime(time1, time2, operation_type):
    """
    Calculates the sum or difference between two time strings in the format 'hh:mm'.
    
    Parameters:
    time1 (str): the first time string.
    time2 (str): the second time string.
    operation_type (str): the type of operation to perform ('add' or 'subtract').
    
    Returns:
    str: the resulting time string in the format 'hh:mm'.
    """
    h1, m1 = map(int, time1.split(':'))
    h2, m2 = map(int, time2.split(':'))
    
    t1 = timedelta(hours=h1, minutes=m1)
    t2 = timedelta(hours=h2, minutes=m2)
    
    if operation_type == "add":
        result = t1 + t2
    elif operation_type == "subtract":
        result = t1 - t2
    else:
        raise ValueError("Invalid operation type. Allowed values are 'add' and 'subtract'.")
    
    hours, minutes = divmod(result.seconds//60, 60)
    return f"{hours:02d}:{minutes:02d}"

def get_slug(channel_name, data):
    for i in data:
        if data[i][0]['title'] == channel_name:
            return i

def merge_video_segments(segment_files):
    """
    Merges multiple video segments into a single video file.
    
    Parameters:
    segment_files (list): A list of file paths for the video segments to merge.
    
    Returns:
    str: The file path of the merged video file.
    """
    output_file = "merged_video.mkv"
    
    # Create a temporary text file to store the list of segment files
    with open("segment_list.txt", "w") as f:
        for segment_file in segment_files:
            f.write(f"file '{segment_file}'\n")
    
    # Use ffmpeg to merge the segments
    try:
        subprocess.check_call(["ffmpeg", "-f", "concat", "-safe", "0", "-i", "segment_list.txt", "-c", "copy", output_file])
        return output_file
    except subprocess.CalledProcessError as e:
        print(f"Error merging video segments: {e}")
        return None
    finally:
        # Remove the temporary segment list file
        os.remove("segment_list.txt")


def get_yt_dlp_output(url):
    command = [f'{ytdlp}', '--allow-unplayable-formats', '--geo-bypass-country', 'IN', '--dump-json', url]
    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode == 0:
        return remove_fragments(json.loads(result.stdout))
    else:
        print(f'Error running command: {result.stderr}')
        return None

def remove_fragments(json_data):
    if isinstance(json_data, dict):
        new_dict = {}
        for key, value in json_data.items():
            if key == 'fragments':
                continue
            elif isinstance(value, dict) or isinstance(value, list):
                new_dict[key] = remove_fragments(value)
            else:
                new_dict[key] = value
        return new_dict
    elif isinstance(json_data, list):
        new_list = []
        for item in json_data:
            if isinstance(item, dict) or isinstance(item, list):
                new_list.append(remove_fragments(item))
            else:
                new_list.append(item)
        return new_list
    else:
        return json_data

def lang_mapping(lang_code, mapping_type):
    if lang_code is None:
        return 'NA'

    lang_code = lang_code.lower()

    language_mapping = {
        'short': {
            'hin': 'hi',
            'tam': 'ta',
            'tel': 'te',
            'ben': 'bn',
            'guj': 'gu',
            'pun': 'pa',
            'asm': 'ass',
            'odi': 'or',
            'mal': 'ml',
            'mar': 'mr',
            'kan': 'kn',
            'eng': 'en',
            'jap': 'jp',
            None: 'NA'
        },
        'expand': {
            'hi': 'Hindi',
            'ta': 'Tamil',
            'ta': 'Tamil',
            'te': 'Telugu',
            'bn': 'Bengali',
            'gu': 'Gujarati',
            'pa': 'Punjabi',
            'as': 'Assamese',
            'or': 'Odia',
            'ml': 'Malayalam',
            'mr': 'Marathi',
            'kn': 'Kannada',
            'en': 'English',
            'jp': 'Japanese',
            'th': 'Thai',
            'id': 'Indonesian',
            'ms': 'Malay',
            None: 'NA'
        }
    }

    return language_mapping[mapping_type].get(lang_code, 'NA')




def parse_mpd(url, audio_quality=None, video_resolution=None, video_quality=None, alang=None):
    output = get_yt_dlp_output(url)
    # output = fetch_url(url)
    # print(output)
    data = {
        'audio': [],
        'video': []
    }

    ext_mapping = {
        'm4a': 'AAC',
        'ac-3': 'DD',
        'ec-3': 'DD+'
    }

    for format in output['formats']:
        if "video" in format['format_note']:
            data['video'].append({
                'formatID': format['format_id'],
                'tbr' : format['tbr'],
                'resolution': format['resolution'],
                'width': format['width'],
                'height': format['height']
            })

        if "audio" in format['format_note']:
            lang_code = (lambda x: x if isinstance(x, str) else None)(format['language']) if format['language'] is not None else None
            data['audio'].append({
              'formatID': format['format_id'],
              'tbr' : format['tbr'],
              'languageCode' : lang_code,
              'languageName' : lang_mapping(lang_code, "expand"),
              'codec' : ext_mapping[format['ext']]
          })

    audio_data = data['audio']
    language_order = ['hi', 'ta', 'te', 'bn', 'gu', 'pa', 'as', 'or', 'ml', 'mr', 'kn', 'en', 'th', 'jp', 'th', 'id','ms', None]
    audio_data.sort(key=lambda x: language_order.index(x['languageCode']))
    data['audio'] = audio_data

    highest_resolution = max(data['video'], key=lambda x: (x['width'], x['height']))
    data['highest_resolution'] = highest_resolution

    lowest_resolution = min(data['video'], key=lambda x: (x['width'], x['height']))
    data['lowest_resolution'] = lowest_resolution



    if audio_quality:
        filtered_audio_data = []
        for audio in audio_data:
            tbr = audio['tbr']
            if audio_quality == "LQ":
                if abs(int(tbr)) <= 64:
                    audio['bitrate_category'] = "LQ"
                    filtered_audio_data.append(audio)
            elif audio_quality == "MQ":
                if abs(int(tbr)) > 64 and abs(int(tbr)) <= 128:
                    audio['bitrate_category'] = "MQ"
                    filtered_audio_data.append(audio)
            elif audio_quality == "HQ":
                if abs(int(tbr)) > 128 and abs(int(tbr)) <= 192:
                    audio['bitrate_category'] = "HQ"
                    filtered_audio_data.append(audio)

        data['audio'] = filtered_audio_data


    if video_resolution:
        filtered_video_data = []
        for video in data['video']:
            #If the requested resolution is in MPD then add that resolution
            if video['height'] == int(video_resolution.replace("p" , "")):
                filtered_video_data.append(video)
        #If the requested resolution not in MPD then add the highest resolution
        if len(filtered_video_data) < 1:
          data['video'] = highest_resolution


        if video_quality:
          if len(filtered_video_data) < 1:
            data['video'] = highest_resolution
          else:
            if video_quality == 'HQ':
                highest_bitrate_video = max(filtered_video_data, key=lambda x: x['tbr'])
                highest_bitrate_video['quality'] = 'HQ'
                data['video'] = [highest_bitrate_video]
            elif video_quality == 'LQ':
                lowest_bitrate_video = min(filtered_video_data, key=lambda x: x['tbr'])
                lowest_bitrate_video['quality'] = 'LQ'
                data['video'] = [lowest_bitrate_video]  
        else:
          highest_bitrate_video = max(filtered_video_data, key=lambda x: x['tbr'])
          highest_bitrate_video['quality'] = 'HQ'
          data['video'] = [highest_bitrate_video]
    else:
      #If no video_resolution provided then add the highest video data
      highest_bitrate_video = max(data['video'], key=lambda x: x['tbr'])
      highest_bitrate_video['quality'] = 'HQ'
      data['video'] = [highest_bitrate_video]


    if alang:
        requested_languages = alang.split('-')
        filtered_audio_data = [audio for audio in audio_data if audio['languageCode'] in requested_languages]
        data['audio'] = filtered_audio_data




    audio_ids = []
    video_ids = None
    langs = []
    audio_codec = None
    resolution = None


    for audio in data['audio']:
      audio_ids.append(audio['formatID'])
      langs.append(audio['languageName'])
      audio_codec = audio['codec'] + '2.0'
    
    resolution = str(data['video'][0]['height']) + "p"
    video_ids = data['video'][0]['formatID']

    return audio_ids, video_ids, langs, audio_codec, resolution  



def get_group_tag(userID):
   userID = str(userID)
   mapping = {
      '1130243906' : 'YK',
      '6307971588' : 'YK',
    '1680140272' : '@WorldFamousCartoons',
     '-1001946482613' : 'YK',
       '1626927985' : 'YK',
       '1144660525' : 'YK',
       '-997306137' : 'YK',
       '2020270268' : 'YK',
       '5798120731' : '@WorldFamousCartoons',
      '1640783367' : '@WorldFamousCartoons',
      '2036297424' : '@WorldFamousCartoons',
      '5043657911' : 'YK',
       
   }

   return mapping[userID]


def humanbytes(size):
    # https://stackoverflow.com/a/49361727/4723940
    # 2**10 = 1024
    if not size:
        return ""
    power = 2 ** 10
    n = 0
    Dic_powerN = {0: ' ', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'




def get_duration(filepath):
    metadata = extractMetadata(createParser(filepath))
    if metadata.has("duration"):
      return metadata.get('duration').seconds
    else:
      return 0
    

def get_thumbnail(in_filename, path, ttl):
    out_filename = os.path.join(path, str(time.time()) + ".jpg")
    open(out_filename, 'a').close()
    try:
        (
            ffmpeg
            .input(in_filename, ss=ttl)
            .output(out_filename, vframes=1)
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        return out_filename
    except ffmpeg.Error as e:
      return None
    
def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") + \
        ((str(hours) + "h, ") if hours else "") + \
        ((str(minutes) + "m, ") if minutes else "") + \
        ((str(seconds) + "s, ") if seconds else "") + \
        ((str(milliseconds) + "ms, ") if milliseconds else "")
    return tmp[:-2]


async def progress_for_pyrogram(
    current,
    total,
    ud_type,
    message,
    start
):
    now = time.time()
    diff = now - start
    if round(diff % 10.00) == 0 or current == total:
        # if round(current / total * 100, 0) % 5 == 0:
        percentage = current * 100 / total
        speed = current / diff
        elapsed_time = round(diff) * 1000
        time_to_completion = round((total - current) / speed) * 1000
        estimated_total_time = elapsed_time + time_to_completion

        elapsed_time = TimeFormatter(milliseconds=elapsed_time)
        estimated_total_time = TimeFormatter(milliseconds=estimated_total_time)

        progress = "[{0}{1}] \n**Process**: {2}%\n".format(
            ''.join(["█" for i in range(math.floor(percentage / 5))]),
            ''.join(["░" for i in range(20 - math.floor(percentage / 5))]),
            round(percentage, 2))

        tmp = progress + "{0} of {1}\n**Speed:** {2}/s\n**ETA:** {3}\n".format(
            humanbytes(current),
            humanbytes(total),
            humanbytes(speed),
            estimated_total_time if estimated_total_time != '' else "0 s"
        )
        try:
            await message.edit(
                text="{}\n {}".format(
                    ud_type,
                    tmp
                )
            )
        except:
            pass


def getTplayTime(time1 , time2 , data):
    # begin = int(data) / 1000
    # naive = str(time.strftime('%Y%m%d', time.localtime(begin)))
    date , month , year = data.split("/")
    hh, mm, ss = map(int, time1.split(':'))
    hh2 , mm2 , ss2 = map(int, time2.split(':'))
    t1 = timedelta(hours=hh, minutes=mm , seconds=ss)
    t2 = timedelta(hours=hh2, minutes=mm2 , seconds=ss2)
    f = str(t1 - t2)
    
    # if len(f.split(":")[0]) == 1:
    #         g = str(year) + str(month) + str(int(date) - 1) + "T" + "0" + str(f.replace(":" , ""))
    # else:
    #         g = str(year) + str(month) + str(int(date) - 1) + "T" + str(f.replace(":" , ""))
    
    if "-1" in f:
        if len(f.split(":")[0]) == 1:
            date_sub = int(date) - 1
            if int(date_sub) < 10:
                
                g = str(year) + str(month) + "0" + str(date_sub) + "T" + "0" + str(f.replace(":" , ""))
            else:
                g = str(year) + str(month) + str(date_sub) + "T" + "0" + str(f.replace(":" , ""))
        else:
            date_sub = int(date) - 1
            if int(date_sub) < 10:

                g = str(year) + str(month) + "0" + str(date_sub) + "T" + str(f.replace(":" , ""))
            else:
                g = str(year) + str(month) + str(date_sub) + "T" + str(f.replace(":" , ""))
            
        return g.replace("-1 day, " , "")
        
    else:
        if len(f.split(":")[0]) == 1:
            g = str(year) + str(month) + str(date) + "T" + "0" + str(f.replace(":" , ""))
        else:
            g = str(year) + str(month) + str(date) + "T" + str(f.replace(":" , ""))
        return g

def get_tplay_past_details(date_text):
    sTime, eTime = date_text.split("-")
    begin = getTplayTime(sTime.split("+")[1] , "05:30:00" , sTime.split("+")[0])
    end = getTplayTime(eTime.split("+")[1] , "05:30:00" , eTime.split("+")[0])
    date_of = sTime.split("+")[0]
    date_of = datetime.strptime(date_of, "%d/%m/%Y").strftime("%d-%m-%Y")
    time_data = "[" + sTime.split('+')[1][:len(sTime.split('+')[1]) - 3] + "-" + eTime.split('+')[1][:len(eTime.split('+')[1]) - 3] + "]"+ ".[" + date_of + "]"

    return begin, end, date_of, time_data



def get_sec(time_str):
    h, m, s = time_str.split(':')
    return int(h) * 3600 + int(m) * 60 + int(s)

def subtractTime(time1 , time2):
    hh, mm, ss = map(int, time1.split(':'))
    hh2 , mm2 , ss2 = map(int, time2.split(':'))
    t1 = timedelta(hours=hh, minutes=mm , seconds=ss)
    t2 = timedelta(hours=hh2, minutes=mm2 , seconds=ss2)

    return t1 - t2



def get_readable_time(seconds: int) -> str:
    result = ''
    (days, remainder) = divmod(seconds, 86400)
    days = int(days)
    if days != 0:
        result += f'{days}d'
    (hours, remainder) = divmod(remainder, 3600)
    hours = int(hours)
    if hours != 0:
        result += f'{hours}h'
    (minutes, seconds) = divmod(remainder, 60)
    minutes = int(minutes)
    if minutes != 0:
        result += f'{minutes}m'
    seconds = int(seconds)
    result += f'{seconds}s'
    return result


def tg_upload_to_sudo_user(filename, app, msg):
    group_chat_id = msg.chat.id
    
    caption = SIMPLE_CAPTION.format(filename)
    size = humanbytes(os.path.getsize(filename))
    duration = get_duration(filename)
    thumb = get_thumbnail(filename, "", duration / 2)
    
    try:
        app.send_video(
            video=filename,
            chat_id=group_chat_id,
            caption=caption,
            progress=progress_for_pyrogram,
            progress_args=("**Uploading...** \n", msg, time.time()),
            thumb=thumb,
            duration=duration,
            width=1280,
            height=720
        )
        print("Video sent successfully to group chat ID:", group_chat_id)
    except Exception as e:
        print("Error sending video to group chat ID:", group_chat_id)
        print("Error message:", str(e))
    
    try:
        os.remove(filename)
        os.remove(thumb)
    except:
        pass



        )
    
    audio_ids, video_ids, langs, audio_codec, resolution = parse_mpd(mpd, audio_quality=audio_quality, video_resolution=video_resolution, video_quality=video_quality, alang=alang)

    GR = get_group_tag(str(message.from_user.id))

    final_file_name = "{}.{}.{}.WEB-DL.{}.{}.H264-{}.mkv".format(name, resolution, ott, "-".join(langs) , audio_codec, GR)  

    msg.edit(f'''<b>Downloading...</b>\n<code>{final_file_name}</code>''')

    end_code = mpd_download(mpd , audio_ids , video_ids, msg)
    msg.edit(f'''<b>Decrypting...</b>''')
    decrypt(audio_ids, video_ids, key, end_code, msg)
    
    msg.edit(f'''<b>Muxing...</b>\n<code>{final_file_name}</code>''')

    filename = mux_video(audio_ids, video_ids, end_code, final_file_name, GR, msg)

    tg_upload(filename, app, msg)

    msg.delete()


def mpd_table(url, name):
    output = get_yt_dlp_output(url)
    print(output)
    
    data = {
        'audio': [],
        'video': []
    }

    ext_mapping = {
        'm4a': 'AAC',
        'ac3': 'DD',
        'eac3': 'DD+'
    }
    
    for format in output['formats']:
        if "video" in format.get('format_note', ''):
            data['video'].append({
                'formatID': format['format_id'],
                'tbr': format['tbr'],
                'resolution': format['resolution'],
                'width': format['width'],
                'height': format['height']
            })

        if "audio" in format.get('format_note', ''):
            lang_code = format.get('language', '')
            lang_name = lang_mapping(lang_code, "expand")
            codec = ext_mapping.get(format['ext'], '')
            data['audio'].append({
                'formatID': format['format_id'],
                'tbr': format['tbr'],
                'languageCode': lang_code,
                'languageName': lang_name,
                'codec': codec
            })
    
    print(data)
    audio_data = data.get('audio', [])
    video_data = data.get('video', [])
    
    audio_list = ['- {language} ({languageCode}) [{formatID}] [{audio_info}]'.format(
        language=audio['languageName'],
        languageCode=audio['languageCode'],
        formatID=audio['formatID'],
        audio_info=codec + f"2.0 - {int(audio['tbr'])} Kbps"
        
    ) for audio in audio_data]
    
    video_list = ['- {resolution} [{formatID}]'.format(
        resolution=video['resolution'],
        formatID=video['formatID']
    ) for video in video_data]
    
    table = ''
    table += name + "\n\n"

    if audio_list:
        table += 'Audio:\n'
        table += '\n'.join(audio_list) + '\n\n'
    
    if video_list:
        table += 'Video:\n'
        table += '\n'.join(video_list) + '\n'
    
    return table


import cv2
import sys
import asyncio

# Function to add semi-transparent text to a video
def add_semi_transparent_text_to_video(input_video_path, output_video_path, text_to_add):
    cap = cv2.VideoCapture(input_video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (int(cap.get(3)), int(cap.get(4))))

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Add semi-transparent text
        text_position = (20, int(cap.get(4)) - 20)  # Bottom-left corner
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1
        font_color = (255, 255, 255, 128)  # White color with reduced opacity (4th value)
        thickness = 2

        frame = cv2.putText(frame, text_to_add, text_position, font, font_scale, font_color, thickness, cv2.LINE_AA)

        # Write the frame to the output video
        out.write(frame)

    cap.release()
    out.release()

# Function to upload a file to Telegram using the /tg_upload_to_sudo_users command
async def tg_upload_to_sudo_users(input_video_path, chat_id):
    # Replace this with your actual code for uploading to Telegram using the /tg_upload_to_sudo_users command
    print(f"Uploading {input_video_path} to Telegram chat {chat_id}...")

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python add_semi_transparent_text.py input_video_path output_video_path 'text_to_add'")
        sys.exit(1)

    command = sys.argv[1]

    if command == "/add":
        input_video_path = sys.argv[2]
        output_video_path = sys.argv[3]
        text_to_add = sys.argv[4]

        # Add semi-transparent text to the video
        add_semi_transparent_text_to_video(input_video_path, output_video_path, text_to_add)
    elif command == "/tg_upload_to_sudo_users":
        # Handle the custom /tg_upload_to_sudo_users command here
        if len(sys.argv) != 7:
            print("Usage: python add_semi_transparent_text.py /tg_upload_to_sudo_users input_video_path chat_id")
            sys.exit(1)

        input_video_path = sys.argv[2]
        chat_id = sys.argv[3]

        # Upload the video to Telegram using the /tg_upload_to_sudo_users command
        loop = asyncio.get_event_loop()
        loop.run_until_complete(tg_upload_to_sudo_users(input_video_path, chat_id))
    else:
        print("Unknown command. Use '/add' to add semi-transparent text to a video or '/tg_upload_to_sudo_users' to upload the video to Telegram.")
        loop = asyncio.get_event_loop()
        loop.run_until_complete(tg_upload_to_sudo_users(input_video_path, chat_id))
