import ollama
from config import MODEL_NAME, SYSTEM_PROMPT

def chat(user_message: str, history: list = [], context: str = "") -> str:
    messages = []
    messages.append({"role": "system", "content": SYSTEM_PROMPT})
    messages += history

#     if context:
#         augmented_message = f"""IMPORTANT: You MUST answer using ONLY the information below. Do not use your own knowledge. Do not add anything extra.

# INFORMATION:
# {context}

# USER QUESTION: {user_message}"""
    if context:
      augmented_message = f"""IMPORTANT: You MUST answer using ONLY the information below. Do not ask the user to describe what they see — you already know from the screen information provided.

INFORMATION:
{context}

USER QUESTION: {user_message}"""
    else:
        augmented_message = user_message

    messages.append({"role": "user", "content": augmented_message})

    stream = ollama.chat(model=MODEL_NAME, messages=messages, stream=True)

    full_response = ""
    print("\nAssistant: ", end="", flush=True)
    for chunk in stream:
        text = chunk['message']['content']
        print(text, end="", flush=True)
        full_response += text

    print("\n")
    return full_response