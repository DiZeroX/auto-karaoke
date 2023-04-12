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
import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilename, asksaveasfilename
from functools import partial
import importlib.resources
import os
# import stable_whisper
# import textdistance


def wrapper():
    parser = argparse.ArgumentParser(
        description="Create karaoke .ass file from song audio and lyric text",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("song_path", help="file path for song audio file")
    parser.add_argument("lyrics_path", help="file path for lyric text file")
    # parser.add_argument("output_path", help="")
    parser.add_argument("--encoding", help="text encoding of lyric text file", choices=["utf-8", "windows-1252"],
                        default="utf-8")
    parser.add_argument("--language", help=f"language spoken in the audio, specify None to perform language detection",
                        choices=sorted(whisper.tokenizer.LANGUAGES.keys()) + sorted(
                            [k.title() for k in whisper.tokenizer.TO_LANGUAGE_CODE.keys()]), default=None)

    args = parser.parse_args()

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
            if line == "":
                continue
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
        word1 = word1.lower().translate(str.maketrans("", "", string.punctuation)).strip().strip("[-––]")
        word2 = word2.lower().translate(str.maketrans("", "", string.punctuation)).strip().strip("[-––]")
        return word1 == word2
        # else:
        #     similarity = textdistance.levenshtein.normalized_similarity(word1, word2)
        #     return similarity >= 0.625

    def process_karaoke(input_karaoke: ass.Document, input_lyrics, input_song_analysis):
        ai_word_timings = []
        ai_word_timings_undo_stack = []
        ai_word_timings_redo_stack = []
        for segment in input_song_analysis["segments"]:
            for word in segment["words"]:
                # convert seconds to centiseconds
                temp_word = copy.copy(word)
                temp_word["start"] = temp_word["start"] * 100
                temp_word["end"] = temp_word["end"] * 100
                ai_word_timings.append(temp_word)
        ai_word_timings = ai_word_timings[:-3]  # remove "Thanks for watching"

        window = tk.Tk()
        window.title('Karaoke Correction')
        window.geometry("1200x800")

        longest_line_word_count = 0
        lyric_lines_by_words = []
        dynamic_ai_word_texts = []
        temp_ai_word_timings_index = 0
        for lyric_line in input_lyrics:
            lyric_line_words = lyric_line.split(" ")
            lyric_lines_by_words.append(lyric_line_words)
            lyric_line_length = len(lyric_line_words)
            if lyric_line_length > longest_line_word_count:
                longest_line_word_count = lyric_line_length
            for lyric_line_word in lyric_line_words:
                # dynamic_ai_word_texts.append(tk.StringVar(window, ai_word_timings[temp_ai_word_timings_index]["text"]))
                dynamic_ai_word_texts.append(tk.StringVar())
                temp_ai_word_timings_index += 1
        lyric_word_count = 0
        for lyric_line in lyric_lines_by_words:
            for lyric_word in lyric_line:
                lyric_word_count += 1

        # Create A Main frame
        main_frame = tk.Frame(window)
        main_frame.pack(fill=tk.BOTH, expand=1)

        # Create Frame for X Scrollbar
        sec = tk.Frame(main_frame)
        sec.pack(fill=tk.X, side=tk.BOTTOM)

        # Create A Canvas
        my_canvas = tk.Canvas(main_frame)
        my_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

        # Add A Scrollbars to Canvas
        x_scrollbar = ttk.Scrollbar(sec, orient=tk.HORIZONTAL, command=my_canvas.xview)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        y_scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=my_canvas.yview)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Configure the canvas
        my_canvas.configure(xscrollcommand=x_scrollbar.set)
        my_canvas.configure(yscrollcommand=y_scrollbar.set)
        my_canvas.bind("<Configure>", lambda e: my_canvas.config(scrollregion=my_canvas.bbox(tk.ALL)))

        # Create Another Frame INSIDE the Canvas
        second_frame = tk.Frame(my_canvas)

        # Add that New Frame a Window In The Canvas
        my_canvas.create_window((0, 0), window=second_frame, anchor="nw")

        # edit_label = tk.Label(master=second_frame, text="Enter edited value here:")
        # edit_label.grid(row=0, column=longest_line_word_count + 1)
        # edit_entry = tk.Entry(master=second_frame)
        # edit_entry.grid(row=1, column=longest_line_word_count + 1)

        def finalize_karaoke():
            if len(ai_word_timings) != lyric_word_count:
                return False

            output_karaoke = copy.deepcopy(input_karaoke)
            del output_karaoke.events[-1]

            temp_ai_word_index = 0
            # previous_end_timing = ai_word_timings[0]['start']
            for temp_lyric_line in lyric_lines_by_words:
                subtitle_text = ""
                subtitle_start_timing = None
                subtitle_end_timing = None
                for lyric_word_index, temp_lyric_word in enumerate(temp_lyric_line):
                    ai_word = ai_word_timings[temp_ai_word_index]
                    word_duration = int(round(ai_word['end'] - ai_word['start']))
                    # if previous_end_timing < ai_word['start']:
                    #     word_duration += int(round(ai_word['start'] - previous_end_timing))
                    subtitle_text += f"{{\\k{word_duration}}}{temp_lyric_word} "
                    previous_end_timing = ai_word['end']
                    if lyric_word_index == 0:
                        subtitle_start_timing = ai_word['start']
                    if lyric_word_index == len(temp_lyric_line) - 1:
                        subtitle_end_timing = ai_word['end']
                    temp_ai_word_index += 1
                subtitle_text = subtitle_text.strip()
                subtitle_style = "Sample KM [Up]"
                # .ass /k centiseconds (100 centiseconds = 1 second) and is duration based
                # whisper-timestamped is in seconds and is absolute based
                subtitle_start = datetime.timedelta(seconds=subtitle_start_timing / 100)
                subtitle_end = datetime.timedelta(seconds=subtitle_end_timing / 100)
                dialogue_event = ass.Dialogue(layer=0, start=subtitle_start, end=subtitle_end, style=subtitle_style,
                                              name='',
                                              margin_l=0, margin_r=0, margin_v=0, effect='', text=subtitle_text)
                output_karaoke.events.append(dialogue_event)
            with open(os.path.splitext(args.song_path)[0] + ".ass", "w", encoding="utf_8_sig") as file:
                output_karaoke.dump_file(file)
            return True

        def update_dynamic_texts():
            for dynamic_ai_word_index, dynamic_ai_word in enumerate(dynamic_ai_word_texts):
                if dynamic_ai_word_index < len(ai_word_timings):
                    dynamic_ai_word.set(ai_word_timings[dynamic_ai_word_index]["text"])
                else:
                    dynamic_ai_word.set("")
            ai_counter = 0
            for lyric_line_by_word in lyric_lines_by_words:
                for temp_lyric_word in lyric_line_by_word:
                    if is_same_word(temp_lyric_word, dynamic_ai_word_texts[ai_counter].get()):
                        word_frames[ai_counter].configure(bg="green")
                    else:
                        word_frames[ai_counter].configure(bg="red")
                    ai_counter += 1

        def save(event=None):
            filepath = asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON Files", "*.json")]
            )
            if not filepath:
                return
            with open(filepath, mode="w", encoding="utf-8") as output_file:
                json_str = json.dumps(ai_word_timings, indent=4)
                output_file.write(json_str)

        def load(event=None):
            filepath = askopenfilename(filetypes=[("JSON Files", "*.json")])
            if not filepath:
                return
            with open(filepath, mode="r", encoding="utf-8") as input_file:
                nonlocal ai_word_timings
                ai_word_timings_json = json.load(input_file)
                ai_word_timings = ai_word_timings_json.copy()
                update_dynamic_texts()

        save_button = tk.Button(
            master=second_frame,
            text="Save",
            command=partial(save)
        )
        save_button.grid(row=0, column=longest_line_word_count + 1)
        load_button = tk.Button(
            master=second_frame,
            text="Load",
            command=partial(load)
        )
        load_button.grid(row=1, column=longest_line_word_count + 1)
        finalize_button = tk.Button(
            master=second_frame,
            text="Output subtitle file (only when all cells are green)",
            command=finalize_karaoke
        )
        finalize_button.grid(row=2, column=longest_line_word_count + 1)

        # render words
        ai_word_index = 0
        word_frames = []

        def add_to_changelog():
            ai_word_timings_redo_stack.clear()
            ai_word_timings_undo_stack.append(ai_word_timings.copy())

        def undo(event=None):
            nonlocal ai_word_timings
            if len(ai_word_timings_undo_stack) > 0:
                ai_word_timings_redo_stack.append(ai_word_timings.copy())
                ai_word_timings = ai_word_timings_undo_stack.pop()
                update_dynamic_texts()

        def redo(event=None):
            nonlocal ai_word_timings
            if len(ai_word_timings_redo_stack) > 0:
                ai_word_timings_undo_stack.append(ai_word_timings.copy())
                ai_word_timings = ai_word_timings_redo_stack.pop()
                update_dynamic_texts()

        window.bind('<Control-z>', undo)
        window.bind('<Control-y>', redo)
        window.bind('<Control-s>', save)
        window.bind('<Control-o>', load)

        for row_index in range(len(input_lyrics)):
            for col_index in range(longest_line_word_count):
                frame = tk.Frame(
                    master=second_frame,
                    relief=tk.RAISED,
                    borderwidth=1
                )
                frame.grid(row=row_index, column=col_index, sticky="nsew")
                if col_index < len(lyric_lines_by_words[row_index]):
                    lyric_word_text = lyric_lines_by_words[row_index][col_index]
                    lyric_word_label = tk.Label(
                        master=frame,
                        text=lyric_word_text
                    )
                    # ai_word_text = ai_word_timings[ai_word_index]["text"]
                    ai_word_text = dynamic_ai_word_texts[ai_word_index]
                    ai_word_label = tk.Label(
                        master=frame
                    )
                    ai_word_text.set(ai_word_timings[ai_word_index]["text"])
                    ai_word_label["textvariable"] = ai_word_text
                    if is_same_word(lyric_word_text, ai_word_text.get()):
                        frame.configure(bg="green")
                    else:
                        frame.configure(bg="red")
                    word_frames.append(frame)

                    def add_ai_word(index):
                        add_to_changelog()
                        # edit_entry_text = edit_entry.get()
                        # 'text': edit_entry_text if len(edit_entry_text) > 0 else "",
                        blank_ai_word = {
                            'text': "",
                            'start': ai_word_timings[index - 1]["end"] if index > 0 else 0.0,
                            'end': ai_word_timings[index]["start"]
                        }
                        ai_word_timings.insert(index, blank_ai_word)
                        update_dynamic_texts()

                    def match_lyric_word(index, lyric):
                        add_to_changelog()
                        ai_word_timings[index]["text"] = lyric
                        update_dynamic_texts()

                    # def edit_ai_word(index):
                    #     add_to_changelog()
                    #     ai_word_timings[index]["text"] = edit_entry.get()
                    #     update_dynamic_texts()

                    def delete_ai_word(index):
                        add_to_changelog()
                        del ai_word_timings[index]
                        update_dynamic_texts()

                    def merge_ai_word_with_right(index):
                        add_to_changelog()
                        if index >= len(ai_word_timings) - 1:
                            print("merge_ai_word_with_right(): can't merge last word")
                        merged_word = {
                            'text': ai_word_timings[index]['text'] + ai_word_timings[index + 1]['text'],
                            'start': ai_word_timings[index]['start'],
                            'end': ai_word_timings[index + 1]['end']
                        }
                        ai_word_timings[index] = merged_word
                        del ai_word_timings[index + 1]
                        update_dynamic_texts()

                    def split_ai_word(index):
                        add_to_changelog()
                        whole_word = ai_word_timings[index]['text']
                        halfway_index = int(len(whole_word) / 2)
                        split_word1 = whole_word[:halfway_index]
                        split_word2 = whole_word[halfway_index:]
                        start = ai_word_timings[index]['start']
                        end = ai_word_timings[index]['end']
                        halfway_time = start + ((end - start) / 2)

                        new_word1 = {
                            'text': split_word1,
                            'start': start,
                            'end': halfway_time
                        }
                        new_word2 = {
                            'text': split_word2,
                            'start': halfway_time,
                            'end': end
                        }
                        ai_word_timings[index] = new_word1
                        ai_word_timings.insert(index + 1, new_word2)
                        update_dynamic_texts()

                    popup_menu = tk.Menu(frame, tearoff=0)
                    popup_menu.add_command(
                        label="Add word",
                        command=partial(add_ai_word, ai_word_index)
                    )
                    popup_menu.add_command(
                        label="Match word with lyric",
                        command=partial(match_lyric_word, ai_word_index, lyric_word_text)
                    )
                    # popup_menu.add_command(
                    #     label="Edit word",
                    #     command=partial(edit_ai_word, ai_word_index)
                    # )
                    popup_menu.add_command(
                        label="Delete word",
                        command=partial(delete_ai_word, ai_word_index)
                    )
                    popup_menu.add_command(
                        label="Merge word with right",
                        command=partial(merge_ai_word_with_right, ai_word_index)
                    )
                    popup_menu.add_command(
                        label="Split word",
                        command=partial(split_ai_word, ai_word_index)
                    )
                    popup_menu.add_separator()
                    popup_menu.add_command(
                        label="Undo",
                        command=undo
                    )
                    popup_menu.add_command(
                        label="Redo",
                        command=redo
                    )

                    def do_popup(event=None, temp_popup_menu=None):
                        try:
                            temp_popup_menu.tk_popup(event.x_root, event.y_root)
                        finally:
                            temp_popup_menu.grab_release()

                    def make_lambda(pop):
                        return lambda ev: do_popup(ev, pop)

                    ai_word_label.bind("<Button-3>", make_lambda(popup_menu))

                    lyric_word_label.pack()
                    ai_word_label.pack()
                    ai_word_index += 1
        # TODO: add ai word overflow line
        overflow_ai_words = ai_word_timings[ai_word_index:]
        overflow_label_text = "OVERFLOW: "
        for overflow_index in range(len(overflow_ai_words)):
            overflow_label_text += overflow_ai_words[overflow_index]["text"] + " "
        overflow_label = tk.Label(master=window, text=overflow_label_text)
        overflow_label.pack()

        window.mainloop()

    try:
        # AI analysis of song
        result_json_path = os.path.splitext(args.song_path)[0] + "_transcription.json"
        lyric_processed_path = os.path.splitext(args.lyrics_path)[0] + "_processed.txt"
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
        # package_files = importlib.resources.files("auto_karaoke") # maybe later 3.9 version
        with importlib.resources.path("auto_karaoke", "sampleKaraokeMugen.ass") as sample_karaoke_path:
            with open(sample_karaoke_path, encoding="utf_8_sig") as f:
                base_karaoke = ass.parse(f)

        process_karaoke(base_karaoke, lyrics, song_analysis)

    except Exception as e:
        print(str(e))


if __name__ == "__main__":
    wrapper()
