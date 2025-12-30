import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta
import os
import json
import re
from PIL import Image
import altair as alt


st.set_page_config(page_title="Radix Time Tracker", layout="wide", page_icon="⏱")

PRIMARY_COLOR = "#6A1B9A"
SECONDARY_COLOR = "#AB47BC"
BG_LIGHT = "#F3E5F5"
SUCCESS_COLOR = "#43A047"
DANGER_COLOR = "#D32F2F"
CAMINHO_LOGO = "fotos/radix_logo2.png"

def configurar_estilo():
    st.markdown(f"""
    <style>
    div[data-testid="metric-container"] {{
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }}
    div.stButton > button {{
        width: 100%;
        border-radius: 8px;
        font-weight: bold;
    }}
    .big-timer {{
        font-size: 5rem;
        font-weight: 700;
        text-align: center;
        color: {PRIMARY_COLOR};
        font-family: 'Courier New', monospace;
        background-color: #FFF;
        border-radius: 15px;
        padding: 20px;
        border: 2px solid {BG_LIGHT};
        margin-bottom: 20px;
    }}
    </style>
    """, unsafe_allow_html=True)

FILE_DB = "registro_atividades.csv"
FILE_USERS = "usuarios.json"
FILE_RITM_STATUS = "ritms_status.json"

def init_db():
    if not os.path.exists(FILE_DB):
        df = pd.DataFrame(columns=["usuario", "atividade", "hora_inicio", "hora_fim", "duracao_formatada", "segundos_totais", "data", "tipo"])
        df.to_csv(FILE_DB, index=False)
    
    if not os.path.exists(FILE_USERS):
        users = {
            "admin": {"nome": "Administrador", "senha": "123", "cargo": "chefe", "foto": "fotos/user_admin.jpg"},
            "dev": {"nome": "Desenvolvedor", "senha": "123", "cargo": "funcionario", "foto": "fotos/user_dev.jpg"}
        }
        with open(FILE_USERS, "w", encoding="utf-8") as f:
            json.dump(users, f)
            
    if not os.path.exists(FILE_RITM_STATUS):
        with open(FILE_RITM_STATUS, "w", encoding="utf-8") as f:
            json.dump({}, f)

def carregar_usuarios():
    with open(FILE_USERS, "r", encoding="utf-8") as f:
        return json.load(f)

def carregar_status_ritm():
    with open(FILE_RITM_STATUS, "r", encoding="utf-8") as f:
        return json.load(f)

def atualizar_status_ritm(ritm_code, status):
    dados = carregar_status_ritm()
    dados[ritm_code] = status 
    with open(FILE_RITM_STATUS, "w", encoding="utf-8") as f:
        json.dump(dados, f)

def salvar_registro(dados):
    df = pd.read_csv(FILE_DB)
    df_novo = pd.DataFrame([dados])
    df = pd.concat([df, df_novo], ignore_index=True)
    df.to_csv(FILE_DB, index=False)

def formatar_tempo(segundos):
    return str(timedelta(seconds=int(segundos)))

def extrair_ritm(texto):
    if not isinstance(texto, str): return None
    match = re.search(r'(RITM[-]?\d+)', texto.upper())
    if match:
        return match.group(1)
    return None


if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "timer_status" not in st.session_state:
    st.session_state.timer_status = "parado" 
if "inicio_tempo" not in st.session_state:
    st.session_state.inicio_tempo = None
if "tempo_acumulado" not in st.session_state:
    st.session_state.tempo_acumulado = 0
if "atividade_atual" not in st.session_state:
    st.session_state.atividade_atual = ""

init_db()
configurar_estilo()


def login_screen():
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        if os.path.exists(CAMINHO_LOGO):
            try:
                st.image(Image.open(CAMINHO_LOGO), use_container_width=True)
            except:
                st.markdown(f"<h1 style='text-align: center; color: {PRIMARY_COLOR};'>Radix Ponto</h1>", unsafe_allow_html=True)
        else:
            st.markdown(f"<h1 style='text-align: center; color: {PRIMARY_COLOR};'>Radix Ponto</h1>", unsafe_allow_html=True)
        
        st.markdown(f"<h3 style='text-align: center; color: #555;'>Acesso ao Sistema</h3>", unsafe_allow_html=True)
        st.write("---")
        with st.container(border=True):
            user = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            
            if st.button("Acessar Sistema", type="primary"):
                usuarios = carregar_usuarios()
                if user in usuarios and usuarios[user]["senha"] == senha:
                    st.session_state.logged_in = True
                    st.session_state.usuario_info = usuarios[user]
                    st.session_state.usuario_info["user_id"] = user
                    st.toast(f"Bem-vindo, {usuarios[user]['nome']}!", icon="👋")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Credenciais inválidas.")

def sidebar_info():
    with st.sidebar:
        if os.path.exists(CAMINHO_LOGO):
            st.image(CAMINHO_LOGO, width=180)
            st.write('')
        
        info = st.session_state.usuario_info
        foto_path = info.get("foto", "")
        if foto_path and os.path.exists(foto_path):
            st.image(Image.open(foto_path), width=150)
        else:
            st.markdown(f"<div style='font-size: 80px; color: {PRIMARY_COLOR};'>👤</div>", unsafe_allow_html=True)

        st.markdown(f"### Olá, **{st.session_state.usuario_info['nome']}**")
        st.caption(f"Perfil: {st.session_state.usuario_info['cargo'].upper()}")
        st.divider()
        if st.button("Sair / Logout"):
            st.session_state.logged_in = False
            st.rerun()

