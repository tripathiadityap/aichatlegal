"""
AIChatLegal - Vercel Serverless Entrypoint (FastAPI)
Project: aichatlegal
"""

import sys
import os
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Any, Optional

from database import db_manager
from gemini_engine import gemini_engine

app = FastAPI(title="AIChatLegal API", version="2.6.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

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

@app.get("/api/static/chat.js")
def serve_chat_js():
    js_path = root_dir / "static" / "chat.js"
    try:
        js_content = js_path.read_text()
    except Exception:
        js_content = "console.error('chat.js not found');"
    return Response(content=js_content, media_type="application/javascript")

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
    try:
        policies = db_manager.get_all_policies()
        return policies if policies is not None else []
    except Exception as e:
        print(f"[API Get Policies] {e}")
        return []

@app.get("/api/policies/{policy_id}")
def get_policy(policy_id: str):
    try:
        if not policy_id or policy_id.startswith("sample-"):
            raise HTTPException(status_code=404, detail="Sample policy details loaded locally")
        p = db_manager.get_policy_by_id(policy_id)
        if not p:
            raise HTTPException(status_code=404, detail="Policy not found")
        return p
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze")
def analyze_policy(req: PolicyUploadRequest):
    try:
        risk_analysis = gemini_engine.analyze_policy_upload(
            title=req.title, client_name=req.client_name,
            deal_value=req.deal_value_usd, content=req.raw_content
        )
        policy_id = db_manager.insert_policy(req.dict(), risk_analysis)
        return {"policy_id": policy_id, "risk_analysis": risk_analysis}
    except Exception as e:
        print(f"[API Analyze] {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
def chat_with_gemini(req: ChatRequest):
    try:
        policy_ctx = None
        if req.policy_id and not str(req.policy_id).startswith("sample-"):
            policy_ctx = db_manager.get_policy_by_id(req.policy_id)
        response = gemini_engine.generate_chat_response(
            user_role=req.user_role, user_query=req.user_query,
            chat_history=[], policy_context=policy_ctx
        )
        return {"response": response}
    except Exception as e:
        print(f"[API Chat] {e}")
        return {"response": "Gemini AI Assistant: I am ready to assist with your banking legal inquiries."}

@app.post("/api/advice")
def add_advice(req: LegalAdviceRequest):
    try:
        advice_id = db_manager.add_legal_advice(req.dict())
        return {"advice_id": advice_id, "status": "recorded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/", response_class=HTMLResponse)
def index_page():
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AIChatLegal | Enterprise Bank Policy & Legal AI Advisor</title>
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #070a12; --panel: rgba(15,23,42,0.75); --border: rgba(255,255,255,0.08);
            --indigo: #6366f1; --emerald: #10b981; --amber: #f59e0b; --rose: #f43f5e;
            --text: #f8fafc; --muted: #94a3b8;
        }
        * { box-sizing: border-box; }
        body { margin:0; background:var(--bg); color:var(--text); font-family:'DM Sans',sans-serif; height:100vh; display:flex; flex-direction:column; overflow:hidden; }
        .navbar { background:linear-gradient(135deg,#0f172a,#1e1b4b,#0f172a); border-bottom:1px solid var(--border); padding:14px 24px; display:flex; justify-content:space-between; align-items:center; }
        .brand { display:flex; align-items:center; gap:12px; font-weight:700; font-size:20px; }
        .pill { background:rgba(16,185,129,.15); color:#34d399; border:1px solid rgba(16,185,129,.3); padding:4px 12px; border-radius:20px; font-size:12px; font-family:'JetBrains Mono',monospace; display:flex; align-items:center; gap:6px; }
        .dot { width:8px; height:8px; background:#34d399; border-radius:50%; animation:pulse 2s infinite; }
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }
        .app { display:flex; flex:1; overflow:hidden; }
        .sidebar { width:320px; background:var(--panel); border-right:1px solid var(--border); padding:20px; display:flex; flex-direction:column; gap:20px; overflow-y:auto; }
        .ctrl { display:flex; flex-direction:column; gap:8px; }
        .lbl { font-size:12px; font-weight:600; text-transform:uppercase; letter-spacing:.5px; color:var(--muted); }
        select,input,textarea { background:#1e293b; border:1px solid rgba(255,255,255,.1); color:white; padding:10px 12px; border-radius:8px; font-family:inherit; font-size:14px; width:100%; outline:none; transition:border-color .2s; }
        select:focus,input:focus,textarea:focus { border-color:var(--indigo); }
        .workspace { flex:1; display:flex; flex-direction:column; background:rgba(10,15,26,.5); }
        .messages { flex:1; padding:24px; overflow-y:auto; display:flex; flex-direction:column; gap:16px; }
        .bubble { max-width:80%; padding:14px 18px; border-radius:12px; line-height:1.5; font-size:15px; animation:fadein .2s ease; }
        @keyframes fadein { from{opacity:0;transform:translateY(6px)} to{opacity:1;transform:translateY(0)} }
        .user { background:#1e293b; align-self:flex-end; border:1px solid rgba(255,255,255,.08); border-bottom-right-radius:2px; }
        .ai { background:rgba(30,41,59,.85); align-self:flex-start; border-left:3px solid var(--indigo); border-bottom-left-radius:2px; }
        .chips { display:flex; gap:8px; padding:0 24px 12px; overflow-x:auto; }
        .chip { background:rgba(30,41,59,.7); border:1px solid rgba(255,255,255,.1); color:#cbd5e1; padding:8px 14px; border-radius:20px; font-size:13px; cursor:pointer; white-space:nowrap; transition:all .2s; }
        .chip:hover { background:rgba(99,102,241,.2); border-color:var(--indigo); color:white; }
        .inputbar { padding:16px 24px; background:#0f172a; border-top:1px solid var(--border); display:flex; gap:12px; }
        .inputbar input { flex:1; height:44px; }
        .sendbtn { background:var(--indigo); color:white; border:none; padding:0 24px; border-radius:8px; font-weight:600; cursor:pointer; height:44px; font-size:15px; }
        .sendbtn:hover { background:#4f46e5; }
        .detail { width:300px; background:var(--panel); border-left:1px solid var(--border); padding:20px; display:flex; flex-direction:column; gap:16px; overflow-y:auto; }
        .card { background:rgba(30,41,59,.6); border:1px solid var(--border); border-radius:10px; padding:14px; }
        .bigval { font-size:22px; font-weight:700; font-family:'JetBrains Mono',monospace; margin-top:4px; }
        .modal { display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,.75); backdrop-filter:blur(4px); z-index:1000; justify-content:center; align-items:center; }
        .modalbox { background:#0f172a; border:1px solid var(--indigo); border-radius:12px; padding:24px; width:500px; max-width:90%; }
    </style>
</head>
<body>
    <div class="navbar">
        <div class="brand"><span>🏛️</span><span>AIChatLegal</span><span style="font-size:12px;color:var(--muted);font-weight:400;">| Enterprise Bank Policy Advisory</span></div>
        <div style="display:flex;gap:12px;align-items:center;">
            <div class="pill"><div class="dot"></div><span>Supabase DB & Gemini AI Connected</span></div>
            <button onclick="openUploadModal()" class="chip" style="background:var(--indigo);color:white;border:none;">+ Upload Deal Proposal</button>
        </div>
    </div>

    <div class="app">
        <div class="sidebar">
            <div class="ctrl">
                <div class="lbl">👤 Active Persona</div>
                <select id="user-role">
                    <option value="sales_head">👔 Sales Repo Head (VP)</option>
                    <option value="sales_rep">💼 Sales Lead / Deal Officer</option>
                    <option value="legal_counsel">⚖️ Senior Legal Counsel</option>
                    <option value="compliance_officer">🛡️ Compliance Officer</option>
                </select>
            </div>
            <div class="ctrl">
                <div class="lbl">📋 Attach Policy / Deal Context (RAG)</div>
                <select id="policy-select" onchange="onPolicySelected()">
                    <option value="">-- General Banking Regulations --</option>
                </select>
            </div>
            <hr style="border-color:var(--border);margin:0;">
            <div class="ctrl">
                <div class="lbl">⚡ Live Bank Policies</div>
                <div id="policies-list" style="display:flex;flex-direction:column;gap:8px;font-size:13px;"></div>
            </div>
        </div>

        <div class="workspace">
            <div class="messages" id="chat-box">
                <div class="bubble ai">👋 Welcome to <strong>AIChatLegal</strong>. I am your Gemini-powered Bank Legal &amp; Regulatory Assistant.<br><br>Select an active deal from the left sidebar to ground our analysis, or ask any question regarding corporate credit overrides, SEC/OCC compliance, or contract riders!</div>
            </div>
            <div class="chips">
                <button class="chip" onclick="sendSuggestion('What contract riders are required by legal for this deal?')">📋 Required Contract Riders</button>
                <button class="chip" onclick="sendSuggestion('Summarize key legal risk vectors and covenant waivers.')">⚠️ Summarize Legal Risk</button>
                <button class="chip" onclick="sendSuggestion('How does AIChatLegal ensure banking security and PII masking?')">🔒 Banking Security</button>
            </div>
            <div class="inputbar">
                <input type="text" id="chat-input" placeholder="Ask Gemini AI about policy terms, lawyer advice, or regulatory compliance...">
                <button class="sendbtn" id="send-btn" onclick="submitChat()">Send ⚡</button>
            </div>
        </div>

        <div class="detail">
            <div class="lbl">📊 Active Deal Overview</div>
            <div class="card"><div style="font-size:12px;color:var(--muted);">CLIENT CORPORATE ENTITY</div><div id="d-client" style="font-weight:600;font-size:15px;margin-top:4px;">Apex Global Logistics Inc.</div></div>
            <div class="card"><div style="font-size:12px;color:var(--muted);">DEAL CAPITAL VOLUME</div><div id="d-value" class="bigval">$14.50M</div></div>
            <div class="card"><div style="font-size:12px;color:var(--muted);">AI RISK SCORE</div><div id="d-score" class="bigval" style="color:var(--amber);">68 / 100</div></div>
            <div class="card" style="flex:1;overflow-y:auto;"><div style="font-size:12px;color:var(--muted);margin-bottom:6px;">RECOMMENDED LEGAL ACTION</div><div id="d-rec" style="font-size:13px;line-height:1.4;color:#cbd5e1;">Sales requested 45 bps rate discount and leverage ratio relaxation to 4.25x EBITDA. Requires Schedule 14B Covenant Rider.</div></div>
        </div>
    </div>

    <div class="modal" id="upload-modal">
        <div class="modalbox">
            <h3 style="margin-top:0;">🚀 Submit Deal Proposal for Gemini Pre-Screening</h3>
            <div class="ctrl" style="margin-bottom:12px;"><div class="lbl">Proposal Title*</div><input type="text" id="m-title" value="Commercial Credit Override - Apex Global Logistics"></div>
            <div class="ctrl" style="margin-bottom:12px;"><div class="lbl">Client Name*</div><input type="text" id="m-client" value="Apex Global Logistics Inc."></div>
            <div style="display:flex;gap:12px;margin-bottom:12px;">
                <div class="ctrl" style="flex:1;"><div class="lbl">Deal Value ($)*</div><input type="number" id="m-value" value="25000000"></div>
                <div class="ctrl" style="flex:1;"><div class="lbl">Category*</div><select id="m-cat"><option value="Commercial Credit Override">Credit Override</option><option value="Syndicated Revolving Credit">Syndicated Credit</option><option value="Asset Securitization">Asset Securitization</option></select></div>
            </div>
            <div class="ctrl" style="margin-bottom:16px;"><div class="lbl">Policy Override Clauses*</div><textarea id="m-content" rows="4">SECTION 3.1: Client requests 45 bps rate discount on SOFR margin. SECTION 8.2: Maximum leverage ratio relaxed to 4.0x EBITDA.</textarea></div>
            <div style="display:flex;justify-content:flex-end;gap:10px;">
                <button class="chip" onclick="closeUploadModal()">Cancel</button>
                <button class="chip" onclick="submitModalUpload()" style="background:var(--indigo);color:white;border:none;">Run Gemini Screening ⚡</button>
            </div>
        </div>
    </div>

    <script src="/api/static/chat.js"></script>
</body>
</html>"""

handler = app
