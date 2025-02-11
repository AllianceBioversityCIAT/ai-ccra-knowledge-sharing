import streamlit as st
from openai import OpenAI
import time
from dotenv import load_dotenv
import os
import pyperclip

load_dotenv()

client = OpenAI(
    organization=os.getenv('OPENAI_ORGANIZATION_ID'),
    api_key=os.getenv('OPENAI_API_KEY')
)

def get_assistant_by_id(assistant_id):
    return client.beta.assistants.retrieve(assistant_id=assistant_id)

def create_thread():
    return client.beta.threads.create()

def create_message(thread_id, user_message):
    return client.beta.threads.messages.create(
        thread_id,
        role="user",
        content=user_message,
    )

def list_vector_store(vector_id):
    return client.beta.vector_stores.files.list(
       vector_store_id=vector_id
    )

def delete_vector_store_file(vector_store_id, file_id):
    remove_vector_file = client.beta.vector_stores.files.delete(
        vector_store_id=vector_store_id,
        file_id=file_id
    )

    return client.files.delete(
        file_id=file_id
    )

def upload_to_vector_store(vector_store_id, file):
    formatted_filename = file.name.lower().replace(' ', '_')
    file.name = formatted_filename
    
    uploadFile = client.files.create(
        file=file,
        purpose="assistants"
    )

    return client.beta.vector_stores.files.create(
        vector_store_id=vector_store_id,
        file_id=uploadFile.id,
    )

def find_file_metadate(file_id):
    return client.files.retrieve(file_id)

def update_assistant_metadata(assistant_id, instruction, temperature=1):
    return client.beta.assistants.update(
        assistant_id,
        instructions=instruction,
        temperature=temperature,
    )

def read_prompt_file(indicator_key):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_path = os.path.join(base_dir, "prompts", f"{indicator_key}.txt")
    print(f"Looking for prompt file at: {prompt_path}")
    try:
        with open(prompt_path, 'r') as file:
            data = file.read().strip()
            print(f"Found prompt content: {data}")
            return data
    except FileNotFoundError:
        print(f"Prompt file not found at: {prompt_path}")
        return f"Generate the narrative for {indicator_key} for the Annual Report 2024."

