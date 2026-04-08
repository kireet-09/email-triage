"""
Typed Pydantic models for email-triage-env.
"""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict


class Email(BaseModel):
    """Represents a single email in the inbox."""
    model_config = ConfigDict(populate_by_name=True)
    
    id: str = Field(..., description="Unique email identifier (e.g., 'e1', 'm5', 'h10')")
    subject: str = Field(..., description="Email subject line")
    from_: str = Field(..., description="Sender email address", alias="from")
    body: str = Field(..., description="Email body text (3-5 sentences)")
    gt_priority: str = Field(
        ...,
        description="Ground truth priority level: HIGH, MEDIUM, or LOW"
    )
    gt_category: str = Field(
        ...,
        description="Ground truth category: Support, Sales, HR, Legal, Finance, or Spam"
    )
    needs_response: bool = Field(
        default=False,
        description="Whether this email requires a response (hard task only)"
    )
    response_keywords: Optional[List[str]] = Field(
        default=None,
        description="Keywords that should appear in response draft (hard task only)"
    )


class Action(BaseModel):
    """Agent action: triage, categorize, or respond."""
    action_type: str = Field(
        ...,
        description="Type of action: 'triage', 'categorize', 'triage_and_respond', or 'skip'"
    )
    email_id: str = Field(..., description="ID of email being processed")
    priority: Optional[Literal["HIGH", "MEDIUM", "LOW"]] = Field(
        default=None,
        description="Assigned priority level (required for triage/categorize/triage_and_respond)"
    )
    category: Optional[Literal["Support", "Sales", "HR", "Legal", "Finance", "Spam"]] = Field(
        default=None,
        description="Assigned category (required for categorize/triage_and_respond)"
    )
    response_draft: Optional[str] = Field(
        default=None,
        description="Draft response text (required for triage_and_respond on HIGH emails)"
    )


class ProcessedEmail(BaseModel):
    """Record of a processed email with assigned values and reward."""
    email_id: str = Field(..., description="Email ID")
    priority: Optional[str] = Field(default=None, description="Assigned priority")
    category: Optional[str] = Field(default=None, description="Assigned category")
    response_draft: Optional[str] = Field(default=None, description="Response draft if provided")
    reward: float = Field(..., description="Reward for this step")


class Reward(BaseModel):
    """Reward signal from environment.step()."""
    value: float = Field(..., description="Step reward value")
    priority_correct: Optional[bool] = Field(
        default=None,
        description="Whether priority assignment was correct"
    )
    category_correct: Optional[bool] = Field(
        default=None,
        description="Whether category assignment was correct"
    )
    response_quality: Optional[float] = Field(
        default=None,
        description="Quality score of response draft (0.0-1.0) for hard task"
    )
    penalty: float = Field(default=0.0, description="Total penalties applied")
    message: str = Field(default="", description="Human-readable reward explanation")


class Observation(BaseModel):
    """Current observation of the environment state."""
    inbox: List[Email] = Field(..., description="List of unprocessed emails in current task")
    processed: List[ProcessedEmail] = Field(..., description="List of already-processed emails")
    current_step: int = Field(..., description="Current step number (0-indexed)")
    task_id: str = Field(..., description="Current task ID")
    instructions: str = Field(..., description="Task-specific instructions for agent")
    remaining_emails: int = Field(..., description="Number of unprocessed emails in inbox")


class StepResult(BaseModel):
    """Result of environment.step()."""
    observation: Observation = Field(..., description="New observation after step")
    reward: Reward = Field(..., description="Reward signal")
    done: bool = Field(..., description="Whether episode ended")
    info: dict = Field(default_factory=dict, description="Additional info (email_id, action details, etc.)")


class ResetResult(BaseModel):
    """Result of environment.reset()."""
    observation: Observation = Field(..., description="Initial observation for episode")
    info: dict = Field(
        default_factory=dict,
        description="Task metadata (task_id, max_steps, difficulty, etc.)"
    )


class EnvironmentState(BaseModel):
    """Complete snapshot of environment state."""
    task_id: str = Field(..., description="Current task ID")
    current_step: int = Field(..., description="Current step number")
    max_steps: int = Field(..., description="Maximum steps allowed")
    done: bool = Field(..., description="Whether episode is done")
    emails_total: int = Field(..., description="Total emails in task")
    emails_processed: int = Field(..., description="Number of emails processed")
    cumulative_reward: float = Field(..., description="Sum of all step rewards so far")
    processed: List[ProcessedEmail] = Field(..., description="List of all processed emails")
    episode_score: float = Field(..., description="Final graded task score (0.0-1.0)")


class TaskConfig(BaseModel):
    """Configuration for a single task."""
    id: str = Field(..., description="Task ID (e.g., 'easy_triage')")
    name: str = Field(..., description="Human-readable task name")
    difficulty: str = Field(..., description="Difficulty level: easy, medium, hard")
    description: str = Field(..., description="Task description")
    email_ids: List[str] = Field(..., description="List of email IDs in this task")
    max_steps: int = Field(..., description="Maximum steps allowed")
    reward_threshold: float = Field(..., description="Target reward threshold for success")
