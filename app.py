import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta
import os
import json
from PIL import Image

# --------------------------
# CONFIGURAÇÃO DA PÁGINA
# --------------------------
st.set_page_config(page_title="Sistema de Ponto", layout="wide", page_icon="⏱")

FILE_DB = "registro_atividades.csv"
FILE_USERS = "usuarios.json"

# --------------------------
# FUNÇÕES DE BANCO DE DADOS
# --------------------------
def init_db():
    if not os.path.exists(FILE_DB):
        # ADICIONADO: Coluna 'hora_inicio'
        df = pd.DataFrame(columns=["usuario", "atividade", "hora_inicio", "hora_fim", "duracao_formatada", "segundos_totais", "data"])
        df.to_csv(FILE_DB, index=False)

def carregar_usuarios():
    if not os.path.exists(FILE_USERS):
        return {}
    with open(FILE_USERS, "r", encoding="utf-8") as f:
        return json.load(f)

# ALTERADO: Agora recebe o 'inicio_float' para calcular o horário exato
def salvar_atividade(usuario, atividade, segundos, inicio_float):
    df = pd.read_csv(FILE_DB)
    
    # Converte o timestamp (ex: 17092323.22) para hora legível (ex: "14:30:05")
    hora_inicio_str = datetime.fromtimestamp(inicio_float).strftime("%H:%M:%S")
    hora_fim_str = datetime.now().strftime("%H:%M:%S")
    
    nova_linha = {
        "usuario": usuario,
        "atividade": atividade,
        "hora_inicio": hora_inicio_str,  # Nova informação
        "hora_fim": hora_fim_str,
        "duracao_formatada": str(timedelta(seconds=int(segundos))),
        "segundos_totais": segundos,
        "data": datetime.now().strftime("%Y-%m-%d")
    }
    
    df_novo = pd.DataFrame([nova_linha])
    df = pd.concat([df, df_novo], ignore_index=True)
    df.to_csv(FILE_DB, index=False)

def formatar_tempo(seg):
    return str(timedelta(seconds=int(seg)))

# --------------------------
# ESTADO DA SESSÃO
# --------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "usuario_info" not in st.session_state:
    st.session_state.usuario_info = {}
if "timer_status" not in st.session_state:
    st.session_state.timer_status = "parado"
if "inicio_tempo" not in st.session_state:
    st.session_state.inicio_tempo = None
if "tempo_acumulado" not in st.session_state:
    st.session_state.tempo_acumulado = 0

init_db()

# --------------------------
# TELA DE LOGIN
# --------------------------
def login_screen():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 style='text-align: center;'>🔐 Acesso ao Sistema</h1>", unsafe_allow_html=True)
        st.markdown("---")
        user = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar", use_container_width=True):
            usuarios_db = carregar_usuarios()
            if user in usuarios_db and usuarios_db[user]["senha"] == senha:
                st.session_state.logged_in = True
                st.session_state.usuario_info = usuarios_db[user]
                st.session_state.usuario_info["user_id"] = user
                st.success(f"Bem-vindo, {usuarios_db[user]['nome']}!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")

# --------------------------
# BARRA LATERAL (PERFIL)
# --------------------------
def show_sidebar():
    with st.sidebar:
        info = st.session_state.usuario_info
        if "foto" in info and os.path.exists(info["foto"]):
            st.image(Image.open(info["foto"]), width=150)
        else:
            st.markdown("# 👤")
        st.markdown(f"### {info.get('nome', 'Usuário')}")
        st.caption(f"Cargo: {info.get('cargo', 'N/A').upper()}")
        st.divider()
        if st.button("Sair", type="primary"):
            st.session_state.logged_in = False
            st.session_state.usuario_info = {}
            st.session_state.timer_status = "parado"
            st.rerun()

