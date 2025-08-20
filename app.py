# FMEA Analysis & Root Cause Application - End-to-End MVP
#
# Covers key skills:
# - Generative AI integration using a free, open-source model (Ollama)
# - End-to-end application development with Streamlit
# - Data processing and structured output (JSON/YAML)
# - Robust error handling for configuration issues
#
# NOTE: This application requires an Ollama server to be running and
# the specified model to be available locally.
#
# >>> STEPS TO RUN THIS APPLICATION <<<
# 1. Ensure Ollama is installed and running on your machine.
# 2. Open a terminal and run 'ollama pull mistral' to download the model.
# 3. Create a folder named '.streamlit' in the same directory as app.py.
# 4. Inside the '.streamlit' folder, create a file named 'secrets.toml'.
# 5. Paste the following text into your 'secrets.toml' file:
#
#    [ollama]
#    OLLAMA_HOST = "http://localhost:11434"
#    OLLAMA_MODEL = "mistral"
#
# 6. Save the file and then run the app with 'streamlit run app.py'.
#
# Requirements: streamlit, autogen, pyyaml, ollama (client lib is autogen dependency)

import streamlit as st
import autogen
import json
import yaml

# =====================================================================
# 1. Streamlit UI Configuration
# =====================================================================
st.set_page_config(page_title="FMEA & Root Cause Analysis", layout="wide")
st.title("FMEA & Root Cause Analysis")
st.markdown("Use this AI-powered assistant to perform Failure Mode and Effects Analysis (FMEA) on a component or system based on a description of its requirements.")
st.markdown("---")


# =====================================================================
# 2. Configuration & Secrets Handling
# =====================================================================
def get_ollama_config():
    """
    Checks for and returns the Ollama configuration from Streamlit secrets.
    Raises an exception if the required secrets are not found.
    """
    try:
        ollama_host = st.secrets["ollama"]["OLLAMA_HOST"]
        ollama_model = st.secrets["ollama"]["OLLAMA_MODEL"]
        return ollama_host, ollama_model
    except KeyError as e:
        st.error(
            f"❌ Missing Ollama configuration in Streamlit secrets.toml. "
            f"Please add a `[ollama]` section with `OLLAMA_HOST` and `OLLAMA_MODEL`."
            f"\n\nExample:\n"
            f"```toml\n"
            f"[ollama]\n"
            f"OLLAMA_HOST = \"http://localhost:11434\"\n"
            f"OLLAMA_MODEL = \"mistral\"\n"
            f"```"
        )
        st.stop()
    except Exception as e:
        st.error(
            f"An unexpected error occurred while reading secrets: {e}"
        )
        st.stop()


# =====================================================================
# 3. User Input & Agent Initialization
# =====================================================================

# Get LLM configuration from secrets
ollama_host, ollama_model = get_ollama_config()

# Define default FMEA prompt
default_prompt = (
    "Perform a Failure Mode and Effects Analysis (FMEA) for a car brake system. "
    "Identify potential failure modes, their effects, severity, causes, and recommended actions. "
    "Present the output as a YAML object. "
    "The FMEA table should include the following columns: 'Failure Mode', 'Effect', 'Severity (1-10)', 'Cause', 'Recommended Action'."
)

# Text area for user to define the FMEA prompt
requirements = st.text_area(
    "Enter your requirements for the FMEA analysis:",
    value=default_prompt,
    height=200
)

# Initialize the LLM configuration for AutoGen
llm_config = {
    "config_list": [
        {
            "model": ollama_model,
            "api_key": "not-needed", # API key is not required for local Ollama
            "base_url": ollama_host,
        }
    ]
}

# Define the AI assistant agent with instructions for FMEA
assistant = autogen.AssistantAgent(
    name="FMEA_Expert",
    system_message=(
        "You are an expert in Failure Mode and Effects Analysis (FMEA). "
        "Your task is to take a set of requirements and generate a detailed FMEA report. "
        "You must follow the format instructions precisely and provide only the requested output."
    ),
    llm_config=llm_config,
)

# Define the user proxy agent
user_proxy = autogen.UserProxyAgent(
    name="User",
    human_input_mode="NEVER",  # Do not wait for human input
    max_consecutive_auto_reply=10,
    is_termination_msg=lambda x: "```yaml" in x or "```json" in x,
    code_execution_config={"work_dir": "coding", "use_docker": False},
)


# =====================================================================
# 4. Main Application Logic
# =====================================================================

if st.button("Run FMEA Analysis", key="run_fmea"):
    with st.spinner("Generating FMEA report... Please wait."):
        try:
            # Start the conversation and get the response
            response = user_proxy.initiate_chat(
                assistant,
                message=requirements
            )

            # Extract the generated content
            fmea_content = response.chat_history[-1]["content"]

            # Display the raw output
            st.subheader("Raw Output")
            st.code(fmea_content, language="yaml")

            # Try to parse and display the YAML
            st.subheader("Parsed & Formatted Output")
            fmea_data = yaml.safe_load(fmea_content.strip().strip("```yaml").strip())
            st.json(fmea_data)

        except Exception as e:
            st.error(f"An error occurred during agent execution: {e}")
            st.warning(
                "Please ensure that the specified Ollama model is downloaded and running."
            )
            st.code("Example: ollama run mistral")
