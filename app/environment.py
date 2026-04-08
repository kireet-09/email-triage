"""
Core EmailTriageEnvironment class for email triage task.
Implements reset(), step(), and state() methods.
"""
from typing import Dict, List
from app.models import (
    Email, Action, Reward, Observation, StepResult, ResetResult, 
    ProcessedEmail, EnvironmentState, TaskConfig
)
from app.graders import grade_task


class EmailTriageEnvironment:
    """
    Email triage simulation environment.
    
    Agent receives business emails and must:
    - Assign priority (HIGH/MEDIUM/LOW)
    - Assign category (Support/Sales/HR/Legal/Finance/Spam)
    - Draft responses for critical emails (hard task)
    """
    
    def __init__(self, tasks_config: Dict[str, TaskConfig], emails_dict: Dict[str, Email]):
        """
        Initialize environment with task configs and email dataset.
        
        Args:
            tasks_config: Dict of task configurations by ID
            emails_dict: Dict of all emails by ID
        """
        self.tasks_config = tasks_config
        self.emails_dict = emails_dict
        
        # Episode state
        self.current_task_id: str = None
        self.current_step: int = 0
        self.max_steps: int = 0
        self.done: bool = False
        self.cumulative_reward: float = 0.0
        self.inbox: List[Email] = []
        self.processed: List[ProcessedEmail] = []
        self._initialized = False
    
    def reset(self, task_id: str) -> ResetResult:
        """
        Reset environment for a new episode.
        
        Args:
            task_id: Task to run (easy_triage, medium_categorize, hard_respond)
        
        Returns:
            ResetResult with initial observation and info
        
        Raises:
            ValueError: if task_id is unknown
        """
        if task_id not in self.tasks_config:
            raise ValueError(f"Unknown task_id: {task_id}")
        
        task = self.tasks_config[task_id]
        
        # Load emails for this task
        self.inbox = [self.emails_dict[eid] for eid in task.email_ids if eid in self.emails_dict]
        
        # Reset state
        self.current_task_id = task_id
        self.current_step = 0
        self.max_steps = task.max_steps
        self.done = False
        self.cumulative_reward = 0.0
        self.processed = []
        self._initialized = True
        
        # Build task-specific instructions
        if task_id == "easy_triage":
            instructions = (
                "You are an email triage agent. For each email, assign a priority level (HIGH, MEDIUM, or LOW). "
                "HIGH priority emails are urgent, require immediate action, or have business impact. "
                "LOW priority emails are newsletters, casual communications, or low-impact. "
                "MEDIUM priority emails are important but not immediately urgent. "
                "Respond with only valid JSON: {\"action_type\": \"triage\", \"email_id\": \"<id>\", \"priority\": \"<HIGH|MEDIUM|LOW>\"}"
            )
        elif task_id == "medium_categorize":
            instructions = (
                "You are an email categorization agent. For each email, assign a priority AND category. "
                "Priority: HIGH (urgent/high impact), MEDIUM (important), LOW (low impact). "
                "Category: Support (customer issues), Sales (deals/partnerships), HR (personnel), "
                "Legal (contracts/compliance), Finance (payments/budgets), Spam (unsolicited). "
                "Respond with only valid JSON: {\"action_type\": \"categorize\", \"email_id\": \"<id>\", "
                "\"priority\": \"<HIGH|MEDIUM|LOW>\", \"category\": \"<Support|Sales|HR|Legal|Finance|Spam>\"}"
            )
        else:  # hard_respond
            instructions = (
                "You are a comprehensive email triage agent. For each email: "
                "1. Assign priority (HIGH/MEDIUM/LOW) and category (Support/Sales/HR/Legal/Finance/Spam). "
                "2. For HIGH+sensitive emails, draft a substantive response (40-80 words) acknowledging the issue. "
                "For HIGH emails: use action_type 'triage_and_respond' with all three fields. "
                "For other emails: use action_type 'categorize' with priority and category. "
                "Response should be professional, specific to the problem, and actionable."
            )
        
        observation = Observation(
            inbox=self.inbox,
            processed=self.processed,
            current_step=self.current_step,
            task_id=self.current_task_id,
            instructions=instructions,
            remaining_emails=len(self.inbox)
        )
        
        info = {
            "task_id": task_id,
            "max_steps": self.max_steps,
            "difficulty": task.difficulty,
            "reward_threshold": task.reward_threshold,
            "total_emails": len(self.inbox)
        }
        
        return ResetResult(observation=observation, info=info)
    
    def step(self, action: Action) -> StepResult:
        """
        Execute one step: process an email with the given action.
        
        Args:
            action: Action specifying email_id, priority, category, response_draft
        
        Returns:
            StepResult with observation, reward, done flag, info
        
        Raises:
            RuntimeError: if environment not initialized or episode already done
        """
        if not self._initialized:
            raise RuntimeError("Must call reset() before step()")
        if self.done:
            raise RuntimeError("Episode already done, call reset() to start new episode")
        
        # Initialize reward computation
        raw_reward = 0.0
        penalties = 0.0
        priority_correct = None
        category_correct = None
        response_quality = None
        message = ""
        
        # Validate email_id exists
        email = self.emails_dict.get(action.email_id)
        if not email:
            penalties += 0.1
            message = f"Email {action.email_id} not found"
        else:
            # Check if already processed
            if any(pe.email_id == action.email_id for pe in self.processed):
                penalties += 0.05
                message = f"Email {action.email_id} already processed"
            else:
                # Handle skip action
                if action.action_type == "skip":
                    penalties += 0.05
                    message = "Skipped email"
                else:
                    # Validate task-specific action type
                    task = self.tasks_config[self.current_task_id]
                    if task.difficulty == "easy" and action.action_type != "triage":
                        penalties += 0.1
                        message = f"task {self.current_task_id} requires action_type='triage', got '{action.action_type}'"
                    elif task.difficulty in ["medium", "hard"]:
                        if action.action_type not in ["categorize", "triage_and_respond"]:
                            penalties += 0.1
                            message = f"Invalid action_type '{action.action_type}' for {task.difficulty} task"
                    
                    # Reward computation per task
                    if not penalties:  # Only compute rewards if no validation errors
                        if self.current_task_id == "easy_triage":
                            raw_reward = self._compute_easy_reward(action, email)
                            priority_correct = (action.priority == email.gt_priority or
                                              (action.priority == "MEDIUM" and email.gt_priority in ["HIGH", "LOW"]))
                            message = f"Priority: {action.priority} (gt: {email.gt_priority})"
                        
                        elif self.current_task_id == "medium_categorize":
                            raw_reward, priority_correct, category_correct = self._compute_medium_reward(action, email)
                            message = f"Priority: {action.priority} (gt: {email.gt_priority}), Category: {action.category} (gt: {email.gt_category})"
                        
                        elif self.current_task_id == "hard_respond":
                            raw_reward, priority_correct, category_correct, response_quality = self._compute_hard_reward(action, email)
                            message = f"Priority: {action.priority}, Category: {action.category}"
                            if response_quality is not None:
                                message += f", Response Quality: {response_quality:.2f}"
        
        # Clamp final reward
        final_reward_value = max(-0.5, raw_reward - penalties)
        
        # Record processed email
        if email:
            processed = ProcessedEmail(
                email_id=action.email_id,
                priority=action.priority,
                category=action.category,
                response_draft=action.response_draft,
                reward=final_reward_value
            )
            self.processed.append(processed)
        
        # Update cumulative reward
        self.cumulative_reward += final_reward_value
        self.current_step += 1
        
        # Check if done
        self.done = (self.current_step >= self.max_steps) or len(self.processed) >= len(self.inbox)
        
        # Build observation
        remaining_inbox = [e for e in self.inbox if e.id not in [p.email_id for p in self.processed]]
        observation = Observation(
            inbox=remaining_inbox,
            processed=self.processed,
            current_step=self.current_step,
            task_id=self.current_task_id,
            instructions="Continue processing remaining emails.",
            remaining_emails=len(remaining_inbox)
        )
        
        # Build reward
        reward = Reward(
            value=final_reward_value,
            priority_correct=priority_correct,
            category_correct=category_correct,
            response_quality=response_quality,
            penalty=penalties,
            message=message
        )
        
        # Build info
        info = {
            "email_id": action.email_id,
            "action_type": action.action_type,
            "step": self.current_step,
            "cumulative_reward": self.cumulative_reward
        }
        
        return StepResult(observation=observation, reward=reward, done=self.done, info=info)
    
    def state(self) -> EnvironmentState:
        """
        Return complete environment state snapshot.
        
        Returns:
            EnvironmentState with all current values including episode_score
        """
        if not self._initialized:
            raise RuntimeError("Must call reset() before state()")
        
        # Compute episode score
        episode_score = grade_task(self.current_task_id, self.processed, self.emails_dict)
        
        return EnvironmentState(
            task_id=self.current_task_id,
            current_step=self.current_step,
            max_steps=self.max_steps,
            done=self.done,
            emails_total=len(self.inbox),
            emails_processed=len(self.processed),
            cumulative_reward=self.cumulative_reward,
            processed=self.processed,
            episode_score=episode_score
        )
    
    # ========================================================================
    # Helper methods for reward computation
    # ========================================================================
    
    def _compute_easy_reward(self, action: Action, email: Email) -> float:
        """
        Compute step reward for easy_triage task.
        
        Scoring:
        - 1.0: correct priority
        - 0.5: MEDIUM when should be HIGH/LOW
        - 0.0: wrong direction
        
        Penalties:
        - -0.1: priority missing
        """
        if action.priority is None:
            return -0.1
        
        if action.priority == email.gt_priority:
            return 1.0
        elif action.priority == "MEDIUM" and email.gt_priority in ["HIGH", "LOW"]:
            return 0.5
        else:
            return 0.0
    
    def _compute_medium_reward(self, action: Action, email: Email) -> tuple:
        """
        Compute step reward for medium_categorize task.
        
        Returns: (reward, priority_correct, category_correct)
        """
        penalties = 0.0
        priority_correct = False
        category_correct = False
        
        # Priority scoring
        if action.priority is None:
            penalties += 0.1
            priority_score = 0.0
        elif action.priority == email.gt_priority:
            priority_score = 1.0
            priority_correct = True
        elif action.priority == "MEDIUM" and email.gt_priority in ["HIGH", "LOW"]:
            priority_score = 0.2
        elif email.gt_priority == "MEDIUM" and action.priority in ["HIGH", "LOW"]:
            priority_score = 0.2
        else:
            priority_score = 0.0
        
        # Category scoring
        if action.category is None:
            penalties += 0.1
            category_score = 0.0
        elif action.category == email.gt_category:
            category_score = 1.0
            category_correct = True
        else:
            category_score = 0.0
        
        raw_reward = 0.4 * priority_score + 0.6 * category_score - penalties
        return (raw_reward, priority_correct, category_correct)
    
    def _compute_hard_reward(self, action: Action, email: Email) -> tuple:
        """
        Compute step reward for hard_respond task.
        
        Returns: (reward, priority_correct, category_correct, response_quality)
        """
        penalties = 0.0
        priority_correct = False
        category_correct = False
        response_quality = None
        
        # Priority scoring
        if action.priority is None:
            penalties += 0.1
            priority_score = 0.0
        elif action.priority == email.gt_priority:
            priority_score = 0.4
            priority_correct = True
        elif action.priority == "MEDIUM" and email.gt_priority in ["HIGH", "LOW"]:
            priority_score = 0.2
        elif email.gt_priority == "MEDIUM" and action.priority in ["HIGH", "LOW"]:
            priority_score = 0.2
        else:
            priority_score = 0.0
        
        # Category scoring
        if action.category is None:
            penalties += 0.1
            category_score = 0.0
        elif action.category == email.gt_category:
            category_score = 0.6
            category_correct = True
        else:
            category_score = 0.0
        
        # Response quality scoring (for HIGH+needs_response emails)
        response_reward = 0.0
        if email.gt_priority == "HIGH" and email.needs_response:
            if action.response_draft is None:
                penalties += 0.15
                response_quality = 0.0
            else:
                # Compute response quality
                response_draft = action.response_draft
                word_count = len(response_draft.split())
                
                # Keyword coverage
                if email.response_keywords:
                    keywords_found = sum(
                        1 for kw in email.response_keywords
                        if kw.lower() in response_draft.lower()
                    )
                    keyword_coverage = keywords_found / len(email.response_keywords)
                else:
                    keyword_coverage = 0.0
                
                # Length bonus
                if word_count >= 30:
                    length_bonus = 0.15
                elif word_count >= 15:
                    length_bonus = 0.05
                else:
                    length_bonus = 0.0
                
                response_quality = min(1.0, keyword_coverage * 0.85 + length_bonus)
                response_reward = response_quality * 0.5
        
        raw_reward = priority_score + category_score + response_reward - penalties
        return (raw_reward, priority_correct, category_correct, response_quality)
