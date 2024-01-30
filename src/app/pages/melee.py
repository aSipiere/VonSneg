"""
app.melee
~~~~~~~~~
Melee streamlit page
"""
import json

import pandas as pd
import streamlit as st

st.title("Melee")

with open("data/units.json", encoding="utf8") as file:
    units = json.load(file)
with st.sidebar:
    attacker = st.selectbox("Attacker", units.keys())
    attacker_equip = st.selectbox(
        "Attacker Equipment", ["Black Powder", "Missile", "Close Combat Weapons"]
    )
    defender = st.selectbox("Defender", units.keys())
    defender_equip = st.selectbox(
        "Defender Equipment", ["Black Powder", "Missile", "Close Combat Weapons"]
    )


col1, col2 = st.columns(2)

with col1:
    st.title(attacker)
    st.table(pd.Series(units[attacker]))
with col2:
    st.title(defender)
    st.table(pd.Series(units[defender]))