def main():
    st.set_page_config(
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    left_margin, main_content, right_margin = st.columns([1, 3, 1])

    with st.sidebar:
        assistant_id = os.getenv('ASSISTANT_ID')
        assistant = get_assistant_by_id(assistant_id)
        vector_store_id = assistant.tool_resources.file_search.vector_store_ids[0]

        st.header("⚙️ Settings")
        with st.expander("🤖 Assistant Settings"):
            default_instructions = assistant.instructions
            assistant_instructions = st.text_area(
                "Assistant Instructions",
                value=default_instructions,
                height=150
            )
            
            temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=2.0,
                value=assistant.temperature,
                step=0.1,
                help="Higher values make the output more random, lower values make it more focused and deterministic"
            )

            if st.button("Save Changes", key="save_instructions"):
                try:
                    update_assistant_metadata(
                        assistant_id, 
                        assistant_instructions,
                        temperature
                    )
                    st.success("Instructions saved successfully!")
                except Exception as e:
                    st.error(f"Error saving instructions: {str(e)}")
        
        assistant_id = os.getenv('ASSISTANT_ID')
        assistant = get_assistant_by_id(assistant_id)
        vector_store_id = assistant.tool_resources.file_search.vector_store_ids[0]

        with st.expander("📃 File Settings"):
            st.subheader("📂 Vector Store Files")
            vector_store_files = list_vector_store(vector_store_id)

            if vector_store_files.data:
                for file in vector_store_files.data:
                    col1, col2, col3 = st.columns([2, 2, 1])
                    metadate = find_file_metadate(file.id)
                    with col1:
                        filename = metadate.filename
                        if len(filename) > 18:
                            short_filename = filename[:18] + "..."
                            st.markdown(f"<div style='font-size: 14px; color: #666666;' title='{filename}'>📄 {short_filename}</div>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<div style='font-size: 14px; color: #666666;'>📄 {filename}</div>", unsafe_allow_html=True)
                    with col2:
                        st.caption(f"📊 {file.usage_bytes/1024:.1f}KB | {file.status}")
                    with col3:
                        if st.button("🗑️", key=f"delete_{file.id}"):
                            try:
                                delete_vector_store_file(vector_store_id, file.id)
                                st.success("File deleted successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error deleting file: {str(e)}")
                    st.markdown("<hr style='margin: 5px 0px'>", unsafe_allow_html=True)
            else:
                st.info("No files in vector store")

            st.subheader("⬆️ Upload to Vector Store")
            vector_store_files = st.file_uploader(
                "Upload files to vector store",
                type=["json", "txt", "pdf"],
                accept_multiple_files=True,
                key="vector_store_upload"
            )
            
            if vector_store_files:
                if st.button("Upload to Vector Store", icon="⬆️"):
                    try:
                        with st.spinner("🔄 Processing..."):
                            for file in vector_store_files:
                                upload_to_vector_store(vector_store_id, file)
                            st.success("Files uploaded successfully!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error uploading files: {str(e)}")

        prompt = st.text_area(
            "✍️ Prompt",
            "Generate the narrative of Indicators for the Annual Report 2024.",
            height=200,
            disabled=True
        )

    with main_content:
        st.title("🤖 AI-CCRA Annual Report Generator 2024")

        st.markdown("""
        This tool helps you generate comprehensive narratives for the CGIAR Annual Report 2024. 
        It uses AI to analyze your data and create detailed reports based on the provided indicators.
        
        **How to use:**
        1. 📁 Upload your data files using the sidebar (⚙️)
        2. ✍️ Customize your prompt if needed
        3. 🚀 Click 'Generate Report' to create your narrative
        """)

        indicators = [
            {"key": "pdo_indicator_1", "value": "PDO Indicator 1"},
            {"key": "pdo_indicator_2", "value": "PDO Indicator 2"},
            {"key": "pdo_indicator_3", "value": "PDO Indicator 3"},
            {"key": "pdo_indicator_4", "value": "PDO Indicator 4"},
            {"key": "pdo_indicator_5", "value": "PDO Indicator 5"},
            {"key": "ipi_1_1", "value": "IPI 1.1"},
            {"key": "ipi_1_2", "value": "IPI 1.2"},
            {"key": "ipi_1_3", "value": "IPI 1.3"},
            {"key": "ipi_1_4", "value": "IPI 1.4"},
            {"key": "ipi_2_1", "value": "IPI 2.1"},
            {"key": "ipi_2_2", "value": "IPI 2.2"},
            {"key": "ipi_2_3", "value": "IPI 2.3"},
            {"key": "ipi_3_1", "value": "IPI 3.1"},
            {"key": "ipi_3_2", "value": "IPI 3.2"},
            {"key": "ipi_3_3", "value": "IPI 3.3"},
            {"key": "ipi_3_4", "value": "IPI 3.4"},
        ]
        
        selected_indicator = st.selectbox(
            "Select Indicator",
            ["Select an indicator..."] + [ind["value"] for ind in indicators],
            index=0
        )

        selected_key = next(
            (ind["key"] for ind in indicators if ind["value"] == selected_indicator),
            None
        )

        if 'thread' not in st.session_state:
            st.session_state.thread = create_thread()
        
        user_input = read_prompt_file(selected_key) if selected_key else prompt
        prompt = user_input
        print('🚀 ------------------------------------', user_input)

        if st.button("🚀 Generate Report", disabled=(selected_indicator == "Select an indicator...")):
            try:
                with st.spinner("🔄 Processing..."):
                    assistant = get_assistant_by_id(os.getenv('ASSISTANT_ID'))
                    create_message(st.session_state.thread.id, user_input)
                    
                    stream = client.beta.threads.runs.create(
                        thread_id=st.session_state.thread.id,
                        assistant_id=assistant.id,
                        stream=True
                    )
                    
                    output_container = st.empty()
                    full_response = ""
                    
                    for event in stream:
                        if hasattr(event, 'data') and hasattr(event.data, 'delta'):
                            if hasattr(event.data.delta, 'content') and event.data.delta.content:
                                for content in event.data.delta.content:
                                    if content.type == "text":
                                        text_value = content.text.value
                                        full_response += text_value
                                        output_container.markdown(full_response)
                        
                        elif hasattr(event, 'status'):
                            if event.status == 'completed':
                                if st.button("📋 Copy Output", key="copy_button"):
                                    st.write("Copied to clipboard! ✨")
                                    st.clipboard_data(full_response)
                                st.success("Report generated successfully!")
                                break
                            elif event.status == 'failed':
                                st.error("❌ Execution failed. Please try again.")
                                return
                        
            except Exception as e:
                st.error(f"❌ An error occurred: {str(e)}")

if __name__ == '__main__':
    main()