def funcionario_dashboard():
    sidebar_info()
    user_id = st.session_state.usuario_info["user_id"]
    hoje_str = datetime.now().strftime("%Y-%m-%d")

    df = pd.read_csv(FILE_DB)
    
  
    total_hoje_seg = 0
    if not df.empty:
        df_hoje = df[(df["usuario"] == user_id) & (df["data"] == hoje_str)]
        total_hoje_seg = df_hoje["segundos_totais"].sum()
    
    tempo_sessao_atual = 0
    if st.session_state.timer_status == "rodando":
        tempo_sessao_atual = (time.time() - st.session_state.inicio_tempo)
    
    total_geral = total_hoje_seg + st.session_state.tempo_acumulado + tempo_sessao_atual

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        st.title("Meu Ponto")
        st.caption(f"Data: {datetime.now().strftime('%d/%m/%Y')}")
    with c2:
        st.metric("Status", st.session_state.timer_status.upper())
    with c3:
        st.metric("Total Hoje", formatar_tempo(total_geral).split(".")[0])

    st.markdown("---")


    tab_timer, tab_manual, tab_ritm = st.tabs(["⏱ Cronômetro", "📝 Registro Manual", "💼 Gestão de Chamados (RITM)"])

  
    with tab_timer:
        col_input, col_timer = st.columns([1, 1])
        with col_input:
            st.subheader("Atividade Atual")
            disabled_inputs = st.session_state.timer_status != "parado"
            atividade = st.text_input("Nome da Tarefa", 
                                    value=st.session_state.atividade_atual if disabled_inputs else "",
                                    placeholder="Ex: Desenvolvimento Frontend...", 
                                    disabled=disabled_inputs)
            
            col_check, col_code = st.columns([1, 2])
            is_chamado = col_check.checkbox("Vincular RITM", disabled=disabled_inputs)
            ritm_code = col_code.text_input("Código", placeholder="RITM0000", disabled=(not is_chamado or disabled_inputs))

            b1, b2, b3 = st.columns(3)
            
            if st.session_state.timer_status == "parado":
                if b1.button("▶ INICIAR", type="primary"):
                    if not atividade:
                        st.toast("Preencha o nome!", icon="⚠️")
                    else:
                        nome_final = f"{atividade} [{ritm_code.upper()}]" if is_chamado and ritm_code else atividade
                        st.session_state.atividade_atual = nome_final
                        st.session_state.inicio_tempo = time.time()
                        st.session_state.timer_status = "rodando"
                        st.rerun()
            
            elif st.session_state.timer_status == "rodando":
                if b2.button("⏸ PAUSAR"):
                    st.session_state.tempo_acumulado += time.time() - st.session_state.inicio_tempo
                    st.session_state.timer_status = "pausado"
                    st.rerun()
                if b3.button("✅ FINALIZAR", type="primary"):
                    total = st.session_state.tempo_acumulado + (time.time() - st.session_state.inicio_tempo)
                    dados = {
                        "usuario": user_id,
                        "atividade": st.session_state.atividade_atual,
                        "hora_inicio": datetime.fromtimestamp(st.session_state.inicio_tempo).strftime("%H:%M:%S"),
                        "hora_fim": datetime.now().strftime("%H:%M:%S"),
                        "duracao_formatada": formatar_tempo(total),
                        "segundos_totais": int(total),
                        "data": hoje_str,
                        "tipo": "timer"
                    }
                    salvar_registro(dados)
                    st.session_state.timer_status = "parado"
                    st.session_state.tempo_acumulado = 0
                    st.session_state.atividade_atual = ""
                    st.toast("Salvo!", icon="💾")
                    time.sleep(1)
                    st.rerun()

            elif st.session_state.timer_status == "pausado":
                if b1.button("▶ RETOMAR"):
                    st.session_state.inicio_tempo = time.time()
                    st.session_state.timer_status = "rodando"
                    st.rerun()
                if b3.button("✅ FINALIZAR", type="primary"):
                    total = st.session_state.tempo_acumulado
                    dados = {
                        "usuario": user_id,
                        "atividade": st.session_state.atividade_atual,
                        "hora_inicio": "N/A",
                        "hora_fim": datetime.now().strftime("%H:%M:%S"),
                        "duracao_formatada": formatar_tempo(total),
                        "segundos_totais": int(total),
                        "data": hoje_str,
                        "tipo": "timer"
                    }
                    salvar_registro(dados)
                    st.session_state.timer_status = "parado"
                    st.session_state.tempo_acumulado = 0
                    st.session_state.atividade_atual = ""
                    st.rerun()

        with col_timer:
            container_timer = st.empty()
            if st.session_state.timer_status == "rodando":
                while st.session_state.timer_status == "rodando":
                    agora = time.time()
                    delta = st.session_state.tempo_acumulado + (agora - st.session_state.inicio_tempo)
                    fmt = str(timedelta(seconds=int(delta)))
                    container_timer.markdown(f"<div class='big-timer'>{fmt}</div>", unsafe_allow_html=True)
                    time.sleep(0.5)
            elif st.session_state.timer_status == "pausado":
                 fmt = str(timedelta(seconds=int(st.session_state.tempo_acumulado)))
                 container_timer.markdown(f"<div class='big-timer' style='color:#FF9800'>{fmt}</div>", unsafe_allow_html=True)
            else:
                 container_timer.markdown(f"<div class='big-timer' style='color:#BDBDBD'>00:00:00</div>", unsafe_allow_html=True)

   
    with tab_manual:
        with st.form("manual_form"):
            c_m1, c_m2, c_m3 = st.columns(3)
            ativ_manual = c_m1.text_input("Atividade (Inclua o código RITM se houver)")
            h_ini = c_m2.time_input("Início")
            h_fim = c_m3.time_input("Fim")
            if st.form_submit_button("Lançar"):
                dt_ini = datetime.combine(datetime.today(), h_ini)
                dt_fim = datetime.combine(datetime.today(), h_fim)
                if dt_fim > dt_ini:
                    secs = (dt_fim - dt_ini).total_seconds()
                    dados = {
                        "usuario": user_id,
                        "atividade": ativ_manual,
                        "hora_inicio": str(h_ini),
                        "hora_fim": str(h_fim),
                        "duracao_formatada": formatar_tempo(secs),
                        "segundos_totais": int(secs),
                        "data": hoje_str,
                        "tipo": "manual"
                    }
                    salvar_registro(dados)
                    st.toast("Salvo!", icon="✅")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Hora fim < Hora início")

   
    with tab_ritm:
        st.subheader("Meus Chamados e Entregas")
        st.info("Aqui você gerencia o encerramento dos chamados em que trabalhou.")
   
        if not df.empty:
            df_user_ritm = df[df["usuario"] == user_id].copy()
            df_user_ritm["ritm_code"] = df_user_ritm["atividade"].apply(extrair_ritm)
            df_user_ritm = df_user_ritm.dropna(subset=["ritm_code"])
            
            if df_user_ritm.empty:
                st.write("Você ainda não registrou atividades vinculadas a um RITM.")
            else:
                
                status_db = carregar_status_ritm()
                
                meus_ritms = df_user_ritm['ritm_code'].unique()
                
                for ritm in meus_ritms:
                
                    df_ritm_global = df[df["atividade"].str.contains(ritm, na=False)]
                    total_horas_ritm = df_ritm_global["segundos_totais"].sum()
                    
                    status_atual = status_db.get(ritm, "Aberto")
                 
                    cor_status = SUCCESS_COLOR if status_atual == "Aberto" else "#BDBDBD"
                    icon_status = "🟢 Em Andamento" if status_atual == "Aberto" else "🔒 Encerrado"
                    
                    with st.container(border=True):
                        col_info, col_action = st.columns([3, 1])
                        
                        with col_info:
                            st.markdown(f"### {ritm}")
                            st.markdown(f"**Status:** <span style='color:{cor_status}; font-weight:bold'>{icon_status}</span>", unsafe_allow_html=True)
                            st.write(f"Tempo Total Investido (Equipe): **{formatar_tempo(total_horas_ritm)}**")
                        
                        with col_action:
                            if status_atual == "Aberto":
                                if st.button(f"Encerrar Chamado", key=f"close_{ritm}", type="primary"):
                                    atualizar_status_ritm(ritm, "Fechado")
                                    st.success("Chamado Encerrado!")
                                    time.sleep(1)
                                    st.rerun()
                            else:
                                st.button("Reabrir Chamado", key=f"reopen_{ritm}", on_click=atualizar_status_ritm, args=(ritm, "Aberto"))
                                
                            # Botão de Email (Sempre visível se quiser reenviar)
                            assunto = f"Encerramento do Chamado {ritm}"
                            corpo = f"Prezados,%0A%0AInformamos que o chamado {ritm} foi concluído.%0A%0ATempo total investido: {formatar_tempo(total_horas_ritm)}%0A%0AAtenciosamente,%0A{st.session_state.usuario_info['nome']}."
                            link_email = f"mailto:?subject={assunto}&body={corpo}"
                            
                            st.markdown(f"""
                            <a href="{link_email}" target="_blank" style="text-decoration:none;">
                                <div style="background-color: #f0f2f6; color: #31333F; padding: 8px; border-radius: 5px; text-align: center; border: 1px solid #d6d6d8; font-weight: 500; margin-top: 5px;">
                                    📧 Preparar Email
                                </div>
                            </a>
                            """, unsafe_allow_html=True)

    
    st.divider()
    st.markdown("### 📊 Minhas Estatísticas")
    periodo = st.radio("Período", ["Hoje", "7 Dias", "30 Dias"], horizontal=True)
    
    df_user = df[df["usuario"] == user_id].copy()
    if not df_user.empty:
        df_user['data_dt'] = pd.to_datetime(df_user['data'])
        hoje_dt = pd.to_datetime(hoje_str)
        if periodo == "Hoje":
            df_chart = df_user[df_user['data_dt'] == hoje_dt]
        elif periodo == "7 Dias":
            data_limite = hoje_dt - timedelta(days=7)
            df_chart = df_user[df_user['data_dt'] >= data_limite]
        else:
            data_limite = hoje_dt - timedelta(days=30)
            df_chart = df_user[df_user['data_dt'] >= data_limite]
        
        if not df_chart.empty:
            df_chart['Horas'] = df_chart['segundos_totais'] / 3600
            g1, g2 = st.columns([1.5, 1])
            with g1:
                chart_bar = alt.Chart(df_chart).mark_bar().encode(
                    x=alt.X('sum(Horas)', title='Total de Horas', axis=alt.Axis(format='.1f')),
                    y=alt.Y('atividade', sort='-x', title=''),
                    color=alt.value(PRIMARY_COLOR),
                    tooltip=['atividade', alt.Tooltip('sum(Horas)', format='.2f')]
                )
                st.altair_chart(chart_bar, use_container_width=True)
            with g2:
                if periodo == "Hoje":
                    st.dataframe(df_chart[['atividade', 'hora_inicio', 'duracao_formatada']], hide_index=True, use_container_width=True)
                else:
                    chart_line = alt.Chart(df_chart).mark_bar(width=20).encode(
                        x=alt.X('data', title='Data'),
                        y=alt.Y('sum(Horas)', title='Horas'),
                        color=alt.value(SECONDARY_COLOR)
                    )
                    st.altair_chart(chart_line, use_container_width=True)

