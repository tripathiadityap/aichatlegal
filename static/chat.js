// AIChatLegal - Frontend JavaScript
// Served as /api/chat.js to avoid Python string escaping issues

const sampleDeals = [
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
        console.log("Using sample deals:", err);
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
        opt.textContent = (p.policy_code || 'POL') + ' - ' + p.client_name + ' ($' + ((p.deal_value_usd || 0)/1e6).toFixed(1) + 'M)';
        sel.appendChild(opt);

        const item = document.createElement('div');
        item.style.padding = '10px';
        item.style.background = 'rgba(30, 41, 59, 0.5)';
        item.style.border = '1px solid rgba(255,255,255,0.06)';
        item.style.borderRadius = '8px';
        item.style.cursor = 'pointer';
        item.style.transition = 'all 0.2s';
        item.onmouseover = function() { item.style.borderColor = '#6366f1'; };
        item.onmouseout = function() { item.style.borderColor = 'rgba(255,255,255,0.06)'; };
        item.onclick = function() { sel.value = p.id; onPolicySelected(); };

        const badgeColor = p.status === 'flagged_high_risk' ? '#f43f5e' : (p.status === 'approved_with_riders' ? '#34d399' : '#f59e0b');
        const displayStatus = (p.status || 'Pending').replace(/_/g, ' ').toUpperCase();
        const dealSize = '$' + ((p.deal_value_usd || 0)/1e6).toFixed(1) + 'M';

        item.innerHTML = '<div style="font-weight:600;color:#f8fafc;">' + p.client_name + '</div>'
            + '<div style="display:flex;justify-content:space-between;font-size:12px;margin-top:4px;">'
            + '<span style="color:#6366f1;font-weight:600;">' + dealSize + '</span>'
            + '<span style="color:' + badgeColor + ';font-weight:600;">' + displayStatus + '</span>'
            + '</div>';
        listContainer.appendChild(item);
    });

    if (policiesData.length > 0 && !sel.value) {
        sel.value = policiesData[0].id;
        onPolicySelected();
    }
}

function onPolicySelected() {
    const id = document.getElementById('policy-select').value;
    const p = policiesData.find(function(x) { return x.id === id; });

    if (p) {
        document.getElementById('d-client').textContent = p.client_name;
        document.getElementById('d-value').textContent = '$' + ((p.deal_value_usd || 0)/1e6).toFixed(2) + 'M';

        const score = p.risk_score ? p.risk_score.overall_risk_score : 50;
        const scoreElem = document.getElementById('d-score');
        const statusText = (p.status || 'Review').replace(/_/g, ' ');
        scoreElem.textContent = score + ' / 100 (' + statusText + ')';
        scoreElem.style.color = score > 70 ? '#f43f5e' : (score > 40 ? '#f59e0b' : '#34d399');
        document.getElementById('d-rec').textContent = p.summary || (p.raw_content ? p.raw_content.substring(0, 150) + '...' : '');
    } else {
        document.getElementById('d-client').textContent = 'General Guidelines';
        document.getElementById('d-value').textContent = '$0.00';
        document.getElementById('d-score').textContent = 'Low Risk';
        document.getElementById('d-score').style.color = '#34d399';
        document.getElementById('d-rec').textContent = 'Select a specific policy upload to view breakdown.';
    }
}

function sendSuggestion(q) {
    document.getElementById('chat-input').value = q;
    submitChat();
}

function submitChat() {
    const input = document.getElementById('chat-input');
    const q = input.value.trim();
    if (!q) return;

    const chatBox = document.getElementById('chat-box');
    const role = document.getElementById('user-role').value;
    const policySel = document.getElementById('policy-select').value;

    const userMsg = document.createElement('div');
    userMsg.className = 'chat-bubble bubble-user';
    userMsg.textContent = q;
    chatBox.appendChild(userMsg);
    input.value = '';
    chatBox.scrollTop = chatBox.scrollHeight;

    const aiMsg = document.createElement('div');
    aiMsg.className = 'chat-bubble bubble-ai';
    aiMsg.innerHTML = '<em>⚡ Gemini AI searching policy vectors & regulatory precedent...</em>';
    chatBox.appendChild(aiMsg);
    chatBox.scrollTop = chatBox.scrollHeight;

    var controller = new AbortController();
    var timer = setTimeout(function() { controller.abort(); }, 28000);

    fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_role: role, user_query: q, policy_id: policySel || null }),
        signal: controller.signal
    })
    .then(function(res) { clearTimeout(timer); return res.json(); })
    .then(function(data) {
        var text = data.response || '';
        // Convert markdown-style formatting to HTML
        text = text.split('\n').join('<br>');
        text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        text = text.replace(/###\s(.+?)(<br>|$)/g, '<h4 style="margin:8px 0 4px 0;color:#a5b4fc;">$1</h4>');
        aiMsg.innerHTML = text;
        chatBox.scrollTop = chatBox.scrollHeight;
    })
    .catch(function(err) {
        clearTimeout(timer);
        console.error('Chat fetch error:', err);
        aiMsg.innerHTML = '<em>❌ Error communicating with Gemini AI assistant. Please try again.</em>';
        chatBox.scrollTop = chatBox.scrollHeight;
    });
}

function openUploadModal() { document.getElementById('upload-modal').style.display = 'flex'; }
function closeUploadModal() { document.getElementById('upload-modal').style.display = 'none'; }

function submitModalUpload() {
    const title = document.getElementById('m-title').value;
    const client = document.getElementById('m-client').value;
    const val = parseFloat(document.getElementById('m-value').value);
    const cat = document.getElementById('m-cat').value;
    const content = document.getElementById('m-content').value;

    closeUploadModal();

    const chatBox = document.getElementById('chat-box');
    const aiMsg = document.createElement('div');
    aiMsg.className = 'chat-bubble bubble-ai';
    aiMsg.innerHTML = '<em>⚡ Gemini AI performing automated document screening...</em>';
    chatBox.appendChild(aiMsg);

    fetch('/api/analyze', {
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
    })
    .then(function(res) { return res.json(); })
    .then(function(data) {
        const ra = data.risk_analysis;
        aiMsg.innerHTML = '<strong>✅ Proposal Submitted & Pre-Screened!</strong><br>'
            + 'Deal: <strong>' + client + '</strong> ($' + (val/1e6).toFixed(1) + 'M)<br>'
            + 'AI Risk Score: <strong>' + ra.overall_risk_score + '/100</strong> (' + ra.risk_level.toUpperCase() + ')<br>'
            + 'Recommendation: ' + ra.ai_recommendation;
        return initApp().then(function() {
            document.getElementById('policy-select').value = data.policy_id;
            onPolicySelected();
        });
    })
    .catch(function(err) {
        aiMsg.innerHTML = '<em>❌ Failed to submit policy proposal.</em>';
    });
}

window.onload = initApp;
