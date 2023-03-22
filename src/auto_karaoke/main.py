import whisper_timestamped as whisper
import torch
import json
import ass
import argparse
from pathlib import Path
import re
# import stable_whisper

def preprocess_lyrics(input_lyrics):
    output_lyrics = []
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
                output_lyrics.extend(current_group)
            current_group = []
        else:
            is_line_repetition = re.search("[x×][0-9]*$", new_line)
            if is_line_repetition:
                repeat_count = int(new_line[-1])  # TODO: make more flexible for 2+ digit numbers
                new_line = new_line[:-2].strip()
                new_line = remove_end_punctuation(new_line)
                for _i in range(repeat_count):
                    output_lyrics.append(new_line)
                    current_group.append(new_line)
            else:
                current_group.append(new_line)
                output_lyrics.append(new_line)

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

def process_karaoke(input_karaoke, input_lyrics):
    output_karaoke = input_karaoke

    return output_karaoke


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("song_path")
    parser.add_argument("lyrics_path")
    parser.add_argument("language")
    parser.add_argument("output_path")

    args = parser.parse_args()
    try:
        # AI analysis of song
        result_json_path = args.song_path + "_analysis.json"
        lyric_processed_path = args.lyrics_path + "_processed.txt"
        if Path(result_json_path).exists():
            print("AI analysis already done")
            with open(result_json_path, "r") as infile:
                result = json.load(infile)
        else:
            print("Using CUDA: " + str(torch.cuda.is_available()))
            devices = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
            audio = whisper.load_audio(args.song_path)
            model = whisper.load_model("large-v2", device=devices)
            result = whisper.transcribe(model, audio, language=args.language)

            with open(result_json_path, "w") as outfile:
                outfile.write(json.dumps(result, indent=2, ensure_ascii=True))

        # Process lyrics text file
        with open(args.lyrics_path, "r", encoding="utf_8") as infile:
            og_lyrics = infile.read().splitlines()
        lyrics = preprocess_lyrics(og_lyrics)
        with open(lyric_processed_path, "w") as outfile:
            for current_line in lyrics:
                outfile.write(("%s\n" % current_line))

        # Process karaoke subtitles
        with open("sampleKaraokeMugen.ass", encoding="utf_8_sig") as f:
            base_karaoke = ass.parse(f)
        karaoke = process_karaoke(base_karaoke, lyrics)

    except Exception as e:
        print(str(e))
