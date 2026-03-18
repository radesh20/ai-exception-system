1. STEP-BY-STEP WORKFLOW: From Input to Output

┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  STEP 1: DATA ARRIVES                                                   │
│  ─────────────────                                                      │
│  Celonis detects a process deviation in your P2P process.               │
│  Example: "Purchase Order PO-2024-0001 payment got blocked"             │
│  Data includes: event log, financial value, vendor, timestamps          │
│                                                                         │
│                              ↓                                          │
│                                                                         │
│  STEP 2: AI AGENT ANALYZES                                              │
│  ─────────────────────────                                              │
│  Deep Agent (powered by Azure GPT-4o) runs 4 sub-agents:               │
│    Agent 1: Context Builder  → Parses raw data into structured format   │
│    Agent 2: Root Cause       → Compares against 25+ historical cases    │
│    Agent 3: Classifier       → Assigns category, priority (1-5),        │
│                                 decides: AUTO or HUMAN routing          │
│    Agent 4: Action Recommender → Finds best resolution from policies    │
│                                                                         │
│                              ↓                                          │
│                                                                         │
│  STEP 3: ROUTING DECISION                                               │
│  ────────────────────────                                               │
│  IF low risk + high confidence → AUTO                                   │
│    → Action executes automatically                                      │
│    → No human needed                                                    │
│    → Result saved to database                                           │
│                                                                         │
│  IF high risk OR low confidence → HUMAN                                 │
│    → Notification sent (Teams + Outlook + Slack + Gmail)                │
│    → Exception appears in React dashboard                               │
│    → Analyst reviews and decides                                        │
│                                                                         │
│                              ↓                                          │
│                                                                         │
│  STEP 4: HUMAN DECISION (if routed to human)                            │
│  ──────────────────────────────────────────                             │
│  Analyst opens React dashboard or clicks Slack/Teams/Email link         │
│  Reads: AI analysis, root cause, confidence score, recommendation       │
│  Decides: ✅ Approve | ❌ Reject | ✏️ Modify | ⬆️ Escalate              │
│                                                                         │
│                              ↓                                          │
│                                                                         │
│  STEP 5: EXECUTION                                                      │
│  ────────────────                                                       │
│  If approved → Action runs (internal DB or ServiceNow ticket)           │
│  If rejected → No action, AI learns it was wrong                        │
│  If modified → Custom action runs instead                               │
│  If escalated → Senior analyst gets notified                            │
│                                                                         │
│                              ↓                                          │
│                                                                         │
│  STEP 6: AI LEARNS                                                      │
│  ─────────────────                                                      │
│  Every decision is recorded:                                            │
│    Approve → policy success rate goes UP                                │
│    Reject  → policy success rate goes DOWN                              │
│  Historical case added for future pattern matching                      │
│  Next time: AI is more confident → less human intervention needed       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘




2. HOW THE AI AGENT PROCESSES TASKS AND MAKES DECISIONS

