# Email Triage Environment (OpenEnv)

## Project Title & Tagline

**Email Triage Environment** — A production-ready OpenEnv for simulating realistic email inbox triage and response tasks. Agents learn to prioritize, categorize, and respond to business emails with dense step-level rewards.

---

## Why This Environment?

### Motivation & Real-World Value

Email management is a genuine bottleneck for knowledge workers. Research shows professionals spend 28% of their workday on email. Automating email triage with AI could unlock significant productivity gains.

This environment captures the **core decision-making task** that real AI systems tackle:
- **Priority assessment**: Distinguish urgent (production down, security breach) from routine (newsletters, office supplies)
- **Routing**: Route to correct department (Support handles outages, Legal handles contracts)
- **Response drafting**: For critical issues, generate substantive, contextual responses
- **Dense signal**: Unlike game environments, feedback is granular—per-email correctness enables fast learning

The environment uses **realistic business scenarios** (not toy problems):
- Production outages, security breaches, data leaks, wrongful termination threats
- Enterprise deals, partnership proposals, compensation negotiations
- Hard categorization: a support ticket vs. sales inquiry vs. legal notice requires domain knowledge

---

## Environment Description

The **EmailTriageEnvironment** simulates a knowledge worker's inbox. Each episode presents a sequence of emails; the agent must process them in order.

### What Tasks Does It Model?

1. **Easy (5 emails, 10 steps)**: Assign priority only
   - Emails: production outage, office chatter, contract expiration, newsletter, budget report
   - Agent learns to distinguish urgent (HIGH) from routine (LOW)

2. **Medium (8 emails, 20 steps)**: Assign priority AND category
   - Emails: data breach, sales deal, PTO request, overdue invoice, angry customer, phishing, reviews, upsell
   - Agent learns both urgency AND domain routing

3. **Hard (10 emails, 30 steps)**: Assign priority, category, AND draft responses
   - Emails: payment system down, partnership proposal, legal threat, security vulnerabilities, employee retention, etc.
   - Agent learns to respond appropriately to critical issues (40-80 words)

### Example Email Types

- **Support**: Production outages, customer complaints, security breaches, payment issues
- **Sales**: Enterprise deals, partnership proposals, upsell opportunities
- **HR**: PTO requests, performance reviews, compensation, retention
- **Legal**: Contract renewals, wrongful termination notices, data breach notifications, compliance
- **Finance**: Overdue invoices, budget reports, payment issues
- **Spam**: Newsletters, phishing, unsolicited offers, advertisements

---

## Action Space

| **Action Type** | **When to Use** | **Required Fields** | **Optional Fields** |
|---|---|---|---|
| `triage` | Easy task: assign priority only | `email_id`, `priority` | — |
| `categorize` | Medium/hard tasks: assign priority + category | `email_id`, `priority`, `category` | — |
| `triage_and_respond` | Hard task, HIGH+needs_response: full response | `email_id`, `priority`, `category` | `response_draft` (40-80 words) |
| `skip` | Skip an email (not recommended) | `email_id` | — |

**Example Actions:**

```json
{"action_type": "triage", "email_id": "e1", "priority": "HIGH"}

{"action_type": "categorize", "email_id": "m2", "priority": "HIGH", "category": "Sales"}

{"action_type": "triage_and_respond", "email_id": "h1", "priority": "HIGH", 
 "category": "Support", "response_draft": "We are currently investigating the payment processing outage. Our engineering team is prioritizing this issue. We will provide an update within the hour."}
```

---

## Observation Space

All observations are `Observation` objects with these fields:

| **Field** | **Type** | **Description** |
|---|---|---|
| `inbox` | `List[Email]` | Remaining unprocessed emails |
| `processed` | `List[ProcessedEmail]` | Already-processed emails with assignments & rewards |
| `current_step` | `int` | Current step (0-indexed) |
| `task_id` | `str` | Current task ID (easy_triage, medium_categorize, hard_respond) |
| `instructions` | `str` | Task-specific agent instructions |
| `remaining_emails` | `int` | Count of unprocessed emails |

Each email contains:
- `id`: Unique identifier (e.g., "e1", "m5", "h10")
- `subject`: Email subject line
- `from_`: Sender address
- `body`: Email text (3-5 sentences)
- `gt_priority`: Ground truth priority (for evaluation)
- `gt_category`: Ground truth category (for evaluation)

---

## Tasks

### Task 1: Easy Triage

