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

app = FastAPI(title="AIChatLegal API", version="2.7.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

# ── JS served as a Python string constant (no file I/O, no Vercel path issues) ──
CHAT_JS = r"""
const sampleDeals = [
    {id:"sample-1",policy_code:"POL-2026-8819",title:"Commercial Credit Override - Apex Global Logistics",client_name:"Apex Global Logistics Inc.",deal_value_usd:14500000,product_category:"Syndicated Revolving Credit",status:"pending_legal_review",summary:"Sales requested 45 bps rate discount and leverage ratio relaxation to 4.25x EBITDA for $14.5M syndicated facility.",risk_score:{overall_risk_score:68}},
    {id:"sample-2",policy_code:"POL-2026-7402",title:"Asset-Backed Financing Terms - Meridian Healthcare",client_name:"Meridian Healthcare Partners",deal_value_usd:38000000,product_category:"Asset Securitization",status:"approved_with_riders",summary:"Asset securitization deal with Medicare/Medicaid receivables pledge and HIPAA data processing disclosures.",risk_score:{overall_risk_score:25}},
    {id:"sample-3",policy_code:"POL-2026-9104",title:"Cross-Border Trade Line - Cyberdyne Systems",client_name:"Cyberdyne Systems LLC",deal_value_usd:62000000,product_category:"Structured Trade Finance",status:"flagged_high_risk",summary:"Unconfirmed LC proposal with OFAC liability cap request. High regulatory risk requiring Legal & Compliance intervention.",risk_score:{overall_risk_score:88}}
];
let policiesData = [...sampleDeals];

async function initApp() {
    populatePoliciesDropdown();
    try {
        const res = await fetch('/api/policies');
        const live = await res.json();
        if (Array.isArray(live) && live.length > 0) { policiesData = live; populatePoliciesDropdown(); }
    } catch(e) { console.log('Using sample deals'); }
}

function populatePoliciesDropdown() {
    const sel = document.getElementById('policy-select');
    const list = document.getElementById('policies-list');
    sel.innerHTML = '<option value="">-- General Banking Regulations --</option>';
    list.innerHTML = '';
    policiesData.forEach(function(p) {
        const opt = document.createElement('option');
        opt.value = p.id;
        opt.textContent = (p.policy_code||'POL') + ' - ' + p.client_name + ' ($' + ((p.deal_value_usd||0)/1e6).toFixed(1) + 'M)';
        sel.appendChild(opt);
        const item = document.createElement('div');
        item.style.cssText = 'padding:10px;background:rgba(30,41,59,.5);border:1px solid rgba(255,255,255,.06);border-radius:8px;cursor:pointer;transition:all .2s;';
        item.onmouseover = function() { item.style.borderColor='#6366f1'; };
        item.onmouseout  = function() { item.style.borderColor='rgba(255,255,255,.06)'; };
        item.onclick     = function() { sel.value = p.id; onPolicySelected(); };
        const bc = p.status==='flagged_high_risk'?'#f43f5e':(p.status==='approved_with_riders'?'#34d399':'#f59e0b');
        const ds = (p.status||'Pending').replace(/_/g,' ').toUpperCase();
        const dv = '$'+((p.deal_value_usd||0)/1e6).toFixed(1)+'M';
        item.innerHTML = '<div style="font-weight:600;color:#f8fafc;">'+p.client_name+'</div>'
            +'<div style="display:flex;justify-content:space-between;font-size:12px;margin-top:4px;">'
            +'<span style="color:#6366f1;font-weight:600;">'+dv+'</span>'
            +'<span style="color:'+bc+';font-weight:600;">'+ds+'</span></div>';
        list.appendChild(item);
    });
    if (policiesData.length > 0 && !sel.value) { sel.value = policiesData[0].id; onPolicySelected(); }
}

function onPolicySelected() {
    const id = document.getElementById('policy-select').value;
    const p  = policiesData.find(function(x) { return x.id === id; });
    if (p) {
        document.getElementById('d-client').textContent = p.client_name;
        document.getElementById('d-value').textContent  = '$'+((p.deal_value_usd||0)/1e6).toFixed(2)+'M';
        const score = p.risk_score ? p.risk_score.overall_risk_score : 50;
        const el = document.getElementById('d-score');
        el.textContent  = score+' / 100 ('+(p.status||'Review').replace(/_/g,' ')+')';
        el.style.color  = score>70?'#f43f5e':(score>40?'#f59e0b':'#34d399');
        document.getElementById('d-rec').textContent = p.summary||(p.raw_content?p.raw_content.substring(0,150)+'...':'');
    } else {
        document.getElementById('d-client').textContent = 'General Guidelines';
        document.getElementById('d-value').textContent  = '$0.00';
        const el = document.getElementById('d-score');
        el.textContent = 'Low Risk'; el.style.color = '#34d399';
        document.getElementById('d-rec').textContent = 'Select a policy to view breakdown.';
    }
}

function sendSuggestion(q) { document.getElementById('chat-input').value = q; submitChat(); }

function submitChat() {
    const input   = document.getElementById('chat-input');
    const q       = input.value.trim();
    if (!q) return;
    const chatBox = document.getElementById('chat-box');
    const role    = document.getElementById('user-role').value;
    const pid     = document.getElementById('policy-select').value;

    const userDiv = document.createElement('div');
    userDiv.className = 'bubble user';
    userDiv.textContent = q;
    chatBox.appendChild(userDiv);
    input.value = '';
    chatBox.scrollTop = chatBox.scrollHeight;

    const aiDiv = document.createElement('div');
    aiDiv.className = 'bubble ai';
    aiDiv.innerHTML = '<em>&#9889; Gemini AI analysing policy vectors...</em>';
    chatBox.appendChild(aiDiv);
    chatBox.scrollTop = chatBox.scrollHeight;

    const ctrl  = new AbortController();
    const timer = setTimeout(function() { ctrl.abort(); }, 28000);

    fetch('/api/chat', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({user_role:role, user_query:q, policy_id:pid||null}),
        signal: ctrl.signal
    })
    .then(function(r) { clearTimeout(timer); return r.json(); })
    .then(function(data) {
        var t = (data.response || '').split('\n').join('<br>');
        t = t.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        t = t.replace(/###\s(.+?)(<br>|$)/g, '<h4 style="margin:6px 0 3px;color:#a5b4fc;">$1</h4>');
        aiDiv.innerHTML = t;
        chatBox.scrollTop = chatBox.scrollHeight;
    })
    .catch(function(err) {
        clearTimeout(timer);
        aiDiv.innerHTML = '<em>&#10060; Error contacting Gemini. Please retry.</em>';
        chatBox.scrollTop = chatBox.scrollHeight;
    });
}

function openUploadModal()  { document.getElementById('upload-modal').style.display='flex'; }
function closeUploadModal() { document.getElementById('upload-modal').style.display='none'; }

function submitModalUpload() {
    const title   = document.getElementById('m-title').value;
    const client  = document.getElementById('m-client').value;
    const val     = parseFloat(document.getElementById('m-value').value);
    const cat     = document.getElementById('m-cat').value;
    const content = document.getElementById('m-content').value;
    closeUploadModal();
    const chatBox = document.getElementById('chat-box');
    const aiDiv   = document.createElement('div');
    aiDiv.className = 'bubble ai';
    aiDiv.innerHTML = '<em>&#9889; Running Gemini pre-screening...</em>';
    chatBox.appendChild(aiDiv);
    fetch('/api/analyze',{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({title:title,client_name:client,deal_value_usd:val,product_category:cat,sales_rep_name:'Aditya Tripathi',sales_head_approval:true,raw_content:content})})
    .then(function(r){return r.json();})
    .then(function(data){
        const ra=data.risk_analysis;
        aiDiv.innerHTML='<strong>&#10003; Proposal Submitted!</strong><br>Deal: <strong>'+client+'</strong> ($'+(val/1e6).toFixed(1)+'M)<br>Risk Score: <strong>'+ra.overall_risk_score+'/100</strong> ('+ra.risk_level.toUpperCase()+')<br>'+ra.ai_recommendation;
        initApp().then(function(){document.getElementById('policy-select').value=data.policy_id;onPolicySelected();});
    })
    .catch(function(){aiDiv.innerHTML='<em>&#10060; Failed to submit proposal.</em>';});
}

document.addEventListener('DOMContentLoaded', function() {
    initApp();
    document.getElementById('chat-input').addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submitChat(); }
    });
});
"""


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
    return Response(content=CHAT_JS, media_type="application/javascript")

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
            raise HTTPException(status_code=404, detail="Sample policy")
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
        return {"response": "Gemini AI: I am ready to assist with banking legal inquiries."}

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
    <title>AIChatLegal | Enterprise Bank Policy &amp; Legal AI Advisor</title>
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
    <style>
        :root{--bg:#070a12;--panel:rgba(15,23,42,.75);--border:rgba(255,255,255,.08);--indigo:#6366f1;--amber:#f59e0b;--text:#f8fafc;--muted:#94a3b8;}
        *{box-sizing:border-box;}
        body{margin:0;background:var(--bg);color:var(--text);font-family:'DM Sans',sans-serif;height:100vh;display:flex;flex-direction:column;overflow:hidden;}
        .navbar{background:linear-gradient(135deg,#0f172a,#1e1b4b,#0f172a);border-bottom:1px solid var(--border);padding:14px 24px;display:flex;justify-content:space-between;align-items:center;}
        .brand{display:flex;align-items:center;gap:12px;font-weight:700;font-size:20px;}
        .pill{background:rgba(16,185,129,.15);color:#34d399;border:1px solid rgba(16,185,129,.3);padding:4px 12px;border-radius:20px;font-size:12px;font-family:'JetBrains Mono',monospace;display:flex;align-items:center;gap:6px;}
        .dot{width:8px;height:8px;background:#34d399;border-radius:50%;animation:pulse 2s infinite;}
        @keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
        .app{display:flex;flex:1;overflow:hidden;}
        .sidebar{width:300px;background:var(--panel);border-right:1px solid var(--border);padding:18px;display:flex;flex-direction:column;gap:16px;overflow-y:auto;}
        .ctrl{display:flex;flex-direction:column;gap:6px;}
        .lbl{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.6px;color:var(--muted);}
        select,input,textarea{background:#1e293b;border:1px solid rgba(255,255,255,.1);color:white;padding:10px 12px;border-radius:8px;font-family:inherit;font-size:14px;width:100%;outline:none;transition:border-color .2s;}
        select:focus,input:focus,textarea:focus{border-color:var(--indigo);}
        .workspace{flex:1;display:flex;flex-direction:column;background:rgba(10,15,26,.5);}
        .messages{flex:1;padding:20px 24px;overflow-y:auto;display:flex;flex-direction:column;gap:14px;}
        .bubble{max-width:80%;padding:13px 17px;border-radius:12px;line-height:1.55;font-size:15px;animation:fadein .2s ease;}
        @keyframes fadein{from{opacity:0;transform:translateY(5px)}to{opacity:1;transform:translateY(0)}}
        .bubble.user{background:#1e293b;align-self:flex-end;border:1px solid rgba(255,255,255,.08);border-bottom-right-radius:2px;}
        .bubble.ai{background:rgba(30,41,59,.85);align-self:flex-start;border-left:3px solid var(--indigo);border-bottom-left-radius:2px;}
        .chips{display:flex;gap:8px;padding:0 24px 10px;overflow-x:auto;scrollbar-width:none;}
        .chip{background:rgba(30,41,59,.7);border:1px solid rgba(255,255,255,.1);color:#cbd5e1;padding:7px 14px;border-radius:20px;font-size:13px;cursor:pointer;white-space:nowrap;transition:all .2s;font-family:inherit;}
        .chip:hover{background:rgba(99,102,241,.25);border-color:var(--indigo);color:white;}
        .inputbar{padding:14px 24px;background:#0f172a;border-top:1px solid var(--border);display:flex;gap:10px;}
        .inputbar input{flex:1;height:44px;}
        .sendbtn{background:var(--indigo);color:white;border:none;padding:0 22px;border-radius:8px;font-weight:700;cursor:pointer;height:44px;font-size:15px;font-family:inherit;transition:background .2s;}
        .sendbtn:hover{background:#4f46e5;}
        .detail{width:280px;background:var(--panel);border-left:1px solid var(--border);padding:18px;display:flex;flex-direction:column;gap:14px;overflow-y:auto;}
        .card{background:rgba(30,41,59,.6);border:1px solid var(--border);border-radius:10px;padding:13px;}
        .bigval{font-size:21px;font-weight:700;font-family:'JetBrains Mono',monospace;margin-top:4px;}
        .modal{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.75);backdrop-filter:blur(4px);z-index:1000;justify-content:center;align-items:center;}
        .modalbox{background:#0f172a;border:1px solid var(--indigo);border-radius:12px;padding:24px;width:500px;max-width:90%;}
    </style>
</head>
<body>
<div class="navbar">
    <div class="brand"><span>&#127963;</span><span>AIChatLegal</span><span style="font-size:12px;color:var(--muted);font-weight:400;">| Enterprise Bank Policy Advisory</span></div>
    <div style="display:flex;gap:12px;align-items:center;">
        <div class="pill"><div class="dot"></div><span>Supabase DB &amp; Gemini AI Connected</span></div>
        <button onclick="openUploadModal()" class="chip" style="background:var(--indigo);color:white;border:none;">+ Upload Deal Proposal</button>
    </div>
</div>
<div class="app">
    <div class="sidebar">
        <div class="ctrl">
            <div class="lbl">&#128100; Active Persona</div>
            <select id="user-role">
                <option value="sales_head">&#128084; Sales Repo Head (VP)</option>
                <option value="sales_rep">&#128188; Sales Lead / Deal Officer</option>
                <option value="legal_counsel">&#9878; Senior Legal Counsel</option>
                <option value="compliance_officer">&#128737; Compliance Officer</option>
            </select>
        </div>
        <div class="ctrl">
            <div class="lbl">&#128203; Policy / Deal Context (RAG)</div>
            <select id="policy-select" onchange="onPolicySelected()">
                <option value="">-- General Banking Regulations --</option>
            </select>
        </div>
        <hr style="border-color:var(--border);margin:0;">
        <div class="ctrl">
            <div class="lbl">&#9889; Live Bank Policies</div>
            <div id="policies-list" style="display:flex;flex-direction:column;gap:8px;font-size:13px;"></div>
        </div>
    </div>
    <div class="workspace">
        <div class="messages" id="chat-box">
            <div class="bubble ai">&#128075; Welcome to <strong>AIChatLegal</strong> &mdash; your Gemini-powered Bank Legal &amp; Regulatory Assistant.<br><br>Select an active deal from the sidebar to ground our RAG analysis, or ask any question about credit overrides, SEC/OCC compliance, or contract riders!</div>
        </div>
        <div class="chips">
            <button class="chip" onclick="sendSuggestion('What contract riders are required by legal for this deal?')">&#128203; Required Contract Riders</button>
            <button class="chip" onclick="sendSuggestion('Summarize key legal risk vectors and covenant waivers.')">&#9888; Summarize Legal Risk</button>
            <button class="chip" onclick="sendSuggestion('What OFAC and Basel III compliance steps are needed?')">&#127961; OFAC &amp; Basel III</button>
            <button class="chip" onclick="sendSuggestion('How does AIChatLegal ensure banking security and PII masking?')">&#128274; Banking Security</button>
        </div>
        <div class="inputbar">
            <input type="text" id="chat-input" placeholder="Ask Gemini AI about policy terms, legal riders, or regulatory compliance...">
            <button class="sendbtn" id="send-btn" onclick="submitChat()">Send &#9889;</button>
        </div>
    </div>
    <div class="detail">
        <div class="lbl">&#128202; Active Deal Overview</div>
        <div class="card"><div style="font-size:11px;color:var(--muted);">CLIENT CORPORATE ENTITY</div><div id="d-client" style="font-weight:600;font-size:15px;margin-top:4px;">Apex Global Logistics Inc.</div></div>
        <div class="card"><div style="font-size:11px;color:var(--muted);">DEAL CAPITAL VOLUME</div><div id="d-value" class="bigval">$14.50M</div></div>
        <div class="card"><div style="font-size:11px;color:var(--muted);">AI RISK SCORE</div><div id="d-score" class="bigval" style="color:var(--amber);">68 / 100</div></div>
        <div class="card" style="flex:1;overflow-y:auto;"><div style="font-size:11px;color:var(--muted);margin-bottom:6px;">RECOMMENDED LEGAL ACTION</div><div id="d-rec" style="font-size:13px;line-height:1.45;color:#cbd5e1;">Sales requested 45 bps rate discount and leverage relaxation to 4.25x EBITDA. Requires Schedule 14B Covenant Rider.</div></div>
    </div>
</div>
<div class="modal" id="upload-modal">
    <div class="modalbox">
        <h3 style="margin-top:0;">&#128640; Submit Deal Proposal for Gemini Pre-Screening</h3>
        <div class="ctrl" style="margin-bottom:12px;"><div class="lbl">Proposal Title*</div><input type="text" id="m-title" value="Commercial Credit Override - Apex Global Logistics"></div>
        <div class="ctrl" style="margin-bottom:12px;"><div class="lbl">Client Name*</div><input type="text" id="m-client" value="Apex Global Logistics Inc."></div>
        <div style="display:flex;gap:12px;margin-bottom:12px;">
            <div class="ctrl" style="flex:1;"><div class="lbl">Deal Value ($)*</div><input type="number" id="m-value" value="25000000"></div>
            <div class="ctrl" style="flex:1;"><div class="lbl">Category*</div><select id="m-cat"><option value="Commercial Credit Override">Credit Override</option><option value="Syndicated Revolving Credit">Syndicated Credit</option><option value="Asset Securitization">Asset Securitization</option></select></div>
        </div>
        <div class="ctrl" style="margin-bottom:16px;"><div class="lbl">Policy Override Clauses*</div><textarea id="m-content" rows="4">SECTION 3.1: Client requests 45 bps rate discount on SOFR margin. SECTION 8.2: Maximum leverage ratio relaxed to 4.0x EBITDA.</textarea></div>
        <div style="display:flex;justify-content:flex-end;gap:10px;">
            <button class="chip" onclick="closeUploadModal()">Cancel</button>
            <button class="chip" onclick="submitModalUpload()" style="background:var(--indigo);color:white;border:none;">Run Gemini Screening &#9889;</button>
        </div>
    </div>
</div>
<script src="/api/static/chat.js"></script>
</body>
</html>"""

handler = app
