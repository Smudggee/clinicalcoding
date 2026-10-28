"""
Unit tests for Module 2: Classifier, Dataset, Model Architecture, Losses, and Inference.
Compatible with standard unittest runner and pytest.
"""
import os
import unittest
import tempfile
import json
import torch
import pandas as pd
from transformers import AutoTokenizer

from module2_classifier.model import BioClinicalBERTClassifier
from module2_classifier.dataset import ClinicalDataset
from module2_classifier.losses import FocalLoss, class_weighted_bce
from module2_classifier.inference import ClinicalInferenceEngine
from module2_classifier.schemas import ClassifiedDocument, Prediction


class TestModule2Classifier(unittest.TestCase):
    def setUp(self):
        self.label_map = {
            "A41.9": 0,
            "J18.9": 1,
            "E11.9": 2,
            "I10": 3
        }
        self.tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
        self.temp_dir = tempfile.TemporaryDirectory()

        # Create dummy CSV
        self.csv_path = os.path.join(self.temp_dir.name, "test_notes.csv")
        df = pd.DataFrame([
            {
                "document_id": "doc_01",
                "text": "Patient with fever and hypotension diagnosed with sepsis.",
                "codes": "A41.9;I10"
            },
            {
                "document_id": "doc_02",
                "text": "Severe community-acquired pneumonia and type 2 diabetes.",
                "codes": "J18.9;E11.9"
            }
        ])
        df.to_csv(self.csv_path, index=False)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_dataset_multi_hot_encoding(self):
        dataset = ClinicalDataset(
            data_source=self.csv_path,
            tokenizer=self.tokenizer,
            label_map=self.label_map,
            max_length=64
        )
        self.assertEqual(len(dataset), 2)
        item = dataset[0]

        self.assertIn("input_ids", item)
        self.assertIn("attention_mask", item)
        self.assertIn("labels", item)
        self.assertEqual(item["labels"].shape, (len(self.label_map),))

        # Item 0 has A41.9 (0) and I10 (3)
        self.assertEqual(item["labels"][0].item(), 1.0)
        self.assertEqual(item["labels"][1].item(), 0.0)
        self.assertEqual(item["labels"][2].item(), 0.0)
        self.assertEqual(item["labels"][3].item(), 1.0)

    def test_model_forward_and_probabilities(self):
        num_labels = len(self.label_map)
        model = BioClinicalBERTClassifier(num_labels=num_labels, model_name="bert-base-uncased")

        batch_size = 2
        seq_len = 32
        input_ids = torch.randint(0, 1000, (batch_size, seq_len))
        attention_mask = torch.ones((batch_size, seq_len))

        logits = model(input_ids, attention_mask)
        self.assertEqual(logits.shape, (batch_size, num_labels))

        probs = model.predict_proba(input_ids, attention_mask)
        self.assertEqual(probs.shape, (batch_size, num_labels))
        self.assertTrue((probs >= 0.0).all() and (probs <= 1.0).all())

    def test_loss_functions(self):
        num_labels = len(self.label_map)
        logits = torch.randn(4, num_labels)
        targets = torch.randint(0, 2, (4, num_labels)).float()

        # BCE Loss
        bce = torch.nn.BCEWithLogitsLoss()
        loss_bce = bce(logits, targets)
        self.assertGreater(loss_bce.item(), 0.0)

        # Focal Loss
        focal = FocalLoss(gamma=2.0, alpha=0.25)
        loss_focal = focal(logits, targets)
        self.assertGreater(loss_focal.item(), 0.0)
        self.assertTrue(torch.isfinite(loss_focal))

    def test_checkpoint_save_and_load(self):
        num_labels = len(self.label_map)
        model = BioClinicalBERTClassifier(num_labels=num_labels, model_name="bert-base-uncased")

        checkpoint_file = os.path.join(self.temp_dir.name, "test_model.pt")
        model.save_checkpoint(checkpoint_file, label_map=self.label_map)

        loaded_model, loaded_map = BioClinicalBERTClassifier.load_checkpoint(checkpoint_file, device="cpu")
        self.assertEqual(loaded_model.num_labels, num_labels)
        self.assertEqual(loaded_map, self.label_map)

    def test_inference_pipeline_contract(self):
        num_labels = len(self.label_map)
        model = BioClinicalBERTClassifier(num_labels=num_labels, model_name="bert-base-uncased")
        checkpoint_file = os.path.join(self.temp_dir.name, "test_model.pt")
        model.save_checkpoint(checkpoint_file, label_map=self.label_map)

        engine = ClinicalInferenceEngine(
            checkpoint_path=checkpoint_file,
            tokenizer_name="bert-base-uncased"
        )

        sample_text = "The patient presented with fever and hypotension secondary to severe sepsis."
        result = engine.predict(text_or_windows=sample_text, document_id="doc_test_123", threshold=0.10)

        self.assertIsInstance(result, ClassifiedDocument)
        self.assertEqual(result.document_id, "doc_test_123")
        self.assertIsInstance(result.predictions, list)

        for p in result.predictions:
            self.assertIsInstance(p, Prediction)
            self.assertIn(p.code, self.label_map)
            self.assertTrue(0.0 <= p.probability <= 1.0)
            self.assertIsInstance(p.evidence_span, str)
            self.assertGreaterEqual(p.evidence_start_char, 0)


if __name__ == "__main__":
    unittest.main()
