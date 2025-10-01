import streamlit as st
import pandas as pd
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
import matplotlib.pyplot as plt
import seaborn as sns
import io

# --- Configuración de la Página ---
st.set_page_config(
    page_title="Visualizador de Enlazado Interno",
    page_icon="🔗",
    layout="wide"
)

# --- Título y Descripción ---
st.title('🔗 Visualizador de Enlazado Interno')
st.markdown("""
Sube un archivo CSV para analizar la estructura de enlaces internos de tu sitio web.
La herramienta generará:
- Un **mapa de red interactivo** para explorar las conexiones.
- Un **gráfico con las páginas más enlazadas**.
- Una **tabla de datos** con todos los enlaces detectados.
""")

# --- Función para Procesar los Datos ---
def process_data(uploaded_file):
    """Lee y procesa el archivo CSV para extraer las relaciones de enlazado."""
    df = pd.read_csv(uploaded_file)
    
    # Columnas de URLs y textos ancla
    url_cols = [col for col in df.columns if 'URL_Destino_Contenido' in col]
    texto_cols = [col for col in df.columns if 'Texto_Ancla_Contenido' in col]

    # Transformar de formato ancho a largo
    melted_urls = df.melt(id_vars='Dirección', value_vars=url_cols, var_name='url_col_name', value_name='URL_Destino')
    melted_textos = df.melt(id_vars='Dirección', value_vars=texto_cols, var_name='texto_col_name', value_name='Texto_Ancla')

    # Extraer número de columna para alinear URLs y textos ancla
    melted_urls['link_num'] = melted_urls['url_col_name'].str.extract('(\\d+)').fillna(0).astype(int)
    melted_textos['link_num'] = melted_textos['texto_col_name'].str.extract('(\\d+)').fillna(0).astype(int)

    # Unir dataframes
    df_long = pd.merge(melted_urls, melted_textos, on=['Dirección', 'link_num'])

    # Limpieza final
    df_long = df_long[['Dirección', 'URL_Destino', 'Texto_Ancla']].copy()
    df_long.dropna(subset=['URL_Destino'], inplace=True)
    df_long.rename(columns={'Dirección': 'Source', 'URL_Destino': 'Target', 'Texto_Ancla': 'Anchor_Text'}, inplace=True)
    
    # Eliminar espacios en blanco
    df_long['Source'] = df_long['Source'].str.strip()
    df_long['Target'] = df_long['Target'].str.strip()

    return df_long

# --- Carga del Archivo ---
uploaded_file = st.file_uploader("📂 Sube tu archivo CSV aquí", type="csv")

if uploaded_file is not None:
    try:
        df_links = process_data(uploaded_file)

        st.success(f"¡Archivo procesado con éxito! Se encontraron {len(df_links)} enlaces.")

        # --- Visualizaciones en Pestañas ---
        tab1, tab2, tab3 = st.tabs(["🗺️ Mapa de Red Interactivo", "📊 Páginas más Enlazadas", "📋 Tabla de Datos"])

        # --- Pestaña 1: Mapa de Red ---
        with tab1:
            st.header('Mapa de Red de Enlaces Internos')
            st.markdown("Cada punto (nodo) es una página. Las líneas representan los enlaces. Puedes hacer zoom y arrastrar los nodos.")

            # Crear el grafo
            G = nx.from_pandas_edgelist(df_links, 'Source', 'Target')

            # Asignar tamaño a los nodos basado en la cantidad de enlaces entrantes
            in_degree = dict(G.in_degree)
            node_sizes = [v * 10 + 10 for v in in_degree.values()] # Ajusta el multiplicador para el tamaño

            # Crear el grafo con Pyvis
            net = Network(height='750px', width='100%', bgcolor='#222222', font_color='white', notebook=True, directed=True)
            net.from_nx(G)

            # Personalizar nodos
            for node, in_degree_val in in_degree.items():
                net.get_node(node)['size'] = in_degree_val * 5 + 10 # Nodos más grandes reciben más enlaces
                net.get_node(node)['title'] = f"{node}<br>Enlaces entrantes: {in_degree_val}" # Tooltip con info

            net.set_options("""
            var options = {
              "nodes": {
                "font": {
                  "size": 12,
                  "strokeWidth": 2
                }
              },
              "edges": {
                "color": {
                  "inherit": true
                },
                "smooth": {
                  "type": "continuous"
                }
              },
              "physics": {
                "barnesHut": {
                  "gravitationalConstant": -30000,
                  "centralGravity": 0.3,
                  "springLength": 150
                },
                "minVelocity": 0.75
              }
            }
            """)
            
            # Guardar y mostrar el grafo
            net.save_graph('network_graph.html')
            with open('network_graph.html', 'r', encoding='utf-8') as f:
                html_content = f.read()
            components.html(html_content, height=800)


        # --- Pestaña 2: Gráfico de Barras ---
        with tab2:
            st.header("Páginas que Reciben Más Enlaces Internos")
            
            # Calcular el recuento de enlaces
            link_counts = df_links['Target'].value_counts().nlargest(20)

            # Crear el buffer de la imagen
            buf = io.BytesIO()
            
            # Crear el gráfico
            fig, ax = plt.subplots(figsize=(12, 10))
            sns.barplot(x=link_counts.values, y=link_counts.index, ax=ax, palette='viridis')
            ax.set_title('Top 20 Páginas con más Enlaces Entrantes', fontsize=16)
            ax.set_xlabel('Cantidad de Enlaces Entrantes', fontsize=12)
            ax.set_ylabel('URL de Destino', fontsize=12)
            plt.tight_layout()
            
            # Guardar figura en el buffer y mostrarla
            plt.savefig(buf, format="png")
            st.image(buf)


        # --- Pestaña 3: Tabla de Datos ---
        with tab3:
            st.header("Todos los Enlaces Detectados")
            st.dataframe(df_links, use_container_width=True)

    except Exception as e:
        st.error(f"Ocurrió un error al procesar el archivo: {e}")
        st.warning("Por favor, asegúrate de que el archivo CSV tiene la estructura correcta con las columnas 'Dirección', 'URL_Destino_Contenido' y 'Texto_Ancla_Contenido'.")