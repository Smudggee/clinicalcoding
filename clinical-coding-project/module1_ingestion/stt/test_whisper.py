
from module1_ingestion.stt.whisper_service import WhisperTranscriptionService

audio_path = "data/audio/Malayalam_test.m4a"

service = WhisperTranscriptionService(model_size="large-v3", device="cpu")
print("Transcribing Malayalam audio... Please wait.")

result = service.transcribe(audio_path, language="ml")

print("\nDetected language:", result["language"])
print("Language confidence:", result["language_probability"])
print("\nTranscript:")
print(result["transcript"])