def chefe_dashboard():
    sidebar_info()
    st.title("📊 Painel de Gestão")
    
    tab_geral, tab_ritm_admin = st.tabs(["📈 Visão Geral", "📋 Relatório de Chamados"])
    
    df = pd.read_csv(FILE_DB)
    if df.empty:
        st.warning("Sem dados.")
        return

 
    with tab_geral:
        c1, c2 = st.columns(2)
        with c1:
            datas = sorted(df["data"].unique(), reverse=True)
            sel_data = st.selectbox("Data", datas)
        with c2:
            usuarios = ["Todos"] + list(df["usuario"].unique())
            sel_user = st.selectbox("Funcionário", usuarios)

        df_filtered = df[df["data"] == sel_data]
        if sel_user != "Todos":
            df_filtered = df_filtered[df_filtered["usuario"] == sel_user]

        st.markdown("---")
        k1, k2, k3 = st.columns(3)
        total_secs = df_filtered["segundos_totais"].sum()
        k1.metric("Total Horas", formatar_tempo(total_secs).split(".")[0])
        k2.metric("Tarefas", len(df_filtered))
        k3.metric("Média", formatar_tempo(total_secs / len(df_filtered) if len(df_filtered) > 0 else 0).split(".")[0])
        st.dataframe(df_filtered, use_container_width=True, hide_index=True)

  
    with tab_ritm_admin:
        st.subheader("Status dos Chamados (Read-Only)")
        
        df["ritm_code"] = df["atividade"].apply(extrair_ritm)
        df_ritms = df.dropna(subset=["ritm_code"])
        
        if df_ritms.empty:
            st.info("Nenhum RITM encontrado.")
        else:
            status_db = carregar_status_ritm()
           
            resumo_ritm = df_ritms.groupby(['ritm_code'])['segundos_totais'].sum().reset_index()
            
            
            for idx, row in resumo_ritm.iterrows():
                ritm = row['ritm_code']
                total = row['segundos_totais']
                status = status_db.get(ritm, "Aberto")
              
                cor_card = "#E8F5E9" if status == "Aberto" else "#EEEEEE" # Verde claro ou Cinza
                cor_texto = "#2E7D32" if status == "Aberto" else "#616161"
                icon = "🟢 EM ABERTO" if status == "Aberto" else "🔒 FECHADO"
                
                with st.container():
                    st.markdown(f"""
                    <div style="background-color: {cor_card}; padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 5px solid {cor_texto}">
                        <h4 style="margin:0; color: #333">{ritm}</h4>
                        <p style="margin:0; font-weight:bold; color: {cor_texto}">{icon}</p>
                        <p style="margin:0">Tempo Total Gasto: {formatar_tempo(total)}</p>
                    </div>
                    """, unsafe_allow_html=True)


if not st.session_state.logged_in:
    login_screen()
else:
    if st.session_state.usuario_info.get("cargo") == "chefe":
        chefe_dashboard()
    else:
        funcionario_dashboard()