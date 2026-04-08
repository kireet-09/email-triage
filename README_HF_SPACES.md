# Deploying to Hugging Face Spaces

This guide explains how to deploy the Email Triage Environment to Hugging Face Spaces.

## Prerequisites

1. **Hugging Face Account** - Sign up at https://huggingface.co if you don't have an account
2. **Hugging Face CLI** - Install with `pip install huggingface-hub`
3. **HF Token** - Get from https://huggingface.co/settings/tokens (create a new token with write access)

## Quick Deployment

### Step 1: Create a Hugging Face Space

```bash
# Use the HF CLI to create a new Space
huggingface-cli repo create --type space --space-sdk streamlit email-triage-env
```

Or manually:
1. Go to https://huggingface.co/spaces
2. Click "Create new Space"
3. Set **Space name**: `email-triage-env`
4. Set **Space SDK**: `Streamlit`
5. Click "Create Space"

### Step 2: Clone and Update the Space Repository

```bash
# Clone the newly created Space
git clone https://huggingface.co/spaces/YOUR_USERNAME/email-triage-env
cd email-triage-env

# Copy files from your local repository
# (Or add this repository as a remote)
```

### Step 3: Add Remote to Your Local Repository

```bash
cd /path/to/email-triage-env

# Add HF Spaces as a remote
git remote add hf-spaces https://huggingface.co/spaces/YOUR_USERNAME/email-triage-env

# Push to HF Spaces
git push hf-spaces main
```

### Step 4: Configure Environment Variables

On the Hugging Face Space:
1. Go to your Space settings
2. Click "Repository settings"
3. Scroll to "Repository secrets"
4. Add a new secret:
   - **Name**: `HF_TOKEN`
   - **Value**: Your OpenAI API Key

### Step 5: Application Architecture

The Space will run:

1. **Streamlit Frontend** (`streamlit_app.py`)
   - Interactive UI on port 7860
   - Accessible at: `https://huggingface.co/spaces/YOUR_USERNAME/email-triage-env`

2. **FastAPI Backend** (`app/main.py`)
   - Runs independently
   - Can be started with: `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`
   - Exposes 6 endpoints: `/reset`, `/step`, `/state`, `/tasks`, `/health`, `/grade`

## Environment Variables

- **HF_TOKEN** - Your OpenAI API key (required)
- **API_BASE_URL** - OpenAI API base URL (optional, default: `https://api.openai.com/v1`)
- **MODEL_NAME** - Model to use (optional, default: `gpt-4o-mini`)
- **ENV_BASE_URL** - Environment API URL (optional, default: `http://localhost:7860`)

## Running Locally First

Before deploying to HF Spaces, test locally:

```bash
# Terminal 1: Start FastAPI backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 7860

# Terminal 2: Start Streamlit frontend
streamlit run streamlit_app.py
```

Access at: http://localhost:8501

## Deployment URL

Once deployed, your Space will be available at:

```
https://huggingface.co/spaces/YOUR_USERNAME/email-triage-env
```

## Troubleshooting

### Connection Errors
- Ensure both backend and frontend are running
- Check that `API_BASE_URL` is correctly configured
- Verify network connectivity

### API Key Issues
- Confirm `HF_TOKEN` is set in Space secrets
- Ensure the key has proper OpenAI API access
- Check for typos in the token

### Port Conflicts
- HF Spaces runs apps on port 7860 by default
- Streamlit will auto-configure to available ports
- FastAPI backend should use a different port (8000) if running alongside

## API Reference

### Endpoints

**POST /reset**
- Reset environment for a new episode
- Body: `{"task_id": "easy_triage|medium_categorize|hard_respond"}`

**POST /step**
- Execute an action in the environment
- Body: `{"action_type": "triage|categorize|respond", "email_id": "...", ...}`

**GET /state**
- Get current environment state

**GET /tasks**
- List available tasks

**GET /health**
- Health check endpoint

**POST /grade**
- Grade a completed episode

See [README.md](README.md) for full API documentation.

## Support

For issues with:
- **Email Triage Environment**: See [README.md](README.md)
- **Hugging Face Spaces**: Visit https://huggingface.co/spaces
- **OpenAI API**: Visit https://platform.openai.com/docs
