from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Literal
import threading
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TextIteratorStreamer
)
from backend.gpt2_chat import router as gpt2_router
from backend.onnx_chat import router as onnx_router

# --- Schemas ---
class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]

class ChatResponse(BaseModel):
    reply: str

# --- App & CORS ---
app = FastAPI()
app.include_router(onnx_router)
app.include_router(gpt2_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Model Load ---
tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-2-7b-chat-hf")
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-2-7b-chat-hf",
    torch_dtype=torch.float16,
    device_map="auto"
)

# --- Non-streaming endpoint ---
@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    prompt = "".join(
        ("User: " if m.role == "user" else "Assistant: ") + m.content + "\n"
        for m in req.messages
    ) + "Assistant: "

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(
        **inputs,
        max_new_tokens=200,
        do_sample=True,
        temperature=0.7,
        pad_token_id=tokenizer.eos_token_id
    )
    reply = tokenizer.decode(
        outputs[0][inputs["input_ids"].shape[-1]:],
        skip_special_tokens=True
    )
    return ChatResponse(reply=reply)

# --- Streaming endpoint ---
@app.post("/chat/stream")
def chat_stream(req: ChatRequest):
    # 1) Build the prompt
    prompt = "".join(
        ("User: " if m.role == "user" else "Assistant: ") + m.content + "\n"
        for m in req.messages
    ) + "Assistant: "

    # 2) Tokenize & move to device
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    # 3) Use TextIteratorStreamer for iterable output
    streamer = TextIteratorStreamer(
        tokenizer,
        skip_prompt=True,
        skip_special_tokens=True,
        timeout=60.0
    )

    # 4) Kick off generation in a background thread
    thread = threading.Thread(
        target=model.generate,
        kwargs=dict(
            **inputs,
            max_new_tokens=200,
            do_sample=True,
            temperature=0.7,
            pad_token_id=tokenizer.eos_token_id,
            streamer=streamer
        ),
        daemon=True
    )
    thread.start()

    # 5) Return the streamer itself as the ASGI iterable
    return StreamingResponse(streamer, media_type="text/plain")