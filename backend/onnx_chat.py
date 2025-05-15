# File: backend/onnx_chat.py

import os
import numpy as np
import onnxruntime as ort
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Literal
from transformers import GPT2Tokenizer

# Define the ONNX GPT2 chat router
router = APIRouter()

tok = GPT2Tokenizer.from_pretrained("gpt2")
# Ensure EOS token is defined
eos_id = tok.eos_token_id if tok.eos_token_id is not None else tok.pad_token_id

class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    model: str

class ChatResponse(BaseModel):
    reply: str

# Lazy-loaded ONNX session and path
SESSION_PATH = os.path.join(os.path.dirname(__file__), "onnx_models", "gpt2.onnx")
onnx_session: ort.InferenceSession = None  # type: ignore

@router.post("/chat/onnx-gpt2", response_model=ChatResponse)
def chat_onnx_gpt2(req: ChatRequest):
    global onnx_session
    # Validate model param
    if req.model.lower() != "gpt2":
        raise HTTPException(400, "ONNX-GPT2 endpoint only supports model 'gpt2'.")

    # Lazy-load ONNX session
    if onnx_session is None:
        if not os.path.isfile(SESSION_PATH):
            raise HTTPException(500, f"ONNX model not found at {SESSION_PATH}. Export GPT2 to ONNX before use.")
        try:
            onnx_session = ort.InferenceSession(
                SESSION_PATH,
                providers=["CUDAExecutionProvider", "CPUExecutionProvider"]
            )
        except Exception as e:
            raise HTTPException(500, f"Failed to load ONNX session: {e}")

    # Build prompt text
    prompt = "".join(
        ("User: " if m.role=="user" else "Assistant: ") + m.content + "\n"
        for m in req.messages
    ) + "Assistant: "

    # Tokenize prompt
    inputs = tok(prompt, return_tensors="np")
    input_ids = inputs["input_ids"]  # shape (1, seq_len)
    attention_mask = inputs.get("attention_mask", np.ones_like(input_ids))

    # Generate up to max_new_tokens
    max_new_tokens = 20
    generated = input_ids.copy()

    for _ in range(max_new_tokens):
        onnx_inputs = {"input_ids": generated.astype(np.int64),
                       "attention_mask": attention_mask.astype(np.int64)}
        try:
            logits = onnx_session.run(None, onnx_inputs)[0]
        except Exception as e:
            raise HTTPException(500, f"ONNX runtime error: {e}")
        # Greedy next token
        next_id = int(np.argmax(logits[0, -1, :]))
        # Append and update masks
        generated = np.concatenate([generated, np.array([[next_id]], dtype=np.int64)], axis=1)
        attention_mask = np.concatenate([attention_mask, np.array([[1]], dtype=np.int64)], axis=1)
        if next_id == eos_id:
            break

    # Decode just the newly generated tokens
    new_tokens = generated[0, input_ids.shape[1]:].tolist()
    reply = tok.decode(new_tokens, skip_special_tokens=True)
    return ChatResponse(reply=reply)

# In backend/main.py, include this router:
# from backend.onnx_chat import router as onnx_gpt2_router
# app.include_router(onnx_gpt2_router)
