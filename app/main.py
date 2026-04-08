"""
FastAPI server for email-triage-env.
Provides REST API for environment interaction.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.models import (
    Action, TaskConfig, Observation, StepResult, ResetResult, ResetRequest, EnvironmentState
)
from app.environment import EmailTriageEnvironment
from app.email_data import get_all_emails, get_all_task_configs
from app.graders import grade_task

# ============================================================================
# Initialize environment (module-level singleton)
# ============================================================================

emails_dict = get_all_emails()
tasks_config = get_all_task_configs()
environment = EmailTriageEnvironment(tasks_config, emails_dict)

# ============================================================================
# Create FastAPI app
# ============================================================================

app = FastAPI(
    title="Email Triage Environment",
    description="OpenEnv environment for email triage and response task",
    version="1.0.0"
)

# Add CORS middleware FIRST (before other middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Endpoints
# ============================================================================

@app.get("/health", tags=["System"])
def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.options("/reset")
async def options_reset():
    """Handle CORS preflight requests for /reset endpoint."""
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET,HEAD,PUT,PATCH,POST,DELETE",
            "Access-Control-Allow-Headers": "origin,content-type,accept,authorization",
        },
    )


@app.post("/reset", tags=["Episode"], response_model=ResetResult)
def reset(request: ResetRequest):
    """
    Reset environment for a new episode.
    
    Request body: {"task_id": "easy_triage" | "medium_categorize" | "hard_respond"}
    
    Response: ResetResult with initial observation and task info
    """
    try:
        return environment.reset(request.task_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/step", tags=["Episode"], response_model=StepResult)
def step(action: Action):
    """
    Execute one step: process an email with the given action.
    
    Request body: Action with action_type, email_id, priority, category, response_draft
    
    Response: StepResult with observation, reward, done flag, info
    """
    return environment.step(action)


@app.get("/state", tags=["State"], response_model=EnvironmentState)
def get_state():
    """
    Get complete environment state snapshot.
    
    Response: EnvironmentState with all current values
    """
    return environment.state()


@app.get("/tasks", tags=["Metadata"])
def list_tasks():
    """
    List all available tasks with metadata.
    
    Response: List of TaskConfig objects
    """
    return list(tasks_config.values())


@app.post("/grade", tags=["Evaluation"])
def grade(body: dict):
    """
    Grade task performance.
    
    Request body: {"task_id": str, "processed": List[ProcessedEmail]}
    
    Response: {"score": float, "details": dict}
    """
    task_id = body.get("task_id")
    processed = body.get("processed", [])
    
    if not task_id:
        return {"error": "Missing task_id"}
    
    # Convert dict representations back to ProcessedEmail objects if needed
    from app.models import ProcessedEmail
    if processed and isinstance(processed[0], dict):
        processed = [ProcessedEmail(**p) for p in processed]
    
    score = grade_task(task_id, processed, emails_dict)
    
    return {
        "score": score,
        "details": {
            "task_id": task_id,
            "emails_processed": len(processed),
            "endpoints": {
                "reset": "POST /reset",
                "step": "POST /step",
                "state": "GET /state",
                "tasks": "GET /tasks",
                "grade": "POST /grade"
            }
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
