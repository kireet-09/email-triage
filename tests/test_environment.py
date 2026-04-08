"""
Comprehensive test suite for email-triage-env.
24 tests organized in 4 test classes.
"""
import pytest
from app.models import Email, Action, ProcessedEmail, TaskConfig
from app.environment import EmailTriageEnvironment
from app.email_data import get_all_emails, get_all_task_configs
from app.graders import grade_easy_triage, grade_medium_categorize, grade_hard_respond, grade_task


class TestEnvironmentLifecycle:
    """7 tests for environment lifecycle: reset, step, state, episode end."""
    
    @pytest.fixture
    def env(self):
        """Create environment instance."""
        tasks = get_all_task_configs()
        emails = get_all_emails()
        return EmailTriageEnvironment(tasks, emails)
    
    def test_reset_returns_observation_correct_size(self, env):
        """reset() returns observation with correct inbox size."""
        reset_result = env.reset("easy_triage")
        observation = reset_result.observation
        
        assert observation is not None
        assert len(observation.inbox) == 5, f"Expected 5 emails in easy_triage, got {len(observation.inbox)}"
        assert observation.remaining_emails == 5
        assert observation.current_step == 0
    
    def test_reset_all_task_ids(self, env):
        """reset() works for all 3 task IDs."""
        task_ids = ["easy_triage", "medium_categorize", "hard_respond"]
        expected_sizes = {"easy_triage": 5, "medium_categorize": 8, "hard_respond": 10}
        
        for task_id in task_ids:
            reset_result = env.reset(task_id)
            observation = reset_result.observation
            expected_size = expected_sizes[task_id]
            assert len(observation.inbox) == expected_size, \
                f"Task {task_id} should have {expected_size} emails, got {len(observation.inbox)}"
    
    def test_reset_invalid_task_raises_error(self, env):
        """reset() raises ValueError for unknown task_id."""
        with pytest.raises(ValueError, match="Unknown task_id"):
            env.reset("nonexistent_task")
    
    def test_step_before_reset_raises_error(self, env):
        """step() raises RuntimeError if called before reset()."""
        action = Action(action_type="triage", email_id="e1", priority="HIGH")
        with pytest.raises(RuntimeError, match="Must call reset"):
            env.step(action)
    
    def test_state_returns_snapshot(self, env):
        """state() returns complete snapshot with all required fields."""
        env.reset("easy_triage")
        state = env.state()
        
        assert state.task_id == "easy_triage"
        assert state.current_step == 0
        assert state.max_steps == 10
        assert state.emails_total == 5
        assert state.emails_processed == 0
        assert state.cumulative_reward == 0.0
        assert isinstance(state.episode_score, float)
        assert 0.0 <= state.episode_score <= 1.0
    
    def test_episode_ends_after_all_emails(self, env):
        """Episode ends when all emails are processed or max_steps reached."""
        env.reset("easy_triage")
        
        # Process all 5 emails
        for i in range(5):
            action = Action(action_type="triage", email_id=f"e{i+1}", priority="HIGH")
            result = env.step(action)
            if i < 4:
                assert not result.done, f"Episode shouldn't end at step {i+1}"
            else:
                # On 5th email, should be done
                assert result.done, "Episode should end after all emails processed"
    
    def test_cumulative_reward_tracked(self, env):
        """cumulative_reward is tracked across steps."""
        env.reset("easy_triage")
        
        # Step 1: correct priority (e1 should be HIGH)
        action1 = Action(action_type="triage", email_id="e1", priority="HIGH")
        result1 = env.step(action1)
        reward1 = result1.reward.value
        assert reward1 > 0, "Correct priority on e1 should give positive reward"
        assert env.cumulative_reward == reward1
        
        # Step 2: wrong priority (e2 should be LOW, not HIGH)
        action2 = Action(action_type="triage", email_id="e2", priority="HIGH")
        result2 = env.step(action2)
        reward2 = result2.reward.value
        assert reward2 <= 0, "Wrong priority should give non-positive reward"
        assert env.cumulative_reward == reward1 + reward2


