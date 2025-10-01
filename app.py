import streamlit as st
import pandas as pd
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
import matplotlib.pyplot as plt
import seaborn as sns

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Visualizador de Enlazado Interno",
    page_icon="🔗",
    layout="wide"
)

# --- 2. TÍTULO Y DESCRIPCIÓN ---
st.title('Visualizador de Enlazado Interno')
st.markdown("Sube tu archivo CSV para analizar la estructura de enlaces. La herramienta se adapta a un número variable de columnas de enlaces.")

# --- 3. FUNCIÓN DE PROCESAMIENTO (CORREGIDA) ---
def process_data(uploaded_file):
    """
    Lee y procesa el CSV con estructura de columnas intercaladas y variables.
    """
    df = pd.read_csv(uploaded_file)
    
    links_list = []
    
    # La primera columna siempre es la URL de origen
    source_col_name = df.columns[0]
    
    # Itera sobre cada fila del DataFrame
    for index, row in df.iterrows():
        source_url = row[source_col_name]
        
        # Itera sobre el resto de las columnas en pares (URL, Ancla)
        # Empieza en la columna 1 y avanza de 2 en 2
        for i in range(1, len(df.columns), 2):
            # Asegurarse de que hay un par completo (URL, Ancla)
            if i + 1 < len(df.columns):
                url_col_name = df.columns[i]
                anchor_col_name = df.columns[i+1]
                
                target_url = row[url_col_name]
                anchor_text = row[anchor_col_name]
                
                # Solo añade el enlace si la URL de destino existe
                if pd.notna(target_url) and str(target_url).strip() != '':
                    links_list.append({
                        'Source': source_url,
                        'Target': target_url,
                        'Anchor_Text': anchor_text
                    })
                    
    # Crea el DataFrame final a partir de la lista
    df_links = pd.DataFrame(links_list)
    
    # Limpieza de espacios en blanco
    df_links['Source'] = df_links['Source'].astype(str).str.strip()
    df_links['Target'] = df_links['Target'].astype(str).str.strip()
    
    return df_links

# --- 4. CARGADOR DE ARCHIVOS ---
uploaded_file = st.file_uploader("📂 Sube tu archivo CSV aquí", type="csv")

# --- 5. LÓGICA PRINCIPAL Y VISUALIZACIONES ---
if uploaded_file is not None:
    try:
        df_links = process_data(uploaded_file)

        if df_links.empty:
            st.warning("No se encontraron enlaces válidos en el archivo. Revisa que el formato sea el correcto.")
        else:
            st.success(f"¡Archivo procesado con éxito! Se encontraron **{len(df_links)}** enlaces internos.")

            tab1, tab2, tab3 = st.tabs(["🗺️ Mapa de Red Interactivo", "📊 Páginas más Enlazadas", "📋 Tabla de Datos"])

            # Pestaña 1: Mapa de Red
            with tab1:
                st.header('Mapa de Red de Enlaces Internos')
                st.markdown("Cada punto es una página. Las líneas son los enlaces. **Puedes hacer zoom, mover los nodos y pasar el cursor sobre ellos**.")

                G = nx.from_pandas_edgelist(df_links, 'Source', 'Target', create_using=nx.DiGraph())
                net = Network(height='750px', width='100%', bgcolor='#222222', font_color='white', notebook=True, directed=True)
                net.from_nx(G)

                in_degree = dict(G.in_degree)
                for node in net.nodes:
                    degree = in_degree.get(node['id'], 0)
                    node['size'] = 10 + degree * 3
                    node['title'] = f"{node['id']}<br>Enlaces entrantes: {degree}"

                net.save_graph('network_graph.html')
                with open('network_graph.html', 'r', encoding='utf-8') as f:
                    html_content = f.read()
                components.html(html_content, height=800, scrolling=True)

            # Pestaña 2: Gráfico de Barras
            with tab2:
                st.header("URL con más Páginas Enlazadas")
                link_counts = df_links['Target'].value_counts().nlargest(20)

                fig, ax = plt.subplots(figsize=(12, 10))
                sns.barplot(x=link_counts.values, y=link_counts.index, ax=ax, palette='viridis')
                ax.set_title('Top 20 Páginas con más Enlaces Entrantes', fontsize=16)
                ax.set_xlabel('Cantidad de Enlaces Entrantes', fontsize=12)
                ax.set_ylabel('URL de Destino', fontsize=12)
                st.pyplot(fig)

            # Pestaña 3: Tabla de datos
            with tab3:
                st.header("Todos los Enlaces Detectados")
                st.dataframe(df_links, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Ocurrió un error al procesar el archivo: {e}")
        st.warning("Asegúrate de que la primera columna sea 'Dirección' y las siguientes sean pares de 'URL_Destino_X' y 'Texto_Ancla_X'.")
