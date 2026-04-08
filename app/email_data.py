"""
Email dataset and task configurations for email-triage-env.
"""
from typing import Dict, List
from app.models import Email, TaskConfig


# ============================================================================
# EASY TASK EMAILS (e1-e5)
# ============================================================================

EASY_EMAILS = [
    Email(
        id="e1",
        subject="URGENT: Production server down - all services offline",
        **{"from": "ops-alerts@company.com"},
        body="Our primary production server is returning 503 Service Unavailable errors across all endpoints. "
             "Customers are unable to access any services. Current impact is estimated at $5,000 per minute in lost revenue. "
             "Engineering team is investigating root cause. Please advise on escalation procedures.",
        gt_priority="HIGH",
        gt_category="Support"
    ),
    Email(
        id="e2",
        subject="Team lunch this Friday?",
        **{"from": "sarah.jones@company.com"},
        body="Hey team! I was thinking about going out for lunch this Friday and wanted to see who's interested. "
             "I found a great Thai restaurant downtown that everyone seems to like. "
             "Let me know by Wednesday if you want to join. Looking forward to it!",
        gt_priority="LOW",
        gt_category="HR"
    ),
    Email(
        id="e3",
        subject="Contract renewal due in 30 days - Action required",
        **{"from": "legal@partnerco.com"},
        body="Our service agreement with ABC Partners expires on February 15, 2024. "
             "We need your approval on the renewal terms before submitting to legal review. "
             "Key changes include a 15% rate increase and extended data retention requirements. "
             "Please review attached terms and confirm by January 20.",
        gt_priority="HIGH",
        gt_category="Legal"
    ),
    Email(
        id="e4",
        subject="Monthly newsletter - January 2024",
        **{"from": "newsletter@industrydigest.com"},
        body="This month's top trends in technology and business. "
             "Featuring articles on AI adoption, cloud migration strategies, and DevOps best practices. "
             "Unsubscribe anytime by clicking the link at the bottom.",
        gt_priority="LOW",
        gt_category="Spam"
    ),
    Email(
        id="e5",
        subject="Q4 budget report - please review before Thursday meeting",
        **{"from": "cfo@company.com"},
        body="Attached is the Q4 budget report for your review. "
             "We'll be discussing these numbers at the board meeting Thursday at 2 PM. "
             "Please provide any questions or concerns by end of day Wednesday so we can address them.",
        gt_priority="MEDIUM",
        gt_category="Finance"
    ),
]


# ============================================================================
# MEDIUM TASK EMAILS (m1-m8)
# ============================================================================

MEDIUM_EMAILS = [
    Email(
        id="m1",
        subject="Data breach notification: 2,400 customer records exposed",
        **{"from": "security@thirdparty.com"},
        body="We discovered unauthorized access to customer data on January 12. "
             "Approximately 2,400 customer records may have been accessed, including names, emails, and partially obfuscated payment methods. "
             "We are required to notify you under GDPR within 72 hours. Please coordinate your incident response and notification procedures.",
        gt_priority="HIGH",
        gt_category="Legal"
    ),
    Email(
        id="m2",
        subject="Enterprise deal: 500-seat license inquiry",
        **{"from": "procurement@megacorp.com"},
        body="We are evaluating your platform for enterprise deployment across 500 seats. "
             "Finance has pre-approved a budget of $250,000 for this fiscal year. "
             "Can you provide enterprise licensing terms and volume discount structure? "
             "We'd like to schedule a call with your sales team.",
        gt_priority="HIGH",
        gt_category="Sales"
    ),
    Email(
        id="m3",
        subject="PTO request: approved for next week",
        **{"from": "hr@company.com"},
        body="Your paid time off request for January 22-26 has been approved. "
             "Make sure all your tasks are handed off to team members and mark them in the project management system. "
             "Have a great vacation!",
        gt_priority="MEDIUM",
        gt_category="HR"
    ),
    Email(
        id="m4",
        subject="Invoice #INV-47382: $12,400 now 60 days overdue",
        **{"from": "accounts@vendor.com"},
        body="Our records show invoice #INV-47382 for $12,400 (software maintenance contract) is now 60 days past due. "
             "Without payment within 5 business days, we will be forced to suspend your service access and escalate to collections. "
             "Please remit payment immediately or contact us to arrange a payment plan.",
        gt_priority="HIGH",
        gt_category="Finance"
    ),
    Email(
        id="m5",
        subject="COMPLAINT: Unauthorized charges and service failure",
        **{"from": "angry_customer@email.com"},
        body="I've been charged $500 twice for a service that didn't work as promised. "
             "Your support team has ignored my last 3 emails. I'm filing a chargeback with my bank and reporting this to the Better Business Bureau. "
             "Respond immediately or I will pursue legal action.",
        gt_priority="HIGH",
        gt_category="Support"
    ),
    Email(
        id="m6",
        subject="You won a free iPad! Claim your prize now",
        **{"from": "contests@freeprizes.net"},
        body="Congratulations! You've been randomly selected to receive a complimentary iPad Air! "
             "Click here to claim your prize. Offer expires in 24 hours. "
             "This is clearly a phishing attempt trying to harvest email addresses.",
        gt_priority="LOW",
        gt_category="Spam"
    ),
    Email(
        id="m7",
        subject="Quarterly performance reviews: scheduling now",
        **{"from": "hr@company.com"},
        body="It's time for our Q1 performance reviews. All reviews must be completed by January 31. "
             "Sign up for your review slot here. We'll be discussing goals, achievements, and development opportunities. "
             "Please prepare your self-assessment before your meeting.",
        gt_priority="MEDIUM",
        gt_category="HR"
    ),
    Email(
        id="m8",
        subject="Feature request: timeline view for enterprise customer",
        **{"from": "account_manager@company.com"},
        body="Acme Corp (our $180k ARR customer) is requesting a timeline view feature for their Q1 renewal. "
             "This is a renewal blocker. Engineering estimates 3 weeks implementation. "
             "Should we commit to this in the renewal agreement or propose an alternative?",
        gt_priority="MEDIUM",
        gt_category="Sales"
    ),
]


