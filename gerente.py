import streamlit as st
import requests

st.title("Relatório Diário")

func = st.text_input("Funcionário")

if st.button("Ver relatório"):
    r = requests.get(f"https://minhaapi.com/relatorio/{func}")
    st.dataframe(r.json()["registros"])
