sudo apt install git cmake build-essential ffmpeg

git clone https://github.com/ggerganov/whisper.cpp
cd whisper.cpp
make

bash ./models/download-ggml-model.sh small