# ============================================================================
# HARD TASK EMAILS (h1-h10)
# ============================================================================

HARD_EMAILS = [
    Email(
        id="h1",
        subject="CRITICAL: Payment processing system down 45 minutes - $30K lost revenue",
        **{"from": "ops@company.com"},
        body="Payment processing gateway is down. No transactions have been processed for the past 45 minutes. "
             "Estimated impact is $30,000 in lost revenue. Customers are reporting errors at checkout. "
             "We've escalated to our payment processor but need to investigate our side. "
             "What is the incident status and ETA to resolution?",
        gt_priority="HIGH",
        gt_category="Support",
        needs_response=True,
        response_keywords=["investigating", "engineers", "update", "urgent", "priority"]
    ),
    Email(
        id="h2",
        subject="Strategic partnership proposal: $2M ARR opportunity",
        **{"from": "ceo@partner.com"},
        body="We believe there is significant synergy between our platforms. "
             "Our CEO would like to schedule an executive-level call to explore a potential partnership worth $2M in combined ARR. "
             "Are you interested in discussing this opportunity? We're looking to move quickly.",
        gt_priority="HIGH",
        gt_category="Sales",
        needs_response=True,
        response_keywords=["schedule", "call", "excited", "partnership", "team"]
    ),
    Email(
        id="h3",
        subject="LEGAL NOTICE: Wrongful termination lawsuit",
        **{"from": "attorney@lawfirm.com"},
        body="Dear Sir/Madam, I represent [former employee] in a wrongful termination matter against your company. "
             "Please be advised that we intend to file a lawsuit unless we can resolve this matter. "
             "We will be sending formal discovery requests within 10 days. Please forward this to your legal counsel immediately.",
        gt_priority="HIGH",
        gt_category="Legal",
        needs_response=True,
        response_keywords=["legal", "counsel", "attorney", "acknowledge", "review"]
    ),
    Email(
        id="h4",
        subject="Office supplies monthly restock order",
        **{"from": "supplies@vendor.com"},
        body="This is your monthly restock notification for office supplies. "
             "Standard order: 5 reams of paper, 2 ink cartridges, pens, sticky notes. "
             "Monthly cost is approximately $85. Order will be delivered Friday. "
             "Reply SKIP to cancel this subscription.",
        gt_priority="LOW",
        gt_category="Finance",
        needs_response=False
    ),
    Email(
        id="h5",
        subject="Security audit results: 3 CRITICAL vulnerabilities found",
        **{"from": "auditor@securityfirm.com"},
        body="Our annual security audit identified 3 critical vulnerabilities in your infrastructure: "
             "SQL injection vulnerability in admin panel, exposed AWS access keys in public GitHub repo, exposed database credentials in config file. "
             "These must be remediated immediately. Full report attached. "
             "Please confirm receipt and provide remediation timeline.",
        gt_priority="HIGH",
        gt_category="Support",
        needs_response=True,
        response_keywords=["security", "team", "remediation", "immediately", "urgent"]
    ),
    Email(
        id="h6",
        subject="Amazon shipping confirmation: Package arriving Friday",
        **{"from": "shipments@amazon.com"},
        body="Your Amazon order ABC123 has shipped and is arriving Friday. "
             "Track your package using the link below. "
             "We appreciate your business!",
        gt_priority="LOW",
        gt_category="Spam",
        needs_response=False
    ),
    Email(
        id="h7",
        subject="Your top engineer has competing offer ($145K) - retention at risk",
        **{"from": "hr@company.com"},
        body="Our top backend engineer just informed us they have received a competing offer for $145,000 (our current offer: $125,000). "
             "They are leaving the door open for a counter-offer conversation but need a response by Friday. "
             "How do you want to proceed on retention?",
        gt_priority="HIGH",
        gt_category="HR",
        needs_response=True,
        response_keywords=["meet", "discuss", "value", "compensation", "schedule"]
    ),
    Email(
        id="h8",
        subject="Q1 marketing campaign: creative review needed by Thursday",
        **{"from": "marketing@company.com"},
        body="We've finalized creative assets for the Q1 product launch campaign. "
             "We need your approval on the messaging and visuals for the website and social media. "
             "Please review the shared folder and provide feedback by Thursday EOD so we can begin paid advertising.",
        gt_priority="MEDIUM",
        gt_category="Sales",
        needs_response=False
    ),
    Email(
        id="h9",
        subject="Your 2023 W-2 tax forms are now available",
        **{"from": "payroll@company.com"},
        body="Your 2023 W-2 form is now available in the employee portal. "
             "Please download and securely store for your tax filing. "
             "If you have questions about the amounts, contact payroll@company.com.",
        gt_priority="MEDIUM",
        gt_category="HR",
        needs_response=False
    ),
    Email(
        id="h10",
        subject="Case study approval request: Acme Corp success story",
        **{"from": "marketing@company.com"},
        body="We'd like to create a case study featuring Acme Corp's implementation and ROI results. "
             "Acme has agreed to participate but we need your sign-off on sharing specific metrics and quotes. "
             "Case study will be used in sales materials and our website. Can you review and approve by next Tuesday?",
        gt_priority="MEDIUM",
        gt_category="Sales",
        needs_response=False
    ),
]


