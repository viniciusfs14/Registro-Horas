import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta
import os
import json
from PIL import Image

# --------------------------
# 1. AUTOCONFIGURAÇÃO DO TEMA
# --------------------------
def criar_tema_radix():
    dir_streamlit = ".streamlit"
    arquivo_config = os.path.join(dir_streamlit, "config.toml")
    
    if not os.path.exists(arquivo_config):
        if not os.path.exists(dir_streamlit):
            os.makedirs(dir_streamlit)
        conteudo_tema = """
[theme]
base = "light"
primaryColor = "#6A1B9A"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F3E5F5"
textColor = "#333333"
font = "sans serif"
        """
        with open(arquivo_config, "w") as f:
            f.write(conteudo_tema.strip())
        st.warning("⚠️ Tema configurado! PARE a execução (Ctrl+C) e rode novamente para aplicar.")
        st.stop()

criar_tema_radix()

# --------------------------
# CONFIGURAÇÃO DA PÁGINA
# --------------------------
st.set_page_config(page_title="Sistema de Ponto Radix", layout="wide", page_icon="⏱")

FILE_DB = "registro_atividades.csv"
FILE_USERS = "usuarios.json"

# --------------------------
# ESTILO VISUAL (CSS)
# --------------------------
def configurar_estilo():
    COR_ROXO_FORTE = "#6A1B9A"
    COR_VERDE_ACAO = "#43A047"
    
    st.markdown(f"""
    <style>
    div.stButton > button[kind="primary"] {{
        background-color: {COR_ROXO_FORTE};
        color: white;
        border: none;
        border-radius: 8px;
    }}
    div.stButton > button[kind="primary"]:hover {{
        background-color: #4A148C;
    }}
    div.stButton > button[kind="secondary"] {{
        background-color: {COR_VERDE_ACAO};
        color: white;
        border: none;
        border-radius: 8px;
    }}
    div.stButton > button[kind="secondary"]:hover {{
        background-color: #2E7D32;
        color: white;
    }}
    .stTextInput > div > div > input {{
        background-color: #FAFAFA;
        color: #333;
        border: 1px solid {COR_ROXO_FORTE};
        border-radius: 6px;
    }}
    </style>
    """, unsafe_allow_html=True)

# --------------------------
# FUNÇÕES DE BANCO DE DADOS
# --------------------------
def init_db():
    if not os.path.exists(FILE_DB):
        df = pd.DataFrame(columns=["usuario", "atividade", "hora_inicio", "hora_fim", "duracao_formatada", "segundos_totais", "data"])
        df.to_csv(FILE_DB, index=False)

def carregar_usuarios():
    if not os.path.exists(FILE_USERS):
        return {}
    with open(FILE_USERS, "r", encoding="utf-8") as f:
        return json.load(f)

# === FUNÇÃO SALVAR BLINDADA ===
def salvar_atividade(usuario, atividade, segundos, inicio_float=None, hora_inicio_manual=None, hora_fim_manual=None):
    df = pd.read_csv(FILE_DB)
    
    # Prioridade para Horário Manual
    if hora_inicio_manual is not None and hora_fim_manual is not None:
        hora_inicio_str = hora_inicio_manual
        hora_fim_str = hora_fim_manual
    else:
        # Automático (Cronômetro)
        if inicio_float is None:
            inicio_float = time.time()
        hora_inicio_str = datetime.fromtimestamp(inicio_float).strftime("%H:%M:%S")
        hora_fim_str = datetime.now().strftime("%H:%M:%S")
    
    nova_linha = {
        "usuario": usuario,
        "atividade": atividade,
        "hora_inicio": hora_inicio_str,
        "hora_fim": hora_fim_str,
        "duracao_formatada": str(timedelta(seconds=int(segundos))),
        "segundos_totais": int(segundos),
        "data": datetime.now().strftime("%Y-%m-%d")
    }
    
    df_novo = pd.DataFrame([nova_linha])
    df = pd.concat([df, df_novo], ignore_index=True)
    df.to_csv(FILE_DB, index=False)

def formatar_tempo(seg):
    return str(timedelta(seconds=int(seg)))

# --------------------------
# ESTADOS DA SESSÃO (AQUI ESTAVA O ERRO!)
# --------------------------
# Esse bloco precisa existir antes de tudo!
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "usuario_info" not in st.session_state:
    st.session_state.usuario_info = {}
if "timer_status" not in st.session_state:
    st.session_state.timer_status = "parado"
if "inicio_tempo" not in st.session_state:
    st.session_state.inicio_tempo = None
if "primeiro_inicio" not in st.session_state: # Importante para correção do pause
    st.session_state.primeiro_inicio = None
if "tempo_acumulado" not in st.session_state:
    st.session_state.tempo_acumulado = 0

init_db()

