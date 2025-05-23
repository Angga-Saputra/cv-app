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

with st.spinner("Preparing Application"):
    time.sleep(1)

def get_base64_of_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        st.error(f"Background image not found: {image_path}")
        return None

def set_responsive_background():
    """Set background that responds to Streamlit Cloud theme settings"""
    light_bg = get_base64_of_image("./light_bg.png")
    dark_bg = get_base64_of_image("./dark_bg.png")
    
    if not light_bg or not dark_bg:
        return
    
    # Get the configured theme from Streamlit settings
    configured_theme = st.get_option("theme.base") or "light"
    
    st.markdown(
        f"""
        <style>
        /* Base background for light theme or default */
        .stApp {{
            background-image: url("data:image/png;base64,{light_bg}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        }}
        
        /* Override for dark theme when configured in Streamlit Cloud */
        .stApp[data-theme="dark"],
        [data-theme="dark"] .stApp,
        body[data-theme="dark"] .stApp {{
            background-image: url("data:image/png;base64,{dark_bg}") !important;
        }}
        
        /* Media query fallback for system dark mode preference */
        @media (prefers-color-scheme: dark) {{
            .stApp {{
                background-image: url("data:image/png;base64,{dark_bg}");
            }}
        }}
        
        /* Force dark background if theme is configured as dark */
        {"" if configured_theme != "dark" else f'''
        .stApp {{
            background-image: url("data:image/png;base64,{dark_bg}") !important;
        }}
        '''}
        </style>
        
        <script>
        // Set theme attribute based on Streamlit's theme configuration
        document.documentElement.setAttribute('data-theme', '{configured_theme}');
        document.body.setAttribute('data-theme', '{configured_theme}');
        
        // Also check for runtime theme indicators
        setTimeout(function() {{
            const appContainer = document.querySelector('.stApp');
            if (appContainer) {{
                appContainer.setAttribute('data-theme', '{configured_theme}');
            }}
        }}, 100);
        </script>
        """,
        unsafe_allow_html=True
    )

# Apply the responsive background
set_responsive_background()

# Debug info in sidebar
with st.sidebar:
    st.write("**Theme Debug Info:**")
    current_theme = st.get_option("theme.base")
    st.write(f"Configured theme: `{current_theme}`")
    st.write("*Theme changes require app restart in Streamlit Cloud*")

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
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_results.to_excel(writer, index=False, sheet_name='CV Analysis')
            excel_data = output.getvalue()

            # Add download button
            st.download_button(
                label="📥 Download Analysis Results as Excel",
                data=excel_data,
                file_name="cv_analysis_results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )