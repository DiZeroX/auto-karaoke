import datetime
import ass
import textdistance
import string
import copy


def is_same_word(word1: str, word2: str):
    # lowercase and remove punctuation and whitespace
    word1 = word1.lower().translate(str.maketrans("", "", string.punctuation)).strip()
    word2 = word2.lower().translate(str.maketrans("", "", string.punctuation)).strip()
    if word1 == word2:
        return True
    else:
        similarity = textdistance.levenshtein.normalized_similarity(word1, word2)
        return similarity >= 0.625


def process_invalid_timings(invalid_word_timings, current_timing_group, invalid_ai_words, matched_word_start):
    if len(invalid_word_timings) > 0:
        # there is 1-1 match for each invalid ai word with lyric word
        if len(invalid_word_timings) == len(invalid_ai_words):
            for invalid_timing in invalid_word_timings:
                current_timing_group.append({
                    "text": invalid_timing["text"],
                    "start": invalid_timing["start"],
                    "end": invalid_timing["end"],
                })
        else:  # combine words into single subtitle karaoke timing
            invalid_timing_start = invalid_word_timings[0]["start"]
            if invalid_word_timings[-1]["end"] < matched_word_start:
                invalid_timing_end = invalid_word_timings[-1]["end"]
            else:
                invalid_timing_end = invalid_word_timings[0]["start"]
            full_text = ""
            for invalid_timing in invalid_word_timings:
                full_text += invalid_timing["text"] + " "
            current_timing_group.append({
                "text": full_text.strip(),
                "start": invalid_timing_start,
                "end": invalid_timing_end,
            })
        invalid_word_timings.clear()
    invalid_ai_words.clear()


def process_karaoke(input_karaoke: ass.Document, input_lyrics, input_song_analysis):
    output_karaoke = copy.deepcopy(input_karaoke)
    del output_karaoke.events[-1]
    ai_word_timings = []

    for segment in input_song_analysis["segments"]:
        for word in segment["words"]:
            # convert seconds to centiseconds
            temp_word = copy.copy(word)
            temp_word["start"] = temp_word["start"] * 100
            temp_word["end"] = temp_word["end"] * 100
            ai_word_timings.append(temp_word)

    ai_word_timing_index = 0
    current_timing_group = []
    invalid_word_timings = []
    # ai_word = None
    for lyric_line_index, lyric_line in enumerate(input_lyrics):
        # TODO process all words in line as invalid timing if no more ai words left
        if ai_word_timing_index >= len(ai_word_timings):
            print("ai_word_timing_index overflow")
            break
        lyric_line_words = lyric_line.split(" ")
        ai_word_buffer = len(lyric_line_words) + 3
        ai_word_timings_range = ai_word_timings[ai_word_timing_index:ai_word_timing_index + ai_word_buffer]
        ai_word_timings_range_index = 0
        ai_word_count_since_last_match = 0
        for line_word_index, line_word in enumerate(lyric_line_words):
            match_found = False
            # TODO process remaining words in line as invalid timing if no more ai words left
            if ai_word_timings_range_index >= len(ai_word_timings_range):
                print("ai_word_timings_range_index overflow")
                print(line_word)
                print(lyric_line)
                print(ai_word_timings_range)
                break
            invalid_ai_words = []
            current_ai_word_timings_range = ai_word_timings_range[ai_word_timings_range_index:]
            for current_ai_word_timing_index, current_ai_word_timing in enumerate(current_ai_word_timings_range):
                # if current_ai_word_timing_index > 4:  # buffer is still too lenient
                #     break
                ai_word = current_ai_word_timing["text"]
                if is_same_word(line_word, ai_word):
                    match_found = True
                    # If match found, insert invalid words timings that preceded it
                    process_invalid_timings(invalid_word_timings, current_timing_group, invalid_ai_words, current_ai_word_timing["start"])

                    current_timing_group.append({
                        "text": line_word,
                        "start": current_ai_word_timing["start"],
                        "end": current_ai_word_timing["end"],
                    })
                    ai_word_timings_range_index += current_ai_word_timing_index + 1
                    break
                else:
                    invalid_ai_words.append(current_ai_word_timing["text"])
            if not match_found:  # no word match found
                if ai_word_timings_range_index < len(ai_word_timings_range) - 1:
                    ai_word_timings_range_index += 1
                invalid_word = {
                    "text": line_word,
                    "start": ai_word_timings_range[ai_word_timings_range_index]["start"],
                    "end": ai_word_timings_range[ai_word_timings_range_index]["end"],
                    "aitext": ai_word_timings_range[ai_word_timings_range_index]["text"],
                }
                invalid_word_timings.append(invalid_word)
                # ai_word_timing_index += 1
                # If that last word in line is not found, then insert invalid timings
                if line_word_index == len(lyric_line_words) - 1:
                    process_invalid_timings(invalid_word_timings, current_timing_group, invalid_ai_words, 99999999)
                # If AI word is not in rest of current lyric line or the next lyric line, increment index to next AI
                # word TODO: cleanup this nightmare
                # if ai_word_timing_index < len(ai_word_timings) - 1:
                #     temp_lyric_words = []
                #     line_words_index_start = line_word_index + 1 if line_word_index < len(lyric_line_words) - 1 else len(lyric_line_words) - 1
                #     line_words_index_stop = len(lyric_line_words)
                #     for temp_line_word_index in range(line_words_index_start, line_words_index_stop):
                #         temp_lyric_words.append(lyric_line_words[temp_line_word_index])
                #     if lyric_line_index < len(input_lyrics) - 1:
                #         temp_lyric_line = input_lyrics[lyric_line_index+1]
                #         temp_lyric_line_words = temp_lyric_line.split(" ")
                #         for temp_lyric_line_word in temp_lyric_line_words:
                #             temp_lyric_words.append(temp_lyric_line_word)
                #     found_future_lyric_match = False
                #     for temp_lyric_word in temp_lyric_words:
                #         if is_same_word(temp_lyric_word, ai_word):
                #             found_future_lyric_match = True
                #             break
                #     if not found_future_lyric_match:
                #         ai_word_timing_index += 1

        subtitle_text = ""
        previous_end_timing = current_timing_group[0]['start']
        for current_timing_word in current_timing_group:
            word_duration = int(round(current_timing_word['end'] - current_timing_word['start']))
            if previous_end_timing < current_timing_word['start']:
                word_duration += int(round(current_timing_word['start'] - previous_end_timing))
            subtitle_text += f"{{\\k{word_duration}}}{current_timing_word['text']} "
            previous_end_timing = current_timing_word['end']
        subtitle_text = subtitle_text.strip()
        subtitle_style = "Sample KM [Up]"
        # .ass /k centiseconds (100 centiseconds = 1 second) and is duration based
        # whisper-timestamped is in seconds and is absolute based
        subtitle_start = datetime.timedelta(seconds=current_timing_group[0]["start"] / 100)
        subtitle_end = datetime.timedelta(seconds=current_timing_group[-1]["end"] / 100)
        dialogue_event = ass.Dialogue(layer=0, start=subtitle_start, end=subtitle_end, style=subtitle_style, name='', margin_l=0, margin_r=0, margin_v=0, effect='', text=subtitle_text)
        output_karaoke.events.append(dialogue_event)
        current_timing_group = []
        ai_word_timing_index += ai_word_timings_range_index

    return output_karaoke