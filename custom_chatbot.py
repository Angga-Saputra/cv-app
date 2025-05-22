import streamlit as st
import base64, time
from streamlit_theme import st_theme
from openai import OpenAI

from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

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
st.title("Custom Chatbot")

# User input for API key
api_key = st.text_input("Enter your API Key:", type="password")
if api_key:
    llm = ChatOpenAI(
        model='gpt-4o-mini', 
        api_key=api_key
    )

    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=api_key)

    db_path = "./faiss_small"
    vectorstore = FAISS.load_local(db_path, embeddings, allow_dangerous_deserialization=True)
    retriever = vectorstore.as_retriever()

    @tool
    def search_articles(question):
        """Use this tools to search relevant documents for answering the question."""
        result = retriever.invoke(question)
        return result

    tools = [search_articles]

    agent_prompt = '''Kamu adalah asisten AI yang ramah dan sopan. Tugas kamu adalah menjawab pertanyaan yang diberikan oleh user. Jawab pertanyaan menggunakan bahasa Indonesia.
Kamu disediakan tools untuk retrieve informasi mengenai laporan tahunan "PT Jasa Raharja", jadi jangan ragu untuk menggunakan tools tersebut untuk menjawab pertanyaan tentang "Jasa Raharja".
Silahkan bertanya balik apabila dirasa pertanyaan dari user masih ambigu atau belum jelas.
'''

    agent_executor = create_react_agent(
        llm, tools, prompt=agent_prompt
    )

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
        input_query = f"User : {prompt}\nHistory : {history}"
        question = {"messages": [("user", input_query)]}
        response_llm = agent_executor.invoke(question)
        response = response_llm["messages"][-1]
        answer = response.content
        completion_tokens = response.response_metadata["token_usage"]["completion_tokens"]
        prompt_tokens = response.response_metadata["token_usage"]["prompt_tokens"]
        price = 17_000 * ((prompt_tokens*0.15) + (completion_tokens*0.6))/1_000_000
        st.markdown(answer)
    st.session_state.messages.append({"role": "AI", "content": answer})

    with st.expander("**Usage Details:**"):
        st.code(f'input tokens : {prompt_tokens}\noutput tokens : {completion_tokens}\nprice (IDR): {price}')
    