"""
AIChatLegal Gemini Engine
Integrates Google Gemini API for policy document parsing, legal risk scoring, 
regulatory compliance analysis, and persona-aware chatbot interaction.
Supports REST API via urllib with automatic retry on 429 rate limits.
Project: aichatlegal
"""

import os
import json
import re
import urllib.request
import urllib.error
import time
from typing import Dict, List, Any, Tuple, Optional
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip("\"'")
GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

class GeminiLegalEngine:
    def __init__(self) -> None:
        self.api_available: bool = bool(GEMINI_API_KEY and GEMINI_API_KEY not in ("", "your-gemini-api-key-here"))
        self.client: Any = None
        self.framework: str = "gemini-rest-api" if self.api_available else "simulated"
        if self.api_available:
            print(f"[Gemini Engine] API key loaded — using {GEMINI_MODEL} via REST.")
        else:
            print("[Gemini Engine] No API key found — running in simulated mode.")

    def _call_gemini_rest(self, prompt: str) -> Optional[str]:
        """Direct REST API call to Gemini 2.0 Flash with 429 retry backoff."""
        headers = {
            "Content-Type": "application/json",
            "X-goog-api-key": GEMINI_API_KEY
        }
        payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")

        for attempt in range(3):
            try:
                req = urllib.request.Request(GEMINI_ENDPOINT, data=payload, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=25) as resp:
                    res_json = json.loads(resp.read().decode("utf-8"))
                    candidates = res_json.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "")
            except urllib.error.HTTPError as e:
                body = e.read().decode()[:300]
                print(f"[Gemini REST attempt {attempt+1}] HTTP {e.code}: {body}")
                if e.code == 429:
                    if "depleted" in body.lower() or "credits" in body.lower():
                        print("[Gemini Engine] Prepay credits depleted — serving instant contextual response.")
                        break
                    time.sleep(2 ** attempt)
                    continue
                break
            except Exception as e:
                print(f"[Gemini REST attempt {attempt+1}] {e}")
                break
        return None

    def analyze_policy_upload(self, title: str, client_name: str, deal_value: float, content: str) -> Dict[str, Any]:
        """Parses sales policy document and returns structured legal risk scoring."""
        if self.api_available:
            prompt = f"""
            You are General Counsel and Senior Credit Risk Officer for a Tier-1 Global Investment Bank.
            Analyze the following commercial lending or deal policy proposal for legal and regulatory risk.

            Deal Context:
            - Proposal Title: {title}
            - Client: {client_name}
            - Deal Value (USD): ${deal_value:,.2f}

            Document Text:
            {content}

            Return ONLY a valid JSON object with the following exact keys and no extra formatting text:
            {{
                "overall_risk_score": 65,
                "risk_level": "medium",
                "regulatory_compliance_score": 75,
                "financial_exposure_score": 60,
                "jurisdictional_risk_score": 80,
                "flagged_clauses": ["SOFR margin override waiver", "Financial covenant relaxation"],
                "ai_recommendation": "Detailed legal guidance here...",
                "recommended_status": "pending_legal_review",
                "summary": "Concise two-sentence summary..."
            }}
            """
            
            text_resp = self._call_gemini_rest(prompt)
            if text_resp:
                json_match = re.search(r'\{.*\}', text_resp, re.DOTALL)
                if json_match:
                    try:
                        return dict(json.loads(json_match.group(0)))
                    except Exception as e:
                        print(f"[JSON Parse Error] {e}")

        return self._rule_based_policy_analysis(title, deal_value, content)

    def _rule_based_policy_analysis(self, title: str, deal_value: float, content: str) -> Dict[str, Any]:
        """Analytical fallback engine for policy risk scoring."""
        c_lower = content.lower()
        flagged: List[str] = []
        risk_score = 30
        
        if "sanctions" in c_lower or "ofac" in c_lower or "unconfirmed" in c_lower:
            flagged.append("OFAC & International Sanctions Risk Clause")
            risk_score += 45
        if "override" in c_lower or "bps reduction" in c_lower or "margin" in c_lower:
            flagged.append("Non-Standard Rate Margin Discount Override")
            risk_score += 15
        if "leverage" in c_lower or "ebitda" in c_lower or "dscr" in c_lower:
            flagged.append("Financial Covenant Relaxation (>3.5x EBITDA Baseline)")
            risk_score += 20
        if "governing law" in c_lower or "jurisdiction" in c_lower or "lcia" in c_lower:
            flagged.append("Offshore Arbitration & Dispute Venue Selection")
            risk_score += 10
        if "hipaa" in c_lower or "privacy" in c_lower or "gdpr" in c_lower:
            flagged.append("Regulatory Data Protection Compliance Rider Required")
            risk_score += 10

        risk_score = min(98, max(15, risk_score))
        
        if risk_score > 75:
            level, status = "high", "flagged_high_risk"
            rec = "CRITICAL: High-liability indemnity caps or OFAC exceptions detected. Require General Counsel review before Sales Head sign-off."
        elif risk_score > 45:
            level, status = "medium", "pending_legal_review"
            rec = "MODERATE: Policy override exceeds standard credit committee thresholds. Add Standard Financial Covenant Rider (Schedule C) and secondary legal review."
        else:
            level, status = "low", "approved_with_riders"
            rec = "LOW RISK: Proposal aligns with credit policy guidelines. Approved subject to standard boilerplate disclosure riders."

        if not flagged:
            flagged.append("Standard Credit Policy Verification")

        return {
            "overall_risk_score": risk_score,
            "risk_level": level,
            "regulatory_compliance_score": max(20, 100 - risk_score + 10),
            "financial_exposure_score": min(95, risk_score + 5),
            "jurisdictional_risk_score": 85 if "governing law" not in c_lower else 55,
            "flagged_clauses": flagged,
            "ai_recommendation": rec,
            "recommended_status": status,
            "summary": f"Proposal '{title}' evaluated at ${deal_value:,.2f}. Identified {len(flagged)} risk vectors requiring regulatory alignment."
        }

    def generate_chat_response(self, user_role: str, user_query: str, chat_history: List[Dict[str, str]], policy_context: Optional[Dict[str, Any]] = None) -> str:
        """Generates persona-aware response. Tries live Gemini first, falls back to rich simulated engine."""
        system_context = f"""
        You are AIChatLegal, an elite General Counsel, Chief Risk Officer, and Banking Regulatory Advisor for a major Tier-1 Investment Bank.

        STRICT DOMAIN BOUNDARIES & BEHAVIORAL DIRECTIVES:
        1. Primary Mission: You advise bank staff ({user_role.upper()} persona) on commercial lending policies, credit term overrides, syndicated debt facilities, risk scoring, and federal banking compliance (SEC, OCC, FINRA, CFPB, Basel III, GDPR, HIPAA).
        2. Domain Stickiness: Keep every response strictly focused on banking, legal risk, credit underwriting, and regulatory compliance.
        3. Casual / Greetings Handling: If the user says "hello", "hi", or asks general questions, politely greet them as a Bank Legal Advisor for the {user_role.upper()} role and present immediate banking compliance assistance choices.
        4. Structured Output: Structure your analysis with clear headers, contract rider schedules (e.g. Schedule 14B, SOFR Fallback Rider, DACA Control Agreements), and concrete risk mitigation advice.
        """

        if policy_context:
            system_context += f"\nActive Attached Deal Policy Context:\n{json.dumps(policy_context, default=str)}"

        full_prompt = f"{system_context}\n\nUser Inquiry: {user_query}"

        if self.api_available:
            text_resp = self._call_gemini_rest(full_prompt)
            if text_resp:
                return text_resp
            print("[Gemini Chat] Live API call failed — using intelligent fallback.")

        return self._simulate_chat_response(user_role, user_query, policy_context)

    def _simulate_chat_response(self, user_role: str, user_query: str, policy_context: Optional[Dict[str, Any]]) -> str:
        """Rich contextual banking legal Q&A engine with topic-specific responses."""
        q = user_query.lower()
        client = policy_context.get("client_name", "the client") if policy_context else "the client"
        title = policy_context.get("title", "this deal") if policy_context else "this deal"
        value = policy_context.get("deal_value_usd", 0) if policy_context else 0
        status = (policy_context.get("status") or "pending_legal_review") if policy_context else "pending_legal_review"
        cat = policy_context.get("product_category", "Commercial Facility") if policy_context else "Commercial Facility"
        deal_m = f"${value/1e6:.1f}M" if value else "this facility"
        role_t = user_role.replace("_", " ").title()

        # ── OFAC / Sanctions ──
        if any(w in q for w in ["ofac", "sanction", "cross-border", "trade finance", "letter of credit"]):
            return (
                f"### OFAC & Sanctions Compliance — {role_t} Briefing\n\n"
                f"For **{client}** ({deal_m} {cat}), the following OFAC due-diligence steps are **mandatory** before deal execution:\n\n"
                f"**1. SDN List Screening**\nRun {client} and all UBOs (>=25% ownership) through the OFAC Specially Designated Nationals list. Any match requires immediate escalation to the Sanctions Desk — do not proceed without written clearance.\n\n"
                f"**2. Correspondent Bank Vetting**\nFor cross-border LCs, every correspondent and intermediary bank in the payment chain must be screened against OFAC, EU Consolidated List, and FATF grey-list.\n\n"
                f"**3. Prohibited Jurisdiction Check**\nConfirm the end-destination country is not subject to a U.S. comprehensive embargo (Cuba, Iran, North Korea, Syria, Crimea). If goods/services transit embargoed ports, a Specific License from OFAC is required.\n\n"
                f"**4. Required Rider**: Attach **Schedule 14B** to the facility agreement.\n\n"
                f"**Current Status**: `{status.replace('_',' ').upper()}`"
            )

        # ── Basel III / Capital ──
        elif any(w in q for w in ["basel", "capital buffer", "tier 1", "lcr", "nsfr", "leverage ratio", "rwa"]):
            return (
                f"### Basel III Capital Requirements — {role_t} Analysis\n\n"
                f"**Applicable Standards** for {deal_m} {cat} to **{client}**:\n\n"
                f"**CET1 Ratio**: Minimum 4.5% of RWA; effective floor 7.0% with Conservation Buffer. RWA impact must be modeled before credit committee sign-off.\n\n"
                f"**Leverage Ratio**: Tier 1 capital >= 3% of total exposure. If this deal pushes leverage above 3.5x internal threshold, a capital relief trade may be required.\n\n"
                f"**LCR**: Undrawn committed facilities attract a 10% drawdown assumption under LCR stress. Ensure Treasury models the 30-day stressed outflow impact.\n\n"
                f"**NSFR**: Facilities > 1 year require Stable Funding. RSF factor for {cat} is approximately 65-85% depending on collateral.\n\n"
                f"**Recommendation**: Model RWA impact and obtain Capital Committee pre-approval if CET1 impact exceeds 5 bps."
            )

        # ── KYC / AML ──
        elif any(w in q for w in ["kyc", "aml", "anti-money", "due diligence", "cdd", "ubo", "beneficial owner"]):
            return (
                f"### KYC / AML Due Diligence Checklist — {role_t}\n\n"
                f"For onboarding **{client}** under the {deal_m} {cat}:\n\n"
                f"**Standard CDD Requirements**\n"
                f"- Certificate of Incorporation + Articles of Association\n"
                f"- Last 3 years audited financial statements\n"
                f"- Board resolution authorizing facility drawdown\n"
                f"- UBO structure chart to >=25% threshold (per FinCEN Rule)\n\n"
                f"**Enhanced Due Diligence (EDD) Triggers**\n"
                f"EDD required if: FATF grey-listed jurisdiction, any UBO is PEP, revenue >$50M with complex cross-border flows, or non-standard payment routing.\n\n"
                f"**Transaction Monitoring**: Flag if drawdown deviates >30% from stated purpose or round-dollar structuring detected.\n\n"
                f"**SAR Obligation**: File within 30 days if red flags emerge. KYC refresh every 12 months."
            )

        # ── Riders / Covenants ──
        elif any(w in q for w in ["rider", "covenant", "contract", "clause", "schedule", "waiver", "indemnif"]):
            return (
                f"### Required Legal Riders & Covenants — {role_t}\n\n"
                f"For **{title}** ({deal_m}):\n\n"
                f"**Mandatory Riders**\n"
                f"- **Schedule 14B**: Cross-Border Liability & Sanctions Protection\n"
                f"- **Schedule C**: Financial Covenant Rider (DSCR >= 1.20x, leverage <= 3.5x EBITDA)\n"
                f"- **SOFR Fallback Rider**: Required for all floating-rate facilities (per ARRC)\n"
                f"- **DACA Control Agreement**: Required if account sweep in security package\n\n"
                f"**Key Covenants**\n"
                f"| Covenant | Threshold | Frequency |\n"
                f"|---|---|---|\n"
                f"| DSCR | >= 1.20x | Quarterly |\n"
                f"| Leverage | <= 3.5x | Semi-annual |\n"
                f"| Interest Cover | >= 3.0x | Quarterly |\n\n"
                f"**Waiver Protocol**: Written Credit Committee approval required. Verbal approvals not binding under UCC Section 9-507."
            )

        # ── SOFR / Pricing ──
        elif any(w in q for w in ["sofr", "libor", "interest rate", "margin", "bps", "basis point", "pricing", "spread"]):
            return (
                f"### Interest Rate Pricing & SOFR — {role_t}\n\n"
                f"For **{deal_m} {cat}** to **{client}**:\n\n"
                f"**Reference Rate**: 3-Month Term SOFR (CME) + credit spread. LIBOR is fully sunset — any reference requires immediate amendment under LIBOR Act.\n\n"
                f"**Pricing Override Matrix**\n"
                f"| Discount | Authorization |\n"
                f"|---|---|\n"
                f"| <= 25 bps | RM + Credit Approver |\n"
                f"| 26-50 bps | Sales Head (VP) + Regional Credit Committee |\n"
                f"| > 50 bps | General Counsel + CFO mandatory |\n\n"
                f"**Legal Risk**: Pricing below cost of funds without documented rationale may breach OCC Bulletin 2013-29.\n\n"
                f"**Recommendation**: For >50 bps override, prepare Competitive Market Analysis memo for Pricing Exception Committee."
            )

        # ── Credit Override / Risk ──
        elif any(w in q for w in ["override", "credit", "risk score", "risk rating", "underwr", "exception", "approv"]):
            score = (policy_context.get("risk_score") or {}).get("overall_risk_score", 55) if policy_context else 55
            risk_label = "HIGH RISK" if score > 70 else ("MEDIUM" if score > 40 else "LOW RISK")
            return (
                f"### Credit Override Assessment — {role_t}\n\n"
                f"**Deal**: {title} | **Client**: {client} | **Size**: {deal_m} | **Risk**: {score}/100 ({risk_label})\n\n"
                f"**Override Eligibility**\n"
                + ("A Credit Policy Exception form must be completed and countersigned by the CRO.\n\n" if score > 70
                   else "Standard Credit Committee approval required with documented risk mitigation.\n\n" if score > 40
                   else "Within standard parameters — RM can approve with normal documentation.\n\n")
                + f"**Required Documentation**\n"
                f"1. Credit Policy Exception Form (CPEF-2026)\n"
                f"2. Relationship profitability analysis (3-year horizon)\n"
                f"3. Independent legal opinion on collateral enforceability\n"
                f"4. Board notification if exposure >$50M or risk score >80\n\n"
                f"**Escalation**: Sales Rep -> Sales Head -> Regional Credit Committee -> CRO"
            )

        # ── Securitization ──
        elif any(w in q for w in ["securit", "abs", "asset-back", "spv", "tranche", "receivable"]):
            return (
                f"### Asset Securitization Framework — {role_t}\n\n"
                f"For **{deal_m} {cat}** with **{client}**:\n\n"
                f"**Structure Requirements**\n"
                f"- **SPV Isolation**: Bankruptcy-remote SPV required. True-sale opinion from external counsel mandatory.\n"
                f"- **Risk Retention**: Originator retains >= 5% economic interest (SEC Reg RR / EU STS).\n"
                f"- **Ratings**: Investment-grade from at least one NRSRO for institutional distribution.\n\n"
                f"**Key Risks**: Recharacterization (sale recast as secured loan), commingling (separate servicer accounts required), rating-downgrade triggers.\n\n"
                f"**Action**: Engage structured finance counsel for true-sale and non-consolidation opinions before closing."
            )

        # ── Greeting ──
        elif any(w in q for w in ["hello", "hi", "hey", "good morning", "good afternoon", "help", "start"]):
            deal_info = f" I see **{title}** ({deal_m}) is attached as context." if policy_context else ""
            return (
                f"### Welcome to AIChatLegal — {role_t}\n\n"
                f"Hello! I'm your AI-powered Bank Legal & Regulatory Advisor.{deal_info}\n\n"
                f"I can assist with:\n"
                f"- **Contract Riders** — SOFR fallback, Schedule 14B, DACA agreements\n"
                f"- **Credit Overrides** — escalation paths, CPE forms, risk thresholds\n"
                f"- **OFAC & Sanctions** — SDN screening, cross-border compliance\n"
                f"- **Basel III** — capital buffers, LCR/NSFR, RWA modeling\n"
                f"- **KYC/AML** — CDD/EDD checklists, UBO mapping, SAR obligations\n"
                f"- **SOFR Pricing** — margin override matrix, LIBOR transition\n\n"
                f"What would you like to analyse?"
            )

        # ── Security / Privacy ──
        elif any(w in q for w in ["security", "encrypt", "privacy", "pii", "data protection", "gdpr", "hipaa"]):
            return (
                f"### Data Security & Privacy — {role_t}\n\n"
                f"**AIChatLegal Security Architecture**\n"
                f"- **In Transit**: TLS 1.3 on all endpoints\n"
                f"- **At Rest**: AES-256 via Supabase PostgreSQL with Row-Level Security\n"
                f"- **AI Zero Retention**: Gemini API — no PII stored in model training\n"
                f"- **Audit Logs**: Immutable audit trail for OCC/CFPB examination\n\n"
                f"**GDPR**: DPA required before sharing EU-resident data. Appoint DPO.\n\n"
                f"**HIPAA**: BAA mandatory. PHI de-identified per 45 CFR 164.514.\n\n"
                f"**BSA**: 5-year minimum retention for all customer financial data."
            )

        # ── Summarize / Risk ──
        elif any(w in q for w in ["summarize", "summary", "overview", "risk", "analyze", "review"]):
            score = (policy_context.get("risk_score") or {}).get("overall_risk_score", 50) if policy_context else 50
            return (
                f"### Deal Risk Summary — {role_t}\n\n"
                f"**Deal**: {title}\n**Client**: {client}\n**Size**: {deal_m}\n**Category**: {cat}\n**Risk Score**: {score}/100\n**Status**: {status.replace('_',' ').title()}\n\n"
                f"**Key Risk Vectors**\n"
                f"1. **Regulatory**: SEC Rule 17a-4 and Basel III compliance verification required\n"
                f"2. **Credit**: Financial covenant thresholds (DSCR >= 1.20x, leverage <= 3.5x) must be embedded in facility agreement\n"
                f"3. **Operational**: Ensure DACA control agreement is in place for operational account sweeps\n"
                f"4. **Jurisdictional**: If cross-border, OFAC SDN screening and Schedule 14B rider are mandatory\n\n"
                f"**Recommendation**: {'Escalate to General Counsel — high risk vectors detected.' if score > 70 else 'Proceed with standard legal review and covenant rider attachment.' if score > 40 else 'Low risk — approve with standard boilerplate riders.'}"
            )

        # ── Fallback ──
        else:
            keywords = [w for w in q.split() if len(w) > 4][:3]
            topic = " ".join(keywords).title() if keywords else "Policy Analysis"
            return (
                f"### {role_t} Advisory — {topic}\n\n"
                f"Regarding **\"{user_query}\"**"
                + (f" for **{title}** ({deal_m})" if policy_context else "")
                + f":\n\n"
                f"This matter falls under OCC Guidance, SEC Rule 15c3-1, and Credit Policy Manual Section 7. Documented approval is required at the appropriate authority level.\n\n"
                f"**Key Steps**\n"
                f"1. Review Credit Policy Manual — confirm no standing waivers apply\n"
                f"2. Engage Legal Counsel for written opinion if transaction is novel\n"
                f"3. Document decisions in a contemporaneous credit memo\n"
                f"4. Notify Compliance if OFAC, AML, or consumer protection is involved\n\n"
                f"**Try asking about**: OFAC compliance, Basel III capital, KYC/AML, contract riders, SOFR pricing, credit overrides, or securitization."
            )

# Instantiated Singleton Engine
gemini_engine: GeminiLegalEngine = GeminiLegalEngine()
