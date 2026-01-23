import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
import time
import os

# Audio configuration
SAMPLE_RATE = 48000
CHANNELS = 1
INPUT_DEVICE = 13
BLOCK_DURATION = 0.1  # seconds
SILENCE_THRESHOLD = 0.015  # volume threshold
MAX_SILENCE_DURATION = 1.5  # seconds before stopping

has_talk = False

audio_buffer = []
silence_time = 0.0

hasStopped = False


def start_recording():
    global hasStopped
    global audio_buffer
    global silence_time
    global has_talk

    hasStopped = False
    audio_buffer = []
    silence_time = 0.0
    has_talk = False

    print(sd.query_devices())
    print("Default input device:", sd.default.device)

    print("Recording... Speak now")

    try:
        with sd.InputStream(
            device=INPUT_DEVICE,
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            callback=audio_callback,
            blocksize=int(SAMPLE_RATE * BLOCK_DURATION),
            dtype="float32"
        ):
            while not hasStopped:
                time.sleep(0.1)

    except sd.CallbackStop:
        print("Silence detected, stopping recording")


    print("Recording stopped due to silence")

    # Concatenate all recorded blocks
    audio = np.concatenate(audio_buffer, axis=0)

    # Save to WAV file
    write("records/recording.wav", SAMPLE_RATE, audio)

    print("Audio saved as recording.wav")

    return "records/recording.wav"

def try_audio_device():
    try:
        with sd.InputStream(
            device=INPUT_DEVICE,
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            callback=audio_callback,
            blocksize=int(SAMPLE_RATE * BLOCK_DURATION),
            dtype="float32"
        ):
            time.sleep(0.1)
            print("Audio device is working correctly.")

    except sd.CallbackStop:
        print("Silence detected, stopping recording")

def audio_callback(indata, frames, time_info, status):
    global silence_time
    global hasStopped
    global has_talk
    # Convert audio block to numpy array
    audio_data = indata.copy()
    audio_buffer.append(audio_data)

    # Compute RMS (volume)
    rms = np.sqrt(np.mean(audio_data ** 2))

    if rms < SILENCE_THRESHOLD:
        print(f"Silence detected (RMS: {rms:.5f})")
        if has_talk:
            silence_time += BLOCK_DURATION
            
    else:
        has_talk = True
        print(f"Sound detected (RMS: {rms:.5f})")
        silence_time = 0.0

    # Stop recording if silence is long enough
    if silence_time >= MAX_SILENCE_DURATION:
        print("Maximum silence duration reached, stopping recording")
        hasStopped = True
        print(hasStopped)
        raise sd.CallbackStop()


