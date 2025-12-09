import streamlit as st
import time
from datetime import datetime, timedelta

st.set_page_config(page_title="Painel do Funcionário")
st.title("Painel do Funcionário")

# --------------------------
# ESTADOS (SESSION STATE)
# --------------------------
if "status" not in st.session_state:
    st.session_state.status = "parado"  
    # status pode ser: "parado", "rodando", "pausado"

if "inicio_tarefa" not in st.session_state:
    st.session_state.inicio_tarefa = None

if "acumulado" not in st.session_state:
    st.session_state.acumulado = 0  # segundos já contados

if "tarefas" not in st.session_state:
    st.session_state.tarefas = []

# Variáveis para segurar os dados da tarefa EM ANDAMENTO
if "atividade_atual_registrada" not in st.session_state:
    st.session_state.atividade_atual_registrada = ""

if "ritm_atual_registrado" not in st.session_state:
    st.session_state.ritm_atual_registrado = ""


# --------------------------
# FUNÇÃO AUXILIAR
# --------------------------
def formatar_tempo(segundos):
    return str(timedelta(seconds=int(segundos)))


# --------------------------
# INPUTS
# --------------------------
# Só mostra os inputs se estiver parado, para evitar edição durante a execução
if st.session_state.status == "parado":
    atividade_input = st.text_input("Atividade atual:")
    
    # Checkbox para verificar se é item X ou Y
    is_chamado = st.checkbox("Esta tarefa é um Chamado (Item X ou Y)?")
    
    ritm_input = ""
    if is_chamado:
        ritm_input = st.text_input("Código do Chamado (Obrigatório iniciar com RITM):", placeholder="Ex: RITM1234567")

else:
    # Se estiver rodando, mostra apenas o que está sendo feito (texto estático)
    st.info(f"Em andamento: **{st.session_state.atividade_atual_registrada}**")
    if st.session_state.ritm_atual_registrado:
        st.caption(f"Código: {st.session_state.ritm_atual_registrado}")


st.divider()


# --------------------------
# BOTÃO INICIAR
# --------------------------
if st.session_state.status == "parado":
    if st.button("Iniciar"):
        # 1. Validação do Nome
        if atividade_input.strip() == "":
            st.warning("Digite a atividade antes de iniciar!")
        
        # 2. Validação do RITM (se o checkbox estiver marcado)
        elif is_chamado and not ritm_input.upper().startswith("RITM"):
            st.error("Erro: Para esse tipo de tarefa, o código deve começar com 'RITM'.")
        
        else:
            # Inicia o processo
            st.session_state.status = "rodando"
            st.session_state.inicio_tarefa = time.time()
            st.session_state.acumulado = 0
            
            # Salva os dados nos estados para não perder se a tela atualizar
            st.session_state.atividade_atual_registrada = atividade_input
            st.session_state.ritm_atual_registrado = ritm_input.upper() if is_chamado else None
            
            st.success(f"Atividade iniciada!")
            st.rerun()


# --------------------------
# BOTÃO PAUSAR
# --------------------------
if st.session_state.status == "rodando":
    if st.button("Pausar"):
        tempo_atual = time.time() - st.session_state.inicio_tarefa
        st.session_state.acumulado += tempo_atual
        st.session_state.status = "pausado"
        st.success("Atividade pausada.")
        st.rerun()


# --------------------------
# BOTÃO CONTINUAR
# --------------------------
if st.session_state.status == "pausado":
    if st.button("Continuar"):
        st.session_state.status = "rodando"
        st.session_state.inicio_tarefa = time.time()
        st.success("Atividade retomada!")
        st.rerun()


# --------------------------
# BOTÃO FINALIZAR
# --------------------------
if st.session_state.status in ["rodando", "pausado"]:
    if st.button("Finalizar"):
        # Calcula tempo total
        tempo_total = st.session_state.acumulado
        if st.session_state.status == "rodando":
            tempo_total += time.time() - st.session_state.inicio_tarefa

        # Cria o registro final
        registro = {
            "atividade": st.session_state.atividade_atual_registrada,
            "ritm": st.session_state.ritm_atual_registrado, # Campo novo
            "duracao": formatar_tempo(tempo_total),
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }

        # Salva na lista
        st.session_state.tarefas.append(registro)

        # Zera estados
        st.session_state.status = "parado"
        st.session_state.inicio_tarefa = None
        st.session_state.acumulado = 0
        st.session_state.atividade_atual_registrada = ""
        st.session_state.ritm_atual_registrado = ""

        st.success("Atividade finalizada e registrada!")
        st.rerun()


# --------------------------
# CRONÔMETRO EM TEMPO REAL
# --------------------------
if st.session_state.status == "rodando":
    tempo_atual = st.session_state.acumulado + (time.time() - st.session_state.inicio_tarefa)
    st.markdown(f"# ⏱️ {formatar_tempo(tempo_atual)}")
    time.sleep(1)
    st.rerun()

elif st.session_state.status == "pausado":
    st.markdown(f"# ⏸️ {formatar_tempo(st.session_state.acumulado)} (PAUSADO)")


st.divider()

# --------------------------
# LISTA DE ATIVIDADES DO DIA
# --------------------------
st.subheader("📘 Atividades Realizadas Hoje")

if len(st.session_state.tarefas) == 0:
    st.info("Nenhuma atividade registrada ainda.")
else:
    for i, t in enumerate(st.session_state.tarefas, start=1):
        # Formata o texto para mostrar o RITM se existir
        texto_ritm = f" — 🏷️ **{t['ritm']}**" if t['ritm'] else ""
        
        st.write(f"**{i}. {t['atividade']}**{texto_ritm} — ⏱️ {t['duracao']} ({t['timestamp']})")