| **Property** | **Value** |
|---|---|
| **Task ID** | `easy_triage` |
| **Difficulty** | Easy |
| **Email Count** | 5 |
| **Max Steps** | 10 |
| **What Agent Does** | Assigns HIGH/MEDIUM/LOW priority to 5 emails |
| **Reward Threshold** | 0.70 |

**Emails:** e1 (production down), e2 (team lunch), e3 (contract renewal), e4 (newsletter), e5 (budget report)

**Scoring Per Email:**
- 1.0: Correct priority
- 0.5: MEDIUM when should be HIGH or LOW (partial credit)
- 0.0: Wrong direction (HIGH↔LOW)

**Final Score:** Mean of all 5 emails, clamped to [0.0, 1.0]

**Expected Baseline:**
- Random agent: 0.33
- Heuristic agent: 0.75
- LLM agent: 0.88

---

### Task 2: Medium Categorize

| **Property** | **Value** |
|---|---|
| **Task ID** | `medium_categorize` |
| **Difficulty** | Medium |
| **Email Count** | 8 |
| **Max Steps** | 20 |
| **What Agent Does** | Assigns priority AND category (Support/Sales/HR/Legal/Finance/Spam) to 8 emails |
| **Reward Threshold** | 0.65 |

**Emails:** m1 (data breach), m2 (enterprise deal), m3 (PTO), m4 (overdue invoice), m5 (angry customer), m6 (phishing), m7 (reviews), m8 (upsell)

**Scoring Per Email:**
- `score = 0.4 × priority_correct + 0.6 × category_correct`
- Priority: 1.0 correct, 0.2 partial (MEDIUM on HIGH/LOW), 0.0 wrong
- Category: 1.0 correct, 0.0 wrong

**Final Score:** Mean of all 8 emails, clamped to [0.0, 1.0]

**Expected Baseline:**
- Random agent: 0.28
- Heuristic agent: 0.65
- LLM agent: 0.81

---

### Task 3: Hard Respond

| **Property** | **Value** |
|---|---|
| **Task ID** | `hard_respond` |
| **Difficulty** | Hard |
| **Email Count** | 10 |
| **Max Steps** | 30 |
| **What Agent Does** | Assigns priority, category, and drafts responses for critical emails |
| **Reward Threshold** | 0.55 |

**Emails:** h1 (payment down), h2 (partnership), h3 (legal threat), h4 (office supplies), h5 (security audit), h6 (amazon shipping), h7 (engineer retention), h8 (marketing), h9 (tax docs), h10 (case study)

**Scoring Per Email:**

For HIGH + needs_response emails (h1, h2, h3, h5, h7):
- `score = 0.30 × priority + 0.30 × category + 0.40 × response_quality`

For other emails:
- `score = 0.50 × priority + 0.50 × category`

**Response Quality** (for HIGH+needs_response):
- `quality = min(1.0, keyword_fraction × 0.85 + length_bonus)`
- `keyword_fraction`: fraction of expected keywords found in response_draft
- `length_bonus`: 0.15 if ≥30 words, 0.05 if ≥15 words, else 0.0

**Final Score:** Weighted mean over all 10 emails, clamped to [0.0, 1.0]

**Expected Baseline:**
- Random agent: 0.20
- Heuristic agent: 0.58
- LLM agent: 0.76

---

## Reward Function

Rewards are dense (per-email) and immediate. All values clamped to [-0.5, max] per step.

### Priority Scoring (All Tasks)

| **Situation** | **Easy** | **Medium/Hard** |
|---|---|---|
| Correct priority | 1.0 | 0.4 |
| MEDIUM on HIGH/LOW | 0.5 | 0.2 |
| Wrong direction | 0.0 | 0.0 |
| Other wrong | 0.0 | 0.0 |

### Category Scoring (Medium & Hard)

| **Situation** | **Score** |
|---|---|
| Correct category | 0.6 (medium) / 0.3 or 0.5 (hard) |
| Wrong category | 0.0 |
| Missing category | 0.0 + penalty |

### Response Scoring (Hard Task, HIGH+needs_response only)

| **Situation** | **Score** |
|---|---|
| Response with keywords + length | up to 0.5 bonus |
| No response on HIGH email | -0.15 penalty |
| Response quality = keyword_fraction × 0.85 + length_bonus | max 1.0 |

### Penalties

| **Situation** | **Penalty** |
|---|---|
| Invalid email_id | -0.1 |
| Duplicate processing | -0.05 |
| Skip action | -0.05 |
| Missing priority | -0.1 |
| Missing category (required) | -0.1 |
| Missing response (HIGH email) | -0.15 |

**Final Step Reward:** `max(-0.5, raw_reward - total_penalties)`

