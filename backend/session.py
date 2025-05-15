# backend/session.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel

router = APIRouter(prefix="/session")

class Msg(BaseModel):
    role: str
    content: str

class SessionIn(BaseModel):
    messages: list[Msg]
    model: str

@router.post("/")
async def create_session(session: SessionIn, user=Depends(get_current_user)):
    doc = {
      "userId": user["_id"],
      "model": session.model,
      "messages": [
         {**m.dict(), "timestamp": datetime.utcnow()} for m in session.messages
      ]
    }
    result = await db["sessions"].insert_one(doc)
    return {"sessionId": str(result.inserted_id)}