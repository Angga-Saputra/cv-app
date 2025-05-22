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
st.title("Image Generation")

# User input for API key
api_key = st.text_input("Enter your API Key:", type="password")
if api_key:
    client = OpenAI(api_key=api_key)

# Input system prompt
image_prompt = st.text_area(
    "System prompt:",
    "Buatkan gambar poster yang berisi himbauan untuk selalu menjaga kebersihan ruangan kerja")

if st.button("Generate Image"): 
    result = client.images.generate(
        model="gpt-image-1",
        prompt=image_prompt
    )

    base64_str = result.data[0].b64_json
    image_data = base64.b64decode(base64_str)
    st.image(image_data)