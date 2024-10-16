import streamlit as st

def select_items(df):
    """Permite ao usuário selecionar itens a partir de um DataFrame."""
    df['item_display'] = df['ITEM_ID'].astype(str) + ' - ' + df['TITLE']
    item_options = df[['SKU', 'item_display']].set_index('SKU')['item_display'].to_dict()
    selected_display_names = st.multiselect("Pesquisa", options=list(item_options.values()), key=1)
    selected_skus = [key for key, value in item_options.items() if value in selected_display_names]
    selected_items_df = df[df['SKU'].isin(selected_skus)]

    if not selected_items_df.empty:
        st.write("Dataframe dos itens selecionados:")
    # st.dataframe(selected_items_df[['ITEM_ID', 'SKU', 'TITLE']])
        st.dataframe(
            selected_items_df,
            column_config={
                "ITEM_LINK": st.column_config.LinkColumn("Links", display_text="Acessar anúncio"),
            },
        )
        
    return selected_items_df