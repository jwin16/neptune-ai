# File: backend/gpt2_chat.py

import torch
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Literal
from transformers import AutoTokenizer, AutoModelForCausalLM

router = APIRouter()

# Load the GPT-2 tokenizer & model (FP16 on GPU if available)
tokenizer = AutoTokenizer.from_pretrained("gpt2")
model = AutoModelForCausalLM.from_pretrained(
    "gpt2",
    torch_dtype=torch.float16,
    device_map="auto",
)
model.eval()

class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    model: str

class ChatResponse(BaseModel):
    reply: str

@router.post("/chat/native-gpt2", response_model=ChatResponse)
async def chat_native_gpt2(req: ChatRequest):
    if req.model.lower() != "gpt2":
        raise HTTPException(400, "This endpoint only supports model='gpt2'.")

    # Build the prompt
    prompt = "".join(
        ("User: " if m.role == "user" else "Assistant: ") + m.content + "\n"
        for m in req.messages
    ) + "Assistant: "

    # Tokenize & generate (greedy, up to 20 tokens)
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(
        **inputs,
        max_new_tokens=20,
        do_sample=False,
        pad_token_id=tokenizer.eos_token_id,
    )
    # Decode only the newly generated tokens
    gen = outputs[0, inputs["input_ids"].shape[-1] :]
    reply = tokenizer.decode(gen, skip_special_tokens=True)

    return ChatResponse(reply=reply)