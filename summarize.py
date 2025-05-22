import streamlit as st
import base64, time
from streamlit_theme import st_theme
from openai import OpenAI

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
st.title("Summarize Document")

# User input for API key
api_key = st.text_input("Enter your API Key:", type="password")
if api_key:
    client = OpenAI(api_key=api_key)

# Upload file
uploaded_file = st.file_uploader("Upload file", type="pdf")  # None artinya semua jenis file boleh diupload
if uploaded_file is not None:
    # Baca nama dan jenis file
    file_name = uploaded_file.name
    file_type = uploaded_file.type

    # Baca file sebagai bytes
    file_bytes = uploaded_file.read()

    # Encode ke base64
    encoded_base64 = base64.b64encode(file_bytes).decode('utf-8')
    
    # Tampilkan hasil
    st.write(f"Nama file: {file_name}")
    st.write(f"Tipe file: `{file_type}`")

    tab1, tab2 = st.tabs(["Summary", "Points"])
    with tab1:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "file",
                            "file": {
                                "filename": file_name,
                                "file_data": f"data:application/pdf;base64,{encoded_base64}",
                            }
                        },
                        {
                            "type": "text",
                            "text": "Summarize the file into one paragraph. Write the summary in Indonesia language.",
                        }
                    ],
                },
            ],
        )
        answer = completion.choices[0].message.content
        input_tokens = completion.usage.prompt_tokens
        output_tokens = completion.usage.completion_tokens
        price = 17_000 * ((input_tokens*0.15) + (output_tokens*0.6))/1_000_000
        with st.container():
            st.write(answer)
        with st.popover("Open Usage Details"):
            st.write(f"input_tokens : {input_tokens}")
            st.write(f"output_tokens : {output_tokens}")
            st.write(f"price (IDR): {price}")
    with tab2:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "file",
                            "file": {
                                "filename": file_name,
                                "file_data": f"data:application/pdf;base64,{encoded_base64}",
                            }
                        },
                        {
                            "type": "text",
                            "text": "Summarize the file into several bullet points. Write in Indonesia language.",
                        }
                    ],
                },
            ],
        )
        answer = completion.choices[0].message.content
        input_tokens = completion.usage.prompt_tokens
        output_tokens = completion.usage.completion_tokens
        price = 17_000 * ((input_tokens*0.15) + (output_tokens*0.6))/1_000_000
        with st.container():
            st.write(answer)
        with st.popover("Open Usage Details"):
            st.write(f"input_tokens : {input_tokens}")
            st.write(f"output_tokens : {output_tokens}")
            st.write(f"price (IDR): {price}")