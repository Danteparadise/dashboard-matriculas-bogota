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

# ==============================================================================
# DEFINICIÓN MANUAL Y ESTRICTA DE COLUMNAS DE TEXTO (EVITA CÓDIGOS ID)
# ==============================================================================
col_ies = 'INSTITUCIÓN DE EDUCACIÓN SUPERIOR (IES)'
col_sector = 'SECTOR IES'
col_sexo = 'SEXO'
col_matriculados = 'MATRICULADOS'

col_area = next((c for c in df.columns if 'ÁREA DE CONOCIMIENTO' in c or 'AREA DE CONOCIMIENTO' in c), None)
if not col_area:
    col_area = 'PROGRAMA ACADÉMICO' if 'PROGRAMA ACADÉMICO' in df.columns else df.columns

col_nivel_acad = 'NIVEL ACADÉMICO' if 'NIVEL ACADÉMICO' in df.columns else df.columns
col_nivel_form = 'NIVEL DE FORMACIÓN' if 'NIVEL DE FORMACIÓN' in df.columns else df.columns
col_modalidad = 'MODALIDAD' if 'MODALIDAD' in df.columns else df.columns

df[col_matriculados] = pd.to_numeric(df[col_matriculados], errors='coerce').fillna(0)

# ==============================================================================
# ESTANDARIZACIÓN Y LIMPIEZA EXHAUSTIVA DE REGISTROS NO CLASIFICADOS
# ==============================================================================
columnas_analisis = [col_ies, col_sector, col_sexo, col_nivel_acad, col_nivel_form, col_modalidad, col_area]
for c in columnas_analisis:
    if c in df.columns:
        df[c] = df[c].fillna("").astype(str).str.strip()

# Filtrado metodológico riguroso en la columna del Área de Conocimiento
if col_area in df.columns:
    df = df[
        (df[col_area] != "") & 
        (df[col_area].str.upper() != "NO ESPECIFICA") & 
        (df[col_area].str.upper() != "SIN INFORMACIÓN") & 
        (df[col_area].str.upper() != "SIN INFORMACION") & 
        (df[col_area].str.upper() != "SIN CLASIFICACIÓN") & 
        (df[col_area].str.upper() != "SIN CLASIFICACION") & 
        (df[col_area].str.upper() != "N/A") &
        (df[col_area].str.upper() != "NAN")
    ]

st.sidebar.header("🎛️ Panel de Control de Variables")
st.sidebar.markdown("Modifique los parámetros para segmentar la población en tiempo real.")

opciones_sector = sorted(df[col_sector].unique().tolist())
selected_sector = st.sidebar.multiselect("Sector de la Institución", opciones_sector, default=opciones_sector)

opciones_nivel_acad = sorted(df[col_nivel_acad].unique().tolist())
selected_nivel_acad = st.sidebar.multiselect("Nivel Académico", opciones_nivel_acad, default=opciones_nivel_acad)

opciones_nivel_form = sorted(df[col_nivel_form].unique().tolist())
selected_nivel_form = st.sidebar.multiselect("Nivel de Formación", opciones_nivel_form, default=opciones_nivel_form)

opciones_modalidad = sorted(df[col_modalidad].unique().tolist())
selected_modalidad = st.sidebar.multiselect("Modalidad de Estudio", opciones_modalidad, default=opciones_modalidad)

opciones_sexo = sorted(df[col_sexo].unique().tolist())
selected_sexo = st.sidebar.multiselect("Género / Sexo", opciones_sexo, default=opciones_sexo)

mask = (df[col_sector].isin(selected_sector)) & (df[col_sexo].isin(selected_sexo)) & (df[col_nivel_acad].isin(selected_nivel_acad)) & (df[col_nivel_form].isin(selected_nivel_form)) & (df[col_modalidad].isin(selected_modalidad))
df_filtered = df[mask]

