"""
Task graders for email-triage-env.
Score agent performance based on priority/category/response correctness.
"""
from typing import Dict, List
from app.models import Email, ProcessedEmail


def grade_easy_triage(
    processed_emails: List[ProcessedEmail],
    emails_dict: Dict[str, Email]
) -> float:
    """
    Grade easy triage task: priority assignment only.
    
    Scoring per email:
    - 1.0: correct priority
    - 0.5: MEDIUM when should be HIGH or LOW (partial credit)
    - 0.0: wrong direction (HIGH→LOW or LOW→HIGH)
    
    Returns: mean score, clamped to [0.0, 1.0]
    """
    if not processed_emails:
        return 0.0
    
    scores = []
    for pe in processed_emails:
        email = emails_dict.get(pe.email_id)
        if not email:
            scores.append(0.0)
            continue
        
        if pe.priority == email.gt_priority:
            scores.append(1.0)
        elif pe.priority == "MEDIUM" and email.gt_priority in ["HIGH", "LOW"]:
            scores.append(0.5)
        elif email.gt_priority == "MEDIUM" and pe.priority in ["HIGH", "LOW"]:
            scores.append(0.5)
        else:
            scores.append(0.0)
    
    final_score = sum(scores) / len(scores)
    return max(0.0, min(1.0, final_score))


def grade_medium_categorize(
    processed_emails: List[ProcessedEmail],
    emails_dict: Dict[str, Email]
) -> float:
    """
    Grade medium categorize task: priority + category.
    
    Scoring per email: 0.4 × priority_score + 0.6 × category_score
    
    Priority scoring:
    - 1.0: correct
    - 0.2: MEDIUM when should be HIGH/LOW (partial)
    - 0.0: wrong
    
    Category scoring:
    - 1.0: correct
    - 0.0: wrong
    
    Note: missing fields handled as 0.0 in step function (penalty applied there)
    
    Returns: mean score, clamped to [0.0, 1.0]
    """
    if not processed_emails:
        return 0.0
    
    scores = []
    for pe in processed_emails:
        email = emails_dict.get(pe.email_id)
        if not email:
            scores.append(0.0)
            continue
        
        # Priority score
        if pe.priority == email.gt_priority:
            priority_score = 1.0
        elif pe.priority == "MEDIUM" and email.gt_priority in ["HIGH", "LOW"]:
            priority_score = 0.2
        elif email.gt_priority == "MEDIUM" and pe.priority in ["HIGH", "LOW"]:
            priority_score = 0.2
        else:
            priority_score = 0.0
        
        # Category score
        category_score = 1.0 if pe.category == email.gt_category else 0.0
        
        # Weighted score
        email_score = 0.4 * priority_score + 0.6 * category_score
        scores.append(email_score)
    
    final_score = sum(scores) / len(scores)
    return max(0.0, min(1.0, final_score))


def grade_hard_respond(
    processed_emails: List[ProcessedEmail],
    emails_dict: Dict[str, Email]
) -> float:
    """
    Grade hard respond task: priority + category + response quality.
    
    Scoring per email depends on email type:
    - If HIGH+needs_response: 0.30×priority + 0.30×category + 0.40×response_quality
    - Else: 0.50×priority + 0.50×category
    
    Priority scoring:
    - 1.0: correct
    - 0.25: MEDIUM when should be HIGH/LOW (partial)
    - 0.0: wrong
    
    Category scoring:
    - 1.0: correct
    - 0.0: wrong
    
    Response quality (for HIGH+needs_response emails):
    - keyword_coverage: fraction of expected keywords found in response_draft
    - length_bonus: 0.15 if ≥30 words, 0.05 if ≥15 words, else 0.0
    - quality = min(1.0, keyword_coverage × 0.85 + length_bonus)
    
    Returns: weighted mean score, clamped to [0.0, 1.0]
    """
    if not processed_emails:
        return 0.0
    
    scores = []
    for pe in processed_emails:
        email = emails_dict.get(pe.email_id)
        if not email:
            scores.append(0.0)
            continue
        
        # Priority score
        if pe.priority == email.gt_priority:
            priority_score = 1.0
        elif pe.priority == "MEDIUM" and email.gt_priority in ["HIGH", "LOW"]:
            priority_score = 0.25
        elif email.gt_priority == "MEDIUM" and pe.priority in ["HIGH", "LOW"]:
            priority_score = 0.25
        else:
            priority_score = 0.0
        
        # Category score
        category_score = 1.0 if pe.category == email.gt_category else 0.0
        
        # Response quality score (only for HIGH+needs_response emails)
        if email.gt_priority == "HIGH" and email.needs_response:
            # Compute response quality
            response_draft = pe.response_draft or ""
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
            
            # Response quality
            response_quality = min(1.0, keyword_coverage * 0.85 + length_bonus)
            
            # Weighted score for HIGH+needs_response
            email_score = 0.30 * priority_score + 0.30 * category_score + 0.40 * response_quality
        else:
            # Weighted score for other emails
            email_score = 0.50 * priority_score + 0.50 * category_score
        
        scores.append(email_score)
    
    final_score = sum(scores) / len(scores)
    return max(0.0, min(1.0, final_score))


def grade_task(
    task_id: str,
    processed_emails: List[ProcessedEmail],
    emails_dict: Dict[str, Email]
) -> float:
    """
    Route to correct grader based on task_id.
    
    Args:
        task_id: Task identifier (easy_triage, medium_categorize, or hard_respond)
        processed_emails: List of ProcessedEmail results
        emails_dict: Dictionary of all emails by ID
    
    Returns:
        Task score in [0.0, 1.0]
    
    Raises:
        ValueError: if task_id is unknown
    """
    if task_id == "easy_triage":
        return grade_easy_triage(processed_emails, emails_dict)
    elif task_id == "medium_categorize":
        return grade_medium_categorize(processed_emails, emails_dict)
    elif task_id == "hard_respond":
        return grade_hard_respond(processed_emails, emails_dict)
    else:
        raise ValueError(f"Unknown task_id: {task_id}")
