import os
import streamlit as st
import google.generativeai as genai
import json

# --- Hardcode your Gemini API key here ---
GEMINI_API_KEY = "AIzaSyDBXmFHpn4mwAN8BzwKlFsim2V0OLjri4I"  # 👈 replace with your working API key
genai.configure(api_key=GEMINI_API_KEY)

# Function to ask Gemini
def ask_gemini(prompt):
    model = genai.GenerativeModel('gemini-1.5-pro-latest')
    chat = model.start_chat()
    response = chat.send_message(prompt)
    return response.text.strip()

# Function to generate question prompt
def generate_question_prompt(role, domain, mode):
    domain_part = f"in {domain}" if domain else ""
    return f"""You are a professional interviewer for the role of {role} {domain_part}.
Conduct a {mode} interview.
Ask ONE realistic and different interview question suitable for the role.
Do NOT add explanations or answers.
"""

# Function to evaluate answer prompt
def evaluate_answer_prompt(answer, role, domain, mode):
    domain_part = f"in {domain}" if domain else ""
    return f"""Evaluate the following {mode.lower()} interview answer for a {role} {domain_part} position:

Answer:
{answer}

Evaluation Criteria:
- Clarity
- Correctness
- Completeness
- (For Behavioral) STAR Format usage
- (For Technical) Technical Accuracy and Problem-Solving Approach

Provide:
- Overall feedback
- Specific areas to improve
- Score out of 10
"""

# Function to save session
def save_session(session_data):
    if not os.path.exists('sessions'):
        os.makedirs('sessions')
    filename = f"session_{session_data['Role']}_{session_data['Mode']}.json"
    filepath = os.path.join('sessions', filename)
    with open(filepath, 'w') as f:
        json.dump(session_data, f, indent=4)
    return filepath

# --- Streamlit App Starts ---
st.set_page_config(page_title="Interview Preparation Bot", page_icon="🎯")
st.title("🎯 AI Interview Preparation Bot")

st.sidebar.header("Interview Setup")
role = st.sidebar.text_input("Target Role", "Software Engineer")
domain = st.sidebar.text_input("Domain (optional)", "Backend")
mode = st.sidebar.selectbox("Interview Mode", ["Technical", "Behavioral"])
num_questions = st.sidebar.slider("Number of Questions", 3, 5, 3)

# Initialize session state
if 'questions' not in st.session_state:
    st.session_state.questions = []
    st.session_state.answers = []
    st.session_state.feedbacks = []
    st.session_state.scores = []
    st.session_state.current_q = 0
    st.session_state.collecting_answers = False

# Button to start interview
if st.sidebar.button("Start Interview"):
    st.session_state.questions = [
        ask_gemini(generate_question_prompt(role, domain, mode)) for _ in range(num_questions)
    ]
    st.session_state.answers = []
    st.session_state.feedbacks = []
    st.session_state.scores = []
    st.session_state.current_q = 0
    st.session_state.collecting_answers = True
    st.rerun()

# If interview is ongoing
if st.session_state.collecting_answers:
    if st.session_state.current_q < len(st.session_state.questions):
        question = st.session_state.questions[st.session_state.current_q]
        st.subheader(f"Question {st.session_state.current_q + 1} of {len(st.session_state.questions)}")
        st.write(question)

        answer = st.text_area("Your Answer:", key=f"answer_{st.session_state.current_q}")

        if st.button("Submit Answer", key=f"submit_{st.session_state.current_q}"):
            if answer.strip() == "":
                st.warning("⚠️ Please write an answer before submitting!")
            else:
                st.session_state.answers.append(answer)
                st.session_state.current_q += 1
                st.rerun()

    else:
        # After all answers collected
        st.success("🎉 All questions answered! Generating feedback...")
        for idx, ans in enumerate(st.session_state.answers):
            feedback_response = ask_gemini(evaluate_answer_prompt(ans, role, domain, mode))
            st.session_state.feedbacks.append(feedback_response)

            # Extract score
            score = 0
            for line in feedback_response.splitlines():
                if "Score" in line:
                    try:
                        score = float(line.split(":")[-1].strip())
                    except:
                        pass
            st.session_state.scores.append(score)

        avg_score = sum(st.session_state.scores) / len(st.session_state.scores)

        st.markdown(f"""
        ## 📋 Final Summary
        - **Average Score**: {avg_score:.2f} / 10
        """)

        st.markdown("### Strengths and Improvements based on feedbacks:")
        for idx, feedback in enumerate(st.session_state.feedbacks, start=1):
            st.markdown(f"**Question {idx}:**")
            st.write(feedback)

        session_data = {
            "Role": role,
            "Domain": domain,
            "Mode": mode,
            "Questions": st.session_state.questions,
            "Answers": st.session_state.answers,
            "Feedbacks": st.session_state.feedbacks,
            "Scores": st.session_state.scores,
            "AverageScore": avg_score
        }

        filepath = save_session(session_data)
        with open(filepath, "r") as f:
            st.download_button(
                label="Download Full Interview Session 📥",
                data=f,
                file_name="interview_session.json",
                mime="application/json"
            )

        # End the interview session
        st.session_state.collecting_answers = False

st.markdown("---")
st.caption("🚀 Built with ❤️ using Google Gemini API")
