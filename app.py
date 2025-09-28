
import streamlit as st
import re
import sqlite3
from datetime import datetime
import pandas as pd

DB_PATH = 'star_to_shine.db'

# --- Database helpers ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS applicants (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    job_role TEXT,
                    experience_years INTEGER,
                    qualification TEXT,
                    email TEXT,
                    phone TEXT,
                    cover TEXT,
                    submitted_at TEXT
                )''')
    conn.commit()
    conn.close()

def save_applicant(data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT INTO applicants (name, job_role, experience_years, qualification, email, phone, cover, submitted_at)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', (
                     data.get('name'),
                     data.get('job_role'),
                     data.get('experience_years'),
                     data.get('qualification'),
                     data.get('email'),
                     data.get('phone'),
                     data.get('cover'),
                     datetime.utcnow().isoformat()
                 ))
    conn.commit()
    conn.close()

def fetch_applicants():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM applicants ORDER BY submitted_at DESC", conn)
    conn.close()
    return df

# --- Simple NLU / Extractors ---
JOB_ROLES = ['full stack developer', 'software engineer', 'ai/ml engineer', 'ui/ux designer', 'data analyst']

def extract_email(text):
    m = re.search(r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', text)
    return m.group(1) if m else None

def extract_phone(text):
    # Simple phone pattern (international and local)
    m = re.search(r'(\+?\d[\d -]{7,}\d)', text)
    return re.sub(r'[^\d+]', '', m.group(1)) if m else None

def extract_years(text):
    # matches "2 years", "3 yrs", "5", "7+ years"
    m = re.search(r'(\d+)\s*(?:\+|plus)?\s*(?:years|yrs|y)?', text)
    return int(m.group(1)) if m else None

def extract_job_role(text):
    text_l = text.lower()
    for role in JOB_ROLES:
        if role in text_l:
            return role.title()
    # try keyword mapping
    if 'full' in text_l and 'stack' in text_l:
        return 'Full Stack Developer'
    if 'software' in text_l and 'engineer' in text_l:
        return 'Software Engineer'
    if 'ai' in text_l or 'ml' in text_l:
        return 'AI/ML Engineer'
    if 'ui' in text_l or 'ux' in text_l:
        return 'UI/UX Designer'
    if 'data' in text_l and 'analyst' in text_l:
        return 'Data Analyst'
    return None

def extract_qualification(text):
    quals = ['b.tech', 'm.tech', 'bsc', 'msc', 'mba', 'phd', 'bachelor', 'master', 'diploma']
    text_l = text.lower()
    for q in quals:
        if q in text_l:
            return q.upper() if len(q) <= 4 else q.title()
    return None

# --- UI helpers ---
def bot_message(msg):
    st.markdown(f"<div style='background:#0b5cff;color:white;padding:12px;border-radius:10px;margin:6px 0'>{msg}</div>", unsafe_allow_html=True)

def user_message(msg):
    st.markdown(f"<div style='background:#f1f5f9;color:#0b1224;padding:10px;border-radius:10px;margin:6px 0;text-align:right'>{msg}</div>", unsafe_allow_html=True)

def main():
    st.set_page_config(page_title="Star to Shine - Recruitment Chatbot", layout="wide")
    init_db()
    st.sidebar.title("Star to Shine — Admin")
    page = st.sidebar.selectbox("Mode", ["Chatbot", "Admin"])

    if page == "Chatbot":
        st.markdown("<h2 style='color:#0b5cff'>⭐ Star to Shine</h2>", unsafe_allow_html=True)
        st.write("Welcome! I can help you apply for roles: Full Stack Developer, Software Engineer, AI/ML Engineer, UI/UX Designer, Data Analyst.")

        if 'history' not in st.session_state:
            st.session_state.history = []
        if 'slot_data' not in st.session_state:
            st.session_state.slot_data = {
                'name': None,
                'job_role': None,
                'experience_years': None,
                'qualification': None,
                'email': None,
                'phone': None,
                'cover': None
            }
            st.session_state.stage = 'greeting'

        # Show chat history
        for entry in st.session_state.history:
            if entry['sender'] == 'bot':
                bot_message(entry['text'])
            else:
                user_message(entry['text'])

        # Input box
        col1, col2 = st.columns([8,1])
        with col1:
            user_input = st.text_input("Type your message here...", key="user_input")
        with col2:
            submit = st.button("Send", key="send_btn")

        if submit and user_input:
            process_user_input(user_input.strip())

        # If bot finished collecting info, show summary and submit button
        if st.session_state.stage == 'submitted':
            st.success("Application submitted successfully!")
            st.button("Start new application", on_click=reset_conversation)

    else:
        st.header("Applicants (Admin view)")
        df = fetch_applicants()
        st.write(f"Total applicants: {len(df)}")
        st.dataframe(df)
        if not df.empty:
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download CSV", data=csv, file_name='applicants.csv', mime='text/csv')

def reset_conversation():
    st.session_state.history = []
    st.session_state.slot_data = {
        'name': None,
        'job_role': None,
        'experience_years': None,
        'qualification': None,
        'email': None,
        'phone': None,
        'cover': None
    }
    st.session_state.stage = 'greeting'
    st.experimental_rerun()

def process_user_input(text):
    # Save user message to history
    st.session_state.history.append({'sender':'user', 'text': text})
    # handle based on current stage
    stage = st.session_state.stage

    # simple greeting recognition
    if stage == 'greeting':
        # If user gives name directly like "Hi, I'm Riya"
        name = None
        m = re.search(r"i(?:'m| am|`m)\s+([A-Z][a-z]+)", text)
        if m:
            name = m.group(1)
        if not name:
            # try capitalized word heuristics
            caps = re.findall(r'([A-Z][a-z]{1,})', text)
            if caps:
                name = caps[0]
        if name:
            st.session_state.slot_data['name'] = name
            st.session_state.history.append({'sender':'bot', 'text': f"Nice to meet you, {name}! Can you tell me the role you're applying for? Options: Full Stack Developer, Software Engineer, AI/ML Engineer, UI/UX Designer, Data Analyst"})
            st.session_state.stage = 'ask_role'
            return
        st.session_state.history.append({'sender':'bot', 'text': "👋 Hi! Welcome to Star to Shine Careers. I'm here to guide you through the hiring process. Which role are you applying for? (e.g., Data Analyst, UI/UX Designer)"})
        st.session_state.stage = 'ask_role'
        return

    if stage == 'ask_role':
        role = extract_job_role(text)
        if role:
            st.session_state.slot_data['job_role'] = role
            st.session_state.history.append({'sender':'bot', 'text': f"Perfect choice 🌟. How many years of experience do you have in {role}?"})
            st.session_state.stage = 'ask_experience'
            return
        else:
            st.session_state.history.append({'sender':'bot', 'text': "I didn't catch that. Please choose from: Full Stack Developer, Software Engineer, AI/ML Engineer, UI/UX Designer, Data Analyst."})
            return

    if stage == 'ask_experience':
        years = extract_years(text)
        if years is not None:
            st.session_state.slot_data['experience_years'] = years
            st.session_state.history.append({'sender':'bot', 'text': "Thanks! Could you also share your highest qualification? (e.g., B.Tech, M.Tech, MBA)"})
            st.session_state.stage = 'ask_qualification'
            return
        else:
            st.session_state.history.append({'sender':'bot', 'text': "Could you tell me how many years of experience you have? (e.g., 2 years, 5)"})
            return

    if stage == 'ask_qualification':
        qual = extract_qualification(text)
        if qual:
            st.session_state.slot_data['qualification'] = qual
            st.session_state.history.append({'sender':'bot', 'text': "Great. Please provide your email and phone number so we can contact you."})
            st.session_state.stage = 'ask_contact'
            return
        else:
            st.session_state.history.append({'sender':'bot', 'text': "Please state your highest qualification (B.Tech, M.Tech, MBA, B.Sc etc)."})
            return

    if stage == 'ask_contact':
        email = extract_email(text)
        phone = extract_phone(text)
        if email:
            st.session_state.slot_data['email'] = email
        if phone:
            st.session_state.slot_data['phone'] = phone

        if email and phone:
            st.session_state.history.append({'sender':'bot', 'text': f"✅ Thank you, {st.session_state.slot_data.get('name') or ''}! Your application for the {st.session_state.slot_data.get('job_role')} role has been recorded. Would you like to add a short cover note or portfolio link?"})
            st.session_state.stage = 'ask_cover'
            return
        else:
            missing = []
            if not email: missing.append('email')
            if not phone: missing.append('phone')
            st.session_state.history.append({'sender':'bot', 'text': f"I couldn't find your {' and '.join(missing)}. Please provide both email and phone number (e.g., riya@example.com +919876543210)."})
            return

    if stage == 'ask_cover':
        # accept optional cover note / portfolio
        st.session_state.slot_data['cover'] = text
        # finalize and save
        save_applicant(st.session_state.slot_data)
        st.session_state.history.append({'sender':'bot', 'text': "Your application has been submitted. Our HR team will reach out to you soon. Good luck!"})
        st.session_state.stage = 'submitted'
        return

if __name__ == '__main__':
    main()
