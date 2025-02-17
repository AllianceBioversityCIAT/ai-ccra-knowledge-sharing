import streamlit as st
import time
import os
import pyperclip
from openai import OpenAI
from dotenv import load_dotenv
from streamlit_modal import Modal

load_dotenv()

client = OpenAI(
    organization=os.getenv('OPENAI_ORGANIZATION_ID'),
    api_key=os.getenv('OPENAI_API_KEY')
)

modal = Modal(
    "Edit Prompt",
    key="edit-prompt-modal",
    padding=20,
    max_width=800
)

# ---------------------------
# FUNCIONES PARA LA API DE OPENAI
# ---------------------------
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

# ---------------------------
# FUNCIONES PARA MANEJAR LOS ARCHIVOS DE PROMPT
# ---------------------------
def get_prompts_dir():
    """Gets (and creates if it does not exist) the directory 'prompts'.."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    prompts_dir = os.path.join(base_dir, "prompts")
    if not os.path.exists(prompts_dir):
        os.makedirs(prompts_dir)
    return prompts_dir

def read_prompt_file(indicator_key):
    prompts_dir = get_prompts_dir()
    prompt_path = os.path.join(prompts_dir, f"{indicator_key}.txt")
    st.write(f"🔎 Searching prompt: {indicator_key}")
    try:
        with open(prompt_path, 'r') as file:
            data = file.read().strip()
            st.write(f"💾 Prompt loaded: {indicator_key}")
            return data
    except FileNotFoundError:
        st.write(f"File not found: {indicator_key}. Please create one in the sidebar.")
        # Si no existe, se retorna un prompt por defecto
        return f"Generates the narrative for {indicator_key} for the 2024 Annual Report."

def save_prompt_file(indicator_key, content):
    prompts_dir = get_prompts_dir()
    prompt_path = os.path.join(prompts_dir, f"{indicator_key}.txt")
    with open(prompt_path, 'w') as file:
        file.write(content)

def list_prompt_files():
    """Lists the file names (without extension) of the prompts in the 'prompts' folder."""
    prompts_dir = get_prompts_dir()
    files = [f for f in os.listdir(prompts_dir) if f.endswith(".txt")]
    prompt_keys = [os.path.splitext(f)[0] for f in files]
    return prompt_keys

# ---------------------------
# LISTA DE INDICADORES (global para usar en la edición y creación de prompts)
# ---------------------------
INDICATORS = [
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

# ---------------------------
# FUNCIÓN PRINCIPAL
# ---------------------------
def main():
    st.set_page_config(
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    left_margin, main_content, right_margin = st.columns([1, 3, 1])

    # ===========================
    # BARRA LATERAL (Sidebar)
    # ===========================
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
                help="Valores más altos generan respuestas más aleatorias; valores bajos, más enfocadas y deterministas"
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
                                st.experimental_rerun()
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
                            st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Error uploading files: {str(e)}")

        # ---------------------------
        # SECCIÓN PARA EDITAR Y CREAR PROMPTS
        # ---------------------------
        with st.expander("📝 Prompts"):
            st.subheader("Edit existing prompts")
            prompt_keys = list_prompt_files()
            if prompt_keys:
                for key in prompt_keys:
                    col1, col2, col3 = st.columns([3, 1, 1])
                    col1.markdown(f"**{key}**")
                    if col2.button("Edit", key=f"edit_prompt_{key}"):
                        st.session_state.editing_prompt = key
                        modal.open()
                    if col3.button("🗑️", key=f"delete_prompt_{key}"):
                        try:
                            os.remove(os.path.join(get_prompts_dir(), f"{key}.txt"))
                            st.success(f"Prompt {key} deleted successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting prompt: {str(e)}")
            else:
                st.info("No prompts are available for editing.")

            st.markdown("---")
            st.subheader("Create new prompt")
            existing_prompts = set(list_prompt_files())
            # Filtrar indicadores que aún no tienen archivo de prompt
            available_indicators = [ind for ind in INDICATORS if ind["key"] not in existing_prompts]
            if available_indicators:
                selected_new_prompt = st.selectbox(
                    "Select indicator for the new prompt",
                    available_indicators,
                    format_func=lambda ind: f"{ind['value']} ({ind['key']})"
                )
                default_content = f"Generates the narrative for {selected_new_prompt['value']} for the 2024 Annual Report."
                new_prompt_content = st.text_area("Contents of the new prompt", value=default_content)
                if st.button("Create new prompt"):
                    # Se guarda el prompt si la key no existe (ya lo validamos en available_indicators)
                    save_prompt_file(selected_new_prompt["key"], new_prompt_content)
                    st.success("New prompt successfully created!")
                    st.rerun()
            else:
                st.info("All indicators already have a prompt assigned to them.")

    # ===========================
    # Modal para editar un prompt (se abre si se presionó "Editar")
    # ===========================
    if modal.is_open():
        with modal.container():
            if "editing_prompt" in st.session_state:
                key_to_edit = st.session_state.editing_prompt
                st.subheader(f"Editing prompt: {key_to_edit}")
                new_content = st.text_area(
                    "Contents of the prompt",
                    value=read_prompt_file(key_to_edit),
                    height=400
                )
                col1, col2 = st.columns([1, 4])
                if col1.button("Save changes", key=f"save_{key_to_edit}"):
                    save_prompt_file(key_to_edit, new_content)
                    st.success("Prompt updated!")
                    del st.session_state.editing_prompt
                    modal.close()
                    st.rerun()
                if col2.button("Cancel", key="cancel_edit"):
                    del st.session_state.editing_prompt
                    modal.close()
                    st.rerun()

    # ===========================
    # CONTENIDO PRINCIPAL
    # ===========================
    with main_content:
        st.title("🤖 AI-CCRA Annual Report Generator 2024")

        st.markdown("""
        This tool helps you generate comprehensive narratives for the 2024 Annual Report. 
        It uses AI to analyze your data and create detailed reports based on the indicators.
        
        **Cómo usar:**
        1. 📁 Upload your data files from the sidebar (⚙️)
        2. ✍️ Customize the prompt if necessary or use the one assigned to the indicator.
        3. 🚀 Click on 'Generate Report' to create your narrative
        """)

        # Aquí se utiliza la lista global INDICATORS en vez de una variable local
        selected_indicator = st.selectbox(
            "Select Indicator",
            ["Select an indicator..."] + [ind["value"] for ind in INDICATORS],
            index=0
        )

        selected_key = next(
            (ind["key"] for ind in INDICATORS if ind["value"] == selected_indicator),
            None
        )

        if 'thread' not in st.session_state:
            st.session_state.thread = create_thread()
        
        # Si se ha seleccionado un indicador, se lee el contenido del prompt desde el archivo correspondiente
        user_input = read_prompt_file(selected_key) if selected_key else "Generate the narrative of Indicators for the Annual Report 2024."
        prompt = user_input

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