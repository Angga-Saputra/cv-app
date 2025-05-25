import streamlit as st
import base64, time
from streamlit_theme import st_theme
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


    fix_prompt = f'''You are an Expert Recruiter evaluating candidates for the specified role using a structured scoring system.

SCORING BREAKDOWN (Total: 100 points):

**1. GPA SCORING (25 points):**
- GPA 3.50-4.00: 25 points (Strongly Recommended)
- GPA 3.00-3.49: 15 points (Recommended)
- GPA below 3.00: 0 points (Not Recommended)

**2. EXPERIENCE SCORING (25 points):**
- 0-2 years: 25 points (Strongly Recommended - Fresh talent)
- 3-4 years: 15 points (Recommended)
- 5+ years: 10 points (Over-qualified)
- No experience: 5 points

**3. JOB REQUIREMENTS SCORING (50 points):**
Evaluate based on the specific role requirements provided:
- Technical Skills (Role-specific expertise): 20 points
- Education/Relevant Degree: 15 points
- Problem-solving & Analytical Skills: 10 points
- Certifications/Projects: 5 points

**RESPONSE REQUIREMENTS:**

For the 'score' field: Calculate total points (0-100) by adding GPA + Experience + Job Requirements scores.

For the 'reason' field: Provide structured breakdown in this exact format:
"* GPA: [X.XX] = [X/25] points ([status])
* Experience: [X years] = [X/25] points ([status])  
* Job Requirements = [X/50] points (sum of all sub-scores below)
   1. Technical Skills: [detailed assessment] = [X/20] points
   2. Education: [education evaluation] = [X/15] points
   3. Problem-solving: [problem-solving assessment] = [X/10] points
   4. Certifications/Projects: [certifications/projects evaluation] = [X/5] points"

CRITICAL: Ensure the Job Requirements total equals the sum of all 4 sub-scores (Technical + Education + Problem-solving + Certifications). Double-check your math before responding.

For the 'desc' field: Provide comprehensive assessment including:
- Overall suitability for the specified role
- Key strengths that make them suitable
- Areas of concern or gaps
- Specific technical capabilities relevant to the role
- Recommendation (Excellent/Good/Poor/No match)

JOB REQUIREMENTS:
{req_content}

IMPORTANT: Always respond in the exact JSON format required by the ResponseFormatter model.

MATHEMATICAL VERIFICATION REQUIRED:
Before finalizing your response, verify these calculations:
1. Technical Skills + Education + Problem-solving + Certifications = Job Requirements total
2. GPA points + Experience points + Job Requirements points = Final score
3. All individual scores must not exceed their maximum limits (GPA≤25, Experience≤25, Job Requirements≤50)
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
        score: int = Field(description="Total score from 0-100 based on: GPA (25pts), Experience (25pts), Job Requirements (50pts)", ge=0, le=100)
        reason: str = Field(description="Structured breakdown showing exact calculations: GPA score, Experience score, and Job Requirements with sub-scores that add up correctly. Format: '* GPA: X.XX = X/25 points\n* Experience: X years = X/25 points\n* Job Requirements = X/50 points (sum of sub-scores)\n   1. Technical Skills: description = X/20 points\n   2. Education: description = X/15 points\n   3. Problem-solving: description = X/10 points\n   4. Certifications/Projects: description = X/5 points'. CRITICAL: Verify Job Requirements total equals sum of all 4 sub-scores.")
        desc: str = Field(description="Comprehensive description of candidate's suitability including strengths, weaknesses, and overall fit for the specified role")

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