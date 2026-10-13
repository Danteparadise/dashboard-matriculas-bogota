import streamlit as st
import pandas as pd
import plotly.express as px

# ==============================================================================
# 1. CONFIGURACIÓN DE LA PÁGINA (Estilo Ejecutivo/Master)
# ==============================================================================
st.set_page_config(
    page_title="Dashboard de Concentración Estudiantil - Bogotá",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo CSS para acabados profesionales limpios
st.markdown("""
    <style>
    .main .block-container { padding-top: 1.5rem; }
    div[data-testid="stMetricValue"] { font-size: 26px; font-weight: bold; color: #1f77b4; }
    .stAlert p { font-size: 15px; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Distribución y Concentración Estudiantil en Bogotá")
st.markdown("### Análisis Estadístico Multivariado de Matrículas en Educación Superior (Datos SNIES)")
st.markdown("---")

# ==============================================================================
# 2. CARGA Y LIMPIEZA AUTOMÁTICA DE DATOS REALES
# ==============================================================================
try:
    # Carga con los parámetros latinoamericanos validados
    df = pd.read_csv("matriculados_bogota_2025.csv", encoding="latin-1", sep=";")
    
    # Limpieza institucional de nombres de columnas (eliminar espacios invisibles de Excel)
    df.columns = df.columns.str.strip()
    
    # Eliminar columnas vacías fantasmas como 'Unnamed: 41' si existen
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

    # Mapeo estricto de las columnas validadas en el Inspector
    col_sector = 'SECTOR IES'
    col_sexo = 'SEXO'
    col_matriculados = 'MATRICULADOS'
    
    # Identificar columna de Área o Programa de forma flexible
    col_area = next((c for c in df.columns if 'CINE' in c or 'ÁREA' in c or 'AREA' in c or 'NIVEL DE FORMACIÓN' in c), None)
    if not col_area:
        col_area = 'PROGRAMA ACADÉMICO' if 'PROGRAMA ACADÉMICO' in df.columns else df.columns[2]

    # Convertir la columna de estudiantes a número de forma segura
    df[col_matriculados] = pd.to_numeric(df[col_matriculados], errors='coerce').fillna(0)

    # ==============================================================================
    # 3. BARRA LATERAL (Filtros Avanzados)
    # ==============================================================================
    st.sidebar.header("Filtros del Modelo")
    st.sidebar.markdown("Filtre la población bajo estudio en tiempo real.")

    # Filtro Dinámico 1: Sector IES (Oficial / Privado)
    opciones_sector = sorted(df[col_sector].dropna().unique().tolist())
    selected_sector = st.sidebar.multiselect("Sector de la Institución", opciones_sector, default=opciones_sector)

    # Filtro Dinámico 2: Sexo
    opciones_sexo = sorted(df[col_sexo].dropna().unique().tolist())
    selected_sexo = st.sidebar.multiselect("Género / Sexo", opciones_sexo, default=opciones_sexo)

    # Aplicación estricta de filtros sobre la matriz original
    df_filtered = df[
        (df[col_sector].isin(selected_sector)) & 
        (df[col_sexo].isin(selected_sexo))
    ]

    # Verificar si el filtro dejó datos vacíos
    if df_filtered.empty:
        st.warning("No hay registros que coincidan con la combinación de filtros seleccionada.")
    else:
        # ==============================================================================
        # 4. CUERPO PRINCIPAL Y VISUALIZACIONES
        # ==============================================================================
        # Fila de KPIs de Alto Impacto
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        
        total_matriculados = int(df_filtered[col_matriculados].sum())
        ies_unicas = df_filtered["INSTITUCIÓN DE EDUCACIÓN SUPERIOR (IES)"].nunique()
        
        # Área o programa con mayor cantidad de alumnos
        top_area_series = df_filtered.groupby(col_area)[col_matriculados].sum()
        area_top = top_area_series.idxmax() if not top_area_series.empty else "N/A"
        
        # Calcular porcentaje de participación oficial
        total_oficial = df_filtered[df_filtered[col_sector].str.upper() == 'OFICIAL'][col_matriculados].sum() if col_sector in df_filtered.columns else 0
        part_oficial = (total_oficial / total_matriculados) * 100 if total_matriculados > 0 else 0

        with kpi1:
            st.metric("Total Matriculados", f"{total_matriculados:,}")
        with kpi2:
            st.metric("IES en Bogotá Evaluadas", f"{ies_unicas}")
        with kpi3:
            st.metric("Máxima Densidad en", str(area_top)[:22] + "...")
        with kpi4:
            st.metric("Participación Pública", f"{part_oficial:.1f}%")

        st.markdown("---")

        # Fila de Gráficos de Distribución
        col1, col2 = st.columns(2)

        with col1:
            st.subheader(f"Concentración por {col_area}")
            # Agrupar los top 10 para evitar saturar el gráfico horizontal si son muchos programas
            df_area_g = df_filtered.groupby(col_area)[col_matriculados].sum().reset_index()
            df_area_g = df_area_g.sort_values(by=col_matriculados, ascending=True).tail(12)
            df_area_g["Porcentaje"] = (df_area_g[col_matriculados] / df_area_g[col_matriculados].sum()) * 100
            
            fig_bar = px.bar(
                df_area_g, 
                x=col_matriculados, 
                y=col_area, 
                orientation='h',
                text=df_area_g['Porcentaje'].apply(lambda x: f'{x:.1f}%'),
                labels={col_matriculados: "Estudiantes", col_area: "Segmento Académico"},
                color=col_matriculados,
                color_continuous_scale="Blues"
            )
            fig_bar.update_layout(showlegend=False, height=420, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig_bar, use_container_width=True)

        with col2:
            st.subheader("Cuota de Demanda según Sector (Público vs Privado)")
            df_sector_g = df_filtered.groupby(col_sector)[col_matriculados].sum().reset_index()
            fig_pie = px.pie(
                df_sector_g, 
                values=col_matriculados, 
                names=col_sector, 
                hole=0.4,
                color_discrete_sequence=["#1f77b4", "#aec7e8", "#ff7f0e"]
            )
            fig_pie.update_layout(height=420, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig_pie, use_container_width=True)

        st.markdown("---")
        
        # Tabla Dinámica final de Auditoría de Frecuencias
        st.subheader("📋 Matriz de Control de Frecuencias Homologadas")
        df_table = df_filtered.groupby(['INSTITUCIÓN DE EDUCACIÓN SUPERIOR (IES)', col_sector])[col_matriculados].sum().reset_index()
        df_table = df_table.sort_values(by=col_matriculados, ascending=False).rename(
            columns={col_matriculados: "Total Alumnos Matriculados", col_sector: "Carácter Institucional"}
        )
        st.dataframe(df_table, use_container_width=True, hide_index=True, height=300)

except Exception as e:
    st.error(f"Se detectó una inconsistencia estructural al procesar el archivo: {e}")
    st.info("Asegúrate de que el archivo 'matriculados_bogota_2025.csv' se encuentre cerrado en Excel y ubicado en tu carpeta de Documentos.")

st.markdown("---")
st.caption("Ecosistema analítico avanzado desarrollado en Python. Datos validados del Sistema Nacional de Información de la Educación Superior (SNIES).")
