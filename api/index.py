"""
AIChatLegal - Vercel Serverless Entrypoint (FastAPI / WSGI)
Serves API endpoints and web interface on Vercel Serverless Architecture.
Project: aichatlegal
"""

import sys
import os
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any, Optional

from database import db_manager
from gemini_engine import gemini_engine

app = FastAPI(
    title="AIChatLegal API",
    description="Enterprise Bank Policy Analysis & Legal Advisory Engine",
    version="2.4.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PolicyUploadRequest(BaseModel):
    title: str
    client_name: str
    deal_value_usd: float
    product_category: str
    sales_rep_name: str
    sales_head_approval: bool = True
    raw_content: str

class ChatRequest(BaseModel):
    user_role: str = "sales_head"
    user_query: str
    policy_id: Optional[str] = None

class LegalAdviceRequest(BaseModel):
    policy_id: str
    lawyer_name: str
    advice_summary: str
    required_riders: List[str]
    compliance_directives: List[str]
    decision: str

@app.get("/api/health")
def health_check():
    return {
        "status": "online",
        "database": "supabase" if db_manager.use_supabase else "sqlite",
        "supabase_url": db_manager.active_url,
        "gemini": "active" if gemini_engine.api_available else "analytical"
    }

@app.get("/api/policies")
def get_policies():
    return db_manager.get_all_policies()

@app.get("/api/policies/{policy_id}")
def get_policy(policy_id: str):
    p = db_manager.get_policy_by_id(policy_id)
    if not p:
        raise HTTPException(status_code=404, detail="Policy not found")
    return p

@app.post("/api/analyze")
def analyze_policy(req: PolicyUploadRequest):
    risk_analysis = gemini_engine.analyze_policy_upload(
        title=req.title,
        client_name=req.client_name,
        deal_value=req.deal_value_usd,
        content=req.raw_content
    )
    
    policy_id = db_manager.insert_policy(req.dict(), risk_analysis)
    return {
        "policy_id": policy_id,
        "risk_analysis": risk_analysis
    }

@app.post("/api/chat")
def chat_with_gemini(req: ChatRequest):
    policy_ctx = None
    if req.policy_id:
        policy_ctx = db_manager.get_policy_by_id(req.policy_id)
        
    response = gemini_engine.generate_chat_response(
        user_role=req.user_role,
        user_query=req.user_query,
        chat_history=[],
        policy_context=policy_ctx
    )
    return {"response": response}

@app.post("/api/advice")
def add_advice(req: LegalAdviceRequest):
    advice_id = db_manager.add_legal_advice(req.dict())
    return {"advice_id": advice_id, "status": "recorded"}

@app.get("/", response_class=HTMLResponse)
def index_page():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AIChatLegal - Enterprise Banking Policy & Legal Advisor</title>
        <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
        <style>
            body { background-color: #090d16; color: #f3f4f6; font-family: 'DM Sans', sans-serif; margin: 0; padding: 40px; }
            .card { background: rgba(17, 24, 39, 0.8); border: 1px solid rgba(99, 102, 241, 0.3); border-radius: 12px; padding: 30px; max-width: 900px; margin: 0 auto; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
            h1 { color: #ffffff; margin-top: 0; }
            .badge { background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid #10b981; padding: 4px 12px; border-radius: 20px; font-size: 14px; font-family: 'JetBrains Mono', monospace; }
            .mono { font-family: 'JetBrains Mono', monospace; color: #a5b4fc; background: #1e1b4b; padding: 2px 8px; border-radius: 4px; }
            .btn { display: inline-block; background: #6366f1; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600; margin-top: 20px; transition: 0.2s; }
            .btn:hover { background: #4f46e5; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>⚖️ AIChatLegal — Enterprise Bank Advisory Service</h1>
            <p>System Status: <span class="badge">ONLINE (Vercel Serverless)</span></p>
            <p>Integrated with <strong>Google Gemini AI</strong> and <strong>Supabase Cloud PostgreSQL</strong>.</p>
            <hr style="border-color: rgba(255,255,255,0.1); margin: 24px 0;">
            <h3>Available API Endpoints:</h3>
            <ul>
                <li><span class="mono">GET /api/health</span> - Infrastructure Health Monitor</li>
                <li><span class="mono">GET /api/policies</span> - Fetch Bank Deal Proposals</li>
                <li><span class="mono">POST /api/analyze</span> - Gemini AI Pre-Screening & Risk Engine</li>
                <li><span class="mono">POST /api/chat</span> - Natural Language Legal Chatbot</li>
                <li><span class="mono">POST /api/advice</span> - Submit Lawyer Opinions & Riders</li>
            </ul>
            <a href="/api/policies" class="btn">View Live Supabase Policies</a>
        </div>
    </body>
    </html>
    """

# Vercel WSGI/ASGI handler
handler = app