┌─────────────────────────────────────────────────────────────────────┐
│                    AI AGENT DECISION LOGIC                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  INPUT: Raw Celonis exception data (event log + alert + metadata)   │
│                                                                     │
│  ┌────────────────────────────────────────────────────────┐        │
│  │  AGENT 1: CONTEXT BUILDER                              │        │
│  │                                                        │        │
│  │  Takes raw JSON → Extracts:                            │        │
│  │    • Actual process path (what actually happened)      │        │
│  │    • Happy path (what should have happened)            │        │
│  │    • Deviation point (where it went wrong)             │        │
│  │    • Severity score (0.0 to 1.0)                       │        │
│  │    • Financial exposure ($)                            │        │
│  │                                                        │        │
│  │  Formula: severity = (financial/100K)*0.6              │        │
│  │                     + (hours_to_SLA/48)*0.4            │        │
│  └───────────────────────────┬────────────────────────────┘        │
│                              ↓                                      │
│  ┌────────────────────────────────────────────────────────┐        │
│  │  AGENT 2: ROOT CAUSE ANALYZER                          │        │
│  │                                                        │        │
│  │  Compares current exception against historical cases:  │        │
│  │    • Uses SequenceMatcher to find similar paths        │        │
│  │    • Finds top 5 most similar past cases               │        │
│  │    • Identifies common deviation point                 │        │
│  │    • Calculates confidence (0.0 to 1.0)                │        │
│  │                                                        │        │
│  │  Confidence formula:                                   │        │
│  │    volume_score   = min(matches/20, 1.0) * 0.4         │        │
│  │    sim_score      = top_match_similarity * 0.4          │        │
│  │    variety_bonus  = 0.2 if matches >= 5 else 0.1       │        │
│  │                                                        │        │
│  │  If < 5 matches → confidence capped at 0.49            │        │
│  │                                                        │        │
│  │  OUTPUT: "GR delay at Payment Blocked matches 6        │        │
│  │          historical cases with 72% confidence"         │        │
│  └───────────────────────────┬────────────────────────────┘        │
│                              ↓                                      │
│  ┌────────────────────────────────────────────────────────┐        │
│  │  AGENT 3: CLASSIFIER                                   │        │
│  │                                                        │        │
│  │  Category (6 types):                                   │        │
│  │    payment_mismatch | quantity_mismatch                │        │
│  │    invoice_mismatch | goods_receipt_mismatch           │        │
│  │    tax_code_change  | novel_exception                  │        │
│  │                                                        │        │
│  │  Priority (1-5):                                       │        │
│  │    exposure > $100K  → +2                              │        │
│  │    exposure > $50K   → +1                              │        │
│  │    severity > 0.8    → +1                              │        │
│  │    SLA < 24 hours    → +2                              │        │
│  │    SLA < 48 hours    → +1                              │        │
│  │    compliance flag   → +1                              │        │
│  │                                                        │        │
│  │  Routing: HUMAN if ANY of:                             │        │
│  │    ❌ confidence < 0.6 (novel)                          │        │
│  │    ❌ priority >= 4                                     │        │
│  │    ❌ compliance flag = true                            │        │
│  │    ❌ exposure > $100,000                               │        │
│  │  Otherwise → AUTO                                      │        │
│  └───────────────────────────┬────────────────────────────┘        │
│                              ↓                                      │
│  ┌────────────────────────────────────────────────────────┐        │
│  │  AGENT 4: ACTION RECOMMENDER                           │        │
│  │                                                        │        │
│  │  Looks up policy store by category:                    │        │
│  │    payment_mismatch  → three_way_match_recheck (89%)   │        │
│  │    quantity_mismatch → adjust_quantity (92%)            │        │
│  │    invoice_mismatch  → request_invoice_correction (78%)│        │
│  │    goods_receipt     → reverse_and_repost_gr (85%)     │        │
│  │    tax_code_change   → update_tax_code (95%)           │        │
│  │    novel_exception   → escalate_to_human (100%)        │        │
│  │                                                        │        │
│  │  If multiple policies → scores by:                     │        │
│  │    score = success_rate*0.6 + (1/resolution_time)*0.4  │        │
│  │    Picks highest scoring policy                        │        │
│  │                                                        │        │
│  │  OUTPUT: "Recommend three_way_match_recheck            │        │
│  │          Success: 89%, Resolution: ~30 min"            │        │
│  └────────────────────────────────────────────────────────┘        │
│                                                                     │
│  FINAL OUTPUT: ExceptionModel with all analysis + recommendation    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘


3. ROLE OF EACH COMPONENT

