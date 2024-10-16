import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection



def get_categories_ID(data, categorias_df):

    categorias_df['ID'] = categorias_df['ID'].apply(lambda x: f'{int(x):03d}') 
    # Converter a tabela de categorias em um dicionário
    categorias_dict = categorias_df.set_index('CATEGORY')['ID'].to_dict()

    # Verificar se a coluna 'CATEGORY' existe nos anúncios e fazer o mapeamento
    if 'CATEGORY' in data.columns:
        data['CATEGORY_ID'] = data['CATEGORY'].map(categorias_dict)

    return data

def update_product_skus(df):
    current_year_month = datetime.now().strftime("%y%m")

    # Preparando para rastrear informações adicionais sobre novos SKUs
    existing_skus_list = []
    new_skus_list = []
    new_skus_details = []  # Lista para armazenar detalhes para novos SKUs incluindo ITEM_ID e TITLE

    # Certifique-se de que CATEGORY_id tenha 3 dígitos
    df['CATEGORY_ID'] = df['CATEGORY_ID'].str.zfill(3)

    for category_id in df['CATEGORY_ID'].unique():
        category_mask = df['CATEGORY_ID'] == category_id

        existing_skus = df.loc[category_mask & df['SKU'].notna(), 'SKU']
        existing_skus_list.extend(existing_skus)

        year_month = current_year_month

        # Extrai contadores e valida
        counters = existing_skus.str.extract(f"^{category_id}-\d{{4}}-(\d{{4}})$")[0]
        valid_counters = pd.to_numeric(counters, errors='coerce').dropna().astype(int)
        
        next_counter = valid_counters.max() + 1 if not valid_counters.empty else 1

        null_skus_indices = df.index[category_mask & df['SKU'].isna()]
        for idx in null_skus_indices:
            new_sku = f"{category_id}-{year_month}-{next_counter:04d}"
            df.at[idx, 'SKU'] = new_sku
            new_skus_list.append(new_sku)
            new_skus_details.append({
                'TITLE': df.at[idx, 'TITLE'],
                'SKU': new_sku,
                'ITEM_ID': df.at[idx, 'ITEM_ID'],
            })
            next_counter += 1


        # Converte a lista de dicionários em DataFrame
        new_skus_df = pd.DataFrame(new_skus_details)  # Agora inclui ITEM_ID e TITLE

    return df, new_skus_df

def format_prices(data):
    if 'MSHOPS_PRICE' in data.columns:
        data['MSHOPS_PRICE'] = pd.to_numeric(data['MSHOPS_PRICE'], errors='coerce')
        data['MSHOPS_PRICE'] = data['MSHOPS_PRICE'].apply(lambda x: f"R$ {x:,.2f}" if pd.notnull(x) else 'R$ 0.00')
    # Formatação de MARKETPLACE_PRICE
    if 'MARKETPLACE_PRICE' in data.columns:
        data['MARKETPLACE_PRICE'] = pd.to_numeric(data['MARKETPLACE_PRICE'], errors='coerce')
        data['MARKETPLACE_PRICE'] = data['MARKETPLACE_PRICE'].apply(lambda x: f"R$ {x:,.2f}" if pd.notnull(x) else 'R$ 0.00')
    return data

def format_data(data):
    # Transformações de tipo
    data['is_COMPLETE'] = data['is_COMPLETE'].astype(bool)
    data['SERIAL'] = data['SERIAL'].astype(bool)
    data['QUANTITY'] = data['QUANTITY'].fillna(0).astype(int)

    # Criação da coluna de links clicáveis
    data['ITEM_LINK'] = data['ITEM_ID'].apply(lambda x: f"https://produto.mercadolivre.com.br/MLB-{x[3:]}" if pd.notnull(x) else "")

    # Formatação de MSHOPS_PRICE
    format_prices(data)

    # Ordenação das colunas
    var_order = ['ITEM_ID', 'SKU', 'TITLE', 'DESCRIPTION', 'MSHOPS_PRICE', 'MARKETPLACE_PRICE', 'ITEM_LINK', 'CATEGORY', 'STATUS','CONDITION' ,'QUANTITY', 'is_COMPLETE', 'SERIAL']
    data = data.reindex(columns=var_order)

    # Remoção de duplicatas
    data = data.drop_duplicates(subset='ITEM_ID', keep='first')

    return data

def compare_dataframes(df1, df2):
    """
    Compara dois DataFrames e retorna as diferenças, incluindo:
    - Itens adicionados
    - Mudanças de preço (MSHOPS_PRICE e MARKETPLACE_PRICE)
    - Alterações de quantidade (QUANTITY)
    """
    
    df1['QUANTITY'] = df1['QUANTITY'].fillna(0).astype(int)
    df1['QUANTITY'] = df2['QUANTITY'].fillna(0).astype(int)

    # Itens adicionados: presentes na tabela 1 (df1), mas não na tabela 2 (df2)
    items_added = df1[~df1['ITEM_ID'].isin(df2['ITEM_ID'])]
    
    # Itens comuns: presentes em ambas as tabelas, para comparação de preços e quantidade
    common_items = pd.merge(df1, df2, on='ITEM_ID', suffixes=('_new', '_old'))
    
    # Mudanças de preço: verifica se os preços (MSHOPS_PRICE e MARKETPLACE_PRICE) mudaram
    price_changes = common_items[
        (common_items['MSHOPS_PRICE_new'] != common_items['MSHOPS_PRICE_old']) | 
        (common_items['MARKETPLACE_PRICE_new'] != common_items['MARKETPLACE_PRICE_old'])
    ]

    # Alterações de quantidade: verifica se a quantidade mudou
    quantity_changes = common_items[common_items['QUANTITY_new'] != common_items['QUANTITY_old']]
    
    return items_added, price_changes, quantity_changes



class DataProcessor:
    def __init__(self, df):
        """Inicializa a classe com um DataFrame."""
        self.data = df

    def clean_data(self):
        """Remove linhas com valores ausentes e redefine os índices."""
        self.data.drop_duplicates(subset='ITEM_ID', keep='first')
        self.data.drop_duplicates(subset='SKU', keep='first')
        self.data[['ITEM_ID','SKU','CONDITION', 'is_COMPLETE', 'SERIAL']]
        # self.data.reset_index(drop=True, inplace=True)
        return self.data


    def convert_id_format(self, column_name):
        """Converte valores da coluna especificada para um formato de ID com três dígitos."""
        if column_name in self.data.columns:
            self.data[column_name] = self.data[column_name].apply(lambda x: f'{int(x):03d}')
        else:
            raise ValueError(f"A coluna '{column_name}' não existe no DataFrame.")
        return self.data

    def get_summary(self):
        """Retorna um resumo estatístico do DataFrame."""
        return self.data.describe()

    def filter_data(self, condition):
        """Filtra os dados de acordo com uma condição booleana."""
        filtered_data = self.data[condition]
        return filtered_data.reset_index(drop=True)

