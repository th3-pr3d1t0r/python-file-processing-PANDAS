import pandas as pd
import json

INPUT_CSV = "original_document.csv"
OUTPUT_JSONL = "messages_for_labeling.jsonl"

# Define mappings
ACTOR_MAP = {
    'user': 'Customer',
    'bot': 'Agent',
    'agent': 'Agent',
    'system': 'System'
}

def extract_message_content(parts_str):
    try:
        parts = json.loads(parts_str)
        content_pieces = []
        for part in parts:
            if 'text' in part and isinstance(part['text'], dict):
                content_pieces.append(part['text'].get('content', ''))
            elif 'image' in part:
                content_pieces.append("[Image Attached]")
            elif 'file' in part:
                content_pieces.append("[File: {}]".format(part['file'].get('name', 'Unknown')))
        return " ".join(content_pieces).strip()
    except Exception:
        return parts_str[:100] if isinstance(parts_str, str) else ""

# Load data
df = pd.read_csv(INPUT_CSV)
df['message'] = df['message_parts'].apply(extract_message_content)
df['speaker'] = df['actor_type'].map(ACTOR_MAP).fillna('Unknown')

# Filter: drop empty/system messages if needed
df = df[df['message'].str.strip().astype(bool)]
df = df[df['speaker'].str.lower() != 'system']

# Write as JSONL
with open(OUTPUT_JSONL, 'w', encoding='utf-8') as f:
    for _, row in df.iterrows():
        f.write(json.dumps({
            "conversation_id": row['conversation_id'],
            "speaker": row['speaker'],
            "message": row['message']
        }, ensure_ascii=False) + '\n')

print(f"Exported to {OUTPUT_JSONL}")
