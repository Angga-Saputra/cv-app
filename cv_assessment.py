import streamlit as st
import base64, time
#from streamlit_theme import st_theme
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from langchain_community.callbacks.manager import get_openai_callback
from langchain_core.messages import HumanMessage
import pandas as pd
from io import BytesIO

def chat(req_content, uploaded_cv):
    file_content = uploaded_cv.read()
    file_name = uploaded_cv.name
    encoded_base64 = base64.b64encode(file_content).decode('utf-8')


    fix_prompt = f'''You are an Expert Recruiters. Your task is review candidate data wether It's match for job requirements or not with given candidate data provided.
Always answer in Indonesia language.
Here is job requirements:
{req_content}
'''

    prompt_text = HumanMessage(
        content=[
            {
                "type": "text",
                "text": fix_prompt
                },
            {
                "type": "file",
                "file": {
                    "filename": file_name,
                    "file_data": f"data:application/pdf;base64,{encoded_base64}"
                    }
                },
        ]
    )

    class ResponseFormatter(BaseModel):
        score: int = Field(description="Give score from 0 to 100 for how much this candidate suits for AI Engineer role")
        reason: str = Field(description="Give the reason about match or not the candidate with needed role")
        desc: str = Field(description="Describe the candidate's skills and capability for needed role")

    model_with_structure = llm.with_structured_output(ResponseFormatter)

    with get_openai_callback() as cb:
        structured_response = model_with_structure.invoke([prompt_text])
        completion_tokens = cb.completion_tokens
        prompt_tokens = cb.prompt_tokens
        score = structured_response.score
        reason = structured_response.reason
        desc = structured_response.desc
        price = 17_000 * (prompt_tokens*0.15 + completion_tokens*0.6)/1_000_000

    response = {
        "score" : score,
        "reason" : reason,
        "desc" : desc,
        "completion_tokens" : completion_tokens,
        "prompt_tokens" : prompt_tokens,
        "price_idr" : price
    }
    return response

theme = st.get_option("theme.base")

if theme is None:
    theme = "light"  # default fallback

with st.spinner("Preparing Application"):
    time.sleep(1)
    theme = st.get_option("theme.base") or "light"

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
st.title("CV Assesment")

# User input for API key
api_key = st.text_input("Enter your API Key:", type="password")
if api_key:
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=api_key
    )

# Uploaded requirement
uploaded_req = st.file_uploader(
    "**Drop Job Requirements Here**", type="txt", accept_multiple_files=False
)

if uploaded_req:
    req_content = uploaded_req.read().decode("utf-8")
    with st.expander("Job Requirements Detail"):
        st.markdown(req_content)
    
    uploaded_cvs = st.file_uploader(
        "**Upload PDF CV**", type="pdf", accept_multiple_files=True
    )

    if uploaded_cvs:
        if st.button("Analyze"):
            st.write("Candidate Analysis Results:")

            result_list = []
            for uploaded_cv in uploaded_cvs:
                st.subheader(f"📘 {uploaded_cv.name}")
                result = chat(req_content, uploaded_cv)
                result['filename'] = uploaded_cv.name
                result_list.append(result)
                st.write(result)
            
            # Convert results to DataFrame
            df_results = pd.DataFrame(result_list)

            # Save DataFrame to Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_results.to_excel(writer, index=False, sheet_name='CV Analysis')
            excel_data = output.getvalue()

            # Add download button
            st.download_button(
                label="📥 Download Analysis Results as Excel",
                data=excel_data,
                file_name="cv_analysis_results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )