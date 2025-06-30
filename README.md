
# 📊 WhatsApp Conversation Intent Labeling Tool

This is a **Streamlit-based interactive tool** for manually labeling intents in WhatsApp customer support conversations.
It helps you classify each message into meaningful categories like “Validate Meter Number”, “Retrieve Power Token”, “Greeting”, etc.

It is designed to assist teams working with large conversational datasets (like from Zendesk / Twilio / WhatsApp exports), to build training data for machine learning or conduct business analysis.

---

## 🚀 Features

✅ Parses complex JSON message parts into clean text  
✅ Groups messages by `conversation_id`  
✅ Lets you:
- Assign a **default intent** for the whole conversation
- Or **override intent** for individual messages  
✅ Saves labeled data incrementally to `labeled_output_per_message.csv`  
✅ Skips already labeled conversations so you can pick up where you left off.

---

## 🗂 Example of intents you’ll label

- Validate Meter Number
- Retrieve Power Token
- Payment Issue / Refund
- Debt Inquiry / Payment
- Transaction Status Inquiry
- Retry Action
- Connect to Agent
- General Acknowledgment / Closing
- Greeting
- Other
- Empty Chat
- system message
- Transaction history

---

## 💻 How to run locally

### 1️⃣ Clone this repo & set up virtual environment
```bash
git clone https://github.com/your-username/whatsapp-intent-labeling
cd whatsapp-intent-labeling

python -m venv .venv
source .venv/bin/activate  # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

_(Make sure your `requirements.txt` has `streamlit`, `pandas` etc.)_

---

### 2️⃣ Place your input file
Put your CSV file in the same directory.
By default, the tool looks for:

```
Ugochukwu.csv
```

with columns like:

| conversation_id | actor_type | message_parts |
|-----------------|------------|---------------|

---

### 3️⃣ Run the app
```bash
streamlit run label_conversations.py
```

Your browser will open at `localhost:8501`.  
You can now start labeling!

---

## 🔄 Changing which file you want to label
If you want to switch from `Ugochukwu.csv` to e.g. `Temitope.csv`,
just open your Python file (like `label_conversations.py`) and change:

```python
INPUT_CSV_PATH = "Ugochukwu.csv"
```

to:

```python
INPUT_CSV_PATH = "Temitope.csv"
```

That’s it — next time you run, it’ll use the new file.

---

## 📁 Output
Labeled results are saved automatically to:

```
labeled_output_per_message.csv
```

with columns:

| conversation_id | Speaker | Message | Intent |
|-----------------|---------|---------|--------|

---

## ⚠️ Notes & troubleshooting
- The app **skips empty chats** and `system` messages automatically.
- If you accidentally delete your `labeled_output_per_message.csv`, you’ll have to re-label.
- Use `Ctrl + C` in your terminal to stop the app anytime.
- If you get an error like `FileNotFoundError: Ugochukwu.csv`, make sure your file is named correctly and is in the same folder.

---

✅ **Happy labeling!**
