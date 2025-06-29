import streamlit as st
import pandas as pd
import json
import os
import re

# -------------------------------
# Configuration
# -------------------------------
INPUT_CSV_PATH = "Ugochukwu.csv"
OUTPUT_CSV_PATH = "labeled_output_per_message.csv"

ORIGINAL_CONVERSATION_ID_COL = 'conversation_id'
ORIGINAL_ACTOR_TYPE_COL = 'actor_type'
ORIGINAL_MESSAGE_PARTS_COL = 'message_parts'

SPEAKER_MAPPING = {
    'user': 'Customer',
    'agent': 'Agent',
    'bot': 'Agent'
}

INTENT_OPTIONS = [
    "Validate Meter Number",
    "Retrieve Power Token",
    "Payment Issue / Refund",
    "Debt Inquiry / Payment",
    "Transaction Status Inquiry",
    "Retry Action",
    "Navigation / Menu Request",
    "Connect to Agent",
    "General Acknowledgment / Closing",
    "Greeting",
    "Other",
    "Empty Chat"
]

# -------------------------------
# Helper Functions
# -------------------------------

def extract_message_content(message_parts_str):
    if pd.isna(message_parts_str) or not isinstance(message_parts_str, str):
        return ""
    try:
        message_parts = json.loads(message_parts_str)
        if not isinstance(message_parts, list):
            raise ValueError("message_parts is not a list")
        content_pieces = []
        for part in message_parts:
            if 'text' in part and isinstance(part.get('text'), dict):
                content_pieces.append(part['text'].get('content', ''))
            elif 'image' in part:
                content_pieces.append("[Image Attached]")
            elif 'file' in part:
                content_pieces.append(f"[File: {part['file'].get('name', 'Unknown')}]")
        return " ".join(content_pieces).strip()
    except Exception:
        return message_parts_str[:100]

def clean_html(raw_html):
    cleanr = re.compile('<.*?>')
    return re.sub(cleanr, '', raw_html)

# -------------------------------
# Load Data
# -------------------------------

@st.cache_data
def load_data():
    if not os.path.exists(INPUT_CSV_PATH):
        st.error(f"File {INPUT_CSV_PATH} not found.")
        st.stop()
    df = pd.read_csv(INPUT_CSV_PATH)
    df['parsed_message_content'] = df[ORIGINAL_MESSAGE_PARTS_COL].apply(extract_message_content)
    df['parsed_message_content'] = df['parsed_message_content'].apply(clean_html)
    return df

df = load_data()

# -------------------------------
# Load or Initialize labeled data
# -------------------------------

if os.path.exists(OUTPUT_CSV_PATH):
    labeled_df = pd.read_csv(OUTPUT_CSV_PATH)
    labeled_message_ids = set(zip(labeled_df[ORIGINAL_CONVERSATION_ID_COL], labeled_df['Message']))
else:
    labeled_df = pd.DataFrame(columns=[
        ORIGINAL_CONVERSATION_ID_COL, 'Speaker', 'Message', 'Intent'
    ])
    labeled_message_ids = set()

# -------------------------------
# Streamlit App UI
# -------------------------------

st.title("🔍 Per-Message Intent Labeling Tool")

unlabeled_messages = []
for conv_id, conv_df in df.groupby(ORIGINAL_CONVERSATION_ID_COL):
    for _, row in conv_df.iterrows():
        message = row['parsed_message_content']
        speaker = SPEAKER_MAPPING.get(row[ORIGINAL_ACTOR_TYPE_COL], row[ORIGINAL_ACTOR_TYPE_COL])
        if (conv_id, message) not in labeled_message_ids:
            unlabeled_messages.append((conv_id, speaker, message))

if not unlabeled_messages:
    st.success("🎉 All messages have been labeled! You're done.")
    st.stop()

current_conv_id, current_speaker, current_message = unlabeled_messages[0]

# -------------------------------
# Display message with background
# -------------------------------

color = "#f8d7da" if current_speaker == "Customer" else "#d4edda"
st.markdown(f"""
<div style="background-color: {color}; padding: 10px; border-radius: 5px; margin: 5px 0;">
    <strong>{current_speaker}:</strong> {current_message}
</div>
""", unsafe_allow_html=True)

# -------------------------------
# Labeling controls
# -------------------------------

selected_intent = st.selectbox("Select the intent for this message:", INTENT_OPTIONS)

if st.button("Save Intent & Next"):
    new_row = {
        ORIGINAL_CONVERSATION_ID_COL: current_conv_id,
        'Speaker': current_speaker,
        'Message': current_message,
        'Intent': selected_intent
    }
    labeled_df = pd.concat([labeled_df, pd.DataFrame([new_row])], ignore_index=True)
    labeled_df.to_csv(OUTPUT_CSV_PATH, index=False)
    st.rerun()