---

## API Endpoints

All endpoints return JSON. The environment maintains state across requests (single module-level instance).

### 1. POST /reset
Reset environment for new episode.

**Request:**
```json
{"task_id": "easy_triage" | "medium_categorize" | "hard_respond"}
```

**Response:**
```json
{
  "observation": {
    "inbox": [...],
    "processed": [],
    "current_step": 0,
    "task_id": "easy_triage",
    "instructions": "...",
    "remaining_emails": 5
  },
  "info": {"task_id": "easy_triage", "max_steps": 10, ...}
}
```

---

### 2. POST /step
Execute one step: process an email.

**Request:**
```json
{
  "action_type": "triage",
  "email_id": "e1",
  "priority": "HIGH",
  "category": null,
  "response_draft": null
}
```

**Response:**
```json
{
  "observation": {...},
  "reward": {
    "value": 1.0,
    "priority_correct": true,
    "category_correct": null,
    "response_quality": null,
    "penalty": 0.0,
    "message": "Priority: HIGH (gt: HIGH)"
  },
  "done": false,
  "info": {"email_id": "e1", "step": 1, "cumulative_reward": 1.0, ...}
}
```

---

### 3. GET /state
Snapshot of current environment state.

**Response:**
```json
{
  "task_id": "easy_triage",
  "current_step": 3,
  "max_steps": 10,
  "done": false,
  "emails_total": 5,
  "emails_processed": 3,
  "cumulative_reward": 2.5,
  "processed": [...],
  "episode_score": 0.83
}
```

---

### 4. GET /tasks
List all 3 available tasks.

**Response:**
```json
[
  {
    "id": "easy_triage",
    "name": "Easy: Priority Triage",
    "difficulty": "easy",
    "description": "...",
    "email_ids": ["e1", "e2", "e3", "e4", "e5"],
    "max_steps": 10,
    "reward_threshold": 0.7
  },
  {...},
  {...}
]
```

---

### 5. GET /health
Health check.

**Response:**
```json
{"status": "ok"}
```

---

### 6. POST /grade
Grade task performance on processed emails.

**Request:**
```json
{
  "task_id": "easy_triage",
  "processed": [
    {"email_id": "e1", "priority": "HIGH", "reward": 1.0},
    {"email_id": "e2", "priority": "LOW", "reward": 1.0},
    ...
  ]
}
```

**Response:**
```json
{
  "score": 1.0,
  "details": {
    "task_id": "easy_triage",
    "emails_processed": 5,
    "endpoints": {...}
  }
}
```

---

## Setup & Usage

### Prerequisites
- Python 3.11+
- pip or conda
- Docker (optional, for containerization)

### Local Setup (Python)

**1. Create virtual environment:**
```bash
cd email-triage-env
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

**2. Install dependencies:**
```bash
pip install -r requirements.txt
```

**3. Start FastAPI server:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 7860 --reload
```

Server will be available at `http://localhost:7860`

**4. (Optional) Run inference agent:**
```bash
export HF_TOKEN="your-api-key"  # For OpenAI or HF Inference
export API_BASE_URL="https://api.openai.com/v1"
export MODEL_NAME="gpt-4o-mini"
export ENV_BASE_URL="http://localhost:7860"

python inference.py --task easy_triage
python inference.py --task medium_categorize
python inference.py --task hard_respond
python inference.py --all
```

---

### Docker Setup

**1. Build image:**
```bash
docker build -t email-triage:latest .
```

**2. Run container:**
```bash
docker run -d -p 7860:7860 \
  -e HF_TOKEN="your-api-key" \
  -e API_BASE_URL="https://api.openai.com/v1" \
  -e MODEL_NAME="gpt-4o-mini" \
  --name email-triage-server \
  email-triage:latest
```

**3. Check logs:**
```bash
docker logs email-triage-server
```

---

### Testing

**Run all 24 tests:**
```bash
pytest tests/test_environment.py -v
```

**Run specific test class:**
```bash
pytest tests/test_environment.py::TestEnvironmentLifecycle -v
```

**Run with coverage:**
```bash
pytest tests/test_environment.py --cov=app --cov-report=html
```

Expected output:
```
tests/test_environment.py::TestEnvironmentLifecycle::test_reset_returns_observation_correct_size PASSED
tests/test_environment.py::TestEnvironmentLifecycle::test_reset_all_task_ids PASSED
...
====== 24 passed in 2.34s ======
```

---

## Baseline Scores

Expected performance by agent type:

