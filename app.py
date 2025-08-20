# app.py
# A Streamlit application for performing FMEA with Agentic AI using AutoGen.
# This version is designed to run on free hosting platforms like Streamlit Community Cloud.
#
# Key changes from the previous version:
# 1. Replaces the hardcoded `localhost` LLM endpoint with a flexible Streamlit secret.
# 2. Uses `st.file_uploader` to allow the user to upload data files instead of reading from a local disk.
# 3. Provides a simple, interactive UI using Streamlit components.

import streamlit as st
import autogen
import json
import yaml

# --- 1. Streamlit UI Setup ---
st.set_page_config(page_title="Agentic FMEA App", layout="wide")
st.title("🛡️ Agentic FMEA Application")
st.markdown("Perform a Failure Mode and Effects Analysis on your data using Agentic AI.")
st.divider()

# --- 2. LLM Configuration via Streamlit Secrets ---
# The LLM host URL is loaded from Streamlit's secrets management.
# This is crucial for deploying on free cloud services where a local Ollama instance is not available.
# The user must provide `OLLAMA_HOST` and `OLLAMA_MODEL` in a `secrets.toml` file.
# Example secrets.toml:
# OLLAMA_HOST = "http://your-remote-ollama-host:11434/v1"
# OLLAMA_MODEL = "llama3"
if "OLLAMA_HOST" not in st.secrets or "OLLAMA_MODEL" not in st.secrets:
    st.error("Missing Ollama configuration. Please add OLLAMA_HOST and OLLAMA_MODEL to your Streamlit secrets.")
    st.stop()

llm_config = {
    "config_list": [
        {
            "model": st.secrets["OLLAMA_MODEL"],
            "api_key": "ollama", # This is a placeholder for Ollama's API
            "base_url": st.secrets["OLLAMA_HOST"],
        }
    ],
    "cache_seed": None, # Disable cache for dynamic user input
}

# --- 3. Agents Setup ---
# UserProxyAgent acts as the human administrator and handles file I/O.
user_proxy = autogen.UserProxyAgent(
    name="Admin",
    system_message="A human administrator who delegates FMEA tasks to an AI agent.",
    code_execution_config={"work_dir": "coding"},
    human_input_mode="NEVER",
    llm_config=llm_config,
)

# The FMEA Analyst is the specialized AI agent.
fmea_analyst = autogen.AssistantAgent(
    name="FMEA_Analyst",
    system_message="""You are a highly-skilled Failure Mode and Effects Analysis (FMEA) expert.
    Your task is to analyze system data provided by the user and identify potential failure modes, their effects, and their likely causes.
    You will propose corrective actions and a severity rating (on a scale of 1-10, where 10 is most severe).
    Your output should be a detailed FMEA table for each identified failure mode, presented in a clear and readable Markdown format.""",
    llm_config=llm_config,
)

# --- 4. User Interaction and File Upload ---
st.subheader("Upload Data Files")
uploaded_aws_file = st.file_uploader("Upload AWS API Logs (JSON)", type="json")
uploaded_sap_file = st.file_uploader("Upload SAP Config (YAML)", type="yaml")

# --- 5. Run the FMEA Analysis ---
if uploaded_aws_file and uploaded_sap_file:
    aws_logs_content = uploaded_aws_file.getvalue().decode("utf-8")
    sap_config_content = uploaded_sap_file.getvalue().decode("utf-8")

    st.success("Files uploaded successfully! Starting FMEA analysis...")
    st.divider()

    # The task prompt is constructed with the uploaded content.
    fmea_task = f"""
    Perform a detailed FMEA based on the following two data sources:

    1.  **Proposed AWS Application Solutions (API Gateway Logs):**
        Analyze the following mock API Gateway logs to identify potential failure modes.
        Logs:
        ```json
        {aws_logs_content}
        ```

    2.  **Proposed SAP Integration FMEA (Configuration):**
        Analyze the following mock SAP integration configuration to identify potential failure modes.
        Configuration:
        ```yaml
        {sap_config_content}
        ```

    For each identified failure, provide the following details in a clear and concise Markdown table:
    | Failure Mode | Effect(s) of Failure | Cause(s) of Failure | Severity Rating (1-10) | Corrective Action(s) |
    |---|---|---|---|---|
    """

    with st.spinner("Agent is performing FMEA... this may take a moment."):
        chat_result = user_proxy.initiate_chat(
            fmea_analyst,
            message=fmea_task,
            max_turns=5
        )

    st.success("FMEA Analysis Complete!")
    st.balloons()
    st.markdown("### FMEA Report")
    st.markdown(chat_result.summary)
else:
    st.info("Please upload both the AWS API logs and the SAP configuration files to start the analysis.")
