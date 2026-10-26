# Malayalam Whisper Evaluation Report

## Objective

Compare the original Whisper transcription setup with an alternative Malayalam-focused model for the ACCS project's clinical-note ingestion prototype.

## Selected Model

- **Alternative model:** `sajilck/whisper-small-malayalam-v2`
- **Backend:** Hugging Face Transformers pipeline
- **Device used:** CPU
- **Evaluation size:** 5 Malayalam samples

## Results

| Metric | Original model | Alternative model |
|---|---:|---:|
| Word Error Rate (WER) | 42.42% | 21.21% |
| Character Error Rate (CER) | 8.30% | 4.91% |

The alternative model achieved lower WER and CER on the five evaluated samples. The observed relative reductions were 50.0% for WER and approximately 40.8% for CER.

## Integration Verification

The alternative model successfully transcribed a Malayalam sample and passed its transcription through the ingestion pipeline. The project test suite also passed 23 tests in the latest recorded run.

## Limitations

- The comparison uses only five samples and is preliminary.
- These results do not establish general Malayalam transcription accuracy or clinical readiness.
- The transcription pipeline's integration tests do not validate the full downstream clinical coding system.
- Real MIMIC dataset preparation and evaluation remain pending until authorized data is available.

## Evaluation Artifacts

The following files preserve the experimental results and analysis:

- `evaluation/alternative_model_comparison.csv`
- `evaluation/malayalam_evaluation.csv`
- `evaluation/normalized_metrics_comparison.csv`
- `evaluation/transcription_error_analysis.csv`
- `evaluation/whisper_config_comparison.csv`

## Conclusion

The alternative Malayalam Whisper model is the current prototype choice based on the small-sample comparison. Broader evaluation with an appropriately prepared dataset is required before drawing general performance conclusions.