if df_filtered.empty:
    st.warning("La combinación de filtros actual no arrojó resultados. Intente flexibilizar los parámetros en la barra lateral.")
else:
    tab1, tab2 = st.tabs([
        "📈 Diagnóstico Global y Tendencias", 
        "🏢 Enfoque Institucional y de Demanda"
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
            st.subheader("Volumen y Cuota Relativa por Área Académica")
            
            df_area_g = df_filtered.groupby(col_area)[col_matriculados].sum().reset_index()
            df_area_g["%"] = (df_area_g[col_matriculados] / total_matriculados) * 100
            
            df_area_presentation = df_area_g.sort_values(by=col_matriculados, ascending=False)
            df_area_g_top10 = df_area_g.sort_values(by=col_matriculados, ascending=True).tail(10)
            
            with st.expander("🔬 Ver Ficha Cuantitativa por Variable (Clasificación Estadística)", expanded=True):
                st.markdown("""
                    Mapeo multidimensional del ecosistema de educación superior estructurado según las variables metodológicas requeridas:
                """)
                
                df_maestria = df_area_presentation.rename(columns={
                    col_area: "1. Variable Categórica (Área del Conocimiento)",
                    col_matriculados: "2. Variable Discreta (Estudiantes Matriculados)",
                    "%": "3. Variable Continua (% Representación por Área)"
                })
                
                st.dataframe(
                    df_maestria,
                    column_config={
                        "2. Variable Discreta (Estudiantes Matriculados)": st.column_config.NumberColumn(format="%d"),
                        "3. Variable Continua (% Representación por Área)": st.column_config.NumberColumn(format="%.2f%%")
                    },
                    hide_index=True,
                    use_container_width=True,
                    height=200
                )
            
            fig_bar = px.bar(
                df_area_g_top10, x=col_matriculados, y=col_area, orientation='h',
                text=df_area_g_top10["%"].apply(lambda x: f'{x:.1f}%'),
                labels={col_matriculados: "Estudiantes Matriculados", col_area: "Área de Conocimiento / Programa"},
                color=col_matriculados, color_continuous_scale="Blues"
            )
            fig_bar.update_layout(showlegend=False, height=400, margin=dict(l=250, r=20, t=10, b=10))
            st.plotly_chart(fig_bar, use_container_width=True)
            
        with col_g2:
            st.subheader("Concentración por Sector Institucional")
            df_sector_g = df_filtered.groupby(col_sector)[col_matriculados].sum().reset_index()
            df_sector_g["%"] = (df_sector_g[col_matriculados] / total_matriculados) * 100
            
            fig_pie = px.pie(
                df_sector_g, values=col_matriculados, names=col_sector, hole=0.4,
                color_discrete_sequence=["#1f77b4", "#aec7e8", "#ff7f0e", "#2ca02c"]
            )
            fig_pie.update_layout(height=450, margin=dict(l=10, r=10, t=10, b=10))
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
                labels={col_matriculados: "Estudiantes Matriculados", col_ies: "Institución de Educación Superior"},
                color_discrete_map={"Oficial": "#1f77b4", "Privado": "#aec7e8", "PÚBLICA": "#1f77b4", "PRIVADA": "#aec7e8"},
                barmode="stack"
            )
            fig_ies.update_layout(height=480, margin=dict(l=250, r=20, t=10, b=10), showlegend=True)
            st.plotly_chart(fig_ies, use_container_width=True)
            
        with col_ins2:
            st.subheader("Preferencia de Elección por Modalidad")
            df_mod_g = df_filtered.groupby(col_modalidad)[col_matriculados].sum().reset_index()
            
            fig_mod = px.bar(
                df_mod_g, x=col_modalidad, y=col_matriculados, color=col_modalidad,
                text_auto='.2s', color_discrete_sequence=px.colors.qualitative.Pastel,
                labels={col_matriculados: "Estudiantes", col_modalidad: "Modalidad"}
            )
