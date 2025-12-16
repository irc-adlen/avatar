import whisper

model = whisper.load_model("medium")
result = model.transcribe("adlenetmoiuwu.m4a")
print(result["text"])