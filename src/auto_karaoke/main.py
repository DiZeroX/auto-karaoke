import whisper_timestamped as whisper
import torch
import json
import ass
import argparse
from pathlib import Path
import re
import datetime
import string
import copy
import decimal
# import stable_whisper

def preprocess_lyrics(input_lyrics):
    temp_lyrics = []
    current_group = []
    for line in input_lyrics:
        if line == "":
            current_group = []
            continue
        new_line = line.strip()
        new_line = new_line.replace("(", "")
        new_line = new_line.replace(")", "")
        new_line = new_line.replace("[", "")
        new_line = new_line.replace("]", "")
        new_line = remove_end_punctuation(new_line)

        is_group_repetition = re.search("^[x×][0-9]*$", new_line)
        if is_group_repetition:
            repeat_count = int(new_line[1:])
            for _i in range(repeat_count):
                temp_lyrics.extend(current_group)
            current_group = []
        else:
            is_line_repetition = re.search("[x×][0-9]*$", new_line)
            if is_line_repetition:
                repeat_count = int(new_line[-1])  # TODO: make more flexible for 2+ digit numbers
                new_line = new_line[:-2].strip()
                new_line = remove_end_punctuation(new_line)
                for _i in range(repeat_count):
                    temp_lyrics.append(new_line)
                    current_group.append(new_line)
            else:
                current_group.append(new_line)
                temp_lyrics.append(new_line)

    output_lyrics = []
    for line in temp_lyrics:
        remove_dash_lines = re.split(" [-––] ", line)
        if len(remove_dash_lines) == 1:
            output_lyrics.append(line)
        else:
            for split_line in remove_dash_lines:
                output_lyrics.append(split_line)

    return output_lyrics


def remove_end_punctuation(temp_line):
    last_character = temp_line[-1]
    if (last_character == "." or
            last_character == "," or
            last_character == "?" or
            last_character == "!" or
            last_character == " "):
        return remove_end_punctuation(temp_line[:-1])
    else:
        return temp_line


def is_same_word(word1: str, word2: str):
    # lowercase and remove punctuation and whitespace
    word1 = word1.lower().translate(str.maketrans("", "", string.punctuation)).strip()
    word2 = word2.lower().translate(str.maketrans("", "", string.punctuation)).strip()
    return word1 == word2


