"""
app.melee
~~~~~~~~~
Melee streamlit page
"""
import json

import pandas as pd
import streamlit as st

from vonsneg.melee import melee

SIMULATION_SIZE = 10_000

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

if st.button("Run"):
    rows = []
    for i in range(SIMULATION_SIZE):
        rows.append(melee(units[attacker].copy(), units[defender].copy(), can_shoot=False))
    
    result_df = pd.DataFrame.from_records(rows)

    st.write(result_df["winner"].value_counts(normalize=True))
    st.write(f"Attacker - Average wounds dealt: {result_df['charging_wounds_delivered'].mean()}")
    st.write(f"Defender - Average wounds dealt: {result_df['defending_wounds_delivered'].mean()}")
    st.write(f"Average No. Bouts: {result_df['bouts'].mean()}")