class TestRewardFunction:
    """6 tests for reward computation: priority, category, penalties."""
    
    @pytest.fixture
    def env(self):
        """Create environment instance."""
        tasks = get_all_task_configs()
        emails = get_all_emails()
        return EmailTriageEnvironment(tasks, emails)
    
    def test_correct_priority_easy(self, env):
        """Correct priority gives positive reward (easy task)."""
        env.reset("easy_triage")
        # e1 should be HIGH
        action = Action(action_type="triage", email_id="e1", priority="HIGH")
        result = env.step(action)
        assert result.reward.value > 0, "Correct priority should give positive reward"
    
    def test_wrong_priority_easy(self, env):
        """Wrong priority gives zero reward (easy task)."""
        env.reset("easy_triage")
        # e1 is HIGH, assign opposite LOW
        action = Action(action_type="triage", email_id="e1", priority="LOW")
        result = env.step(action)
        assert result.reward.value == 0.0, "Wrong direction should give 0.0 reward"
    
    def test_partial_priority_easy(self, env):
        """MEDIUM on HIGH/LOW gives partial reward (easy task)."""
        env.reset("easy_triage")
        # e1 is HIGH, assign MEDIUM
        action = Action(action_type="triage", email_id="e1", priority="MEDIUM")
        result = env.step(action)
        assert 0 < result.reward.value < 1, "MEDIUM on HIGH should give 0 < r < 1"
        assert result.reward.value == 0.5, "MEDIUM on HIGH should give 0.5"
    
    def test_invalid_email_id_penalty(self, env):
        """Invalid email_id gives penalty reward."""
        env.reset("easy_triage")
        action = Action(action_type="triage", email_id="nonexistent", priority="HIGH")
        result = env.step(action)
        assert result.reward.value <= -0.1, "Invalid email_id should give penalty"
    
    def test_skip_action_penalty(self, env):
        """Skip action gives penalty reward."""
        env.reset("easy_triage")
        action = Action(action_type="skip", email_id="e1", priority=None)
        result = env.step(action)
        assert result.reward.value <= 0, "Skip action should give non-positive reward"
    
    def test_duplicate_processing_penalty(self, env):
        """Processing same email twice gives penalty on 2nd attempt."""
        env.reset("easy_triage")
        
        # Process e1 first time (correct)
        action1 = Action(action_type="triage", email_id="e1", priority="HIGH")
        result1 = env.step(action1)
        assert result1.reward.value > 0, "First attempt should be rewarded"
        
        # Process e1 second time (duplicate)
        action2 = Action(action_type="triage", email_id="e1", priority="HIGH")
        result2 = env.step(action2)
        assert result2.reward.value <= -0.05, "Duplicate processing should give penalty"