# --------------------------
# TELA DE LOGIN
# --------------------------
def login_screen():
    configurar_estilo()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        caminho_logo = "fotos/radix_logo.jpg"
        if os.path.exists(caminho_logo):
            c_esq, c_meio, c_dir = st.columns([1, 2, 1])
            with c_meio:
                st.image(Image.open(caminho_logo), use_container_width=True)

        st.markdown("<h1 style='text-align: center;'>🔐 Acesso ao Sistema</h1>", unsafe_allow_html=True)
        st.markdown("---")
        
        user = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        
        if st.button("Entrar", use_container_width=True, type="primary"):
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
# BARRA LATERAL
# --------------------------
def show_sidebar():
    configurar_estilo()
    with st.sidebar:
        if os.path.exists("fotos/radix_logo.png"):
            st.image("fotos/radix_logo.png", width=180)
            st.write('')
            
        info = st.session_state.usuario_info
        if "foto" in info and os.path.exists(info["foto"]):
            st.image(Image.open(info["foto"]), width=150)
        else:
            st.markdown("<div style='text-align:center; font-size: 80px; color: #6A1B9A;'>👤</div>", unsafe_allow_html=True)
            
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
    
    # 1. CÁLCULO TOTAIS
    df = pd.read_csv(FILE_DB)
    hoje = datetime.now().strftime("%Y-%m-%d")
    user_id = st.session_state.usuario_info["user_id"]
    
    total_segundos = 0
    if not df.empty:
        if "segundos_totais" in df.columns:
            df["segundos_totais"] = pd.to_numeric(df["segundos_totais"], errors='coerce').fillna(0)
        df_hoje = df[(df["usuario"] == user_id) & (df["data"] == hoje)]
        total_segundos = int(df_hoje["segundos_totais"].sum())
        
    tempo_em_andamento = 0
    if st.session_state.timer_status == "rodando":
        tempo_em_andamento = st.session_state.tempo_acumulado + (time.time() - st.session_state.inicio_tempo)
    elif st.session_state.timer_status == "pausado":
        tempo_em_andamento = st.session_state.tempo_acumulado
    
    total_geral = total_segundos + int(tempo_em_andamento)

    # 2. STATUS WIDGET
    if st.session_state.timer_status == "rodando":
        bg_status, border_status, text_status, icon_status = "#E8F5E9", "#43A047", "#1B5E20", "🚀"
    else:
        bg_status, border_status, text_status, icon_status = "#F3E5F5", "#8E24AA", "#4A148C", "💤"
        
    with st.container():
        col_status, col_total = st.columns(2)
        with col_status:
            st.markdown(f"""
            <div style="background-color: {bg_status}; padding: 15px; border-radius: 10px; border: 2px solid {border_status}; text-align: center; height: 100px; display: flex; flex-direction: column; justify-content: center;">
                <span style="font-size: 1.2rem; color: {text_status}; font-weight: bold;">STATUS ATUAL</span>
                <span style="font-size: 1.5rem; color: {text_status};">{icon_status} {st.session_state.timer_status.upper()}</span>
            </div>
            """, unsafe_allow_html=True) 
        with col_total:
            st.markdown(f"""
            <div style="background-color: #FFFFFF; padding: 15px; border-radius: 10px; border: 2px solid #6A1B9A; text-align: center; height: 100px; display: flex; flex-direction: column; justify-content: center;">
                <span style="font-size: 1.2rem; color: #333; font-weight: bold;">TOTAL HOJE</span>
                <span style="font-size: 2rem; color: #6A1B9A; font-weight: bold;">{formatar_tempo(total_geral)}</span>
            </div>
            """, unsafe_allow_html=True)
    
    st.write("") 

    # 3. ABAS
    tab1, tab2 = st.tabs(["⏱ Cronômetro", "📝 Registro Manual"])

    # === ABA 1: CRONÔMETRO ===
    with tab1:
        col_input, col_timer = st.columns([1.5, 1])
        with col_input:
            st.subheader("Nova Tarefa (Ao Vivo)")
            atividade = st.text_input("O que você vai fazer?", key="input_atividade", placeholder="Ex: Relatório Mensal...")
            
            col_b1, col_b2, col_b3 = st.columns(3)
            with col_b1:
                if st.button("▶ INICIAR", use_container_width=True, type="secondary"):
                    if not atividade:
                        st.warning("Digite o nome da atividade!")
                    else:
                        if st.session_state.primeiro_inicio is None: st.session_state.primeiro_inicio = time.time()
                        st.session_state.inicio_tempo = time.time()
                        st.session_state.timer_status = "rodando"
                        st.rerun()
            with col_b2:
                if st.button("⏸ PAUSAR", use_container_width=True, type="primary"):
                    if st.session_state.timer_status == "rodando":
                        st.session_state.tempo_acumulado += time.time() - st.session_state.inicio_tempo
                        st.session_state.timer_status = "pausado"
                        st.rerun()
            with col_b3:
                if st.button("✅ FINALIZAR", use_container_width=True, type="secondary"):
                    if st.session_state.timer_status != "parado":
                        total = st.session_state.tempo_acumulado
                        if st.session_state.timer_status == "rodando":
                            total += time.time() - st.session_state.inicio_tempo
                        
                        user_id = st.session_state.usuario_info["user_id"]
                        tempo_csv = st.session_state.primeiro_inicio if st.session_state.primeiro_inicio else time.time()
                        salvar_atividade(user_id, atividade, int(total), inicio_float=tempo_csv)
                        
                        st.session_state.timer_status = "parado"
                        st.session_state.tempo_acumulado = 0
                        st.session_state.inicio_tempo = None
                        st.session_state.primeiro_inicio = None
                        st.success("Salvo!")
                        time.sleep(1)
                        st.rerun()

        with col_timer:
            placeholder = st.empty()
            cor_relogio = "#43A047" if st.session_state.timer_status == "rodando" else "#6A1B9A"
            if st.session_state.timer_status == "rodando":
                while st.session_state.timer_status == "rodando":
                    agora = time.time()
                    decorrido = st.session_state.tempo_acumulado + (agora - st.session_state.inicio_tempo)
                    placeholder.markdown(f"<div style='text-align:center; font-size:4rem; font-weight:bold; color:{cor_relogio}'>{formatar_tempo(decorrido)}</div>", unsafe_allow_html=True)
                    time.sleep(1)
            elif st.session_state.timer_status == "pausado":
                 placeholder.markdown(f"<div style='text-align:center; font-size:4rem; font-weight:bold; color:#F9A825'>{formatar_tempo(st.session_state.tempo_acumulado)}</div>", unsafe_allow_html=True)
            else:
                 placeholder.markdown(f"<div style='text-align:center; font-size:4rem; font-weight:bold; color:#BDBDBD'>00:00:00</div>", unsafe_allow_html=True)

    # === ABA 2: REGISTRO MANUAL ===
    with tab2:
        st.subheader("Inserir horas passadas")
        with st.form("form_manual"):
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                ativ_manual = st.text_input("Nome da Atividade")
            with col_m2:
                c_h1, c_h2 = st.columns(2)
                with c_h1:
                    hora_ini = st.time_input("Hora Início", value=datetime.now().time(), step=60)
                with c_h2:
                    hora_fim = st.time_input("Hora Fim", value=datetime.now().time(), step=60)
            
            submit_manual = st.form_submit_button("💾 Salvar Registro Manual", type="primary")
            
            if submit_manual:
                if not ativ_manual:
                    st.warning("Preencha o nome da atividade.")
                elif hora_ini >= hora_fim:
                    st.error("A hora final deve ser maior que a hora inicial.")
                else:
                    data_hoje = datetime.now().date()
                    dt_ini = datetime.combine(data_hoje, hora_ini)
                    dt_fim = datetime.combine(data_hoje, hora_fim)
                    duracao_segundos = (dt_fim - dt_ini).total_seconds()
                    
                    str_ini = hora_ini.strftime("%H:%M:%S")
                    str_fim = hora_fim.strftime("%H:%M:%S")
                    
                    user_id = st.session_state.usuario_info["user_id"]
                    
                    # Força envio dos manuais
                    salvar_atividade(
                        usuario=user_id,
                        atividade=ativ_manual,
                        segundos=int(duracao_segundos),
                        inicio_float=None, 
                        hora_inicio_manual=str_ini, 
                        hora_fim_manual=str_fim
                    )
                    st.success(f"Atividade '{ativ_manual}' registrada! ({str_ini} às {str_fim})")
                    time.sleep(1)
                    st.rerun()

    st.divider()
    
    # 4. HISTÓRICO
    st.subheader("🗓 Histórico de Hoje")
    if not df.empty:
        if "segundos_totais" in df.columns:
            df["segundos_totais"] = pd.to_numeric(df["segundos_totais"], errors='coerce').fillna(0)
        df_hoje_tab = df[(df["usuario"] == user_id) & (df["data"] == hoje)]
        if not df_hoje_tab.empty:
            colunas_display = {"atividade": "Atividade", "hora_inicio": "Início", "hora_fim": "Fim", "duracao_formatada": "Duração"}
            cols_existentes = [c for c in colunas_display.keys() if c in df_hoje_tab.columns]
            df_exibir = df_hoje_tab[cols_existentes].rename(columns=colunas_display)
            st.dataframe(df_exibir.style.set_properties(**{'background-color': '#FFFFFF', 'color': '#000000'}), use_container_width=True, hide_index=True)
        else:
            st.info("Nada registrado hoje.")
    else:
        st.info("Nada registrado hoje.")

# --------------------------
# TELA DO EMERSON
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
    
    st.markdown("### Tempo por Atividade")
    st.bar_chart(df_filtered.groupby("atividade")["segundos_totais"].sum(), color="#6A1B9A")
    
    st.subheader("Detalhamento")
    colunas_chefe = {"usuario": "Funcionário", "atividade": "Atividade", "hora_inicio": "Início", "hora_fim": "Fim", "duracao_formatada": "Duração Total"}
    cols_to_use = [c for c in colunas_chefe.keys() if c in df_filtered.columns]
    df_exibir_chefe = df_filtered[cols_to_use].rename(columns=colunas_chefe)
    
    st.dataframe(df_exibir_chefe.style.set_properties(**{'background-color': '#FFFFFF', 'color': '#000000'}), use_container_width=True, hide_index=True)

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