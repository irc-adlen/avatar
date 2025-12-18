import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

def transcribe_audio(path_to_audio_file):
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    print("Using device:", device)
    dtype = torch.float16 if torch.cuda.is_available() else torch.float32
    print("Using dtype:", dtype)
    model_id = "openai/whisper-large-v3"

    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        model_id, dtype=dtype, low_cpu_mem_usage=True, use_safetensors=True
    )
    model.to(device)
    print("model set")
    processor = AutoProcessor.from_pretrained(model_id)
    print("processor set")
    pipe = pipeline(
        "automatic-speech-recognition",
        model=model,
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
        dtype=dtype,
        device=device,
    )
    print("searching for results")
    result = pipe(path_to_audio_file)
    print("transcription complete")
    print(result["text"])
