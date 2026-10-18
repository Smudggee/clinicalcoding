from module1_ingestion.sliding_window import SlidingWindowChunker

text = "Patient has fever and cough. " * 600

chunker = SlidingWindowChunker(
    window_size=512,
    stride=256
)

document = chunker.chunk("DOC001", text)

print("Document ID:", document.document_id)
print("Number of windows:", len(document.windows))

for window in document.windows:
    print(
        "Window ID:", window.window_id,
        "| Start:", window.start_token_offset,
        "| End:", window.end_token_offset,
        "| Text length:", len(window.text)
    )