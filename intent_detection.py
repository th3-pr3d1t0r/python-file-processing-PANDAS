import pandas as pd
import json
import os
import re # Import regex for more flexible keyword matching if needed later

# --- Configuration Constants ---
# Input and Output File Paths
INPUT_CSV_PATH = "Ugochukwu.csv"
OUTPUT_CSV_PATH = "processed_chat_transcript_improved.csv"

# Original CSV Column Names (IMPORTANT: Adjust these to match your Ugochukwu.csv exactly)
ORIGINAL_CONVERSATION_ID_COL = 'conversation_id'
ORIGINAL_ACTOR_TYPE_COL = 'actor_type' # e.g., 'user', 'agent'
ORIGINAL_MESSAGE_PARTS_COL = 'message_parts' # The JSON string column

# Output Column Names
COL_CONVERSATION_ID = 'Conversation ID'
COL_SPEAKER = 'Speaker'
COL_MESSAGE = 'Message'
COL_INTENT = 'Intent'

# Speaker Role Mapping
SPEAKER_MAPPING = {
    'user': 'Customer',
    'agent': 'Agent',
    # Add other mappings if your 'actor_type' column has different values
    # 'bot': 'Agent',
    # 'system': 'System'
}

# Intent Keyword Definitions (Ordered from Most Specific to Most General)
# THIS IS NOW A LIST OF TUPLES TO GUARANTEE EVALUATION ORDER.
# Place more specific intents higher up in this list.
# IMPORTANT: "Connect to Agent" is prioritized as it's often an overarching user goal.
# Use lowercase for keywords for case-insensitive matching.
INTENT_KEYWORDS = [
    ("Connect to Agent", [ # Moved this higher to prioritize direct agent requests
        "chat with an agent", "connect you to an agent", "speak to a human",
        "transfer to agent", "live agent", "need help from a representative",
        "escalate", "talk to someone", "human agent", "customer service",
        "get an agent", "can i speak to someone"
    ]),
    ("Retrieve Power Token", [
        "retrieve power token", "didn't get the token", "no token received",
        "forward token", "token not delivered", "token for my meter",
        "recharge code", "power code", "voucher code", "meter token missing",
        "send me token", "i need my token", "get my token" # Removed standalone "power token"
    ]),
    ("Validate Meter Number", [
        "validate meter number", "meter number is", "metre number",
        "meter no", "check meter number", "confirm meter", "verify meter",
        "meter validation", "is my meter valid", "meter details", "validate my meter",
        "confirm my meter number"
    ]),
    ("Payment Issue/Refund", [
        "transaction failed", "refunded", "payment not reflected",
        "payment issue", "money deducted", "not received credit",
        "double payment", "overcharged", "disputed transaction", "wrong amount",
        "payment error", "charged twice", "deducted money", "refund request", "payment problem",
        "payment not successful", "where is my money"
    ]),
    ("Debt Inquiry/Payment", [
        "debt of", "top up payment", "outstanding balance", "clear debt",
        "how much do i owe", "settle bill", "payment plan", "arrears",
        "due amount", "debt inquiry", "my debt", "check my bill", "pay my bill"
    ]),
    ("Transaction Status Inquiry", [
        "pending", "status of my transaction", "transaction status",
        "has my payment gone through", "where is my transaction",
        "payment confirmed", "what's happening with", "check status", "my transaction",
        "confirm payment"
    ]),
    ("Retry Action", [
        "retry", "try again", "re-send", "do it again", "can you try that again", "resend",
        "please retry"
    ]),
    ("Navigation/Menu Request", [
        "goto menu", "main menu", "return to menu", "menu option",
        "go back", "start over", "home page", "show menu", "menu please"
    ]),
    # General acknowledgments/greetings should come *after* more specific intents
    ("General Acknowledgment/Closing", [
        "thank you", "appreciate", "no thanks", "okay", "ok", "you're welcome",
        "bye", "goodbye", "alright", "understood", "got it", "cheers", "perfect",
        "thank u", "k", "fine" # Common shorthand and acknowledgments
    ]),
    ("Greeting", [
        "hi", "hello", "good morning", "good afternoon", "good evening", "greetings", "hey", "sup",
        "good day"
    ]),
    # Consider adding an 'Other' or 'Miscellaneous' intent if many don't fit
    # ("Other", [ "general question", "i have a query", "help me" ])
]

# Default intent if no keywords match
DEFAULT_INTENT = "General Inquiry / Unclassified"


# --- Helper Functions ---

