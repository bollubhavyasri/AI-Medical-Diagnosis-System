import streamlit as st
import pandas as pd
import base64
import matplotlib.pyplot as plt

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="Medical Diagnosis AI", layout="wide")

# -----------------------------
# BACKGROUND
# -----------------------------
def set_bg(image_file):
    with open(image_file, "rb") as img:
        encoded = base64.b64encode(img.read()).decode()

    st.markdown(f"""
    <style>
    .stApp {{
        background-image: url("data:image/png;base64,{encoded}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
    }}

    .title-style {{
        text-align: center;
        font-size: 60px;
        font-weight: bold;
        color: black;
        margin-top: 150px;
    }}

    div.stButton > button {{
        background-color: #ff4b5c;
        color: white;
        font-size: 20px;
        padding: 12px 40px;
        border-radius: 12px;
        border: none;
    }}

    div.stButton > button:hover {{
        background-color: #e04350;
    }}
    </style>
    """, unsafe_allow_html=True)

# -----------------------------
# DARK MODE
# -----------------------------
def set_dark_bg():
    st.markdown("""
    <style>
    .stApp {
        background-color: #000000;
    }

    h1,h2,h3,h4,h5,h6,p,label,div {
        color: white !important;
    }

    input {
        background-color: #222 !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

# -----------------------------
# SESSION STATE
# -----------------------------
if "page" not in st.session_state:
    st.session_state.page = "home"

if "history" not in st.session_state:
    st.session_state.history = []

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# -----------------------------
# LOAD DATA
# -----------------------------
@st.cache_data
def load_data():
    df_rules = pd.read_csv("dataset.csv")
    df_desc = pd.read_csv("symptom_Description.csv")
    df_prec = pd.read_csv("symptom_precaution.csv")

    df_rules.columns = df_rules.columns.str.strip().str.lower()
    df_desc.columns = df_desc.columns.str.strip().str.lower()
    df_prec.columns = df_prec.columns.str.strip().str.lower()

    return df_rules, df_desc, df_prec

df_rules, df_desc, df_prec = load_data()

# -----------------------------
# RULE ENGINE
# -----------------------------
rules = []

for _, row in df_rules.iterrows():
    disease = str(row["disease"]).strip()
    symptoms = set()

    for col in df_rules.columns[1:]:
        if pd.notna(row[col]) and row[col] != "":
            symptoms.add(str(row[col]).strip().lower())

    rules.append((symptoms, disease))

def diagnose(user_input):
    user_symptoms = set([s.strip().lower() for s in user_input.split(",")])
    results = []

    for condition, disease in rules:
        match = user_symptoms.intersection(condition)

        if match:
            score = len(match) / len(user_symptoms)
            results.append((disease, score, match))

    return sorted(results, key=lambda x: x[1], reverse=True)

def get_description(disease):
    row = df_desc[df_desc["disease"].str.strip().str.lower() == disease.strip().lower()]
    return row.iloc[0]["description"] if not row.empty else "No description available"

def get_precautions(disease):
    row = df_prec[df_prec["disease"].str.strip().str.lower() == disease.strip().lower()]
    return row.iloc[0][1:].dropna().values if not row.empty else []

# -----------------------------
# PDF GENERATOR
# -----------------------------
def generate_pdf(symptoms, disease, score, description, precautions):
    file_name = "medical_report.pdf"
    doc = SimpleDocTemplate(file_name)

    styles = getSampleStyleSheet()
    content = []

    content.append(Paragraph("Medical Diagnosis Report", styles["Title"]))
    content.append(Spacer(1, 12))

    content.append(Paragraph(f"<b>Symptoms:</b> {symptoms}", styles["Normal"]))
    content.append(Spacer(1, 12))

    content.append(Paragraph(f"<b>Disease:</b> {disease}", styles["Normal"]))
    content.append(Spacer(1, 12))

    content.append(Paragraph(f"<b>Confidence:</b> {score}%", styles["Normal"]))
    content.append(Spacer(1, 12))

    content.append(Paragraph(f"<b>Description:</b> {description}", styles["Normal"]))
    content.append(Spacer(1, 12))

    content.append(Paragraph("<b>Precautions:</b>", styles["Normal"]))
    for p in precautions:
        content.append(Paragraph(f"- {p}", styles["Normal"]))

    doc.build(content)
    return file_name

# -----------------------------
# SMART CHATBOT (FIXED)
# -----------------------------
def chatbot_response(msg):

    msg = msg.lower()

    if any(w in msg for w in ["fever", "temperature", "hot"]):
        return "You may have fever symptoms. Take rest and fluids."

    elif any(w in msg for w in ["cough", "cold", "sneezing", "runny nose"]):
        return "It looks like cold/cough. Drink warm fluids."

    elif any(w in msg for w in ["headache", "migraine"]):
        return "Headache may be due to stress or dehydration."

    elif any(w in msg for w in ["stomach pain", "stomach", "gas", "vomit", "vomiting", "nausea"]):
        return "You may have stomach-related issues. Take light food and fluids."

    elif "help" in msg:
        return "I can help with fever, cough, headache, nausea, stomach pain."

    else:
        return "Try symptoms like fever, cough, headache, nausea, stomach pain."

# -----------------------------
# HOME PAGE
# -----------------------------
if st.session_state.page == "home":

    set_bg("AIbg.png")

    st.markdown('<div class="title-style">AI Medical Diagnosis System</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        if st.button("Start Diagnosis"):
            st.session_state.page = "diagnosis"
            st.rerun()

# -----------------------------
# DIAGNOSIS PAGE
# -----------------------------
elif st.session_state.page == "diagnosis":

    set_dark_bg()

    st.sidebar.title("🩺 Dashboard")

    menu = st.sidebar.radio("Menu", [
        "Diagnosis",
        "About",
        "History",
        "Disclaimer",
        "Disease Probability 📊",
        "Symptom Frequency 📊"
    ])

    if st.sidebar.button("🏠 Home"):
        st.session_state.page = "home"
        st.rerun()

    # -----------------------------
    # CHATBOT
    # -----------------------------
    st.sidebar.markdown("---")
    st.sidebar.subheader("🤖 AI Chatbot")

    user_msg = st.sidebar.text_input("Ask symptoms")

    if st.sidebar.button("Send"):
        if user_msg:
            reply = chatbot_response(user_msg)
            st.session_state.chat_history.append(("You", user_msg))
            st.session_state.chat_history.append(("AI", reply))

    for role, msg in st.session_state.chat_history[-6:]:
        if role == "You":
            st.sidebar.write(f"🧑 {msg}")
        else:
            st.sidebar.write(f"🤖 {msg}")

    # -----------------------------
    # STORAGE
    # -----------------------------
    if "last_diseases" not in st.session_state:
        st.session_state.last_diseases = []
    if "last_scores" not in st.session_state:
        st.session_state.last_scores = []
    if "last_symptoms" not in st.session_state:
        st.session_state.last_symptoms = []

    # -----------------------------
    # ABOUT
    # -----------------------------
    if menu == "About":
        st.title("About System")
        st.write("""
AI Medical Diagnosis System

- Predicts disease from symptoms  
- Shows description & precautions  
- Includes chatbot support  

Educational purpose only.
        """)
        st.stop()

    # -----------------------------
    # HISTORY
    # -----------------------------
    if menu == "History":
        st.title("History")

        if not st.session_state.history:
            st.info("No history yet")
        else:
            for h in st.session_state.history[::-1]:
                st.write(h)
        st.stop()

    # -----------------------------
    # DISCLAIMER
    # -----------------------------
    if menu == "Disclaimer":
        st.title("Disclaimer")
        st.write("Educational use only.")
        st.stop()

    # -----------------------------
    # CHARTS
    # -----------------------------
    if menu == "Disease Probability 📊":

        st.title("Disease Probability")

        if st.session_state.last_diseases:
            fig, ax = plt.subplots()
            ax.bar(st.session_state.last_diseases, st.session_state.last_scores)
            plt.xticks(rotation=45)
            st.pyplot(fig)
        else:
            st.warning("Run diagnosis first")
        st.stop()

    if menu == "Symptom Frequency 📊":

        st.title("Symptom Frequency")

        if st.session_state.last_symptoms:
            sym = [s.strip() for s in st.session_state.last_symptoms]
            count = [1 for _ in sym]

            fig, ax = plt.subplots()
            ax.bar(sym, count)
            plt.xticks(rotation=45)
            st.pyplot(fig)
        else:
            st.warning("Run diagnosis first")
        st.stop()

    # -----------------------------
    # DIAGNOSIS
    # -----------------------------
    st.title("Diagnosis Page")

    user_input = st.text_input("Enter Symptoms")

    if st.button("Diagnose"):

        results = diagnose(user_input)

        if results:

            diseases = []
            scores = []

            for disease, score, matched in results:
                st.success(disease)
                st.info(f"{round(score*100,2)}%")
                st.write(get_description(disease))

                precautions = get_precautions(disease)

                if len(precautions) > 0:
                    st.write("Precautions:")
                    for p in precautions:
                        st.write("-", p)

                file_path = generate_pdf(
                    user_input,
                    disease,
                    round(score*100,2),
                    get_description(disease),
                    precautions
                )

                with open(file_path, "rb") as f:
                    st.download_button(
                        f"📄 Download {disease} Report",
                        f,
                        file_name=f"{disease}_report.pdf",
                        mime="application/pdf",
                        key=f"pdf_{disease}"
                    )

                st.write("---")

                diseases.append(disease)
                scores.append(score*100)

            st.session_state.last_diseases = diseases[:5]
            st.session_state.last_scores = scores[:5]
            st.session_state.last_symptoms = user_input.split(",")

            st.session_state.history.append(
                f"{user_input} → {results[0][0]} ({round(results[0][1]*100,2)}%)"
            )

    st.warning("⚠️ Educational purpose only")