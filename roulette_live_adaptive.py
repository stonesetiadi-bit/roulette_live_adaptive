import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter
import time

# Roulette Eropa 0-36
roulette_numbers = [0,32,15,19,4,21,2,25,17,34,6,27,13,36,11,30,8,23,10,5,24,16,33,1,20,14,31,9,22,18,29,7,28,12,35,3,26]
num_positions = len(roulette_numbers)
red_numbers = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]
black_numbers = [2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35]

# Fungsi kategori
def get_color(number):
    if number in red_numbers:
        return 'Red'
    elif number in black_numbers:
        return 'Black'
    else:
        return 'Green'

def get_dozen(number):
    if 1 <= number <= 12:
        return 'Dozen 1'
    elif 13 <= number <= 24:
        return 'Dozen 2'
    elif 25 <= number <= 36:
        return 'Dozen 3'
    else:
        return 'Zero'

def get_low_high(number):
    if 1 <= number <= 18:
        return 'Low'
    elif 19 <= number <= 36:
        return 'High'
    else:
        return 'Zero'

# Riwayat putaran
if 'history' not in st.session_state:
    st.session_state['history'] = []

avg_steps = 12
weight_decay = 0.8

# Fungsi utilitas
def get_index(number):
    return roulette_numbers.index(number)

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

# Fungsi prediksi adaptif
def predict_next(table, direction='clockwise', dealer_factor=1.0):
    last_numbers = [h for h in st.session_state['history'] if h['table']==table]
    if not last_numbers:
        last_number = roulette_numbers[0]
        last_area = None
    else:
        last_number = last_numbers[-1]['number']
        last_area = last_numbers[-1]['area']

    freq = Counter([h['number'] for h in last_numbers[-50:]])  # adaptif: gunakan 50 putaran terakhir
    color_freq = Counter([h['color'] for h in last_numbers[-50:]])
    dozen_freq = Counter([h['dozen'] for h in last_numbers[-50:]])
    lowhigh_freq = Counter([h['low_high'] for h in last_numbers[-50:]])

    max_freq = max(freq.values()) if freq else 1

    idx = get_index(last_number)
    probabilities = {}

    for i, num in enumerate(roulette_numbers):
        # Perhitungan jarak (fisika sederhana)
        if direction=='clockwise':
            steps = (i - idx) % num_positions
        else:
            steps = (idx - i) % num_positions
        prob_distance = max(0, 1 - abs(steps - avg_steps)*(1 - weight_decay)/avg_steps)

        # Probabilitas adaptif berdasarkan histori
        prob_freq = freq.get(num,0)/max_freq
        prob_color = color_freq.get(get_color(num),0)/max(1, sum(color_freq.values()))
        prob_dozen = dozen_freq.get(get_dozen(num),0)/max(1, sum(dozen_freq.values()))
        prob_lowhigh = lowhigh_freq.get(get_low_high(num),0)/max(1, sum(lowhigh_freq.values()))

        # Gabungan bobot adaptif
        prob = (prob_distance*0.4 + prob_freq*0.3 + prob_color*0.1 + prob_dozen*0.1 + prob_lowhigh*0.1) * dealer_factor
        probabilities[num] = prob

    predicted = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)
    return predicted[:10]

# Streamlit UI
st.title("Live Roulette Predictor Adaptive")

# Input putaran baru
with st.form("input_form"):
    number = st.number_input("Nomor keluar (0-36)", min_value=0, max_value=36, step=1)
    table = st.selectbox("Meja", [1,2])
    area = st.selectbox("Area lempar bola / Dozen / Red-Black / Low-High", ['None','Dozen 1','Dozen 2','Dozen 3','Red','Black','Low','High'])
    direction = st.selectbox("Arah putaran", ['clockwise','counterclockwise'])
    dealer_factor = st.slider("Faktor dealer", 0.8, 1.2, 1.0)
    submit = st.form_submit_button("Tambah Putaran")
    if submit:
        area_val = area if area != 'None' else None
        update_history(number, table, area_val, direction, dealer_factor)

# Tampilkan histori nomor yang keluar
st.subheader("Histori Nomor Keluar")
if st.session_state['history']:
    for h in st.session_state['history']:
        st.write(f"Nomor {h['number']} - Meja {h['table']} - Area {h['area']} - Color {h['color']} - Dozen {h['dozen']} - Low/High {h['low_high']}")
else:
    st.write("Belum ada nomor yang dicatat")

# Prediksi
table_pred = st.selectbox("Prediksi Meja", [1,2])
preds = predict_next(table_pred, direction, dealer_factor)
st.subheader(f"Prediksi Top 10 Meja {table_pred}")
for num, prob in preds:
    st.write(f"Nomor {num} ({get_color(num)}, {get_dozen(num)}, {get_low_high(num)}) dengan bobot {prob:.2f}")

# Visualisasi lingkaran
fig, ax = plt.subplots(figsize=(6,6), subplot_kw={'polar':True})
angles = np.linspace(0, 2*np.pi, num_positions, endpoint=False)
for i, num in enumerate(roulette_numbers):
    ax.text(angles[i], 1.0, str(num), fontsize=10, ha='center', va='center')
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
