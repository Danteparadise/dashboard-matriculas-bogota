import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Analítica de Matrículas Educación Superior - Bogotá",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main .block-container { padding-top: 1.5rem; }
    div[data-testid="stMetricValue"] { font-size: 26px; font-weight: bold; color: #1f77b4; }
    .stAlert p { font-size: 15px; }
    .css-1kyx603 { padding-top: 1rem; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Ecosistema de Concentración Estudiantil en Bogotá")
st.markdown("### Modelado Cuantitativo Multivariado de Matrículas en Educación Superior (Datos Oficiales SNIES)")
st.markdown("---")

df = pd.read_csv("matriculados_bogota_2025.csv", encoding="latin-1", sep=";")
df.columns = df.columns.str.strip()
df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

col_ies = 'INSTITUCIÓN DE EDUCACIÓN SUPERIOR (IES)'
col_sector = 'SECTOR IES'
col_sexo = 'SEXO'
col_matriculados = 'MATRICULADOS'

col_nivel_acad = next((c for c in df.columns if 'NIVEL ACADÉMICO' in c and 'CÓDIGO' not in c and 'ID' not in c), 'NIVEL ACADÉMICO')
col_nivel_form = next((c for c in df.columns if 'NIVEL DE FORMACIÓN' in c and 'CÓDIGO' not in c and 'ID' not in c), 'NIVEL DE FORMACIÓN')
col_modalidad = next((c for c in df.columns if ('METODOLOGÍA' in c or 'MODALIDAD' in c) and 'CÓDIGO' not in c and 'ID' not in c), 'MODALIDAD')

col_area = next((c for c in df.columns if ('CINE' in c or 'ÁREA' in c or 'AREA' in c) and 'CÓDIGO' not in c), None)
if not col_area:
    col_area = 'PROGRAMA ACADÉMICO' if 'PROGRAMA ACADÉMICO' in df.columns else df.columns

df[col_matriculados] = pd.to_numeric(df[col_matriculados], errors='coerce').fillna(0)

columnas_analisis = [col_ies, col_sector, col_sexo, col_nivel_acad, col_nivel_form, col_modalidad, col_area]
for c in columnas_analisis:
    if c in df.columns:
        df[c] = df[c].fillna("NO ESPECIFICA").astype(str).str.strip()

st.sidebar.header("🎛️ Panel de Control de Variables")
st.sidebar.markdown("Modifique los parámetros para segmentar la población en tiempo real.")

opciones_sector = sorted(df[col_sector].unique().tolist())
selected_sector = st.sidebar.multiselect("Sector de la Institución", opciones_sector, default=opciones_sector)

if col_nivel_acad in df.columns:
    opciones_nivel_acad = sorted(df[col_nivel_acad].unique().tolist())
    selected_nivel_acad = st.sidebar.multiselect("Nivel Académico", opciones_nivel_acad, default=opciones_nivel_acad)
else:
    selected_nivel_acad = []

if col_nivel_form in df.columns:
    opciones_nivel_form = sorted(df[col_nivel_form].unique().tolist())
    selected_nivel_form = st.sidebar.multiselect("Nivel de Formación", opciones_nivel_form, default=opciones_nivel_form)
else:
    selected_nivel_form = []

if col_modalidad in df.columns:
    opciones_modalidad = sorted(df[col_modalidad].unique().tolist())
    selected_modalidad = st.sidebar.multiselect("Modalidad de Estudio", opciones_modalidad, default=opciones_modalidad)
else:
    selected_modalidad = []

opciones_sexo = sorted(df[col_sexo].unique().tolist())
selected_sexo = st.sidebar.multiselect("Género / Sexo", opciones_sexo, default=opciones_sexo)

mask = (df[col_sector].isin(selected_sector)) & (df[col_sexo].isin(selected_sexo))

if col_nivel_acad in df.columns and selected_nivel_acad:
    mask = mask & (df[col_nivel_acad].isin(selected_nivel_acad))
if col_nivel_form in df.columns and selected_nivel_form:
    mask = mask & (df[col_nivel_form].isin(selected_nivel_form))
if col_modalidad in df.columns and selected_modalidad:
    mask = mask & (df[col_modalidad].isin(selected_modalidad))
    
df_filtered = df[mask]

if df_filtered.empty:
    st.warning("La combinación de filtros actual no arrojó resultados. Intente flexibilizar los parámetros en la barra lateral.")
else:
    tab1, tab2, tab3 = st.tabs([
        "📈 Diagnóstico Global y Tendencias", 
        "🏢 Enfoque Institucional y de Demanda", 
        "📋 Consulta Microdatos y Exportación"
    ])

    with tab1:
        st.markdown("#### Distribución Macro y Concentración de la Matrícula")
        
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        
        total_matriculados = int(df_filtered[col_matriculados].sum())
        ies_unicas = df_filtered[col_ies].nunique()
        
        top_area_series = df_filtered.groupby(col_area)[col_matriculados].sum()
        area_top = top_area_series.idxmax() if not top_area_series.empty else "N/A"
        
        total_femenino = df_filtered[df_filtered[col_sexo].str.upper().str.contains('FEM', na=False)][col_matriculados].sum()
        part_femenina = (total_femenino / total_matriculados) * 100 if total_matriculados > 0 else 0

        with kpi1:
            st.metric("Población Matriculada", f"{total_matriculados:,}")
        with kpi2:
            st.metric("Oferta de IES en Bogotá", f"{ies_unicas}")
        with kpi3:
            st.metric("Núcleo de Mayor Densidad", str(area_top)[:22] + "...")
        with kpi4:
            st.metric("Índice de Participación Fem.", f"{part_femenina:.1f}%")
        
        st.markdown("---")
        
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.subheader(f"Volumen y Cuota Relativa por {col_area}")
            df_area_g = df_filtered.groupby(col_area)[col_matriculados].sum().reset_index()
            df_area_g = df_area_g.sort_values(by=col_matriculados, ascending=True).tail(10)
            df_area_g["%"] = (df_area_g[col_matriculados] / total_matriculados) * 100
            
            fig_bar = px.bar(
                df_area_g, x=col_matriculados, y=col_area, orientation='h',
                text=df_area_g["%"].apply(lambda x: f'{x:.1f}%'),
                labels={col_matriculados: "Estudiantes", col_area: "Área / Programa"},
                color=col_matriculados, color_continuous_scale="Blues"
            )
            fig_bar.update_layout(showlegend=False, height=400, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig_bar, use_container_width=True)
            
        with col_g2:
            st.subheader("Concentración por Sector Institucional")
            df_sector_g = df_filtered.groupby(col_sector)[col_matriculados].sum().reset_index()
            df_sector_g["%"] = (df_sector_g[col_matriculados] / total_matriculados) * 100
            
            fig_pie = px.pie(
                df_sector_g, values=col_matriculados, names=col_sector, hole=0.4,
                color_discrete_sequence=["#1f77b4", "#aec7e8", "#ff7f0e", "#2ca02c"]
            )
            fig_pie.update_layout(height=400, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig_pie, use_container_width=True)

    with tab2:
        st.markdown("#### Análisis Específico de Captación por Institución Superior")
        
        col_ins1, col_ins2 = st.columns(2)
        
        with col_ins1:
            st.subheader("Top 15 Instituciones con Mayor Densidad de Matrícula")
            df_ies_g = df_filtered.groupby([col_ies, col_sector])[col_matriculados].sum().reset_index()
            df_ies_g = df_ies_g.sort_values(by=col_matriculados, ascending=True).tail(15)
            
            fig_ies = px.bar(
                df_ies_g, x=col_matriculados, y=col_ies, color=col_sector,
                labels={col_matriculados: "Estudiantes Matriculados", col_ies: "Institución"},
                color_discrete_map={"Oficial": "#1f77b4", "Privado": "#aec7e8", "PÚBLICA": "#1f77b4", "PRIVADA": "#aec7e8"},
                barmode="stack"
            )
            fig_ies.update_layout(height=480, showlegend=True)
            st.plotly_chart(fig_ies, use_container_width=True)
            
        with col_ins2:
            st.subheader("Preferencia de Elección por Modalidad")
            df_mod_g = df_filtered.groupby(col_modalidad)[col_matriculados].sum().reset_index()
            
            fig_mod = px.bar(
                df_mod_g, x=col_modalidad, y=col_matriculados, color=col_modalidad,
                text_auto='.2s', color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_mod.update_layout(height=480, showlegend=False)
            st.plotly_chart(fig_mod, use_container_width=True)

    with tab3:
        st.markdown("#### Motor de Búsqueda Avanzada y Auditoría de Datos")
        
        search_query = st.text_input("🔍 Filtrar tabla por nombre de Universidad, Programa Académico o Área:", "")
        
        df_table_display = df_filtered[[col_ies, col_sector, col_nivel_acad, col_nivel_form, col_modalidad, col_area, col_sexo, col_matriculados]]
        
        if search_query:
            search_mask = df_table_display.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)
            df_table_display = df_table_display[search_mask]
        
        df_table_display = df_table_display.sort_values(by=col_matriculados, ascending=False)
        st.caption(f"Mostrando {len(df_table_display)} filas.")
        st.dataframe(df_table_display, use_container_width=True, hide_index=True, height=350)
        
        csv_data = df_table_display.to_csv(index=False, sep=";").encode('latin-1')
        st.download_button(
            label="📥 Descargar Base de Datos Filtrada (Formato CSV para Excel)",
            data=csv_data,
            file_name="matriculados_filtrados_bogota.csv",
            mime="text/csv"
        )

st.markdown("---")
st.caption("Ecosistema analítico avanzado desarrollado en Python para tesis de posgrado. Datos validados del Sistema Nacional de Información de la Educación Superior (SNIES).")
