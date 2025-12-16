# Quick start

Clone the whisper.cpp repo 
```
git clone https://github.com/ggml-org/whisper.cpp.git
```

Navigate to the repo 
```
cd whisper.cpp
```

Download one model
```
sh ./models/download-ggml-model.sh base
```

### Models that we can download

| Model  | Disk    | Mem     |
| ------ | ------- | ------- |
| tiny   | 75 MiB  | ~273 MB |
| base   | 142 MiB | ~388 MB |
| small  | 466 MiB | ~852 MB |
| medium | 1.5 GiB | ~2.1 GB |
| large  | 2.9 GiB | ~3.9 GB |

### Build for the real-time input

```
cmake -B build -DWHISPER_SDL2=ON
cmake --build build -j --config Release
```

We can run the code as followed

```
./build/bin/whisper-stream -m ./models/ggml-base.bin -l fr -t 8
```

#### Options
```
  -h,       --help          [default] show this help message and exit
  -t N,     --threads N     [8      ] number of threads to use during computation
            --step N        [500    ] audio step size in milliseconds
            --length N      [5000   ] audio length in milliseconds
            --keep N        [200    ] audio to keep from previous step in ms
  -c ID,    --capture ID    [-1     ] capture device ID
  -mt N,    --max-tokens N  [32     ] maximum number of tokens per audio chunk
  -ac N,    --audio-ctx N   [0      ] audio context size (0 - all)
  -bs N,    --beam-size N   [-1     ] beam size for beam search
  -vth N,   --vad-thold N   [0.60   ] voice activity detection threshold
  -fth N,   --freq-thold N  [100.00 ] high-pass frequency cutoff
  -tr,      --translate     [false  ] translate from source language to english
  -nf,      --no-fallback   [false  ] do not use temperature fallback while decoding
  -ps,      --print-special [false  ] print special tokens
  -kc,      --keep-context  [false  ] keep context between audio chunks
  -l LANG,  --language LANG [fr     ] spoken language
  -m FNAME, --model FNAME   [./models/ggml-base.bin] model path
  -f FNAME, --file FNAME    [       ] text output file name
  -tdrz,    --tinydiarize   [false  ] enable tinydiarize (requires a tdrz model)
  -sa,      --save-audio    [false  ] save the recorded audio to a file
  -ng,      --no-gpu        [false  ] disable GPU inference
  -fa,      --flash-attn    [true   ] enable flash attention during inference
  -nfa,     --no-flash-attn [false  ] disable flash attention during inference
```