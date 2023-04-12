# Auto Karaoke

###CLI
```commandline
usage: autokaraoke [-h] [--encoding {utf-8,windows-1252}]
                   [--language {...}]
                   song_path lyrics_path

Create karaoke .ass file from song audio and lyric text

positional arguments:
  song_path             file path for song audio file
  lyrics_path           file path for lyric text file

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

###CUDA
If you have CUDA-enabled hardware, you can replace the torch packages with:
```commandline
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```
- Currently there is a `numpy` version conflict
  - Have to wait for following code changes in new release:
    - https://github.com/numba/numba/pull/8837
    - https://github.com/numba/numba/pull/8691
- Solve using `pip3 install numpy==1.23.5`


###TODO
- Romaji support for Japanese songs
- Support different karaoke styles
  - Choir
  - Down
  - Duo (Voice1, Voice2, Voice1+2)