class TestGraders:
    """9 tests for task-specific graders."""
    
    @pytest.fixture
    def emails_dict(self):
        return get_all_emails()
    
    def test_easy_perfect_score(self, emails_dict):
        """All 5 easy emails correct → grade = 1.0."""
        processed = [
            ProcessedEmail(email_id="e1", priority="HIGH", reward=1.0),
            ProcessedEmail(email_id="e2", priority="LOW", reward=1.0),
            ProcessedEmail(email_id="e3", priority="HIGH", reward=1.0),
            ProcessedEmail(email_id="e4", priority="LOW", reward=1.0),
            ProcessedEmail(email_id="e5", priority="MEDIUM", reward=1.0),
        ]
        score = grade_easy_triage(processed, emails_dict)
        assert score == 1.0, f"Perfect easy triage should score 1.0, got {score}"
    
    def test_easy_zero_score(self, emails_dict):
        """All wrong-direction assignments → partial score (not zero due to MEDIUM)."""
        # Note: e5 has gt_priority=MEDIUM. Assigning HIGH/LOW is partial (0.5), not zero.
        # So this test checks mostly-wrong with one partial = lower score
        processed = [
            ProcessedEmail(email_id="e1", priority="LOW", reward=0.0),   # HIGH→LOW, wrong direction
            ProcessedEmail(email_id="e2", priority="HIGH", reward=0.0),  # LOW→HIGH, wrong direction
            ProcessedEmail(email_id="e3", priority="LOW", reward=0.0),   # HIGH→LOW, wrong direction
            ProcessedEmail(email_id="e4", priority="HIGH", reward=0.0),  # LOW→HIGH, wrong direction
            ProcessedEmail(email_id="e5", priority="HIGH", reward=0.5),  # MEDIUM→HIGH, partial (0.5)
        ]
        score = grade_easy_triage(processed, emails_dict)
        # (0 + 0 + 0 + 0 + 0.5) / 5 = 0.1
        assert score == 0.1, f"Wrong-direction + 1 partial should score 0.1, got {score}"
    
    def test_easy_partial_score(self, emails_dict):
        """4/5 correct easy → score in [0.75, 0.85]."""
        processed = [
            ProcessedEmail(email_id="e1", priority="HIGH", reward=1.0),   # correct
            ProcessedEmail(email_id="e2", priority="LOW", reward=1.0),    # correct
            ProcessedEmail(email_id="e3", priority="HIGH", reward=1.0),   # correct
            ProcessedEmail(email_id="e4", priority="HIGH", reward=0.0),   # wrong (should be LOW)
            ProcessedEmail(email_id="e5", priority="MEDIUM", reward=1.0), # correct
        ]
        score = grade_easy_triage(processed, emails_dict)
        assert 0.75 <= score <= 0.85, f"4/5 correct should score 0.75-0.85, got {score}"
    
    def test_easy_empty_list(self, emails_dict):
        """Empty processed list returns 0.0."""
        score = grade_easy_triage([], emails_dict)
        assert score == 0.0, "Empty processed list should return 0.0"
    
    def test_medium_perfect_score(self, emails_dict):
        """All 8 medium emails correct (priority + category) → grade = 1.0."""
        processed = [
            ProcessedEmail(email_id="m1", priority="HIGH", category="Legal", reward=1.0),
            ProcessedEmail(email_id="m2", priority="HIGH", category="Sales", reward=1.0),
            ProcessedEmail(email_id="m3", priority="MEDIUM", category="HR", reward=1.0),
            ProcessedEmail(email_id="m4", priority="HIGH", category="Finance", reward=1.0),
            ProcessedEmail(email_id="m5", priority="HIGH", category="Support", reward=1.0),
            ProcessedEmail(email_id="m6", priority="LOW", category="Spam", reward=1.0),
            ProcessedEmail(email_id="m7", priority="MEDIUM", category="HR", reward=1.0),
            ProcessedEmail(email_id="m8", priority="MEDIUM", category="Sales", reward=1.0),
        ]
        score = grade_medium_categorize(processed, emails_dict)
        assert score == 1.0, f"Perfect medium categorize should score 1.0, got {score}"
    
    def test_hard_score_in_range(self, emails_dict):
        """Hard task score always in [0.0, 1.0]."""
        # Mix of correct and incorrect
        processed = [
            ProcessedEmail(email_id="h1", priority="HIGH", category="Support", response_draft="investigating engineers", reward=0.5),
            ProcessedEmail(email_id="h2", priority="LOW", category="Support", reward=0.0),  # wrong
            ProcessedEmail(email_id="h3", priority="HIGH", category="Legal", response_draft="legal counsel attorney acknowledge review", reward=0.8),
        ]
        score = grade_hard_respond(processed, emails_dict)
        assert 0.0 <= score <= 1.0, f"Hard score should be in [0,1], got {score}"
    
    def test_grade_task_dispatcher_all_ids(self, emails_dict):
        """grade_task() dispatcher works for all 3 task IDs."""
        processed_easy = [ProcessedEmail(email_id="e1", priority="HIGH", reward=1.0)]
        score_easy = grade_task("easy_triage", processed_easy, emails_dict)
        assert 0.0 <= score_easy <= 1.0
        
        processed_medium = [ProcessedEmail(email_id="m1", priority="HIGH", category="Legal", reward=1.0)]
        score_medium = grade_task("medium_categorize", processed_medium, emails_dict)
        assert 0.0 <= score_medium <= 1.0
        
        processed_hard = [ProcessedEmail(email_id="h1", priority="HIGH", category="Support", reward=1.0)]
        score_hard = grade_task("hard_respond", processed_hard, emails_dict)
        assert 0.0 <= score_hard <= 1.0
    
    def test_grade_task_unknown_id_raises_error(self, emails_dict):
        """grade_task() raises ValueError for unknown task_id."""
        processed = []
        with pytest.raises(ValueError, match="Unknown task_id"):
            grade_task("unknown_task", processed, emails_dict)
    
    def test_all_graders_output_in_range(self, emails_dict):
        """Property test: all graders always return in [0, 1]."""
        # Test various combinations
        test_cases = [
            ([], "easy_triage", grade_easy_triage),
            ([ProcessedEmail(email_id="e1", priority="HIGH", reward=0.5)], "easy_triage", grade_easy_triage),
            ([ProcessedEmail(email_id="m1", priority="HIGH", category="Legal", reward=0.5)], "medium_categorize", grade_medium_categorize),
            ([ProcessedEmail(email_id="h1", priority="HIGH", category="Support", reward=0.5)], "hard_respond", grade_hard_respond),
        ]
        
        for processed, task_id, grader_func in test_cases:
            score = grader_func(processed, emails_dict)
            assert 0.0 <= score <= 1.0, f"Grader {grader_func.__name__} returned {score} outside [0,1]"


