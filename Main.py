from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import os
import logging
from datetime import datetime

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Initialize OpenAI client
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI(title="SOUL7OS Agent", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request models
class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"

class ChatResponse(BaseModel):
    response: str
    session_id: str
    timestamp: str
    risk_score: float = 0.0

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

# Main chat endpoint
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Simple content filtering
        risky_keywords = ["legal advice", "medical diagnosis", "financial advice"]
        risk_score = 0.0
        
        for keyword in risky_keywords:
            if keyword in request.message.lower():
                risk_score += 0.3
        
        # Call OpenAI
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant that provides accurate information while being careful about compliance and safety."},
                {"role": "user", "content": request.message}
            ],
            max_tokens=500
        )
        
        response_text = response.choices[0].message.content
        
        # Add disclaimer if risky
        if risk_score > 0.6:
            response_text = f"⚠️ **Disclaimer**: I am an AI assistant and cannot provide professional advice. Please consult qualified professionals for specific guidance.\n\n{response_text}"
        
        return ChatResponse(
            response=response_text,
            session_id=request.session_id,
            timestamp=datetime.utcnow().isoformat(),
            risk_score=min(risk_score, 1.0)
        )
        
    except Exception as e:
        logging.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Demo endpoint
@app.get("/")
async def demo():
    return {
        "message": "SOUL7OS Agent Framework - Demo",
        "version": "1.0.0",
        "endpoints": {
            "chat": "/chat (POST)",
            "health": "/health (GET)"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
