import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from collections import Counter
import time

# Roulette Eropa
roulette_numbers = [0,32,15,19,4,21,2,25,17,34,6,27,13,36,11,30,8,23,10,5,24,16,33,1,20,14,31,9,22,18,29,7,28,12,35,3,26]
num_positions = len(roulette_numbers)
red_numbers = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]
black_numbers = [2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35]

# Fungsi kategori
def get_color(n):
    if n in red_numbers: return 'Red'
    if n in black_numbers: return 'Black'
    return 'Green'

def get_dozen(n):
    if 1<=n<=12: return 'Dozen 1'
    if 13<=n<=24: return 'Dozen 2'
    if 25<=n<=36: return 'Dozen 3'
    return 'Zero'

def get_low_high(n):
    if 1<=n<=18: return 'Low'
    if 19<=n<=36: return 'High'
    return 'Zero'

# Histori putaran
if 'history' not in st.session_state: st.session_state['history'] = []

# Utilitas
def get_index(n): return roulette_numbers.index(n)

def update_history(number, table, area=None, direction='clockwise', dealer_factor=1.0):
    st.session_state['history'].append({
        'number': number,
        'table': table,
        'area': area,
        'color': get_color(number),
        'dozen': get_dozen(number),
        'low_high': get_low_high(number),
        'direction': direction,
        'dealer_factor': dealer_factor,
        'time': time.time()
    })

# Prediksi adaptif
def predict_next(table, avg_steps=12, weight_decay=0.8):
    last_numbers = [h for h in st.session_state['history'] if h['table']==table]
    if not last_numbers:
        last_number = roulette_numbers[0]
    else:
        last_number = last_numbers[-1]['number']

    freq = Counter([h['number'] for h in last_numbers[-50:]])
    color_freq = Counter([h['color'] for h in last_numbers[-50:]])
    dozen_freq = Counter([h['dozen'] for h in last_numbers[-50:]])
    lowhigh_freq = Counter([h['low_high'] for h in last_numbers[-50:]])
    max_freq = max(freq.values()) if freq else 1

    idx = get_index(last_number)
    probabilities = {}

    for i, num in enumerate(roulette_numbers):
        steps = (i - idx) % num_positions
        prob_distance = max(0, 1 - abs(steps - avg_steps)*(1 - weight_decay)/avg_steps)
        prob_freq = freq.get(num,0)/max_freq
        prob_color = color_freq.get(get_color(num),0)/max(1,sum(color_freq.values()))
        prob_dozen = dozen_freq.get(get_dozen(num),0)/max(1,sum(dozen_freq.values()))
        prob_lowhigh = lowhigh_freq.get(get_low_high(num),0)/max(1,sum(lowhigh_freq.values()))
        probabilities[num] = 0.4*prob_distance + 0.3*prob_freq + 0.1*prob_color + 0.1*prob_dozen + 0.1*prob_lowhigh

    predicted = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)
    return predicted[:10]

# ----------------- UI -----------------
st.title("Live Roulette Predictor Adaptive v2")

# Sidebar pengaturan prediksi
st.sidebar.header("Parameter Prediksi")
avg_steps = st.sidebar.slider("Average Steps", 1, 36, 12)
weight_decay = st.sidebar.slider("Weight Decay", 0.0, 1.0, 0.8)

# Input putaran baru
with st.expander("Tambah Putaran Baru", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        number = st.number_input("Nomor keluar (0-36)", 0,36,0)
        table = st.selectbox("Meja", [1,2])
        area = st.selectbox("Area / Dozen / Color / Low-High", ['None','Dozen 1','Dozen 2','Dozen 3','Red','Black','Low','High'])
    with col2:
        direction = st.selectbox("Arah putaran", ['clockwise','counterclockwise'])
        dealer_factor = st.slider("Faktor dealer",0.8,1.2,1.0)
    if st.button("Tambah Putaran"):
        area_val = area if area != 'None' else None
        update_history(number, table, area_val, direction, dealer_factor)

# Histori nomor
st.subheader("Histori Nomor Keluar")
if st.session_state['history']:
    df = pd.DataFrame(st.session_state['history'])
    st.dataframe(df[['number','table','area','color','dozen','low_high','direction','dealer_factor']])
    csv = df.to_csv(index=False)
    st.download_button("Download Histori CSV", csv, "roulette_history.csv")
else:
    st.write("Belum ada nomor dicatat")

# Prediksi
table_pred = st.selectbox("Prediksi Meja", [1,2])
preds = predict_next(table_pred, avg_steps, weight_decay)
st.subheader(f"Prediksi Top 10 Meja {table_pred}")
for num, prob in preds:
    st.markdown(f"**Nomor {num} ({get_color(num)}, {get_dozen(num)}, {get_low_high(num)})** – Bobot: {prob:.2f}")

# Visualisasi lingkaran
fig, ax = plt.subplots(figsize=(6,6), subplot_kw={'polar':True})
angles = np.linspace(0, 2*np.pi, num_positions, endpoint=False)
for i, num in enumerate(roulette_numbers):
    color = get_color(num)
    ax.text(angles[i], 1.0, str(num), fontsize=10, ha='center', va='center', color=color.lower())
if st.session_state['history']:
    last_num = st.session_state['history'][-1]['number']
    last_idx = get_index(last_num)
    ax.plot([angles[last_idx]], [1.0], 'ro', markersize=12, label='Last Number')
for num, prob in preds:
    idx = get_index(num)
    ax.plot([angles[idx]], [1.0], 'go', markersize=10, alpha=0.6)
ax.set_yticklabels([])
ax.set_xticklabels([])
ax.set_title(f'Meja {table_pred} Roulette - Prediksi Top 10', fontsize=14)
ax.legend(['Last Number','Top 10 Prediction'])
st.pyplot(fig)