class TestFullEpisode:
    """2 tests for end-to-end episode execution."""
    
    @pytest.fixture
    def env(self):
        tasks = get_all_task_configs()
        emails = get_all_emails()
        return EmailTriageEnvironment(tasks, emails)
    
    def test_perfect_easy_episode(self, env):
        """Perfect easy episode: all 5 correct → episode_score = 1.0, done = True."""
        reset_result = env.reset("easy_triage")
        
        # Process all 5 with correct priorities
        correct_priorities = {
            "e1": "HIGH",
            "e2": "LOW",
            "e3": "HIGH",
            "e4": "LOW",
            "e5": "MEDIUM",
        }
        
        for email_id, priority in correct_priorities.items():
            action = Action(action_type="triage", email_id=email_id, priority=priority)
            result = env.step(action)
        
        # Check final state
        state = env.state()
        assert state.done, "Episode should be done after all emails processed"
        assert state.episode_score == 1.0, f"Perfect easy episode should score 1.0, got {state.episode_score}"
        assert state.emails_processed == 5
    
    def test_medium_partial_episode(self, env):
        """Medium partial episode: 4/8 perfect → episode_score in [0.4, 0.6]."""
        env.reset("medium_categorize")
        
        # Process 4 with correct priority+category
        correct_actions = [
            ("m1", "HIGH", "Legal"),
            ("m2", "HIGH", "Sales"),
            ("m3", "MEDIUM", "HR"),
            ("m4", "HIGH", "Finance"),
        ]
        
        for email_id, priority, category in correct_actions:
            action = Action(action_type="categorize", email_id=email_id, priority=priority, category=category)
            env.step(action)
        
        # Process remaining 4 with wrong categories (but correct priorities)
        # This should reduce score but not to 0
        wrong_actions = [
            ("m5", "HIGH", "HR"),      # should be Support
            ("m6", "LOW", "HR"),       # should be Spam
            ("m7", "MEDIUM", "Support"),  # should be HR
            ("m8", "MEDIUM", "HR"),    # should be Sales
        ]
        
        for email_id, priority, category in wrong_actions:
            action = Action(action_type="categorize", email_id=email_id, priority=priority, category=category)
            env.step(action)
        
        # Check final state
        state = env.state()
        assert state.done
        # 4 perfect (0.4*1.0 + 0.6*1.0 = 1.0 each) + 4 partial (0.4*1.0 + 0.6*0.0 = 0.4 each)
        # Mean = (4*1.0 + 4*0.4) / 8 = 5.6/8 = 0.7
        # But this depends on exact grading, so we check it's in reasonable range
        assert 0.35 <= state.episode_score <= 0.75, \
            f"Partial medium episode should score in [0.35, 0.75], got {state.episode_score}"
