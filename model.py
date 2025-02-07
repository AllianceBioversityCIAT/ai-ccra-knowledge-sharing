import streamlit as st
import pandas as pd
from transformers import pipeline

# Rutas de los archivos CSV (asegúrate de que existen en esa ubicación)
INDICATORS_PATH = "datasource/AR2024 Project contibution.csv"
PARTNERS_PATH = "datasource/Indicators_partners_outcomes.csv"

@st.cache_data(show_spinner=True)
def load_csv(path):
    """Carga un CSV y lo retorna como DataFrame."""
    return pd.read_csv(path)

def main():
    st.title("Generador de Reporte Anual AICCRA 2024")
    st.write("Esta aplicación genera el reporte anual basado en datos estructurados, usando un modelo de generación de texto.")

    # --- Cargar los datos CSV ---
    try:
        indicators_df = load_csv(INDICATORS_PATH)
        partners_df = load_csv(PARTNERS_PATH)
        st.sidebar.success("Datos cargados exitosamente.")
    except Exception as e:
        st.sidebar.error("Error cargando datos: " + str(e))
        return

    # --- Mostrar vista previa de los CSV en la barra lateral ---
    st.sidebar.subheader("Vista previa: AR2024 Project contibution.csv")
    st.sidebar.dataframe(indicators_df.head())
    st.sidebar.subheader("Vista previa: Indicators_partners_outcomes.csv")
    st.sidebar.dataframe(partners_df.head())

    # --- Parámetros de generación ---
    temperature = st.slider("Temperatura de generación", min_value=0.0, max_value=1.0, value=0.5, step=0.1)
    max_length = st.number_input("Longitud máxima del reporte", min_value=100, max_value=2048, value=1024, step=50)

    # --- Prompt base con instrucciones, referencias y un one-shot example (PDO 1) ---
    base_prompt = (
        "System Role and Context:\n"
        "You are an AI specialized in data analysis and report generation. You have access to data from two CSV files:\n"
        "1. 'AR2024 Project contibution.csv' which contains: Year, Component, Name_indicator, Indicator, Cluster type, Cluster id, Cluster, Target_year, Expected end year, End_year_achieved, Expected narrative, Achieved narrative, Cluster Link.\n"
        "2. 'Indicators_partners_outcomes.csv' which contains: acronym, Indicator, partner_name, Outcomes.\n\n"
        "Your goal is to analyze this data to produce a formal, paragraph-based narrative that aligns with AICCRA’s official report style (similar to previous reports), without comparing results to previous years.\n\n"
        "Core Instructions:\n"
        "- Extract the relevant data and perform necessary calculations (e.g., achievement percentages) using the columns provided.\n"
        "- Aggregate data for each unique indicator and identify the top 10 partners (by Outcomes) for each indicator.\n"
        "- Generate a final, integrated report under the heading '3. Outcomes and Indicator Targets (2024)' with the following subsections:\n"
        "    3.1 Project Development Objectives (PDOs)\n"
        "    3.2 Intermediate Performance Indicators (IPI) for Component 1: Knowledge Generation and Sharing\n"
        "    3.3 Intermediate Performance Indicators (IPI) for Component 2: Strengthening Partnerships for Delivery\n"
        "    3.4 Intermediate Performance Indicators (IPI) for Component 3: Validating Climate-Smart Agriculture Innovations through Piloting\n\n"
        "Please include numerical results, achievement percentages, qualitative insights, and list the top 10 partner names for each indicator.\n\n"
        "One-shot example (PDO 1):\n"
        "PDO 1. AICCRA partners and stakeholders in the project area are increasingly accessing enhanced climate information services and/or validated climate-smart agriculture technologies. "
        "By the end of 2023, 82 partners in the project area were increasingly accessing enhanced CIS and/or validated CSA technologies, exceeding the target of 13 set by the PMC for 2023. "
        "These partners included: National meteorological services, National and regional agricultural research institutes, National extension systems, Small and medium enterprises, Ministries of Agriculture, Media, Universities, Regional climate centers, and Youth organizations. "
        "In terms of CIS, examples include AICCRA's NextGen IFSM Agro-advisory in Ethiopia, which provided fertilizer recommendations to multiple stakeholders. "
        "In Kenya, over 471,000 agro-climate advisories were disseminated through a collaboration between the Kenya Meteorological Department and KALRO. "
        "In Ghana, a significant collaborative effort led by the Ministry of Food and Agriculture mobilized 11 organizations to sign an MOU to enhance defenses against crop pests and diseases. "
        "AICCRA Zambia and Mali also made notable contributions through technical support and training.\n\n"
        "Generate a complete, integrated report based on the above instructions and data."
    )

    # Permitir que el usuario edite el prompt si lo desea
    user_prompt = st.text_area("Prompt que se enviará al modelo", value=base_prompt, height=300)

    # --- Botón para generar el reporte ---
    if st.button("Generar Reporte"):
        with st.spinner("Generando reporte..."):
            # Cargamos el pipeline de generación de texto
            generator = pipeline("text-generation", model="EleutherAI/gpt-neo-2.7B", device=-1)
            result = generator(user_prompt, max_length=max_length, do_sample=True, temperature=temperature)
            generated_report = result[0]['generated_text']
        st.subheader("Reporte Generado")
        st.text_area("Reporte", generated_report, height=400)
        st.markdown(
            """
            <button onclick="navigator.clipboard.writeText(document.querySelector('textarea').value)">
                Copiar Reporte
            </button>
            """,
            unsafe_allow_html=True,
        )

if __name__ == "__main__":
    main()