┌─────────────────────────────────────────────────────────────────────┐
│                    SYSTEM ARCHITECTURE                               │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                                                            │    │
│  │  🌐 REACT FRONTEND (http://localhost:3000)                 │    │
│  │                                                            │    │
│  │  WHAT IT DOES:                                             │    │
│  │  • Dashboard — KPIs, pending count, recent exceptions      │    │
│  │  • Incoming Issues — All exceptions with status filters    │    │
│  │  • AI Analysis — Root cause, confidence, causal factors    │    │
│  │  • Pending Decisions — Review queue + Approve/Reject form  │    │
│  │  • Action History — All executed actions                   │    │
│  │  • Learning Insights — AI improvement over time            │    │
│  │  • Settings — What's enabled/disabled                      │    │
│  │                                                            │    │
│  │  HOW IT WORKS:                                             │    │
│  │  • Calls FastAPI endpoints via fetch()                     │    │
│  │  • Auto-refreshes pending count every 15 seconds           │    │
│  │  • Deep links from Slack/Email open specific exception     │    │
│  │                                                            │    │
│  └────────────────────────────┬───────────────────────────────┘    │
│                               │ HTTP REST API calls                 │
│                               ↓                                     │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                                                            │    │
│  │  🔧 FASTAPI BACKEND (http://localhost:8000)                │    │
│  │                                                            │    │
│  │  WHAT IT DOES:                                             │    │
│  │  • /api/exceptions — CRUD for exception data               │    │
│  │  • /api/decisions — Record human decisions                 │    │
│  │  • /api/actions — Track executed actions                   │    │
│  │  • /api/stats — System statistics                          │    │
│  │  • /api/learning — AI improvement metrics                  │    │
│  │  • /api/process — Trigger AI pipeline on new data          │    │
│  │  • /api/variants — Process variant data from Celonis       │    │
│  │  • /api/webhooks/slack — Receive Slack button clicks       │    │
│  │                                                            │    │
│  │  HOW IT WORKS:                                             │    │
│  │  • Receives requests from frontend + Slack + email links   │    │
│  │  • Orchestrates AI agents                                  │    │
│  │  • Triggers notifications (Teams/Outlook/Slack/Gmail)      │    │
│  │  • Manages execution layer (internal DB or ServiceNow)     │    │
│  │  • Records learning data                                   │    │
│  │                                                            │    │
│  └────────────────────────────┬───────────────────────────────┘    │
│                               │                                     │
│              ┌────────────────┼────────────────┐                    │
│              ↓                ↓                ↓                    │
│  ┌──────────────────┐ ┌──────────────┐ ┌──────────────────┐       │
│  │                  │ │              │ │                  │       │
│  │ 🤖 AI AGENTS     │ │ 💾 DATABASE  │ │ 📡 INTEGRATIONS │       │
│  │                  │ │              │ │                  │       │
│  │ WHAT:            │ │ WHAT:        │ │ WHAT:            │       │
│  │ Context Builder  │ │ JSON files   │ │ Celonis          │       │
│  │ Root Cause       │ │ (default)    │ │ Teams            │       │
│  │ Classifier       │ │ OR SQLite    │ │ Outlook          │       │
│  │ Recommender      │ │              │ │ Slack            │       │
│  │ Learning Engine  │ │ STORES:      │ │ Gmail            │       │
│  │                  │ │ exceptions   │ │ ServiceNow       │       │
│  │ HOW:             │ │ decisions    │ │                  │       │
│  │ Rule-based       │ │ actions      │ │ HOW:             │       │
│  │ (default)        │ │ policies     │ │ Teams: webhook   │       │
│  │ OR Azure GPT-4o  │ │ historical   │ │ Outlook: Graph   │       │
│  │ (Deep Agent)     │ │ cases        │ │ Slack: MCP       │       │
│  │                  │ │              │ │ Gmail: MCP       │       │
│  └──────────────────┘ └──────────────┘ └──────────────────┘       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘


4. INTEGRATION EXPLANATIONS

┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  HOW GMAIL WORKS IN THIS SYSTEM                                 │
│                                                                 │
│  Technology: Gmail MCP Server                                   │
│  Package: @gongrzhe/server-gmail-autoauth-mcp                  │
│  Enable: GMAIL_ENABLED=true in .env                            │
│                                                                 │
│  SETUP (one-time):                                              │
│  1. Google Cloud Console → Enable Gmail API                     │
│  2. Create OAuth 2.0 credentials (Desktop type)                 │
│  3. First run → browser opens → you click "Allow"               │
│  4. Token cached → no browser needed again                      │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  FLOW: Exception → Gmail                                │   │
│  │                                                          │   │
│  │  1. Pipeline routes exception to HUMAN                   │   │
│  │  2. NotificationManager.notify() called                  │   │
│  │  3. GmailMCPNotifier connects to MCP server              │   │
│  │  4. MCP server handles OAuth + SMTP                      │   │
│  │  5. Email sent to analyst:                                │   │
│  │                                                          │   │
│  │     Subject: 🔴 [P4] P2P Exception: payment_mismatch    │   │
│  │     Body:                                                │   │
│  │       Exception Alert — Priority 4/5                     │   │
│  │       Category: payment_mismatch                         │   │
│  │       Exposure: $85,000                                  │   │
│  │       Root Cause: GR delay blocking payment              │   │
│  │       Recommended: three_way_match_recheck               │   │
│  │                                                          │   │
│  │       [Review & Decide →] (link to React dashboard)      │   │
│  │                                                          │   │
│  │  6. Analyst reads email                                   │   │
│  │  7. Clicks link → opens React at /exception/{id}         │   │
│  │  8. Makes decision → confirmation email sent back         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  WHEN EMAILS ARE SENT:                                          │
│  • New exception routed to human → alert email                  │
│  • Decision recorded → confirmation email                       │
│                                                                 │
│  WHAT EMAILS CONTAIN:                                           │
│  • Priority emoji + level (🔴 P4/5)                            │
│  • Exception category and ID                                    │
│  • Financial exposure                                           │
│  • AI root cause analysis                                       │
│  • Recommended action                                           │
│  • Direct link to React dashboard                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘


4B. Microsoft Teams Integration — Notifications, Approvals, Human-in-Loop
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  HOW MICROSOFT TEAMS WORKS IN THIS SYSTEM                       │
│                                                                 │
│  Technology: Teams Incoming Webhook + Adaptive Cards            │
│  Enable: TEAMS_ENABLED=true in .env                            │
│  Zero dependencies (just HTTP POST with requests library)       │
│                                                                 │
│  SETUP (5 minutes):                                             │
│  1. Open Microsoft Teams                                        │
│  2. Go to target channel → ••• → Connectors                    │
│  3. Add "Incoming Webhook" → Name it → Create                   │
│  4. Copy webhook URL → paste in .env as TEAMS_WEBHOOK_URL       │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  FLOW: Exception → Teams                                │   │
│  │                                                          │   │
│  │  1. Pipeline routes exception to HUMAN                   │   │
│  │  2. TeamsWebhookNotifier.send() called                   │   │
│  │  3. Builds Adaptive Card with:                           │   │
│  │     • Priority color (red/yellow/green)                  │   │
│  │     • Exception ID and category                          │   │
│  │     • AI analysis summary                                │   │
│  │     • "Review & Decide" button                           │   │
│  │  4. HTTP POST to Teams webhook URL                       │   │
│  │  5. Card appears in Teams channel:                       │   │
│  │                                                          │   │
│  │     ┌──────────────────────────────────────────┐        │   │
│  │     │ 🔴 P2P Exception — Priority 4/5          │        │   │
│  │     │                                          │        │   │
│  │     │ ID:       PO-2024-0001                   │        │   │
│  │     │ Category: payment_mismatch               │        │   │
│  │     │                                          │        │   │
│  │     │ GR delay blocking payment. 72% confidence│        │   │
│  │     │ Recommend: three_way_match_recheck       │        │   │
│  │     │                                          │        │   │
│  │     │ [Review & Decide]                        │        │   │
│  │     └──────────────────────────────────────────┘        │   │
│  │                                                          │   │
│  │  6. Analyst clicks "Review & Decide"                     │   │
│  │  7. Browser opens React dashboard                        │   │
│  │  8. Analyst approves/rejects                             │   │
│  │  9. Confirmation card posted back to Teams               │   │
│  │                                                          │   │
│  │     ✅ Decision: PO-2024-0001 → approved by john.doe    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  HUMAN-IN-THE-LOOP VIA TEAMS:                                   │
│                                                                 │
│  The full approval flow:                                        │
│  Teams Alert → Analyst Reads → Clicks Link → React Dashboard   │
│  → Reviews AI Analysis → Clicks Approve/Reject → System Learns │
│                                                                 │
│  WHY TEAMS:                                                     │
│  • Most enterprise orgs already use Teams                       │
│  • Instant visibility for the team                              │
│  • Adaptive Cards are rich (colors, buttons, facts)             │
│  • No extra app needed — works in existing Teams channels       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘


4C. Microsoft Outlook Integration
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  HOW OUTLOOK WORKS IN THIS SYSTEM                               │
│                                                                 │
│  Technology: Microsoft Graph API (Mail.Send permission)         │
│  Enable: OUTLOOK_ENABLED=true in .env                          │
│  Requires: pip install msal                                     │
│                                                                 │
│  SETUP:                                                         │
│  1. Azure Portal → App Registrations → New                      │
│  2. API Permissions → Microsoft Graph → Mail.Send               │
│  3. Grant admin consent                                         │
│  4. Create client secret                                        │
│  5. Copy Tenant ID, Client ID, Secret → .env                   │
│                                                                 │
│  Same email content as Gmail but sent through corporate          │
│  Outlook using Microsoft Graph API with app-only auth.          │
│  Better for enterprises because:                                │
│  • Uses corporate email domain (alerts@company.com)             │
│  • Managed by Azure AD (IT controls access)                     │
│  • No personal Gmail account needed                             │
│  • Audit trail in Exchange                                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

4D. Slack Integration

┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  HOW SLACK WORKS IN THIS SYSTEM                                 │
│                                                                 │
│  Technology: Slack MCP Server                                   │
│  Package: @modelcontextprotocol/server-slack                   │
│  Enable: SLACK_ENABLED=true in .env                            │
│                                                                 │
│  SETUP:                                                         │
│  1. api.slack.com → Create App → Add scopes:                    │
│     chat:write, chat:write.public, channels:read                │
│  2. Install to workspace → Copy Bot Token                       │
│  3. Set SLACK_BOT_TOKEN in .env                                 │
│  4. Create #p2p-exceptions channel                              │
│  5. /invite @your-bot in channel                                │
│                                                                 │
│  Message format (Slack mrkdwn):                                 │
│                                                                 │
│  🔴 *P2P Exception — P4/5*                                     │
│  *ID:* `PO-2024-0001`                                          │
│  *Category:* payment_mismatch                                   │
│  ───                                                            │
│  Exception: payment_mismatch                                    │
│  Exposure: $85,000.00                                           │
│  Root Cause: GR delay blocking payment                          │
│  Recommended: three_way_match_recheck                           │
│  ───                                                            │
│  <http://localhost:3000/exception/abc-123|🔗 Review & Decide>  │
│                                                                 │
│  WEBHOOK SUPPORT:                                               │
│  If Slack sends interactive button clicks:                      │
│  POST /api/webhooks/slack → system records decision             │
│  Analyst can approve/reject directly from Slack (optional)      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

4E. Celonis Integration — Process Mining & Bottleneck Detection

┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  HOW CELONIS WORKS IN THIS SYSTEM                               │
│                                                                 │
│  Technology: Celonis REST API + PQL (Process Query Language)    │
│  Enable: CELONIS_ENABLED=true, CELONIS_MODE=live in .env       │
│  Default: CELONIS_MODE=mock (uses sample data, no connection)   │
│                                                                 │
│  WHAT CELONIS PROVIDES:                                         │
│                                                                 │
│  1. EVENT LOGS — What happened in each purchase order           │
│     PO Created → GR Posted → Invoice Received → Payment Blocked│
│     Each event has: activity name, timestamp, who did it        │
│                                                                 │
│  2. PROCESS VARIANTS — Different paths cases take               │
│     Happy path (72%): PO → GR → Invoice → Payment ✅           │
│     Variant 2 (18%):  PO → Invoice → GR → Payment              │
│     Variant 3 (10%):  PO → GR → Invoice → Blocked → Review     │
│                                                                 │
│  3. EXCEPTION SIGNALS — Automated alerts when something goes    │
│     wrong. Celonis detects deviations from the happy path.      │
│     Example: "Payment blocked for PO-2024-0001, $85,000"       │
│                                                                 │
│  4. CASE METADATA — Vendor info, PO value, SLA, compliance     │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  FLOW: Celonis → Our System                             │   │
│  │                                                          │   │
│  │  Option A: BATCH (python main.py)                        │   │
│  │    1. MockClient loads data/sample_input.json            │   │
│  │    2. OR LiveClient calls Celonis PQL API                │   │
│  │    3. Returns list of open exceptions                    │   │
│  │    4. Each exception processed through AI pipeline       │   │
│  │                                                          │   │
│  │  Option B: API TRIGGER (POST /api/process)               │   │
│  │    1. Celonis webhook sends exception data to our API    │   │
│  │    2. API receives raw data                              │   │
│  │    3. Passes to ExceptionOrchestrator.process()          │   │
│  │    4. Result saved + notifications sent                  │   │
│  │                                                          │   │
│  │  Option C: POLL (POST /api/process-all)                  │   │
│  │    1. Click "Refresh from Celonis" in dashboard          │   │
│  │    2. System polls Celonis for open exceptions           │   │
│  │    3. Processes any new ones found                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  BOTTLENECK DETECTION:                                          │
│  • Celonis identifies which process steps cause delays          │
│  • Our system receives this as deviation_point                  │
│  • Root Cause Agent correlates deviation with historical cases  │
│  • If "GR Posted" is consistently delayed → hypothesis:         │
│    "Goods receipt delay is the root cause of payment blocks"    │
│                                                                 │
│  VARIANT ANALYSIS:                                              │
│  • React dashboard shows process variants visually              │
│  • /api/variants returns all paths + frequencies                │
│  • Happy path (most frequent) vs deviation paths highlighted    │
│  • Analysts see WHERE and HOW OFTEN processes deviate           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘


5. COMBINED REAL-WORLD EXAMPLE — All Integrations Working Together

┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  SCENARIO: "Vendor ABC payment of $85,000 is blocked"                   │
│                                                                         │
│  ═══════════════════════════════════════════════════════════════════     │
│  MINUTE 0: CELONIS DETECTS THE PROBLEM                                  │
│  ═══════════════════════════════════════════════════════════════════     │
│                                                                         │
│  Celonis process mining analyzes SAP transaction data.                  │
│  Detects: PO-2024-0001 deviated from happy path.                        │
│  Event log shows:                                                       │
│    Jan 1  — PO Created (by buyer_01)                                    │
│    Jan 15 — GR Posted (by warehouse_02)     ← 14 days gap!             │
│    Jan 16 — Invoice Received (by AP team)                               │
│    Jan 17 — Payment Blocked (by system)     ← DEVIATION HERE           │
│                                                                         │
│  Happy path should be: PO → GR → Invoice → Payment ✅                  │
│  Actual path is:       PO → GR → Invoice → Payment Blocked ❌          │
│                                                                         │
│  Celonis signals: {type: "payment_mismatch", value: $85,000}           │
│                                                                         │
│  ═══════════════════════════════════════════════════════════════════     │
│  MINUTE 0.1: DATA ENTERS OUR SYSTEM                                    │
│  ═══════════════════════════════════════════════════════════════════     │
│                                                                         │
│  Via: POST /api/process with raw Celonis data                           │
│  OR:  python main.py processes sample_input.json                        │
│                                                                         │
│  ═══════════════════════════════════════════════════════════════════     │
│  MINUTE 0.2: AI AGENTS ANALYZE (takes ~100ms)                           │
│  ═══════════════════════════════════════════════════════════════════     │
│                                                                         │
│  Agent 1 (Context Builder):                                             │
│    ✅ Parsed event log → actual path extracted                          │
│    ✅ Happy path identified (72% frequency variant)                     │
│    ✅ Deviation at "Payment Blocked"                                    │
│    ✅ Severity: 0.71 (high financial + approaching SLA)                 │
│                                                                         │
│  Agent 2 (Root Cause):                                                  │
│    ✅ Found 6 similar historical cases (payment_mismatch)               │
│    ✅ Top match: 85% path similarity                                    │
│    ✅ Common deviation: "Payment Blocked" in 5/6 cases                  │
│    ✅ Hypothesis: "GR posted 14 days after PO creation.                 │
│       This matches historical GR delay pattern with 72% confidence."    │
│    ✅ Confidence: 0.72                                                  │
│                                                                         │
│  Agent 3 (Classifier):                                                  │
│    ✅ Category: payment_mismatch                                        │
│    ✅ Priority: 4/5 (exposure $85K + approaching SLA)                   │
│    ✅ Novel: No (seen before)                                           │
│    ✅ Routing: HUMAN (priority >= 4)                                    │
│                                                                         │
│  Agent 4 (Action Recommender):                                          │
│    ✅ Policy found: three_way_match_recheck                             │
│    ✅ Historical success: 89%                                           │
│    ✅ Avg resolution time: 30 minutes                                   │
│    ✅ Reasoning: "Policy matched. 89% success across 45 samples."       │
│                                                                         │
│  ═══════════════════════════════════════════════════════════════════     │
│  MINUTE 0.3: NOTIFICATIONS BLAST (all enabled channels)                 │
│  ═══════════════════════════════════════════════════════════════════     │
│                                                                         │
│  Since routing = HUMAN, ALL enabled channels fire simultaneously:       │
│                                                                         │
│  📧 OUTLOOK EMAIL sent to analyst@company.com:                          │
│    Subject: 🔴 [P4] P2P Exception: payment_mismatch — PO-2024-0001    │
│    Body: Full analysis + "Review & Decide" link                         │
│                                                                         │
│  💬 TEAMS CARD posted to #p2p-exceptions channel:                       │
│    Adaptive Card with priority color, facts, action button              │
│    Everyone on the team sees it instantly                                │
│                                                                         │
│  💬 SLACK MESSAGE posted to #p2p-exceptions:                            │
│    Formatted mrkdwn with emoji, priority, analysis, link                │
│                                                                         │
│  📧 GMAIL sent to backup analyst:                                       │
│    Same content as Outlook but via personal Gmail                       │
│                                                                         │
│  ═══════════════════════════════════════════════════════════════════     │
│  MINUTE 1: ANALYST SEES NOTIFICATION                                    │
│  ═══════════════════════════════════════════════════════════════════     │
│                                                                         │
│  John Doe is in a Teams meeting.                                        │
│  He sees the red alert in #p2p-exceptions channel.                      │
│  He clicks "Review & Decide" button in the Teams card.                  │
│                                                                         │
│  ═══════════════════════════════════════════════════════════════════     │
│  MINUTE 1.5: ANALYST REVIEWS IN REACT DASHBOARD                        │
│  ═══════════════════════════════════════════════════════════════════     │
│                                                                         │
│  Browser opens: http://localhost:3000/exception/abc-123-def             │
│                                                                         │
│  John sees:                                                             │
│  • Exception type: payment_mismatch                                     │
│  • Financial exposure: $85,000                                          │
│  • Vendor: Vendor_ABC                                                   │
│  • Process path: PO → GR → Invoice → [Payment Blocked] ← deviation    │
│  • AI says: "GR delay is root cause. 72% confident."                   │
│  • AI recommends: three_way_match_recheck (89% historical success)     │
│  • Supporting cases: PO-2023-0101, PO-2023-0102, PO-2023-0103         │
│                                                                         │
│  John thinks: "Yes, I've seen this before. The 3-way match             │
│  recheck usually fixes these GR delay cases."                           │
│                                                                         │
│  ═══════════════════════════════════════════════════════════════════     │
│  MINUTE 2: ANALYST DECIDES — APPROVE                                    │
│  ═══════════════════════════════════════════════════════════════════     │
│                                                                         │
│  John clicks: ✅ Approve                                                │
│  Types name: "john.doe"                                                 │
│  Notes: "Standard GR delay case. Approve recheck."                      │
│  Clicks: 🚀 Submit Decision                                            │
│                                                                         │
│  ═══════════════════════════════════════════════════════════════════     │
│  MINUTE 2.1: SYSTEM EXECUTES AND LEARNS                                 │
│  ═══════════════════════════════════════════════════════════════════     │
│                                                                         │
│  1. Decision record saved:                                              │
│     {decision_type: "approved", analyst: "john.doe",                    │
│      original_recommendation: "three_way_match_recheck",               │
│      final_action: "three_way_match_recheck"}                          │
│                                                                         │
│  2. Action EXECUTES:                                                    │
│     Internal executor runs three_way_match_recheck                      │
│     Result: {message: "3-way match recheck triggered successfully"}     │
│     Status: completed ✅                                                │
│                                                                         │
│  3. Exception status → "completed" ✅                                   │
│                                                                         │
│  4. LEARNING ENGINE updates:                                            │
│     Policy "three_way_match_recheck" for "payment_mismatch":           │
│       success_rate: 0.89 → 0.891 (slightly up)                         │
│       sample_size: 45 → 46                                              │
│                                                                         │
│  5. HISTORICAL CASE added:                                              │
│     {case_id: "PO-2024-0001", exception_type: "payment_mismatch",      │
│      actual_path: [...], was_approved: true, analyst: "john.doe"}       │
│     → Next time a similar case comes in, AI has MORE data               │
│     → Confidence will be HIGHER                                         │
│     → Eventually this type may route AUTO (no human needed)             │
│                                                                         │
│  6. CONFIRMATION sent:                                                  │
│     Teams:   "✅ Decision: PO-2024-0001 → approved by john.doe"        │
│     Outlook: "✅ Decision recorded"                                     │
│     Slack:   "✅ Decision: PO-2024-0001 → approved by john.doe"        │
│     Gmail:   "✅ Decision recorded"                                     │
│                                                                         │
│  ═══════════════════════════════════════════════════════════════════     │
│  THE LOOP CONTINUES:                                                    │
│  ═══════════════════════════════════════════════════════════════════     │
│                                                                         │
│  Week 1:  AI handles 20% auto, 80% needs human → lots of reviews       │
│  Week 4:  AI handles 50% auto, 50% needs human → fewer reviews         │
│  Week 12: AI handles 80% auto, 20% needs human → mostly automated      │
│                                                                         │
│  The system gets SMARTER with every single decision you make.           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

6. FINAL SUMMARY
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  This system uses AI agents to automatically detect, analyze,           │
│  and recommend resolutions for P2P process exceptions — routing         │
│  complex cases to humans via Teams/Outlook/Slack/Gmail, learning        │
│  from every Approve/Reject decision, and getting smarter over           │
│  time until most exceptions resolve themselves automatically.           │
│                                                                         │
│  In one line:                                                           │
│                                                                         │
│  "Celonis finds the problem → AI diagnoses it → Human approves →       │
│   System executes → AI learns → Next time, less human work needed."     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘


QUICK REFERENCE CARD
COMPONENT           TECHNOLOGY                    PURPOSE
─────────────────────────────────────────────────────────
Frontend            React + Recharts              Dashboard, decisions, charts
Backend             Python + FastAPI              API, orchestration, logic
AI Engine           Deep Agents + Azure GPT-4o    Analysis, recommendations
Database            JSON files (or SQLite)        Store everything
Celonis             REST API + PQL                Process mining, detection
Microsoft Teams     Incoming Webhook              Real-time team alerts
Microsoft Outlook   Graph API + MSAL              Corporate email alerts
Slack               MCP Server                    Developer-friendly alerts
Gmail               MCP Server                    Personal email alerts
ServiceNow          REST API (optional)           Enterprise ticketing
Learning Engine     Rule-based feedback loop      AI improves from decisions