import streamlit as st
import pandas as pd
from vision import segment_rows
from ai_engine import call_gemini
import os, time

st.set_page_config(page_title="Fichas to CSV", layout="wide")

# Inicialização de Estado
if 'queue' not in st.session_state:
    st.session_state.queue = []
if 'db' not in st.session_state:
    st.session_state.db = []

st.title("🖋️ Fichas em JPG para CSV")

with st.sidebar:
    st.header("Setup")
    env_key = os.getenv("GEMINI_API_KEY", "")
    api_key = st.text_input("Gemini API Key", value=env_key, type="password")
    
    st.divider()
    debug_mode = st.checkbox("🔍 Modo Debug de Imagem", help="Mostra os cortes antes de enviar para a IA")
    uploaded_files = st.file_uploader("Upload das Fichas", accept_multiple_files=True, type=['jpg', 'jpeg', 'png'])
    
    if st.button("🚀 Processar Imagens", use_container_width=True):
        if api_key and uploaded_files:
            total_files = len(uploaded_files)
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for idx, f in enumerate(uploaded_files):
                # Progresso Geral
                progress_bar.progress((idx) / total_files)
                status_text.info(f"📂 Analisando arquivo {idx+1}/{total_files}: {f.name}")
                
                # Processamento de Imagem
                file_bytes = f.read()
                crops = segment_rows(file_bytes)
                
                if debug_mode:
                    with st.expander(f"Visualizando cortes: {f.name}", expanded=True):
                        cols = st.columns(3)
                        for i, c in enumerate(crops[:6]): # Mostra até 6 para não poluir
                            cols[i % 3].image(c, caption=f"Linha {i+1}")

                # Processamento de IA
                for j, crop in enumerate(crops):
                    status_text.info(f"Interpretando linha {j+1}/{len(crops)}...")
                    data = call_gemini(crop, api_key)
                    st.session_state.queue.append({"img": crop, "data": data})
                    
                    # Sênior: Delay de 1s entre chamadas para respeitar a API Gratuita
                    time.sleep(1)
            
            progress_bar.progress(1.0)
            status_text.success(f"✅ Concluído! {len(st.session_state.queue)} linhas na fila.")
        else:
            st.error("Preencha a chave e suba os arquivos.")

# --- UI de REVISÃO ---
if st.session_state.queue:
    st.divider()
    st.subheader(f"📝 Revisão Manual ({len(st.session_state.queue)} pendentes)")
    
    current = st.session_state.queue[0]
    col1, col2 = st.columns([1.2, 1]) # Imagem um pouco maior
    
    with col1:
        st.image(current['img'], width=None, use_container_width=True)
    
    with col2:
        with st.form("edit_form", clear_on_submit=True):
            d = current['data']
            # Inputs com valores sugeridos pela IA
            f_nome = st.text_input("NOME", d.get('NOME', ''))
            f_tel = st.text_input("TELEFONE", d.get('TELEFONE', ''))
            f_cid = st.text_input("CIDADE", d.get('CIDADE', ''))
            f_bairro = st.text_input("BAIRRO", d.get('BAIRRO', ''))
            f_orgao = st.text_input("ORGAO", d.get('ORGAO', ''))
            
            c1, c2 = st.columns(2)
            if c1.form_submit_button("✅ Aprovar"):
                st.session_state.db.append({
                    "NOME": f_nome, "TELEFONE": f_tel, "CIDADE": f_cid, "BAIRRO": f_bairro, "ORGAO": f_orgao
                })
                st.session_state.queue.pop(0)
                st.rerun()
            if c2.form_submit_button("🗑️ Descartar"):
                st.session_state.queue.pop(0)
                st.rerun()

# --- EXPORTAÇÃO ---
if st.session_state.db:
    st.divider()
    df = pd.DataFrame(st.session_state.db)
    st.write("### Dados Acumulados")
    st.dataframe(df, use_container_width=True)
    st.download_button("📥 Baixar CSV", df.to_csv(index=False), "fichas.csv", "text/csv")