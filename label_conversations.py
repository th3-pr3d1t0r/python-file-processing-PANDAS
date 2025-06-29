import streamlit as st
import pandas as pd
import json
import os

# -------------------------------
# Configuration
# -------------------------------
INPUT_CSV_PATH = "Ugochukwu.csv"
OUTPUT_CSV_PATH = "labeled_output.csv"

ORIGINAL_CONVERSATION_ID_COL = 'conversation_id'
ORIGINAL_ACTOR_TYPE_COL = 'actor_type'
ORIGINAL_MESSAGE_PARTS_COL = 'message_parts'

SPEAKER_MAPPING = {
    'user': 'Customer',
    'agent': 'Agent'
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
        return message_parts_str[:100]  # fallback snippet

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
    return df

df = load_data()
conversations_grouped = df.groupby(ORIGINAL_CONVERSATION_ID_COL)

# -------------------------------
# Load or Initialize labeled data
# -------------------------------

if os.path.exists(OUTPUT_CSV_PATH):
    labeled_df = pd.read_csv(OUTPUT_CSV_PATH)
    labeled_conversation_ids = set(labeled_df[ORIGINAL_CONVERSATION_ID_COL].unique())
else:
    labeled_df = pd.DataFrame(columns=[
        ORIGINAL_CONVERSATION_ID_COL, 'Speaker', 'Message', 'Intent'
    ])
    labeled_conversation_ids = set()

# -------------------------------
# Streamlit App UI
# -------------------------------

st.title("Conversation Intent Labeling Tool")

remaining_conversations = [conv_id for conv_id in conversations_grouped.groups.keys() if conv_id not in labeled_conversation_ids]

if not remaining_conversations:
    st.success("🎉 All conversations have been labeled! You’re done.")
    st.stop()

# Pick next conversation
current_conv_id = remaining_conversations[0]
current_conv_df = conversations_grouped.get_group(current_conv_id)

# Display conversation
st.subheader(f"Conversation ID: {current_conv_id}")

for _, row in current_conv_df.iterrows():
    speaker = SPEAKER_MAPPING.get(row[ORIGINAL_ACTOR_TYPE_COL], row[ORIGINAL_ACTOR_TYPE_COL])
    message = row['parsed_message_content']
    st.markdown(f"**{speaker}:** {message}")

# Labeling controls
selected_intent = st.selectbox("Select the intent for this conversation:", ["Skip"] + INTENT_OPTIONS)

if selected_intent != "Skip":
    if st.button("Save Intent & Next"):
        # Build labeled rows
        new_rows = []
        for _, row in current_conv_df.iterrows():
            speaker = SPEAKER_MAPPING.get(row[ORIGINAL_ACTOR_TYPE_COL], row[ORIGINAL_ACTOR_TYPE_COL])
            message = row['parsed_message_content']
            new_rows.append({
                ORIGINAL_CONVERSATION_ID_COL: current_conv_id,
                'Speaker': speaker,
                'Message': message,
                'Intent': selected_intent
            })
        labeled_df = pd.concat([labeled_df, pd.DataFrame(new_rows)], ignore_index=True)
        labeled_df.to_csv(OUTPUT_CSV_PATH, index=False)
        st.rerun()
else:
    if st.button("Skip and Next"):
        new_rows = []
        for _, row in current_conv_df.iterrows():
            speaker = SPEAKER_MAPPING.get(row[ORIGINAL_ACTOR_TYPE_COL], row[ORIGINAL_ACTOR_TYPE_COL])
            message = row['parsed_message_content']
            new_rows.append({
                ORIGINAL_CONVERSATION_ID_COL: current_conv_id,
                'Speaker': speaker,
                'Message': message,
                'Intent': "Skipped"
            })
        labeled_df = pd.concat([labeled_df, pd.DataFrame(new_rows)], ignore_index=True)
        labeled_df.to_csv(OUTPUT_CSV_PATH, index=False)
        st.rerun()
