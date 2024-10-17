import streamlit as st
from utils.GoogleSheetManager import update_worksheet
import requests

url = st.secrets["url"]
def filter_by_category(df, category):
    """Filtra o DataFrame pela categoria selecionada."""
    if category != "Todas":
        return df[df['CATEGORY'] == category]
    return df

def filter_by_status(df, status):
    """Filtra o DataFrame pelo status selecionado (Ativo/Inativo)."""
    if status != "Todos":
        return df[df['STATUS'] == status]
    return df

def filter_by_edition(df, edition):
    """Filtra o DataFrame pela edição selecionada."""
    if edition != "Todas":
        return df[df['EDITION'] == edition]
    return df
def shorten_url_with_requests(url, timeout=10):
    api_url = f"http://tinyurl.com/api-create.php?url={url}"
    try:
        response = requests.get(api_url, timeout=timeout)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        return f"Erro ao encurtar a URL: {str(e)}"
    

def shorten_links_in_df(df, link_column="URL"):
    # Verifica se a coluna existe antes de aplicar
    if link_column in df.columns:
        df[link_column] = df[link_column].apply(lambda x: shorten_url_with_requests(x))
    return df[[link_column]]  # Retorna apenas a coluna que foi encurtada

def get_link(data):
    # Verifica se o DataFrame está vazio
    if data.empty:
        return data  # Retorna o DataFrame vazio sem alterações

    # Gerando a coluna de links baseada no 'ITEM_ID' e 'TITLE'
    data['URL'] = data.apply(
        lambda row: f"https://www.collectorsguardian.com.br/{row['ITEM_ID'][:3]}-{row['ITEM_ID'][3:]}-{row['TITLE'].replace(' ', '-').lower()}-_JM#item_id={row['ITEM_ID']}", 
        axis=1
    )

    # Selecionando apenas as colunas desejadas
    selected_columns = ['ITEM_ID', 'TITLE',"DESCRIPTION", 'MSHOPS_PRICE', 'URL']
    data = data[selected_columns]

    # Encurtando os links na coluna 'URL'
    shortened_data = shorten_links_in_df(data, link_column='URL')

    # Aqui estamos atribuindo a coluna 'URL' do DataFrame encurtado de volta ao data
    data['URL'] = shortened_data['URL']

    return data


def select_items(df, url):
    """Permite ao usuário selecionar itens a partir de um DataFrame."""
    df['item_display'] = df['ITEM_ID'].astype(str) + ' - ' + df['TITLE']
    item_options = df[['SKU', 'item_display']].set_index('SKU')['item_display'].to_dict()
    selected_display_names = st.multiselect("Pesquisa", options=list(item_options.values()), key=1)
    selected_skus = [key for key, value in item_options.items() if value in selected_display_names]
    selected_items_df = df[df['SKU'].isin(selected_skus)]

    selected_items_df = selected_items_df[['ITEM_ID', 'SKU', 'TITLE']]

    if not selected_items_df.empty:
        st.markdown("Dataframe dos itens selecionados:")
    # st.dataframe(selected_items_df[['ITEM_ID', 'SKU', 'TITLE']])
        st.data_editor(
            selected_items_df,
            column_config={
                "ITEM_LINK": st.column_config.LinkColumn("Links", display_text="Acessar anúncio"),
            },
        )

    update_worksheet(selected_items_df, "edit_table", 100, url)
        
    return selected_items_df

def apply_filters(df, df2):

    # st.markdown("Enviar Lista com itens selecionados:")
    # select_items(data, url=url)
    # st.divider()

    st.markdown("Filtros de Pesquisa:")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        

        all_categories = ['Todas'] + df2['CATEGORY'].unique().tolist()
        selected_category = st.selectbox("Escolha uma Categoria", all_categories)
        df_filtered = filter_by_category(df, selected_category)

    with col2:
        
        all_subcategories = ['Todas'] + df['SUBCATEGORY'].unique().tolist()
        selected_subcategory = st.selectbox("Escolha uma Subcategoria", all_subcategories)

        if selected_subcategory != 'Todas':
            df_filtered = df_filtered[df_filtered['SUBCATEGORY'] == selected_subcategory]


    with col3:
        all_editions = ['Todas'] + df['EDITION'].unique().tolist()
        selected_edition = st.selectbox("Escolha uma Edição", all_editions)

    with col4:
        all_status = ['Todos', 'Ativo', 'Inativo']
        selected_status = st.selectbox("Escolha o Status", all_status)
        df_filtered = filter_by_status(df_filtered, selected_status)
       


    df_filtered = filter_by_edition(df_filtered, selected_edition)



    return df_filtered