def process_karaoke(input_karaoke: ass.Document, input_lyrics, input_song_analysis):
    output_karaoke = copy.deepcopy(input_karaoke)
    del output_karaoke.events[-1]
    word_timings = []

    for segment in input_song_analysis["segments"]:
        for word in segment["words"]:
            # convert seconds to centiseconds
            temp_word = copy.copy(word)
            temp_word["start"] = temp_word["start"] * 100
            temp_word["end"] = temp_word["end"] * 100
            word_timings.append(temp_word)

    word_timing_index = 0
    current_timing_group = []
    invalid_word_timings = []
    word_timing_text = None
    for lyric_line_index, lyric_line in enumerate(input_lyrics):
        lyric_line_words = lyric_line.split(" ")
        # .ass /k centiseconds (100 centiseconds = 1 second) and is duration based
        # whisper-timestamped is in seconds and is absolute based
        line_found = False
        for line_word_index, line_word in enumerate(lyric_line_words):
            # if word_timing_index >= len(word_timings):
            #     break
            match_found = False
            # TODO: change static range to dynamic using length of this line and next line
            # retry_range = len(lyric_line_words) - line_word_index
            # if lyric_line_index < len(input_lyrics):
            #     retry_range += len(input_lyrics[lyric_line_index+1].split(" "))
            for retry_number in range(4):
                if word_timing_index + retry_number >= len(word_timings):
                    break
                word_timing = word_timings[word_timing_index + retry_number]
                word_timing_text = word_timing["text"]
                if is_same_word(line_word, word_timing_text):
                    match_found = True
                    # If match found, insert invalid words timings that preceded it
                    if len(invalid_word_timings) > 0:
                        invalid_timing_start = invalid_word_timings[0]["start"]
                        invalid_timing_end = invalid_word_timings[-1]["end"]
                        full_text = ""
                        for invalid_timing in invalid_word_timings:
                            full_text += invalid_timing["text"] + " "
                        current_timing_group.append({
                            "text": full_text.strip(),
                            "start": invalid_timing_start,
                            "end": invalid_timing_end,
                        })
                        # word_timing_index += len(invalid_word_timings)
                        invalid_word_timings = []

                    current_timing_group.append({
                        "text": line_word,
                        "start": word_timing["start"],
                        "end": word_timing["end"],
                        # "duration": word_timing["end"] - word_timing["start"]
                    })
                    word_timing_index += 1 + retry_number
                    break

            # no match in upcoming 4 words
            if match_found is False:
                invalid_word = {
                    "text": line_word,
                    "start": word_timings[word_timing_index]["start"],
                    "end": word_timings[word_timing_index]["end"],
                    "aitext": word_timings[word_timing_index]["text"],
                }
                invalid_word_timings.append(invalid_word)
                # word_timing_index += 1
                # If that last word in line is not found, then insert invalid timings
                if line_word_index == len(lyric_line_words) - 1:
                    # TODO: refactor to function
                    invalid_timing_start = invalid_word_timings[0]["start"]
                    invalid_timing_end = invalid_word_timings[-1]["end"]
                    full_text = ""
                    for invalid_timing in invalid_word_timings:
                        full_text += invalid_timing["text"] + " "
                    current_timing_group.append({
                        "text": full_text.strip(),
                        "start": invalid_timing_start,
                        "end": invalid_timing_end,
                    })
                    # word_timing_index += len(invalid_word_timings)
                    invalid_word_timings = []
                # If AI word is not in rest of current lyric line or the next lyric line, increment index to next AI
                # word TODO: cleanup this nightmare
                if word_timing_index < len(word_timings) - 1:
                    temp_lyric_words = []
                    line_words_index_start = line_word_index + 1 if line_word_index < len(lyric_line_words) - 1 else len(lyric_line_words) - 1
                    line_words_index_stop = len(lyric_line_words)
                    for temp_line_word_index in range(line_words_index_start, line_words_index_stop):
                        temp_lyric_words.append(lyric_line_words[temp_line_word_index])
                    if lyric_line_index < len(input_lyrics) - 1:
                        temp_lyric_line = input_lyrics[lyric_line_index+1]
                        temp_lyric_line_words = temp_lyric_line.split(" ")
                        for temp_lyric_line_word in temp_lyric_line_words:
                            temp_lyric_words.append(temp_lyric_line_word)
                    found_future_lyric_match = False
                    for temp_lyric_word in temp_lyric_words:
                        if is_same_word(temp_lyric_word, word_timing_text):
                            found_future_lyric_match = True
                            break
                    if not found_future_lyric_match:
                        word_timing_index += 1

        subtitle_text = ""
        for current_timing_word in current_timing_group:
            word_duration = int(round(current_timing_word['end'] - current_timing_word['start']))
            subtitle_text += f"{{\\k{word_duration}}}{current_timing_word['text']} "
        subtitle_text = subtitle_text.strip()
        subtitle_style = "Sample KM [Up]"
        subtitle_start = datetime.timedelta(seconds=current_timing_group[0]["start"] / 100)
        subtitle_end = datetime.timedelta(seconds=current_timing_group[-1]["end"] / 100)
        dialogue_event = ass.Dialogue(layer=0, start=subtitle_start, end=subtitle_end, style=subtitle_style, name='', margin_l=0, margin_r=0, margin_v=0, effect='', text=subtitle_text)
        output_karaoke.events.append(dialogue_event)
        current_timing_group = []

    return output_karaoke


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create karaoke .ass file from song audio and lyric text",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("song_path")
    parser.add_argument("lyrics_path")
    parser.add_argument("output_path")
    parser.add_argument("--language", help=f"language spoken in the audio, specify None to perform language detection.",
                        choices=sorted(whisper.tokenizer.LANGUAGES.keys()) + sorted(
                            [k.title() for k in whisper.tokenizer.TO_LANGUAGE_CODE.keys()]), default=None)
    parser.add_argument("--encoding", help="Text encoding of lyric text file", choices=["utf-8", "windows-1252"], default="utf-8")

    args = parser.parse_args()
    try:
        # AI analysis of song
        result_json_path = args.song_path + "_analysis.json"
        lyric_processed_path = args.lyrics_path + "_processed.txt"
        if Path(result_json_path).exists():
            print("AI analysis already done")
            with open(result_json_path, "r") as infile:
                song_analysis = json.load(infile)
        else:
            print("Using CUDA: " + str(torch.cuda.is_available()))
            devices = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
            audio = whisper.load_audio(args.song_path)
            model = whisper.load_model("large-v2", device=devices)
            song_analysis = whisper.transcribe(model, audio, language=args.language)

            with open(result_json_path, "w") as outfile:
                outfile.write(json.dumps(song_analysis, indent=2, ensure_ascii=True))

        # Process lyrics text file
        with open(args.lyrics_path, "r", encoding=args.encoding) as infile:
            og_lyrics = infile.read().splitlines()
        lyrics = preprocess_lyrics(og_lyrics)
        with open(lyric_processed_path, "w") as outfile:
            for current_line in lyrics:
                outfile.write(("%s\n" % current_line))

        # Process karaoke subtitles
        with open("sampleKaraokeMugen.ass", encoding="utf_8_sig") as f:
            base_karaoke = ass.parse(f)

        karaoke = process_karaoke(base_karaoke, lyrics, song_analysis)
        with open(args.song_path + ".ass", "w", encoding="utf_8_sig") as f:
            karaoke.dump_file(f)

    except Exception as e:
        print(str(e))
