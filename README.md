# Auto Karaoke
Approximate word-based subtitle timing for karaokes. Further subtitle editing is necessary for usable karaokes. This is meant as a time-saving tool.

PyPi: https://pypi.org/project/auto-karaoke/

## REQUIRED: DO FIRST

Run `pip3 install git+https://github.com/linto-ai/whisper-timestamped` **BEFORE** installing `auto_karaoke`

`whisper-timestamped` does not have a PiPy package, so it is unable to be referenced it in `pyproject.toml`.

Installing `whisper-timestamped` after `auto_karaoke` may cause permission issues with your venv.

Additional installation docs here: https://github.com/linto-ai/whisper-timestamped#installation

## Installation
Run `pip install auto-karaoke`

### CLI
```commandline
usage: autokaraoke [-h] [--encoding {utf-8,windows-1252}]
                   [--language {...}]
                   song_path lyrics_path model_size

Create karaoke .ass file from song audio and lyric text

positional arguments:
  song_path             file path for song audio file
  lyrics_path           file path for lyric text file
  model_size {tiny,small,medium,large,large-v2}
                        model size for whisper (default: medium)

optional arguments:
  -h, --help            show this help message and exit
  --encoding {utf-8,windows-1252}
                        text encoding of lyric text file (default: utf-8)
  --language {af,am,ar,as,az,ba,be,bg,bn,bo,br,bs,ca,cs,cy,da,de,el,en,es,et,eu,fa,fi,fo,fr,gl,gu,ha,haw,he,hi,hr,ht,hu,hy,id,is,it,ja,jw,ka,kk,km,kn,ko,la,lb,ln,lo,lt,
lv,mg,mi,mk,ml,mn,mr,ms,mt,my,ne,nl,nn,no,oc,pa,pl,ps,pt,ro,ru,sa,sd,si,sk,sl,sn,so,sq,sr,su,sv,sw,ta,te,tg,th,tk,tl,tr,tt,uk,ur,uz,vi,yi,yo,zh,Afrikaans,Albanian,Amhar
ic,Arabic,Armenian,Assamese,Azerbaijani,Bashkir,Basque,Belarusian,Bengali,Bosnian,Breton,Bulgarian,Burmese,Castilian,Catalan,Chinese,Croatian,Czech,Danish,Dutch,English
,Estonian,Faroese,Finnish,Flemish,French,Galician,Georgian,German,Greek,Gujarati,Haitian,Haitian Creole,Hausa,Hawaiian,Hebrew,Hindi,Hungarian,Icelandic,Indonesian,Itali
an,Japanese,Javanese,Kannada,Kazakh,Khmer,Korean,Lao,Latin,Latvian,Letzeburgesch,Lingala,Lithuanian,Luxembourgish,Macedonian,Malagasy,Malay,Malayalam,Maltese,Maori,Mara
thi,Moldavian,Moldovan,Mongolian,Myanmar,Nepali,Norwegian,Nynorsk,Occitan,Panjabi,Pashto,Persian,Polish,Portuguese,Punjabi,Pushto,Romanian,Russian,Sanskrit,Serbian,Shon
a,Sindhi,Sinhala,Sinhalese,Slovak,Slovenian,Somali,Spanish,Sundanese,Swahili,Swedish,Tagalog,Tajik,Tamil,Tatar,Telugu,Thai,Tibetan,Turkish,Turkmen,Ukrainian,Urdu,Uzbek,
Valencian,Vietnamese,Welsh,Yiddish,Yoruba}
                        language spoken in the audio, omit to perform language detection (default: None)
```

### GUI - opened when running CLI tool
The transcription from `openai/whisper` will contain inaccuracies.
- 1-to-1 word inaccuracies are fine because the timing is the same regardless
  - ex: `searing` vs `cheering`
- missing or extra words are problematic because the timings don't matchup 
  - LYRIC: `I've infiltrated` vs TRANSCRIPTION: `Infiltrated`
  - LYRIC: `Insurmountable` vs TRANSCRIPTION: `I see my table`

There is a GUI to fix these mistakes before the subtitle file is created. The goal is to have the number of words in the lyrics be the same as the number of transcribed words so that the word timings match up 1-to-1.

The GUI shows the lyrics given by the CLI argument in a grid:
- Each lyric line is a row
- Each word in that lyric line is a column
- Each cell in a row x column holds 2 words stacked on top of each other:
  - the top word is the lyric word
  - the bottom word is the transcribed word from `openai/whisper`
  - the cell is highlighted **green** if the two words match and **red** if the words don't match
- Overflow line
  - if there are extra words left in the transcription after matching 1-1 lyric words with transcribed words, they are shown in the bottom of the GUI
  - this is only for reference

The GUI provides multiple ways to edit the bottom/transcribed word of a cell. By right-clicking a transcribed word, a menu opens up with various options:
- Add word
  - inserts a blank word
  - words after new word are moved to the right
- Match word with lyric
  - replaces text content of word with the lyric word above it
  - **NOTE:** this is not necessary to do as long as the number of lyric words match transcribed words, the lyric word and transcribed word don't have to match in text content. This is mainly to change the color of the cell to green for the user's preference
- Delete word
  - Deletes word
  - words after deleted word are moved to the left
- Merge word with right
  - merges the text content and the timing with the word on the right
  - words after merged word are moved to the left
- Split word
  - splits the word in half
  - timing is only approximate because it is literally halving the duration
  - words right of split word are moved to the right
- Undo | *shortcut: ctrl-z*
- Redo | *shortcut: ctrl-y*

Most of the time, you can hear in the song how these inaccuracies were made. It can be helpful to listen to sections of the song again while using the GUI.

### CUDA
If you have CUDA-enabled hardware, you can replace the torch packages with:
```commandline
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118 --force-reinstall
```
- Currently there is a `numpy` version conflict with `numba`
  - Have to wait for following code changes in new release:
    - https://github.com/numba/numba/pull/8837
    - https://github.com/numba/numba/pull/8691
  - Solve using `pip3 install numpy==1.23.5`


### TODO
- Add pictures to README
- Update overflow line when edits are made
- Support different karaoke styles
  - Choir
  - Down
  - Duo (Voice1, Voice2, Voice1+2)
