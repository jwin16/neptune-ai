# File: backend/export_to_onnx.py
import os
import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer

MODEL_ID = "gpt2"
EXPORT_DIR = os.path.join(os.path.dirname(__file__), "onnx_models")
EXPORT_PATH = os.path.join(EXPORT_DIR, "gpt2.onnx")

if __name__ == "__main__":
    # Ensure export directory exists
    os.makedirs(EXPORT_DIR, exist_ok=True)

    # Load model & tokenizer
    print(f"Loading model and tokenizer for {MODEL_ID}...")
    tokenizer = GPT2Tokenizer.from_pretrained(MODEL_ID)
    model = GPT2LMHeadModel.from_pretrained(MODEL_ID)
    model.eval()

    # Wrapper for ONNX export: only inputs and logits
    class GPT2ExportWrapper(torch.nn.Module):
        def __init__(self, model):
            super().__init__()
            self.model = model
        def forward(self, input_ids, attention_mask):
            outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
            return outputs.logits

    export_model = GPT2ExportWrapper(model)
    export_model.eval()

    # Prepare dummy inputs
    dummy = tokenizer("Hello, world!", return_tensors="pt")
    input_ids = dummy["input_ids"]
    attention_mask = dummy.get("attention_mask", torch.ones_like(input_ids))

    # Export to ONNX
    print(f"Exporting wrapped GPT2 model to ONNX at {EXPORT_PATH}...")
    torch.onnx.export(
        export_model,
        (input_ids, attention_mask),
        EXPORT_PATH,
        opset_version=14,
        input_names=["input_ids", "attention_mask"],
        output_names=["logits"],
        dynamic_axes={
            "input_ids": {0: "batch_size", 1: "sequence"},
            "attention_mask": {0: "batch_size", 1: "sequence"},
            "logits": {0: "batch_size", 1: "sequence"},
        },
    )
    print("Successfully exported GPT2 model to ONNX.")