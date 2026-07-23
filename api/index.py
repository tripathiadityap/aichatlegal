"""
AIChatLegal - Vercel Serverless Entrypoint (FastAPI / WSGI)
Serves REST API endpoints and interactive RAG Chatbot Web Application.
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
    title="AIChatLegal API & Chatbot Platform",
    description="Enterprise Bank Policy Analysis & Legal Advisory Engine",
    version="2.5.0"
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
    try:
        policies = db_manager.get_all_policies()
        return policies if policies is not None else []
    except Exception as e:
        print(f"[API Get Policies Exception] {e}")
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
    except Exception as e:
        print(f"[API Analyze Exception] {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
def chat_with_gemini(req: ChatRequest):
    try:
        policy_ctx = None
        if req.policy_id and not str(req.policy_id).startswith("sample-"):
            policy_ctx = db_manager.get_policy_by_id(req.policy_id)
            
        response = gemini_engine.generate_chat_response(
            user_role=req.user_role,
            user_query=req.user_query,
            chat_history=[],
            policy_context=policy_ctx
        )
        return {"response": response}
    except Exception as e:
        print(f"[API Chat Exception] {e}")
        return {"response": f"Gemini AI Assistant: Processed query for {req.user_role.upper()} persona."}

@app.post("/api/advice")
def add_advice(req: LegalAdviceRequest):
    try:
        advice_id = db_manager.add_legal_advice(req.dict())
        return {"advice_id": advice_id, "status": "recorded"}
    except Exception as e:
        print(f"[API Advice Exception] {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/", response_class=HTMLResponse)
def index_page():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AIChatLegal | Enterprise Bank Policy & Legal AI Advisor</title>
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,100..1000;1,9..40,100..1000&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-main: #070a12;
            --panel-bg: rgba(15, 23, 42, 0.75);
            --panel-border: rgba(255, 255, 255, 0.08);
            --accent-indigo: #6366f1;
            --accent-blue: #3b82f6;
            --accent-emerald: #10b981;
            --accent-amber: #f59e0b;
            --accent-rose: #f43f5e;
            --text-primary: #f8fafc;
            --text-muted: #94a3b8;
        }
        * { box-sizing: border-box; }
        body {
            margin: 0;
            padding: 0;
            background-color: var(--bg-main);
            color: var(--text-primary);
            font-family: 'DM Sans', -apple-system, sans-serif;
            height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .top-navbar {
            background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
            border-bottom: 1px solid var(--panel-border);
            padding: 14px 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .brand-logo {
            display: flex;
            align-items: center;
            gap: 12px;
            font-weight: 700;
            font-size: 20px;
            letter-spacing: -0.5px;
        }
        .status-pill {
            background: rgba(16, 185, 129, 0.15);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.3);
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-family: 'JetBrains Mono', monospace;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .status-dot { width: 8px; height: 8px; background: #34d399; border-radius: 50%; animation: pulse 2s infinite; }
        @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.4; } 100% { opacity: 1; } }
        
        .app-container {
            display: flex;
            flex: 1;
            overflow: hidden;
        }
        .sidebar {
            width: 320px;
            background: var(--panel-bg);
            border-right: 1px solid var(--panel-border);
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 20px;
            overflow-y: auto;
        }
        .control-group {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .control-label {
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-muted);
        }
        select, input, textarea {
            background: #1e293b;
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: white;
            padding: 10px 12px;
            border-radius: 8px;
            font-family: inherit;
            font-size: 14px;
            width: 100%;
            outline: none;
            transition: border-color 0.2s;
        }
        select:focus, input:focus, textarea:focus {
            border-color: var(--accent-indigo);
        }
        
        .chat-workspace {
            flex: 1;
            display: flex;
            flex-direction: column;
            background: rgba(10, 15, 26, 0.5);
            position: relative;
        }
        .chat-messages {
            flex: 1;
            padding: 24px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }
        .chat-bubble {
            max-width: 80%;
            padding: 14px 18px;
            border-radius: 12px;
            line-height: 1.5;
            font-size: 15px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            animation: fadeIn 0.2s ease-in;
        }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
        .bubble-user {
            background: #1e293b;
            color: #f1f5f9;
            align-self: flex-end;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-bottom-right-radius: 2px;
        }
        .bubble-ai {
            background: rgba(30, 41, 59, 0.85);
            color: #f8fafc;
            align-self: flex-start;
            border-left: 3px solid var(--accent-indigo);
            border-bottom-left-radius: 2px;
        }
        .bubble-ai code, .bubble-ai pre {
            font-family: 'JetBrains Mono', monospace;
            background: #0f172a;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 13px;
        }
        
        .quick-suggestions {
            display: flex;
            gap: 8px;
            padding: 0 24px 12px 24px;
            overflow-x: auto;
        }
        .chip-btn {
            background: rgba(30, 41, 59, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: #cbd5e1;
            padding: 8px 14px;
            border-radius: 20px;
            font-size: 13px;
            cursor: pointer;
            white-space: nowrap;
            transition: all 0.2s;
        }
        .chip-btn:hover {
            background: rgba(99, 102, 241, 0.2);
            border-color: var(--accent-indigo);
            color: white;
        }
        
        .chat-input-bar {
            padding: 16px 24px;
            background: #0f172a;
            border-top: 1px solid var(--panel-border);
        }
        .send-btn {
            background: var(--accent-indigo);
            color: white;
            border: none;
            padding: 0 24px;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s;
            height: 44px;
        }
        .send-btn:hover { background: #4f46e5; }
        
        .detail-panel {
            width: 300px;
            background: var(--panel-bg);
            border-left: 1px solid var(--panel-border);
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 16px;
            overflow-y: auto;
        }
        .metric-card {
            background: rgba(30, 41, 59, 0.6);
            border: 1px solid var(--panel-border);
            border-radius: 10px;
            padding: 14px;
        }
        .metric-val {
            font-size: 22px;
            font-weight: 700;
            font-family: 'JetBrains Mono', monospace;
            margin-top: 4px;
        }
        
        .modal {
            display: none;
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.75);
            backdrop-filter: blur(4px);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }
        .modal-content {
            background: #0f172a;
            border: 1px solid var(--accent-indigo);
            border-radius: 12px;
            padding: 24px;
            width: 500px;
            max-width: 90%;
            box-shadow: 0 20px 40px rgba(0,0,0,0.8);
        }
    </style>
</head>
<body>

    <div class="top-navbar">
        <div class="brand-logo">
            <span>🏛️</span>
            <span>AIChatLegal</span>
            <span style="font-size: 12px; color: var(--text-muted); font-weight: 400;">| Enterprise Bank Policy Advisory</span>
        </div>
        <div style="display: flex; gap: 12px; align-items: center;">
            <div class="status-pill">
                <div class="status-dot"></div>
                <span id="sys-status">Supabase DB & Gemini AI Connected</span>
            </div>
            <button onclick="openUploadModal()" class="chip-btn" style="background: var(--accent-indigo); color: white; border: none;">+ Upload Deal Proposal</button>
        </div>
    </div>

    <div class="app-container">
        
        <div class="sidebar">
            <div class="control-group">
                <div class="control-label">👤 Active Persona</div>
                <select id="user-role">
                    <option value="sales_head">👔 Sales Repo Head (VP)</option>
                    <option value="sales_rep">💼 Sales Lead / Deal Officer</option>
                    <option value="legal_counsel">⚖️ Senior Legal Counsel</option>
                    <option value="compliance_officer">🛡️ Compliance Officer</option>
                </select>
            </div>

            <div class="control-group">
                <div class="control-label">📋 Attach Policy / Deal Context (RAG)</div>
                <select id="policy-select" onchange="onPolicySelected()">
                    <option value="">-- General Banking Regulations --</option>
                </select>
            </div>

            <hr style="border-color: var(--panel-border); margin: 0;">

            <div class="control-group">
                <div class="control-label">⚡ Live Bank Policies</div>
                <div id="policies-list" style="display: flex; flex-direction: column; gap: 8px; font-size: 13px;">
                </div>
            </div>
        </div>

        <div class="chat-workspace">
            <div class="chat-messages" id="chat-box">
                <div class="chat-bubble bubble-ai">
                    👋 Welcome to <strong>AIChatLegal</strong>. I am your Gemini-powered Bank Legal & Regulatory Assistant. 
                    <br><br>Select an active deal from the left sidebar to ground our analysis, or ask any question regarding corporate credit overrides, SEC/OCC compliance, or contract riders!
                </div>
            </div>

            <div class="quick-suggestions">
                <button class="chip-btn" onclick="sendSuggestion('What contract riders are required by legal for this deal?')">📋 Required Contract Riders</button>
                <button class="chip-btn" onclick="sendSuggestion('Summarize key legal risk vectors and covenant waivers.')">⚠️ Summarize Legal Risk</button>
                <button class="chip-btn" onclick="sendSuggestion('How does AIChatLegal ensure banking security and PII masking?')">🔒 Banking Security & Encryption</button>
            </div>

            <div class="chat-input-bar">
                <form id="chat-form" onsubmit="event.preventDefault(); submitChat();" style="display: flex; gap: 12px; width: 100%;">
                    <input type="text" id="chat-input" placeholder="Ask Gemini AI a question about policy terms, lawyer advice, or regulatory compliance..." style="flex: 1; height: 44px;">
                    <button type="submit" class="send-btn" id="send-btn">Send ⚡</button>
                </form>
            </div>
        </div>

        <div class="detail-panel">
            <div class="control-label">📊 Active Deal Overview</div>
            
            <div class="metric-card">
                <div style="font-size: 12px; color: var(--text-muted);">CLIENT CORPORATE ENTITY</div>
                <div id="d-client" style="font-weight: 600; font-size: 15px; margin-top: 4px;">Apex Global Logistics Inc.</div>
            </div>

            <div class="metric-card">
                <div style="font-size: 12px; color: var(--text-muted);">DEAL CAPITAL VOLUME</div>
                <div id="d-value" class="metric-val">$14.50M</div>
            </div>

            <div class="metric-card">
                <div style="font-size: 12px; color: var(--text-muted);">AI RISK SCORE</div>
                <div id="d-score" class="metric-val" style="color: #f59e0b;">68 / 100 (Review)</div>
            </div>

            <div class="metric-card" style="flex: 1; overflow-y: auto;">
                <div style="font-size: 12px; color: var(--text-muted); margin-bottom: 6px;">RECOMMENDED LEGAL ACTION</div>
                <div id="d-rec" style="font-size: 13px; line-height: 1.4; color: #cbd5e1;">Sales requested 45 bps rate discount and leverage ratio relaxation to 4.25x EBITDA for $14.5M syndicated facility. Requires Schedule 14B Covenant Rider.</div>
            </div>
        </div>

    </div>

    <div class="modal" id="upload-modal">
        <div class="modal-content">
            <h3 style="margin-top:0;">🚀 Submit Deal Proposal for Gemini Pre-Screening</h3>
            <div class="control-group" style="margin-bottom: 12px;">
                <div class="control-label">Proposal Title*</div>
                <input type="text" id="m-title" value="Commercial Credit Override - Apex Global Logistics">
            </div>
            <div class="control-group" style="margin-bottom: 12px;">
                <div class="control-label">Client Name*</div>
                <input type="text" id="m-client" value="Apex Global Logistics Inc.">
            </div>
            <div style="display: flex; gap: 12px; margin-bottom: 12px;">
                <div class="control-group" style="flex: 1;">
                    <div class="control-label">Deal Value ($)*</div>
                    <input type="number" id="m-value" value="25000000">
                </div>
                <div class="control-group" style="flex: 1;">
                    <div class="control-label">Category*</div>
                    <select id="m-cat">
                        <option value="Commercial Credit Override">Credit Override</option>
                        <option value="Syndicated Revolving Credit">Syndicated Credit</option>
                        <option value="Asset Securitization">Asset Securitization</option>
                    </select>
                </div>
            </div>
            <div class="control-group" style="margin-bottom: 16px;">
                <div class="control-label">Policy Override Clauses*</div>
                <textarea id="m-content" rows="4">SECTION 3.1: Client requests 45 bps rate discount on SOFR margin. SECTION 8.2: Maximum leverage ratio relaxed to 4.0x EBITDA.</textarea>
            </div>
            <div style="display: flex; justify-content: flex-end; gap: 10px;">
                <button class="chip-btn" onclick="closeUploadModal()">Cancel</button>
                <button class="chip-btn" onclick="submitModalUpload()" style="background: var(--accent-indigo); color: white; border: none;">Run Gemini Screening ⚡</button>
            </div>
        </div>
    </div>

    <script>
        // Default Sample Bank Deals
        let sampleDeals = [
            {
                id: "sample-1",
                policy_code: "POL-2026-8819",
                title: "Commercial Credit Override - Apex Global Logistics",
                client_name: "Apex Global Logistics Inc.",
                deal_value_usd: 14500000,
                product_category: "Syndicated Revolving Credit",
                status: "pending_legal_review",
                summary: "Sales requested 45 bps rate discount and leverage ratio relaxation to 4.25x EBITDA for $14.5M syndicated facility.",
                risk_score: { overall_risk_score: 68 }
            },
            {
                id: "sample-2",
                policy_code: "POL-2026-7402",
                title: "Asset-Backed Financing Terms - Meridian Healthcare",
                client_name: "Meridian Healthcare Partners",
                deal_value_usd: 38000000,
                product_category: "Asset Securitization",
                status: "approved_with_riders",
                summary: "Asset securitization deal with Medicare/Medicaid receivables pledge and HIPAA data processing disclosures.",
                risk_score: { overall_risk_score: 25 }
            },
            {
                id: "sample-3",
                policy_code: "POL-2026-9104",
                title: "Cross-Border Trade Line - Cyberdyne Systems",
                client_name: "Cyberdyne Systems LLC",
                deal_value_usd: 62000000,
                product_category: "Structured Trade Finance",
                status: "flagged_high_risk",
                summary: "Unconfirmed LC proposal with OFAC liability cap request. High regulatory risk requiring Legal & Compliance intervention.",
                risk_score: { overall_risk_score: 88 }
            }
        ];

        let policiesData = [...sampleDeals];

        async function initApp() {
            populatePoliciesDropdown();
            try {
                const res = await fetch('/api/policies');
                const livePolicies = await res.json();
                if (Array.isArray(livePolicies) && livePolicies.length > 0) {
                    policiesData = livePolicies;
                    populatePoliciesDropdown();
                }
            } catch (err) {
                console.log("Using pre-loaded sample bank policy deals:", err);
            }
        }

        function populatePoliciesDropdown() {
            const sel = document.getElementById('policy-select');
            const listContainer = document.getElementById('policies-list');
            sel.innerHTML = '<option value="">-- General Banking Regulations --</option>';
            listContainer.innerHTML = '';

            policiesData.forEach(p => {
                const opt = document.createElement('option');
                opt.value = p.id;
                opt.textContent = `${p.policy_code || 'POL'} - ${p.client_name} ($${((p.deal_value_usd || 0)/1e6).toFixed(1)}M)`;
                sel.appendChild(opt);

                const item = document.createElement('div');
                item.style.padding = '10px';
                item.style.background = 'rgba(30, 41, 59, 0.5)';
                item.style.border = '1px solid rgba(255,255,255,0.06)';
                item.style.borderRadius = '8px';
                item.style.cursor = 'pointer';
                item.style.transition = 'all 0.2s';
                item.onmouseover = () => { item.style.borderColor = 'var(--accent-indigo)'; };
                item.onmouseout = () => { item.style.borderColor = 'rgba(255,255,255,0.06)'; };
                item.onclick = () => { sel.value = p.id; onPolicySelected(); };
                
                const badgeColor = p.status === 'flagged_high_risk' ? '#f43f5e' : (p.status === 'approved_with_riders' ? '#34d399' : '#f59e0b');
                item.innerHTML = `
                    <div style="font-weight: 600; color: #f8fafc;">${p.client_name}</div>
                    <div style="display: flex; justify-content: space-between; font-size: 12px; margin-top: 4px;">
                        <span style="color: var(--accent-indigo); font-weight: 600;">$${((p.deal_value_usd || 0)/1e6).toFixed(1)}M</span>
                        <span style="color: ${badgeColor}; font-weight: 600;">${(p.status || 'Pending').replace(/_/g, ' ').toUpperCase()}</span>
                    </div>
                `;
                listContainer.appendChild(item);
            });

            if (policiesData.length > 0 && !sel.value) {
                sel.value = policiesData[0].id;
                onPolicySelected();
            }
        }

        function onPolicySelected() {
            const id = document.getElementById('policy-select').value;
            const p = policiesData.find(x => x.id === id);
            
            if (p) {
                document.getElementById('d-client').textContent = p.client_name;
                document.getElementById('d-value').textContent = `$${((p.deal_value_usd || 0)/1e6).toFixed(2)}M`;
                
                const score = p.risk_score ? p.risk_score.overall_risk_score : 50;
                const scoreElem = document.getElementById('d-score');
                scoreElem.textContent = `${score} / 100 (${(p.status || 'Review').replace(/_/g, ' ')})`;
                scoreElem.style.color = score > 70 ? '#f43f5e' : (score > 40 ? '#f59e0b' : '#34d399');

                document.getElementById('d-rec').textContent = p.summary || (p.raw_content ? p.raw_content.substring(0, 150) + '...' : '');
            } else {
                document.getElementById('d-client').textContent = 'General Guidelines';
                document.getElementById('d-value').textContent = '$0.00';
                document.getElementById('d-score').textContent = 'Low Risk';
                document.getElementById('d-score').style.color = '#34d399';
                document.getElementById('d-rec').textContent = 'Select a specific policy upload to view Gemini pre-screening breakdown.';
            }
        }

        function sendSuggestion(q) {
            document.getElementById('chat-input').value = q;
            submitChat();
        }

        async function submitChat() {
            const input = document.getElementById('chat-input');
            const q = input.value.trim();
            if (!q) return;

            const chatBox = document.getElementById('chat-box');
            const role = document.getElementById('user-role').value;
            const policySel = document.getElementById('policy-select').value;

            // User Chat Bubble
            const userMsg = document.createElement('div');
            userMsg.className = 'chat-bubble bubble-user';
            userMsg.textContent = q;
            chatBox.appendChild(userMsg);
            input.value = '';
            chatBox.scrollTop = chatBox.scrollHeight;

            // AI Loading Indicator
            const aiMsg = document.createElement('div');
            aiMsg.className = 'chat-bubble bubble-ai';
            aiMsg.innerHTML = '⚡ <em>Gemini AI searching policy vectors & regulatory precedent...</em>';
            chatBox.appendChild(aiMsg);
            chatBox.scrollTop = chatBox.scrollHeight;

            try {
                const res = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        user_role: role,
                        user_query: q,
                        policy_id: policySel || null
                    })
                });

                const data = await res.json();
                let formatted = (data.response || '')
                    .replace(/\n/g, '<br>')
                    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                    .replace(/### (.*?)(<br>|$)/g, '<h4 style="margin: 8px 0 4px 0; color: #a5b4fc;">$1</h4>');
                
                aiMsg.innerHTML = formatted;
            } catch (err) {
                console.error("Fetch Chat Error:", err);
                aiMsg.innerHTML = '❌ <em>Error communicating with Gemini AI assistant.</em>';
            }
            chatBox.scrollTop = chatBox.scrollHeight;
        }

        function openUploadModal() { document.getElementById('upload-modal').style.display = 'flex'; }
        function closeUploadModal() { document.getElementById('upload-modal').style.display = 'none'; }

        async function submitModalUpload() {
            const title = document.getElementById('m-title').value;
            const client = document.getElementById('m-client').value;
            const val = parseFloat(document.getElementById('m-value').value);
            const cat = document.getElementById('m-cat').value;
            const content = document.getElementById('m-content').value;

            closeUploadModal();

            const chatBox = document.getElementById('chat-box');
            const aiMsg = document.createElement('div');
            aiMsg.className = 'chat-bubble bubble-ai';
            aiMsg.innerHTML = '⚡ <em>Gemini AI performing automated document screening...</em>';
            chatBox.appendChild(aiMsg);

            try {
                const res = await fetch('/api/analyze', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        title: title,
                        client_name: client,
                        deal_value_usd: val,
                        product_category: cat,
                        sales_rep_name: 'Aditya Tripathi',
                        sales_head_approval: true,
                        raw_content: content
                    })
                });
                const data = await res.json();
                aiMsg.innerHTML = `✅ <strong>Proposal Submitted & Pre-Screened!</strong><br>Deal: <strong>${client}</strong> ($${(val/1e6).toFixed(1)}M)<br>AI Risk Score: <strong>${data.risk_analysis.overall_risk_score}/100</strong> (${data.risk_analysis.risk_level.toUpperCase()})<br>Recommendation: ${data.risk_analysis.ai_recommendation}`;
                
                await initApp();
                document.getElementById('policy-select').value = data.policy_id;
                onPolicySelected();
            } catch (err) {
                aiMsg.innerHTML = '❌ <em>Failed to submit policy proposal.</em>';
            }
        }

        window.onload = initApp;
    </script>
</body>
</html>
    """

# Vercel WSGI/ASGI handler
handler = app