# ============================================================================
# TASK CONFIGURATIONS
# ============================================================================

TASK_CONFIGS = {
    "easy_triage": TaskConfig(
        id="easy_triage",
        name="Easy: Priority Triage",
        difficulty="easy",
        description="Assign HIGH/MEDIUM/LOW priority to 5 urgent emails. No categorization required.",
        email_ids=["e1", "e2", "e3", "e4", "e5"],
        max_steps=10,
        reward_threshold=0.7
    ),
    "medium_categorize": TaskConfig(
        id="medium_categorize",
        name="Medium: Priority + Category",
        difficulty="medium",
        description="Assign priority AND category to 8 emails from mixed departments. "
                    "Categories: Support, Sales, HR, Legal, Finance, Spam.",
        email_ids=["m1", "m2", "m3", "m4", "m5", "m6", "m7", "m8"],
        max_steps=20,
        reward_threshold=0.65
    ),
    "hard_respond": TaskConfig(
        id="hard_respond",
        name="Hard: Priority + Category + Responses",
        difficulty="hard",
        description="Assign priority, category, and draft responses for 10 emails. "
                    "For critical emails, provide substantive 40-80 word response drafts.",
        email_ids=["h1", "h2", "h3", "h4", "h5", "h6", "h7", "h8", "h9", "h10"],
        max_steps=30,
        reward_threshold=0.55
    ),
}


# ============================================================================
# CONSOLIDATED DATASET
# ============================================================================

ALL_EMAILS: Dict[str, Email] = {}
for email in EASY_EMAILS + MEDIUM_EMAILS + HARD_EMAILS:
    ALL_EMAILS[email.id] = email


def get_all_emails() -> Dict[str, Email]:
    """Return all emails by ID."""
    return ALL_EMAILS


def get_task_config(task_id: str) -> TaskConfig:
    """Get task configuration by ID."""
    if task_id not in TASK_CONFIGS:
        raise ValueError(f"Unknown task_id: {task_id}")
    return TASK_CONFIGS[task_id]


def get_all_task_configs() -> Dict[str, TaskConfig]:
    """Get all task configurations."""
    return TASK_CONFIGS
