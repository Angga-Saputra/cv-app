import streamlit as st
import base64, time
from streamlit_theme import st_theme
from openai import OpenAI

def chat(sys_prompt, question, history):
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "developer",
                "content": f"{sys_prompt}\nBerikut ini disajikan history chat sebagai tambahan informasi agar chat kamu semakin relevan.\nChat history : {history}"
            },
            {
                "role": "user",
                "content": question
            }
        ],
    )
    answer = completion.choices[0].message.content
    input_tokens = completion.usage.prompt_tokens
    output_tokens = completion.usage.completion_tokens
    price = 17_000 * ((input_tokens*0.15) + (output_tokens*0.6))/1_000_000
    response_json = {
        'answer' : answer,
        'input_tokens' : input_tokens,
        'output_tokens' : output_tokens,
        'price' : price
    }
    return response_json

with st.spinner("Preparing Application", show_time=True):
    theme_json = st_theme()
    time.sleep(1)
    theme = theme_json['base']

def get_base64_of_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()
    

# Custom CSS to set the background image
def set_background_image(image_path):
    encoded_image = get_base64_of_image(image_path)
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{encoded_image}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

if theme == "dark":
    background_image_path = "./dark_bg.png"
else:
    background_image_path = "./light_bg.png"

set_background_image(background_image_path)

# Judul aplikasi llm
st.title("General Chatbot")

# User input for API key
api_key = st.text_input("Enter your API Key:", type="password")
if api_key:
    client = OpenAI(api_key=api_key)

# Input system prompt
sys_prompt = st.text_area(
    "System prompt:",
    "Kamu adalah asisten AI yang cerdas dan membantu di bidang apapun. Selalu gunakan bahasa Indonesia yang baik dan sopan untuk menjawab pertanyaan.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("Let's say: Hi Celerates!"):
    messages_history = st.session_state.get("messages", [])[-10:]
    history = "\n".join([f'{msg["role"]}: {msg["content"]}' for msg in messages_history]) or " "

    # Display user message in chat message container
    with st.chat_message("Human"):
        st.markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "Human", "content": prompt})
    
    # Display assistant response in chat message container
    with st.chat_message("AI"):
        response = chat(sys_prompt, prompt, history)
        answer = response["answer"]
        st.markdown(answer)
    st.session_state.messages.append({"role": "AI", "content": answer})

    input_tokens = response["input_tokens"]
    output_tokens = response["output_tokens"]
    price = response["price"]
    with st.expander("**Usage Details:**"):
        st.code(f'input tokens : {input_tokens}\noutput tokens : {output_tokens}\nprice (IDR): {price}')