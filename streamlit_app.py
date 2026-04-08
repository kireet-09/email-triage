"""
Streamlit UI for Email Triage Environment
Interactive interface to test email triage tasks
"""
import streamlit as st
import requests
import json
import os
from datetime import datetime
import time

# ============================================================================
# Configuration
# ============================================================================

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:7860")
HF_TOKEN = os.getenv("HF_TOKEN", "")

# Page configuration
st.set_page_config(
    page_title="Email Triage Environment",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================================
# Sidebar Configuration
# ============================================================================

st.sidebar.title("⚙️ Configuration")

# Select environment mode
mode = st.sidebar.radio(
    "Mode:",
    ["Local (localhost:7860)", "Remote Server"],
    help="Select whether the API is running locally or remotely"
)

if mode == "Remote Server":
    api_url = st.sidebar.text_input(
        "API URL:",
        value=API_BASE_URL,
        help="Enter the URL of the running Environment API"
    )
else:
    api_url = "http://localhost:7860"

st.sidebar.markdown("---")

# Task selection
st.sidebar.subheader("📋 Task Selection")
task_options = {
    "Easy: Email Triage": "easy_triage",
    "Medium: Email Categorization": "medium_categorize",
    "Hard: Email Response": "hard_respond",
}
selected_task = st.sidebar.selectbox(
    "Select Task:",
    list(task_options.keys()),
    help="Choose the email triage task"
)
task_id = task_options[selected_task]

st.sidebar.markdown("---")
st.sidebar.info(
    "📌 **How to Use:**\n\n"
    "1. Select a task from the list\n"
    "2. Click 'Reset Environment'\n"
    "3. View the email and make actions\n"
    "4. Watch reward computation\n"
    "5. Complete the episode"
)

# ============================================================================
# Main Content
# ============================================================================

st.title("📧 Email Triage OpenEnv")
st.markdown("Interactive testing interface for email classification and response tasks")

# Initialize session state
if "episode_active" not in st.session_state:
    st.session_state.episode_active = False
if "current_state" not in st.session_state:
    st.session_state.current_state = None
if "step_count" not in st.session_state:
    st.session_state.step_count = 0
if "cumulative_reward" not in st.session_state:
    st.session_state.cumulative_reward = 0.0
if "episode_steps" not in st.session_state:
    st.session_state.episode_steps = []

# ============================================================================
# Helper Functions
# ============================================================================

def call_api(endpoint: str, method: str = "POST", data: dict = None) -> dict:
    """Call the environment API and return response."""
    try:
        url = f"{api_url}{endpoint}"
        if method == "POST":
            response = requests.post(url, json=data, timeout=10)
        else:
            response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": f"API Error: {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def reset_environment():
    """Reset the environment for a new episode."""
    result = call_api("/reset", method="POST", data={"task_id": task_id})
    if result["success"]:
        st.session_state.episode_active = True
        st.session_state.current_state = result["data"]
        st.session_state.step_count = 0
        st.session_state.cumulative_reward = 0.0
        st.session_state.episode_steps = []
        return True, "✅ Environment reset successfully"
    else:
        return False, f"❌ Reset failed: {result['error']}"


def step_environment(action: dict):
    """Execute an action in the environment."""
    result = call_api("/step", method="POST", data=action)
    if result["success"]:
        step_result = result["data"]
        st.session_state.step_count += 1
        st.session_state.current_state = step_result.get("state", {})
        
        reward_value = step_result.get("reward", {}).get("value", 0.0)
        st.session_state.cumulative_reward += reward_value
        
        st.session_state.episode_steps.append({
            "step": st.session_state.step_count,
            "action": action,
            "reward": step_result.get("reward"),
            "done": step_result.get("done"),
        })
        
        if step_result.get("done"):
            st.session_state.episode_active = False
        
        return True, step_result
    else:
        return False, result["error"]


# ============================================================================
# Main UI
# ============================================================================

col1, col2 = st.columns([2, 1])

with col1:
    st.header(f"🎯 {selected_task}")
    st.markdown(f"**Task ID:** `{task_id}`")

with col2:
    if st.button("🔄 Reset Environment", key="reset_btn", use_container_width=True):
        success, message = reset_environment()
        if success:
            st.success(message)
        else:
            st.error(message)

st.markdown("---")

# ============================================================================
# Display Current State
# ============================================================================

if st.session_state.episode_active and st.session_state.current_state:
    state = st.session_state.current_state
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Step", st.session_state.step_count, delta=None)
    with col2:
        st.metric("Cumulative Reward", f"{st.session_state.cumulative_reward:.3f}")
    with col3:
        remaining = state.get("remaining_emails", 0)
        st.metric("Emails Remaining", remaining)
    with col4:
        done = state.get("done", False)
        status = "✅ Done" if done else "🔄 Active"
        st.markdown(f"**Status:** {status}")
    
    st.markdown("---")
    
    # Email Display
    if state.get("current_email"):
        email = state["current_email"]
        st.subheader("📬 Current Email")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**From:** {email.get('from_', 'Unknown')}")
            st.markdown(f"**Subject:** {email.get('subject', '(no subject)')}")
        with col2:
            st.markdown(f"**Email ID:** `{email.get('email_id', 'N/A')}`")
            st.markdown(f"**Difficulty:** {email.get('difficulty', 'N/A').upper()}")
        
        st.markdown(f"**Body:**\n\n{email.get('body', '(no body)')}")
        
        st.markdown("---")
        
        # Action Input
        st.subheader("✉️ Your Action")
        
        if task_id == "easy_triage":
            st.info("**Task:** Assign a priority level (HIGH, MEDIUM, or LOW)")
            priority = st.selectbox("Priority Level:", ["HIGH", "MEDIUM", "LOW"], key="priority_select")
            
            if st.button("Submit Action", use_container_width=True):
                action = {
                    "action_type": "triage",
                    "email_id": email.get("email_id"),
                    "priority": priority
                }
                success, step_result = step_environment(action)
                if success:
                    reward = step_result.get("reward", {})
                    st.success(f"✅ Action recorded | Reward: {reward.get('value', 0):.3f}")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error(f"❌ Error: {step_result}")
        
        elif task_id == "medium_categorize":
            st.info("**Task:** Assign priority (HIGH/MEDIUM/LOW) AND category")
            col1, col2 = st.columns(2)
            
            with col1:
                priority = st.selectbox("Priority:", ["HIGH", "MEDIUM", "LOW"], key="priority_select_med")
            with col2:
                category = st.selectbox(
                    "Category:",
                    ["Support", "Sales", "HR", "Legal", "Finance", "Spam"],
                    key="category_select"
                )
            
            if st.button("Submit Action", use_container_width=True):
                action = {
                    "action_type": "categorize",
                    "email_id": email.get("email_id"),
                    "priority": priority,
                    "category": category
                }
                success, step_result = step_environment(action)
                if success:
                    reward = step_result.get("reward", {})
                    st.success(f"✅ Action recorded | Reward: {reward.get('value', 0):.3f}")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error(f"❌ Error: {step_result}")
        
        elif task_id == "hard_respond":
            st.info("**Task:** Assign priority, category, AND optionally provide a response (for HIGH priority)")
            col1, col2 = st.columns(2)
            
            with col1:
                priority = st.selectbox("Priority:", ["HIGH", "MEDIUM", "LOW"], key="priority_select_hard")
            with col2:
                category = st.selectbox(
                    "Category:",
                    ["Support", "Sales", "HR", "Legal", "Finance", "Spam"],
                    key="category_select_hard"
                )
            
            response_text = ""
            if priority == "HIGH":
                response_text = st.text_area(
                    "Response (40-80 words for HIGH priority):",
                    placeholder="Enter a professional response draft...",
                    height=100
                )
            
            if st.button("Submit Action", use_container_width=True):
                action = {
                    "action_type": "respond",
                    "email_id": email.get("email_id"),
                    "priority": priority,
                    "category": category,
                }
                if priority == "HIGH" and response_text:
                    action["response"] = response_text
                
                success, step_result = step_environment(action)
                if success:
                    reward = step_result.get("reward", {})
                    st.success(f"✅ Action recorded | Reward: {reward.get('value', 0):.3f}")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error(f"❌ Error: {step_result}")
        
        st.markdown("---")
    
    # Episode Completed
    if state.get("done"):
        st.success("🎉 Episode Completed!")
        col1, col2, col3 = st.columns(3)
        col1.metric("Final Score", f"{state.get('final_result', {}).get('final_score', 0):.3f}")
        col2.metric("Total Reward", f"{st.session_state.cumulative_reward:.3f}")
        col3.metric("Steps Taken", st.session_state.step_count)
        
        # Show episode summary
        st.subheader("📊 Episode Summary")
        for step in st.session_state.episode_steps:
            with st.expander(f"Step {step['step']} - Reward: {step['reward'].get('value', 0):.3f}"):
                st.json(step)

else:
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(
            "📌 **Getting Started:**\n\n"
            "1. Select a task from the sidebar\n"
            "2. Click 'Reset Environment' to start\n"
            "3. Classify the email with appropriate actions\n"
            "4. Complete the entire episode\n\n"
            f"**Current Task:** {selected_task}"
        )
    
    with col2:
        st.markdown("### 📚 Task Descriptions")
        st.markdown(
            "**Easy Triage:**\n"
            "Classify emails by priority (HIGH/MEDIUM/LOW)\n\n"
            "**Medium Categorize:**\n"
            "Assign both priority and department category\n\n"
            "**Hard Respond:**\n"
            "Assign priority, category, AND draft responses for urgent emails"
        )

st.markdown("---")

# Footer
st.markdown(
    "🔗 **API Status:**  "
    f"[{api_url}]({api_url})", unsafe_allow_html=True
)
st.caption("Email Triage OpenEnv Streamlit Interface | 📧 Built for AI agent evaluation")
