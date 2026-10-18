
from module1_ingestion.training_examples import make_training_examples


def main():
    records = [
        {
            "document_id": "DOC001",
            "text": "Synthetic clinical note about condition A. " * 600,
            "codes": ["SYNTH_A"],
        },
        {
            "document_id": "DOC002",
            "text": "Synthetic clinical note about condition B. " * 600,
            "codes": ["SYNTH_B"],
        },
    ]

    examples = make_training_examples(records)

    print("Input documents:", len(records))
    print("Output window examples:", len(examples))

    for example in examples:
        assert example["text"].strip()
        assert example["codes"]
        print(
            "Window example — text length:",
            len(example["text"]),
            "| codes:",
            example["codes"],
        )

    assert len(examples) > len(records), (
        "Expected long documents to produce multiple windows."
    )

    print("PASS: Long documents produce valid training examples.")


if __name__ == "__main__":
    main()
