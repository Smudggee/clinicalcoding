import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


from module1_ingestion.stt.whisper_service import WhisperTranscriptionService
from module1_ingestion.preprocessing import normalize
from module1_ingestion.sliding_window import SlidingWindowChunker


def main():
    audio_path = Path("data/audio/sample_01.m4a")

    model_path = (
        Path(__file__).resolve().parents[2]
        / "models"
        / "malayalam-whisper"
    )

    # Step 1: Transcribe audio
    service = WhisperTranscriptionService(
         backend="alternative",
        device="cpu",
    )
    result = service.transcribe(audio_path, language="ml")
    transcript = result["transcript"]

    print("Transcribed Malayalam text:")
    print(transcript)

    # Step 2: Normalize text
    text = normalize(transcript)
    print("\nNormalized text:")
    print(text)

    # Step 3: Inspect the chunker
    chunker = SlidingWindowChunker()

    print(
        "\nTokenizer:",
        type(chunker.tokenizer).__name__
        if chunker.tokenizer is not None
        else "Whitespace fallback",
    )
    print("Input text:", repr(text))
    print("Input length:", len(text))

    # Step 4: Chunk the text
    ingested = chunker.chunk(
        document_id="audio-sample-001",
        text=text,
    )

    print("Number of windows:", len(ingested.windows))

    for window in ingested.windows:
        print("Window text:", repr(window.text))
        print(
            "Token offsets:",
            window.start_token_offset,
            window.end_token_offset,
        )


if __name__ == "__main__":
    main()
