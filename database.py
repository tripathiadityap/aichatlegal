"""
AIChatLegal Database Engine
Provides unified database interface for Supabase PostgreSQL with local fallback capabilities.
Password Assumption: checkfortheway#
Project: aichatlegal
"""

import os
import uuid
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

load_dotenv()

# Environment Credentials
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SUPABASE_PASSWORD = os.getenv("SUPABASE_DB_PASSWORD", "checkfortheway#")

class DatabaseManager:
    def __init__(self):
        self.use_supabase = bool(SUPABASE_URL and SUPABASE_KEY and SUPABASE_URL != "https://your-project.supabase.co")
        self.client = None
        
        if self.use_supabase:
            try:
                from supabase import create_client
                self.client = create_client(SUPABASE_URL, SUPABASE_KEY)
                print("[DB] Connected to remote Supabase database instance.")
            except Exception as e:
                print(f"[DB Warning] Failed to initialize Supabase client ({e}). Falling back to local embedded store.")
                self.use_supabase = False

        # Initialize SQLite fallback database for local execution & offline testing
        self.sqlite_path = os.path.join(os.path.dirname(__file__), "aichatlegal_local.db")
        self._init_local_db()

    def _init_local_db(self):
        """Initializes local SQLite schema with enterprise sample data if empty."""
        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS policies (
            id TEXT PRIMARY KEY,
            policy_code TEXT UNIQUE,
            title TEXT,
            client_name TEXT,
            deal_value_usd REAL,
            product_category TEXT,
            sales_rep_name TEXT,
            sales_head_approval INTEGER,
            raw_content TEXT,
            summary TEXT,
            status TEXT,
            created_at TEXT,
            updated_at TEXT
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS risk_scores (
            id TEXT PRIMARY KEY,
            policy_id TEXT,
            overall_risk_score INTEGER,
            risk_level TEXT,
            regulatory_compliance_score INTEGER,
            financial_exposure_score INTEGER,
            jurisdictional_risk_score INTEGER,
            flagged_clauses TEXT,
            ai_recommendation TEXT,
            created_at TEXT
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS legal_advice (
            id TEXT PRIMARY KEY,
            policy_id TEXT,
            lawyer_name TEXT,
            advice_summary TEXT,
            required_riders TEXT,
            compliance_directives TEXT,
            decision TEXT,
            created_at TEXT
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id TEXT PRIMARY KEY,
            policy_id TEXT,
            actor_name TEXT,
            actor_role TEXT,
            action_type TEXT,
            action_details TEXT,
            ip_address TEXT,
            created_at TEXT
        )
        ''')
        
        conn.commit()

        # Seed sample data if empty
        cursor.execute("SELECT COUNT(*) FROM policies")
        count = cursor.fetchone()[0]
        if count == 0:
            self._seed_sample_bank_policies(conn)
            
        conn.close()

    def _seed_sample_bank_policies(self, conn: sqlite3.Connection):
        """Seeds rich sample banking policy documents for Sales & Legal testing."""
        sample_policies = [
            {
                "id": str(uuid.uuid4()),
                "policy_code": "POL-2026-8819",
                "title": "Commercial Credit Override - Apex Global Logistics",
                "client_name": "Apex Global Logistics Inc.",
                "deal_value_usd": 14500000.00,
                "product_category": "Syndicated Revolving Credit",
                "sales_rep_name": "Aditya Tripathi (VP Structured Sales)",
                "sales_head_approval": 1,
                "raw_content": """SECTION 4.2 - INTEREST RATE MARGIN OVERRIDE REQUEST
Client requests a 45 bps reduction below standard SOFR margin pricing based on annual transaction volume commitments across cross-border cash management.

SECTION 9.1 - FINANCIAL COVENANTS & LEVERAGE RATIO
Maximum Total Leverage Ratio requested at 4.25x EBITDA (Standard Bank Baseline: 3.50x EBITDA).
Debt Service Coverage Ratio (DSCR) requested at 1.15x (Standard Baseline: 1.25x).

SECTION 14.3 - GOVERNING LAW & JURISDICTION
Governing law requested: English Law with London Court of International Arbitration (LCIA) clause.""",
                "summary": "Sales requested 45 bps rate discount and leverage ratio relaxation to 4.25x EBITDA for $14.5M syndicated facility.",
                "status": "pending_legal_review",
                "created_at": "2026-07-22T10:30:00Z",
                "updated_at": "2026-07-22T10:30:00Z"
            },
            {
                "id": str(uuid.uuid4()),
                "policy_code": "POL-2026-7402",
                "title": "Asset-Backed Financing Terms - Meridian Healthcare",
                "client_name": "Meridian Healthcare Partners",
                "deal_value_usd": 38000000.00,
                "product_category": "Asset Securitization",
                "sales_rep_name": "Sarah Jenkins (Managing Director, Healthcare)",
                "sales_head_approval": 1,
                "raw_content": """SECTION 2.1 - COLLATERAL ELIGIBILITY CRITERIA
Pledged Receivables include Medicare & Medicaid billing claims under 90 days past due. Third-party insurer reimbursement claims excluded from borrowing base recalculation.

SECTION 6.4 - EARLY TERMINATION FEE & PREPAYMENT PENALTY
Prepayment fee waived after Month 12 upon 30 days prior written notice.

SECTION 18.2 - PRIVACY & DATA GOVERNANCE
Strict adherence to HIPAA regulations with cross-border cloud hosting permissions for analytical processing.""",
                "summary": "Asset securitization deal with Medicare/Medicaid receivables pledge and HIPAA data processing disclosures.",
                "status": "approved_with_riders",
                "created_at": "2026-07-20T14:15:00Z",
                "updated_at": "2026-07-21T09:00:00Z"
            },
            {
                "id": str(uuid.uuid4()),
                "policy_code": "POL-2026-9104",
                "title": "Cross-Border Trade Line - Cyberdyne Systems",
                "client_name": "Cyberdyne Systems LLC",
                "deal_value_usd": 62000000.00,
                "product_category": "Structured Trade Finance",
                "sales_rep_name": "Marcus Vance (Director Global Markets)",
                "sales_head_approval": 0,
                "raw_content": """SECTION 1.5 - LETTER OF CREDIT ISSUANCE & UNCONFIRMED DISCLOSURE
Irrevocable LC issued through offshore subsidiary without secondary confirmation by Tier-1 correspondent bank.

SECTION 11.2 - SANCTIONS & OFAC INDEMNIFICATION CLAUSE
Limitation of liability capped at 1.0x annual fees in event of sanctions screening delays or vessel tracking flags.""",
                "summary": "Unconfirmed LC proposal with OFAC liability cap request. High regulatory risk requiring Legal & Compliance intervention.",
                "status": "flagged_high_risk",
                "created_at": "2026-07-23T08:00:00Z",
                "updated_at": "2026-07-23T08:00:00Z"
            }
        ]

        cursor = conn.cursor()
        for p in sample_policies:
            cursor.execute('''
            INSERT INTO policies (id, policy_code, title, client_name, deal_value_usd, product_category, sales_rep_name, sales_head_approval, raw_content, summary, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (p["id"], p["policy_code"], p["title"], p["client_name"], p["deal_value_usd"], p["product_category"], p["sales_rep_name"], p["sales_head_approval"], p["raw_content"], p["summary"], p["status"], p["created_at"], p["updated_at"]))

            # Seed matching risk score
            r_id = str(uuid.uuid4())
            if p["status"] == "pending_legal_review":
                risk = (68, "medium", 72, 60, 75, json.dumps(["Leverage Ratio > 3.5x EBITDA", "LCIA Governing Law"]), "Require financial covenant tightening to 3.75x EBITDA baseline.")
            elif p["status"] == "approved_with_riders":
                risk = (25, "low", 90, 85, 95, json.dumps(["HIPAA Cloud Data Rider Needed"]), "Approved subject to Standard HIPAA Data Protection Rider Schedule B.")
            else:
                risk = (88, "high", 30, 92, 40, json.dumps(["OFAC Sanctions Liability Limitation", "Unconfirmed Offshore LC"]), "REJECT OR ESCALATE TO GENERAL COUNSEL. OFAC limitation clause violates Bank Credit Policy Manual v4.2.")

            cursor.execute('''
            INSERT INTO risk_scores (id, policy_id, overall_risk_score, risk_level, regulatory_compliance_score, financial_exposure_score, jurisdictional_risk_score, flagged_clauses, ai_recommendation, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (r_id, p["id"], risk[0], risk[1], risk[2], risk[3], risk[4], risk[5], risk[6], p["created_at"]))

            # Seed sample audit log
            a_id = str(uuid.uuid4())
            cursor.execute('''
            INSERT INTO audit_logs (id, policy_id, actor_name, actor_role, action_type, action_details, ip_address, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (a_id, p["id"], p["sales_rep_name"], "sales_rep", "POLICY_UPLOADED", json.dumps({"deal_value": p["deal_value_usd"]}), "10.14.2.88", p["created_at"]))

        conn.commit()

    def get_all_policies(self) -> List[Dict[str, Any]]:
        """Retrieves all policy records ordered by creation date."""
        if self.use_supabase and self.client:
            try:
                res = self.client.table("policies").select("*").order("created_at", desc=True).execute()
                return res.data
            except Exception as e:
                print(f"[Supabase Query Error] {e}. Falling back to SQLite.")

        conn = sqlite3.connect(self.sqlite_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM policies ORDER BY created_at DESC")
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

    def get_policy_by_id(self, policy_id: str) -> Optional[Dict[str, Any]]:
        """Fetch single policy details including risk scores and legal advice."""
        if self.use_supabase and self.client:
            try:
                res = self.client.table("policies").select("*").eq("id", policy_id).execute()
                if res.data:
                    policy = res.data[0]
                    # Fetch risk score
                    r_res = self.client.table("risk_scores").select("*").eq("policy_id", policy_id).execute()
                    policy["risk_score"] = r_res.data[0] if r_res.data else None
                    # Fetch advice
                    a_res = self.client.table("legal_advice").select("*").eq("policy_id", policy_id).execute()
                    policy["advice"] = a_res.data if a_res.data else []
                    return policy
            except Exception as e:
                print(f"[Supabase Fetch Error] {e}. Falling back to SQLite.")

        conn = sqlite3.connect(self.sqlite_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM policies WHERE id = ?", (policy_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
            
        policy = dict(row)
        
        # Risk score
        cursor.execute("SELECT * FROM risk_scores WHERE policy_id = ?", (policy_id,))
        r_row = cursor.fetchone()
        if r_row:
            r_dict = dict(r_row)
            if isinstance(r_dict.get("flagged_clauses"), str):
                try:
                    r_dict["flagged_clauses"] = json.loads(r_dict["flagged_clauses"])
                except Exception:
                    pass
            policy["risk_score"] = r_dict
        else:
            policy["risk_score"] = None
            
        # Legal advice
        cursor.execute("SELECT * FROM legal_advice WHERE policy_id = ?", (policy_id,))
        advice_rows = []
        for a in cursor.fetchall():
            a_dict = dict(a)
            if isinstance(a_dict.get("required_riders"), str):
                try:
                    a_dict["required_riders"] = json.loads(a_dict["required_riders"])
                except Exception:
                    pass
            if isinstance(a_dict.get("compliance_directives"), str):
                try:
                    a_dict["compliance_directives"] = json.loads(a_dict["compliance_directives"])
                except Exception:
                    pass
            advice_rows.append(a_dict)
        policy["advice"] = advice_rows
        
        conn.close()
        return policy

    def insert_policy(self, policy_data: Dict[str, Any], risk_data: Dict[str, Any]) -> str:
        """Inserts new policy proposal uploaded by Sales along with Gemini pre-screening risk score."""
        policy_id = str(uuid.uuid4())
        policy_code = f"POL-{datetime.now().year}-{uuid.uuid4().hex[:4].upper()}"
        now_str = datetime.now().isoformat()
        
        p_record = {
            "id": policy_id,
            "policy_code": policy_code,
            "title": policy_data.get("title", "Untitled Policy"),
            "client_name": policy_data.get("client_name", "Unknown Client"),
            "deal_value_usd": float(policy_data.get("deal_value_usd", 0.0)),
            "product_category": policy_data.get("product_category", "General Lending"),
            "sales_rep_name": policy_data.get("sales_rep_name", "Sales Representative"),
            "sales_head_approval": 1 if policy_data.get("sales_head_approval") else 0,
            "raw_content": policy_data.get("raw_content", ""),
            "summary": policy_data.get("summary", ""),
            "status": risk_data.get("recommended_status", "pending_legal_review"),
            "created_at": now_str,
            "updated_at": now_str
        }

        r_record = {
            "id": str(uuid.uuid4()),
            "policy_id": policy_id,
            "overall_risk_score": int(risk_data.get("overall_risk_score", 50)),
            "risk_level": risk_data.get("risk_level", "medium"),
            "regulatory_compliance_score": int(risk_data.get("regulatory_compliance_score", 70)),
            "financial_exposure_score": int(risk_data.get("financial_exposure_score", 60)),
            "jurisdictional_risk_score": int(risk_data.get("jurisdictional_risk_score", 75)),
            "flagged_clauses": json.dumps(risk_data.get("flagged_clauses", [])),
            "ai_recommendation": risk_data.get("ai_recommendation", "Awaiting formal legal review."),
            "created_at": now_str
        }

        if self.use_supabase and self.client:
            try:
                self.client.table("policies").insert(p_record).execute()
                # Insert risk
                r_record_supa = dict(r_record)
                r_record_supa["flagged_clauses"] = risk_data.get("flagged_clauses", [])
                self.client.table("risk_scores").insert(r_record_supa).execute()
                self._log_audit_event(policy_id, p_record["sales_rep_name"], "sales_rep", "POLICY_UPLOADED", {"deal_value": p_record["deal_value_usd"]})
                return policy_id
            except Exception as e:
                print(f"[Supabase Insert Error] {e}. Falling back to local store.")

        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO policies VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', tuple(p_record.values()))
        
        cursor.execute('''
        INSERT INTO risk_scores VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', tuple(r_record.values()))
        
        conn.commit()
        conn.close()
        
        self._log_audit_event(policy_id, p_record["sales_rep_name"], "sales_rep", "POLICY_UPLOADED", {"deal_value": p_record["deal_value_usd"]})
        return policy_id

    def add_legal_advice(self, advice_data: Dict[str, Any]) -> str:
        """Lawyer submits legal opinion, advice, and updates policy status."""
        advice_id = str(uuid.uuid4())
        now_str = datetime.now().isoformat()
        policy_id = advice_data["policy_id"]
        decision = advice_data["decision"]
        
        rec = {
            "id": advice_id,
            "policy_id": policy_id,
            "lawyer_name": advice_data.get("lawyer_name", "Senior Legal Counsel"),
            "advice_summary": advice_data.get("advice_summary", ""),
            "required_riders": json.dumps(advice_data.get("required_riders", [])),
            "compliance_directives": json.dumps(advice_data.get("compliance_directives", [])),
            "decision": decision,
            "created_at": now_str
        }

        if self.use_supabase and self.client:
            try:
                # Insert advice
                supa_rec = dict(rec)
                supa_rec["required_riders"] = advice_data.get("required_riders", [])
                supa_rec["compliance_directives"] = advice_data.get("compliance_directives", [])
                self.client.table("legal_advice").insert(supa_rec).execute()
                # Update status
                self.client.table("policies").update({"status": decision, "updated_at": now_str}).eq("id", policy_id).execute()
                self._log_audit_event(policy_id, rec["lawyer_name"], "legal_counsel", "LEGAL_ADVICE_SUBMITTED", {"decision": decision})
                return advice_id
            except Exception as e:
                print(f"[Supabase Advice Insert Error] {e}. Falling back to SQLite.")

        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO legal_advice VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', tuple(rec.values()))
        
        cursor.execute('''
        UPDATE policies SET status = ?, updated_at = ? WHERE id = ?
        ''', (decision, now_str, policy_id))
        
        conn.commit()
        conn.close()
        
        self._log_audit_event(policy_id, rec["lawyer_name"], "legal_counsel", "LEGAL_ADVICE_SUBMITTED", {"decision": decision})
        return advice_id

    def get_audit_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch audit trail for compliance and banking regulatory inspectors."""
        if self.use_supabase and self.client:
            try:
                res = self.client.table("audit_logs").select("*").order("created_at", desc=True).limit(limit).execute()
                return res.data
            except Exception as e:
                print(f"[Supabase Audit Fetch Error] {e}. Falling back to SQLite.")

        conn = sqlite3.connect(self.sqlite_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = []
        for r in cursor.fetchall():
            r_dict = dict(r)
            if isinstance(r_dict.get("action_details"), str):
                try:
                    r_dict["action_details"] = json.loads(r_dict["action_details"])
                except Exception:
                    pass
            rows.append(r_dict)
        conn.close()
        return rows

    def _log_audit_event(self, policy_id: str, actor_name: str, actor_role: str, action_type: str, details: Dict[str, Any]):
        """Internal helper to write audit entries."""
        now_str = datetime.now().isoformat()
        audit_id = str(uuid.uuid4())
        
        if self.use_supabase and self.client:
            try:
                self.client.table("audit_logs").insert({
                    "id": audit_id,
                    "policy_id": policy_id,
                    "actor_name": actor_name,
                    "actor_role": actor_role,
                    "action_type": action_type,
                    "action_details": details,
                    "created_at": now_str
                }).execute()
                return
            except Exception:
                pass

        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO audit_logs VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (audit_id, policy_id, actor_name, actor_role, action_type, json.dumps(details), "127.0.0.1", now_str))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[Audit Log Exception] {e}")

# Instantiated Singleton Database Manager
db_manager = DatabaseManager()