# --------------------------
# TELA DO FUNCIONÁRIO
# --------------------------
def funcionario_screen():
    show_sidebar()
    st.title("⏱ Controle de Atividades")
    
    status_color = "#e8f5e9" if st.session_state.timer_status == "rodando" else "#f5f5f5"
    with st.container():
        st.markdown(f"""
        <div style="background-color: {status_color}; color: black; padding: 20px; border-radius: 10px; border: 1px solid #ddd;">
            <h3 style="margin:0;">Status Atual: {st.session_state.timer_status.upper()}</h3>
        </div>
        """, unsafe_allow_html=True)
    st.write("")

    col_input, col_timer = st.columns([1.5, 1])
    with col_input:
        st.subheader("Nova Tarefa")
        atividade = st.text_input("O que você vai fazer?", key="input_atividade", placeholder="Ex: Relatório Mensal...")
        
        col_b1, col_b2, col_b3 = st.columns(3)
        with col_b1:
            if st.button("▶ INICIAR", use_container_width=True):
                if not atividade:
                    st.warning("Digite o nome da atividade!")
                else:
                    st.session_state.timer_status = "rodando"
                    if st.session_state.inicio_tempo is None:
                        st.session_state.inicio_tempo = time.time()
                    st.rerun()

        with col_b2:
            if st.button("⏸ PAUSAR", use_container_width=True):
                if st.session_state.timer_status == "rodando":
                    st.session_state.tempo_acumulado += time.time() - st.session_state.inicio_tempo
                    st.session_state.timer_status = "pausado"
                    st.rerun()

        with col_b3:
            if st.button("✅ FINALIZAR", use_container_width=True, type="primary"):
                if st.session_state.timer_status != "parado":
                    total = st.session_state.tempo_acumulado
                    if st.session_state.timer_status == "rodando":
                        total += time.time() - st.session_state.inicio_tempo
                    
                    user_id = st.session_state.usuario_info["user_id"]
                    
                    # ALTERADO: Passamos o st.session_state.inicio_tempo original
                    # Se houve pausas, o inicio real é mantido, mas o tempo "corrido" desconta as pausas
                    # Se quiser o inicio REAL (primeiro clique):
                    tempo_inicio_real = st.session_state.inicio_tempo 
                    if tempo_inicio_real is None: 
                        tempo_inicio_real = time.time() # fallback

                    salvar_atividade(user_id, atividade, total, tempo_inicio_real)
                    
                    st.session_state.timer_status = "parado"
                    st.session_state.tempo_acumulado = 0
                    st.session_state.inicio_tempo = None
                    st.success("Salvo!")
                    time.sleep(1)
                    st.rerun()

    with col_timer:
        placeholder = st.empty()
        if st.session_state.timer_status == "rodando":
            while st.session_state.timer_status == "rodando":
                agora = time.time()
                decorrido = st.session_state.tempo_acumulado + (agora - st.session_state.inicio_tempo)
                placeholder.markdown(f"<div style='text-align:center; font-size:4rem; font-weight:bold; color:#2e7d32'>{formatar_tempo(decorrido)}</div>", unsafe_allow_html=True)
                time.sleep(1)
        elif st.session_state.timer_status == "pausado":
             placeholder.markdown(f"<div style='text-align:center; font-size:4rem; font-weight:bold; color:#f9a825'>{formatar_tempo(st.session_state.tempo_acumulado)}</div>", unsafe_allow_html=True)
        else:
             placeholder.markdown(f"<div style='text-align:center; font-size:4rem; font-weight:bold; color:#bdbdbd'>00:00:00</div>", unsafe_allow_html=True)

    st.divider()
    st.subheader("🗓 Histórico de Hoje")
    df = pd.read_csv(FILE_DB)
    hoje = datetime.now().strftime("%Y-%m-%d")
    user_id = st.session_state.usuario_info["user_id"]
    df_user = df[(df["usuario"] == user_id) & (df["data"] == hoje)]
    
    if not df_user.empty:
        colunas_display = {
            "atividade": "Atividade",
            "hora_inicio": "Início",
            "hora_fim": "Fim",
            "duracao_formatada": "Duração"
        }
        df_exibir = df_user[list(colunas_display.keys())].rename(columns=colunas_display)
        # ALTERADO: Mostra Início e Fim na tabela
        st.dataframe(df_exibir, use_container_width=True, hide_index=True)
    else:
        st.info("Nada registrado hoje.")

# --------------------------
# TELA DO CHEFE
# --------------------------
def chefe_screen():
    show_sidebar()
    st.title("📊 Painel de Gestão")
    
    df = pd.read_csv(FILE_DB)
    if df.empty:
        st.warning("Sem dados.")
        return

    col1, col2 = st.columns(2)
    with col1:
        datas = df["data"].unique()
        data_sel = st.selectbox("Data", sorted(datas, reverse=True))
    with col2:
        usuarios_db = carregar_usuarios()
        ids_unicos = df["usuario"].unique()
        opcoes_nomes = ["Todos"] + [f"{usuarios_db.get(uid, {}).get('nome', uid)} ({uid})" for uid in ids_unicos]
        user_sel_fmt = st.selectbox("Funcionário", opcoes_nomes)

    df_filtered = df[df["data"] == data_sel]
    if user_sel_fmt != "Todos":
        user_id_sel = user_sel_fmt.split("(")[-1].replace(")", "")
        df_filtered = df_filtered[df_filtered["usuario"] == user_id_sel]

    total = df_filtered["segundos_totais"].sum()
    st.metric("Total de Horas", formatar_tempo(total))
    
    st.bar_chart(df_filtered.groupby("atividade")["segundos_totais"].sum())
    
    st.subheader("Detalhamento")
    # ALTERADO: Reorganizei as colunas para ficar lógico
    colunas_visiveis = ["usuario", "atividade", "hora_inicio", "hora_fim", "duracao_formatada"]
    st.dataframe(df_filtered[colunas_visiveis], use_container_width=True)

# --------------------------
# FLUXO PRINCIPAL
# --------------------------
if not st.session_state.logged_in:
    login_screen()
else:
    if st.session_state.usuario_info["cargo"] == "chefe":
        chefe_screen()
    else:
        funcionario_screen()