def _extract_message_content(message_parts_str):
    """
    Parses the 'message_parts' JSON string and extracts text content,
    or notes about images/files.
    Handles potential JSON decoding errors and non-string inputs gracefully.
    """
    if pd.isna(message_parts_str) or not isinstance(message_parts_str, str):
        return "" # Return empty string for NaN or non-string inputs

    message_content = []
    try:
        message_parts = json.loads(message_parts_str)
        if not isinstance(message_parts, list): # Ensure it's a list as expected
            raise ValueError("message_parts is not a list")

        for part in message_parts:
            if 'text' in part and isinstance(part.get('text'), dict) and 'content' in part['text']:
                content = part['text']['content']
                if content: # Only add if content is not empty
                    message_content.append(content)
            elif 'image' in part and isinstance(part.get('image'), dict) and 'url' in part['image']:
                message_content.append("[Image Attached]")
            elif 'file' in part and isinstance(part.get('file'), dict) and 'name' in part['file']:
                message_content.append(f"[File: {part['file']['name']}]")
    except (json.JSONDecodeError, ValueError) as e:
        # Fallback if JSON is malformed or structure is unexpected
        print(f"Warning: Could not parse message_parts JSON: {e}. Raw content: {message_parts_str[:100]}...")
        return str(message_parts_str) # Return raw string if parsing fails
    except Exception as e:
        print(f"An unexpected error occurred during message part extraction: {e}. Raw content: {message_parts_str[:100]}...")
        return str(message_parts_str)

    return " ".join(message_content).strip()


def assign_intent(all_conversation_text):
    """
    Assigns an intent to a conversation based on predefined keywords.
    Rules are applied in the order defined in INTENT_KEYWORDS (most specific first).
    """
    all_text_lower = all_conversation_text.lower()

    for intent_name, keywords in INTENT_KEYWORDS: # Iterate through the list of tuples
        for keyword in keywords:
            if keyword in all_text_lower:
                return intent_name
    return DEFAULT_INTENT


# --- Main Processing Function ---

def process_chat_transcript(input_csv_path, output_csv_path):
    """
    Reads the chat transcript CSV, processes it to extract messages and assign intents
    per conversation, and writes the structured data to a new CSV.
    """
    if not os.path.exists(input_csv_path):
        print(f"Error: Input file not found at {input_csv_path}. Please ensure it's in the same directory.")
        return

    try:
        df = pd.read_csv(input_csv_path)
        print(f"Successfully loaded '{input_csv_path}' with {len(df)} rows.")
    except Exception as e:
        print(f"Error reading input CSV file: {e}")
        return

    # Validate essential columns
    required_cols = [
        ORIGINAL_CONVERSATION_ID_COL,
        ORIGINAL_ACTOR_TYPE_COL,
        ORIGINAL_MESSAGE_PARTS_COL
    ]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"Error: Missing required columns in input CSV: {', '.join(missing_cols)}")
        print(f"Please update '{os.path.basename(__file__)}' with correct column names in the Configuration Constants section.")
        return

    # Extract message content
    print("Extracting message content from 'message_parts' column...")
    df['parsed_message_content'] = df[ORIGINAL_MESSAGE_PARTS_COL].apply(_extract_message_content)

    processed_data_rows = []
    conversations_grouped = df.groupby(ORIGINAL_CONVERSATION_ID_COL)

    print("Processing conversations and assigning intents...")
    total_conversations = len(conversations_grouped)
    processed_count = 0

    for conv_id, conv_df in conversations_grouped:
        # Concatenate all messages in the conversation for intent assignment
        all_conversation_messages = conv_df['parsed_message_content'].tolist()
        combined_text_for_intent = " ".join(all_conversation_messages)

        # Determine the intent for the entire conversation
        intent = assign_intent(combined_text_for_intent)

        # Add each message from the conversation with the assigned intent
        for _, row in conv_df.iterrows():
            speaker = SPEAKER_MAPPING.get(row[ORIGINAL_ACTOR_TYPE_COL], row[ORIGINAL_ACTOR_TYPE_COL]) # Use .get() for safer mapping
            message_content = row['parsed_message_content']

            processed_data_rows.append({
                COL_CONVERSATION_ID: conv_id,
                COL_SPEAKER: speaker,
                COL_MESSAGE: message_content,
                COL_INTENT: intent
            })

        processed_count += 1
        if processed_count % 100 == 0 or processed_count == total_conversations:
            print(f"  Processed {processed_count}/{total_conversations} conversations.")

    # Create the final DataFrame
    output_df = pd.DataFrame(processed_data_rows)

    # Save the processed data to a new CSV
    try:
        output_df.to_csv(output_csv_path, index=False)
        print(f"\nProcessing complete! Structured data saved to '{output_csv_path}'")
        print(f"Total rows in output: {len(output_df)}")
        print("Columns in output file:")
        for col in output_df.columns:
            print(f"- {col}")
        print("\nReview the output file. The 'Intent' column is populated based on keyword matching.")
        print("For more advanced intent classification, consider fine-tuning an LLM.")
    except Exception as e:
        print(f"Error saving the processed CSV file: {e}")

# --- Main execution ---
if __name__ == "__main__":
    process_chat_transcript(INPUT_CSV_PATH, OUTPUT_CSV_PATH)
