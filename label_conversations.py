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
    "Connect to Agent",
    "General Acknowledgment / Closing",
    "Greeting",
    "Other",
    "Empty Chat",
    "system message",
    "Transaction history"
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
# Find next conversation that isn't fully labeled
# -------------------------------
unlabeled_conversations = []
for conv_id, conv_df in df.groupby(ORIGINAL_CONVERSATION_ID_COL):
    meaningful_msgs = [
        msg for _, row in conv_df.iterrows()
        if (msg := row['parsed_message_content']) 
        and msg.strip()
        and SPEAKER_MAPPING.get(row[ORIGINAL_ACTOR_TYPE_COL], row[ORIGINAL_ACTOR_TYPE_COL]).lower() != "system"
    ]
    if any((conv_id, msg) not in labeled_message_ids for msg in meaningful_msgs):
        unlabeled_conversations.append((conv_id, conv_df))

total_unlabeled_messages = sum(
    1 for conv_id, conv_df in unlabeled_conversations 
    for _, row in conv_df.iterrows()
    if (msg := row['parsed_message_content'])
    and msg.strip()
    and SPEAKER_MAPPING.get(row[ORIGINAL_ACTOR_TYPE_COL], row[ORIGINAL_ACTOR_TYPE_COL]).lower() != "system"
    and (conv_id, msg) not in labeled_message_ids
)

if not unlabeled_conversations:
    st.success("🎉 All conversations have been labeled!")
    st.stop()

current_conv_id, current_conv_df = unlabeled_conversations[0]

st.markdown(f"### Conversation ID: `{current_conv_id}`")
st.markdown(f"⏳ **{total_unlabeled_messages} messages left to label**")

st.divider()

# -------------------------------
# Show messages with option to override
# -------------------------------
message_intent_overrides = {}

for idx, row in current_conv_df.iterrows():
    message = row['parsed_message_content']
    speaker = SPEAKER_MAPPING.get(row[ORIGINAL_ACTOR_TYPE_COL], row[ORIGINAL_ACTOR_TYPE_COL])

    # Skip empty or purely system messages for labeling
    if not message.strip() or speaker.lower() == "system":
        continue

    color = "#cc2634" if speaker == "Customer" else "#29c54d"
    st.markdown(f"""
    <div style="background-color: {color}; padding: 10px; border-radius: 5px; margin: 5px 0;">
        <strong>{speaker}:</strong> {message}
    </div>
    """, unsafe_allow_html=True)

    if (current_conv_id, message) not in labeled_message_ids:
        selected_intent = st.selectbox(
            f"Override intent for this message? (or leave as default below)",
            ["(Use default)"] + INTENT_OPTIONS,
            key=f"{current_conv_id}_{idx}"
        )
        if selected_intent != "(Use default)":
            message_intent_overrides[message] = selected_intent

st.divider()

# -------------------------------
# Default conversation intent
# -------------------------------
st.markdown("### Default intent for all messages not explicitly overridden")
default_intent = st.selectbox("Select default intent:", INTENT_OPTIONS)

# -------------------------------
# Save logic
# -------------------------------
if st.button("✅ Save intents for this conversation & next"):
    new_rows = []
    for _, row in current_conv_df.iterrows():
        message = row['parsed_message_content']
        speaker = SPEAKER_MAPPING.get(row[ORIGINAL_ACTOR_TYPE_COL], row[ORIGINAL_ACTOR_TYPE_COL])

        if not message.strip() or speaker.lower() == "system":
            continue

        if (current_conv_id, message) not in labeled_message_ids:
            intent = message_intent_overrides.get(message, default_intent)
            new_rows.append({
                ORIGINAL_CONVERSATION_ID_COL: current_conv_id,
                'Speaker': speaker,
                'Message': message,
                'Intent': intent
            })
    if new_rows:
        labeled_df = pd.concat([labeled_df, pd.DataFrame(new_rows)], ignore_index=True)
        labeled_df.to_csv(OUTPUT_CSV_PATH, index=False)
    st.rerun()
