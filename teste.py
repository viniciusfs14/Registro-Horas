import streamlit as st
import time
from datetime import datetime, timedelta

st.set_page_config(page_title="Painel do Funcionário")
st.title("Painel do Funcionário")

# --------------------------
# ESTADOS
# --------------------------
if "status" not in st.session_state:
    st.session_state.status = "parado"  
    # status pode ser: "parado", "rodando", "pausado"

if "inicio_tarefa" not in st.session_state:
    st.session_state.inicio_tarefa = None

if "acumulado" not in st.session_state:
    st.session_state.acumulado = 0  # segundos já contados antes de pausar

if "tarefas" not in st.session_state:
    st.session_state.tarefas = []


# --------------------------
# FUNÇÃO AUXILIAR
# --------------------------
def formatar_tempo(segundos):
    return str(timedelta(seconds=int(segundos)))


# --------------------------
# INPUTS
# --------------------------
atividade = st.text_input("Atividade atual:")

st.divider()


# --------------------------
# BOTÃO INICIAR
# --------------------------
if st.button("Iniciar"):
    if atividade.strip() == "":
        st.warning("Digite a atividade antes de iniciar!")
    else:
        st.session_state.status = "rodando"
        st.session_state.inicio_tarefa = time.time()
        st.session_state.acumulado = 0
        st.success(f"Atividade '{atividade}' iniciada!")
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

        # Salva registro
        st.session_state.tarefas.append({
            "atividade": atividade,
            "duracao": formatar_tempo(tempo_total),
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })

        # Zera estados
        st.session_state.status = "parado"
        st.session_state.inicio_tarefa = None
        st.session_state.acumulado = 0

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
        st.write(f"**{i}. {t['atividade']}** — ⏱️ {t['duracao']} ({t['timestamp']})")