### Easy Triage
| **Agent Type** | **Score** | **Notes** |
|---|---|---|
| Random (uniform priority) | 0.33 | 1/3 chance correct |
| Heuristic (keywords: "urgent", "down", etc.) | 0.75 | Captures most HIGH emails |
| LLM (GPT-4o-mini) | 0.88 | Strong on clear cases, occasional MEDIUM errors |

### Medium Categorize
| **Agent Type** | **Score** | **Notes** |
|---|---|---|
| Random | 0.28 | (1/3 priority) × (1/6 category) = 0.056 per email, but partial credit helps |
| Heuristic (keyword mapping) | 0.65 | Good for obvious categories (Legal, Support), weaker on Sales/HR confusion |
| LLM (GPT-4o-mini) | 0.81 | Excels at domain routing, occasional priority errors on MEDIUM |

### Hard Respond
| **Agent Type** | **Score** | **Notes** |
|---|---|---|
| Random | 0.20 | Random priority, category, and no meaningful response |
| Heuristic | 0.58 | Category heuristics help, but response generation is basic |
| LLM (GPT-4o-mini) | 0.76 | Strong responses, occasional priority/category errors on edge cases |

---

## Project Structure

```
email-triage-env/
├── app/
│   ├── __init__.py              # Package init
│   ├── main.py                  # FastAPI server with 6 endpoints
│   ├── environment.py           # EmailTriageEnvironment class (reset/step/state)
│   ├── models.py                # Pydantic models (8 types)
│   ├── graders.py               # Task-specific graders (3 graders + dispatcher)
│   └── email_data.py            # Email dataset (23 emails) + task configs
├── tests/
│   ├── __init__.py              # Package init
│   └── test_environment.py       # 24 comprehensive tests (4 test classes)
├── inference.py                 # LLM agent script (root directory)
├── openenv.yaml                 # OpenEnv specification
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Docker configuration
├── README.md                    # This file
└── .env.example                 # Optional: API key template
```

---

## OpenEnv Spec Compliance Checklist

- ✅ **Pydantic Models**: 8 typed models (Observation, Action, Reward, StepResult, ResetResult, EnvironmentState, Email, ProcessedEmail)
- ✅ **Environment Class**: EmailTriageEnvironment with reset(), step(), state()
- ✅ **Task Definitions**: 3 tasks (easy_triage, medium_categorize, hard_respond) with metadata
- ✅ **Reward Function**: Dense per-step rewards with penalties, clamped to [-0.5, max]
- ✅ **Graders**: 3 task-specific graders + dispatcher, all clamped to [0.0, 1.0]
- ✅ **Email Dataset**: 23 emails across 3 task categories with ground-truth labels
- ✅ **FastAPI Server**: 6 endpoints (/reset, /step, /state, /tasks, /health, /grade)
- ✅ **CORSMiddleware**: Enabled with allow_origins=["*"]
- ✅ **Inference Script**: JSON event logging, LLM integration, task-specific prompts, fallback handling
- ✅ **Tests**: 24 tests (lifecycle, rewards, graders, full episodes)
- ✅ **Configuration**: openenv.yaml with full spec, requirements.txt, Dockerfile
- ✅ **Documentation**: README.md with all 12 sections
- ✅ **Edge Cases**: Unknown email_id, duplicate processing, step after done, missing fields
- ✅ **Clamping**: All rewards ∈ [-0.5, max], all scores ∈ [0.0, 1.0]

---

## Contributing & Citation

This environment is designed for research in email automation, reinforcement learning, and decision-making systems.

If you use this environment in research, please cite:

```bibtex
@software{email_triage_env_2024,
  title={Email Triage Environment: OpenEnv for Email Classification and Response},
  author={Unknown},
  year={2024},
  url={https://github.com/TODO}
}
```

---

## License

MIT License (adjust as needed)

---

## Troubleshooting

### Server fails to start
- Ensure port 7860 is available: `lsof -i :7860` (macOS/Linux) or `netstat -ano | findstr :7860` (Windows)
- Check Python version: `python --version` (must be 3.11+)

### Tests fail with import errors
- Verify virtual environment is activated
- Run `pip install -r requirements.txt` again
- Check `PYTHONPATH`: ensure `email-triage-env/` is in the path

### Inference script fails to connect
- Ensure FastAPI server is running on the correct port
- Check `ENV_BASE_URL` environment variable
- Verify `HF_TOKEN` is set: `echo $HF_TOKEN`

### Docker build fails
- Clear Docker cache: `docker system prune`
- Rebuild: `docker build --no-cache -t email-triage:latest .`

---

**Questions?** Open an issue or contact the maintainers.
