import streamlit as st
import pandas as pd
from vision import preprocess_image, rotate_image
from ai_engine import call_gemini
import os, time

st.set_page_config(page_title="Fichas to CSV", layout="wide")

# Inicialização de Estado
if 'queue' not in st.session_state:
    st.session_state.queue = []
if 'db' not in st.session_state:
    st.session_state.db = []

st.title("Fichas em JPG/JPEG/PNG para CSV")

with st.sidebar:
    st.header("Setup")
    env_key = os.getenv("GEMINI_API_KEY", "")
    api_key = st.text_input("Gemini API Key", value=env_key, type="password")
    
    st.divider()
    debug_mode = st.checkbox("🔍 Modo Debug de Imagem", help="Mostra os cortes antes de enviar para a IA")
    uploaded_files = st.file_uploader("Upload das Fichas", accept_multiple_files=True, type=['jpg', 'jpeg', 'png'])
    
    if st.button("Processar Imagens", use_container_width=True):
        if api_key and uploaded_files:
            total_files = len(uploaded_files)
            progress_bar = st.progress(0)
            status_text = st.empty()
            all_data = []
            for idx, f in enumerate(uploaded_files):
                status_text.info(f"Analisando arquivo {f.name}) ({idx+1}/{total_files}: {f.name})")
                

                image_bytes = preprocess_image(f)

                if image_bytes:
                    try:
                        data_list = call_gemini(image_bytes,api_key,bool(debug_mode))
                        
                        for item in data_list:
                            st.session_state.queue.append({
                                "img": image_bytes,
                                "data": item,
                                "filename": f.name
                            })
                        if debug_mode:
                            print(f"Arquivo processado. ({f.name})")

                    except Exception as e:
                        if debug_mode:
                            print(f"Erro no arquivo {f.name}: {e}")
                        st.error(f"Erro no arquivo {f.name}: {e}")

                progress_bar.progress((idx + 1) / total_files)

            status_text.success(f"Concluído! {len(st.session_state.queue)} itens para revisar.")
        else:
            st.error("Preencha a chave e suba os arquivos.")

# --- UI de REVISÃO ---
if st.session_state.queue:
    st.divider()
    st.subheader(f"Revisão Manual ({len(st.session_state.queue)} pendentes)")
    
    current_idx = 0
    current = st.session_state.queue[0]
    col1, col2 = st.columns([1.2, 1]) # Imagem um pouco maior
    
    with col1:
        c_rot1, c_rot2 = st.columns(2)
        if c_rot1.button("🔄 Girar 90° (Horário)", use_container_width=True):
            st.session_state.queue[current_idx]['img'] = rotate_image(current['img'], clockwise=True)
            st.rerun()
        
        if c_rot2.button("🔄 Girar 90° (Anti-horário)", use_container_width=True):
            st.session_state.queue[current_idx]['img'] = rotate_image(current['img'], clockwise=False)
            st.rerun()

        rotate_image(current['img'],)
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
    st.download_button("Baixar CSV", df.to_csv(index=False), "fichas.csv", "text/csv")