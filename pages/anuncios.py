
import numpy as np
import streamlit as st
from utils.GoogleSheetManager import GoogleSheetManager, update_worksheet
from utils.DataProcessor import get_categories_ID, update_product_skus, format_prices
from utils.AplyFilters import apply_filters, shorten_links_in_df, get_link
import pandas as pd
from utils.Classifications import classify_items, keywords, classify_editions, edicoes_keywords
import re
import requests
from streamlit_gsheets import GSheetsConnection
from utils.Selectors import select_items
conn = st.connection("gsheets", type=GSheetsConnection)
# Inicializando o gerenciador de planilhas
gs_manager = GoogleSheetManager()
# locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')  
# Permitindo que o usuário insira a URL

url = st.secrets["product_url"]

if url:
    # Adicionando URLs ao gerenciador
    gs_manager.set_url(url)
    # Adicionando worksheets
    gs_manager.add_worksheet(url, "ANUNCIOS")
    gs_manager.add_worksheet(url, "CATEGORIAS")
    gs_manager.add_worksheet(url, "edit_table")
    # # Lendo dados das worksheets
    products = gs_manager.read_sheet(url, "ANUNCIOS")
    categorias = gs_manager.read_sheet(url, "CATEGORIAS")
    edit = gs_manager.read_sheet(url, "edit_table")
    data = products.copy()
    # # Inserindo IDs de categorias nos produtos
    data = get_categories_ID(products, categorias)
    # # Convertendo as colunas para os tipos apropriados
 
    data =  classify_items(data, keywords)
    data = classify_editions(data, edicoes_keywords)
    data['SKU'] = data['SKU'].where(~data['SKU'].duplicated(), np.nan)
    data['STATUS'] = data['STATUS'].str.strip()  # Remove espaços em branco no início e no fim
    data = data.drop_duplicates(subset='ITEM_ID', keep='first')
    # data , updated = update_product_skus(data)
    # st.dataframe(data)
    # st.dataframe(updated)
    data['SKU'] = data['SKU'].where(~data['SKU'].duplicated(), np.nan)
    # Formatação de preços
    # Filtros por quantidade
    min_quantity = st.sidebar.number_input("Quantidade mínima", min_value=0, value=0, step=1)
    max_quantity = 100

    # Filtros por intervalo de preços
    # min_price, max_price = st.sidebar.slider(
    #     "Intervalo de preços",
    #     min_value=0,
    #     max_value=int(data['MSHOPS_PRICE'].max()) + 1,  # Define o valor máximo um acima do maior preço
    #     value=(0, int(data['MSHOPS_PRICE'].max())),  # Define o intervalo padrão
    #     step=1
    # )
    
    #         # Formatando os preços para R$
    # formatted_min_price = locale.currency(min_price, grouping=True)
    # formatted_max_price = locale.currency(max_price, grouping=True)

    # st.sidebar.write(f"Preço mínimo: {formatted_min_price}")
    # st.sidebar.write(f"Preço máximo: {formatted_max_price}")

    # Aplicando filtros personalizados
    
   

    filtered = apply_filters(data, categorias)

    
    # filtered = format_data(filtered)
    # Aplicando filtro de quantidade
    filtered = filtered[(data['QUANTITY'] >= min_quantity) & (filtered['QUANTITY'] <= max_quantity)]
    # Aplicando filtro de preço
    # filtered = filtered[(filtered['MSHOPS_PRICE'] >= min_price) & (filtered['MSHOPS_PRICE'] <= max_price)]
    
    pt_df =filtered.copy()
    

    novos_nomes = {
    'ITEM_ID': 'ID_DO_ITEM',
    'SKU': 'CÓDIGO',
    'TITLE': 'TÍTULO',
    'DESCRIPTION': 'DESCRIÇÃO',
    'MSHOPS_PRICE': 'PREÇO_MSHOPS',
    'MARKETPLACE_PRICE': 'PREÇO_MARKETPLACE',
    'CATEGORY': 'CATEGORIA',
    'STATUS': 'STATUS',
    'QUANTITY': 'QUANTIDADE'
}

# Renomeando as colunas

    pt_df.rename(columns=novos_nomes, inplace=True)

    # else:
    # st.subheader("TABELA DE ITENS FILTRADOS")

    # State to toggle between dataframe and edit mode
    # State to toggle between dataframe and edit mode
    # if 'edit_mode' not in st.session_state:
    #     st.session_state['edit_mode'] = False
    
    # # Button to switch modes
    # if st.sidebar.button("Toggle Edit Mode"):
    #     st.session_state['edit_mode'] = not st.session_state['edit_mode']

    # # Display dataframe or editable data based on the button's state
    # if st.session_state['edit_mode']:
    #     df = st.data_editor(data, num_rows="dynamic")
      
        
    #     if st.sidebar.button("Update Worksheet"):
    #         conn.update(spreadsheet=url, worksheet="products", data=df)
    #         st.success("Worksheet Updated 🤓")
            

    # Exibindo a tabela filtrada com coluna de links
    st.dataframe(
        pt_df,
        column_config={
            "ITEM_LINK": st.column_config.LinkColumn("Links", display_text="Acessar anúncio"),
        }
    )

st.markdown("Criar lista de Produtos:")
select=  select_items(filtered)

st.divider()
# update_worksheet(select, "edit_table", 7, url)

with st.expander('Contagens totais (não otimizado)'):
    total = data['QUANTITY'].sum().astype(int)
    st.write(f"Total de itens: {total}")
    col1, col2, col3,col4 = st.columns(4)

    with col1:
        # Verifique se a coluna 'CATEGORY' existe e não contém valores nulos
        if 'CATEGORY' in data.columns:
            st.write("Categorias (não filtrado):")
            cat_counts = data['CATEGORY'].dropna().value_counts()  # Remova nulos
            st.table(cat_counts)
        else:
            st.error("Coluna 'CATEGORY' não encontrada no DataFrame!")

    with col2:
        # Verifique se a coluna 'SUBCATEGORY' existe no DataFrame filtrado
        if 'SUBCATEGORY' in filtered.columns:
            st.write("Subcategorias (filtrado):")
            cat_counts = filtered['SUBCATEGORY'].dropna().value_counts()  # Remova nulos
            st.table(cat_counts)
        else:
            st.error("Coluna 'SUBCATEGORY' não encontrada no DataFrame filtrado!")
        if 'EDITION' in filtered.columns:
            st.write("Edições (filtrado):")
            cat_counts = filtered['EDITION'].dropna().value_counts()  # Remova nulos
            st.table(cat_counts)
        else:
            st.error("Coluna 'EDITION' não encontrada no DataFrame filtrado!")
    with col3:
        if 'STATUS' in filtered.columns:
            st.write("Status (filtrado):")
            cat_counts = filtered['STATUS'].dropna().value_counts()  # Remova nulos
            st.table(cat_counts)
        else:
            st.error("Coluna 'STATUS' não encontrada no DataFrame filtrado!")

    with col4:
        
        in_stock = data[data['QUANTITY'] >= 1]
  
    st.dataframe(in_stock)

