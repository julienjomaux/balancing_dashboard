import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import date

# --- Streamlit UI ---
st.title("Elia Balancing and Imbalance Data (Opendata)")

# Calendar for date input
selected_date = st.date_input("Select a date", value=date.today())
date_str = selected_date.strftime("%Y-%m-%d")

@st.cache_data(show_spinner=False)
def fetch(dataset, d):
    u = "https://opendata.elia.be/api/records/1.0/search/"
    p = {"dataset": dataset, "rows": 1000, "refine.datetime": d}
    r = requests.get(u, params=p)
    r.raise_for_status()
    return pd.DataFrame([rec['fields'] for rec in r.json().get("records", [])])

try:
    df134 = fetch("ods134", date_str)
    df127 = fetch("ods127", date_str)
    df152 = fetch("ods152", date_str)
    df166 = fetch("ods166", date_str)
except Exception as e:
    st.error(f"Error fetching data: {e}")
    st.stop()

req134 = ['datetime', 'imbalanceprice', 'systemimbalance', 'alpha']
req127 = [
    'datetime', 'igccvolumeup', 'igccvolumedown', 'afrrvolumeup', 'afrrvolumedown',
    'mfrrsaup', 'mfrrsadown', 'mfrrdaup', 'mfrrdadown', 'reserve_sharing_import', 'reserve_sharing_export'
]
req152 = ['datetime', 'downwardavailableafrrvol', 'upwardavailableafrrvol']
req166 = ['datetime', 'cap', 'floorprice']

if not all(c in df134.columns for c in req134) or \
   not all(c in df127.columns for c in req127) or \
   not all(c in df152.columns for c in req152) or \
   not all(c in df166.columns for c in req166):
    st.warning("Some required data columns are missing for the selected date.")
    st.stop()

df134['datetime'] = pd.to_datetime(df134['datetime']); df134.sort_values('datetime', inplace=True)
df127['datetime'] = pd.to_datetime(df127['datetime']); df127.sort_values('datetime', inplace=True)
df152['datetime'] = pd.to_datetime(df152['datetime']); df152.sort_values('datetime', inplace=True)
df166['datetime'] = pd.to_datetime(df166['datetime']); df166.sort_values('datetime', inplace=True)

# --- PLOT 1: Imbalance price + alpha ---
fig1, ax1 = plt.subplots(figsize=(12, 4))
ax1.step(df134['datetime'], df134['imbalanceprice'], where='post', c='tab:blue', label='Imbalance Price', lw=2)
ax1.step(df134['datetime'], df134['alpha'], where='post', c='tab:gray', label='Alpha', lw=2, linestyle='--')
ax1.set_ylabel('Imbalance Price (€/MWh) / Alpha')
ax1.legend(loc='upper left')
ax1.grid(True, axis='y', linestyle=':', alpha=0.7)
ax1.xaxis.set_major_locator(mdates.HourLocator(byhour=range(0,24,2)))
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
plt.xticks(rotation=45)
st.subheader("Imbalance Price and Alpha")
st.pyplot(fig1)

# --- PLOT 2: System imbalance ---
fig2, ax2 = plt.subplots(figsize=(12, 4))
ax2.step(df134['datetime'], df134['systemimbalance'], where='post', c='orange', label='System Imbalance', lw=2)
ax2.set_ylabel('System Imbalance')
ax2.legend(loc='upper left')
ax2.grid(True, axis='y', linestyle=':', alpha=0.7)
ax2.xaxis.set_major_locator(mdates.HourLocator(byhour=range(0,24,2)))
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
plt.xticks(rotation=45)
st.subheader("System Imbalance")
st.pyplot(fig2)

# --- PLOT 3: IGCC and aFRR volumes ---
fig3, ax3 = plt.subplots(figsize=(12, 4))
ax3.step(df127['datetime'], df127['igccvolumeup'], where='post', label='IGCC +', lw=2)
ax3.step(df127['datetime'], -df127['igccvolumedown'], where='post', label='IGCC -', lw=2)
ax3.step(df127['datetime'], df127['afrrvolumeup'], where='post', label='aFRR +', lw=2)
ax3.step(df127['datetime'], -df127['afrrvolumedown'], where='post', label='aFRR -', lw=2)
ax3.set_ylabel('IGCC / aFRR (+/-)')
ax3.legend(loc='upper left')
ax3.grid(True, axis='y', linestyle=':', alpha=0.7)
ax3.xaxis.set_major_locator(mdates.HourLocator(byhour=range(0,24,2)))
ax3.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
plt.xticks(rotation=45)
st.subheader("IGCC and aFRR Volumes")
st.pyplot(fig3)

# --- PLOT 4: mFRR & Reserve Sharing ---
fig4, ax4 = plt.subplots(figsize=(12, 4))
ax4.step(df127['datetime'], df127['mfrrsaup'], where='post', label='mFRR SA +', lw=2)
ax4.step(df127['datetime'], -df127['mfrrsadown'], where='post', label='mFRR SA -', lw=2)
ax4.step(df127['datetime'], df127['mfrrdaup'], where='post', label='mFRR DA +', lw=2)
ax4.step(df127['datetime'], -df127['mfrrdadown'], where='post', label='mFRR DA -', lw=2)
ax4.step(df127['datetime'], df127['reserve_sharing_import'], where='post', label='Reserve +', lw=2)
ax4.step(df127['datetime'], -df127['reserve_sharing_export'], where='post', label='Reserve -', lw=2)
ax4.set_ylabel('mFRR / Reserve Sharing')
ax4.legend(loc='upper left', ncol=2)
ax4.grid(True, axis='y', linestyle=':', alpha=0.7)
ax4.xaxis.set_major_locator(mdates.HourLocator(byhour=range(0,24,2)))
ax4.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
plt.xticks(rotation=45)
st.subheader("mFRR and Reserve Sharing")
st.pyplot(fig4)

# --- PLOT 5: Available aFRR ---
fig5, ax5 = plt.subplots(figsize=(12, 4))
ax5.step(df152['datetime'], df152['upwardavailableafrrvol'], where='post', label='Available aFRR up', lw=2, c='tab:green')
ax5.step(df152['datetime'], df152['downwardavailableafrrvol'], where='post', label='Available aFRR down', lw=2, c='tab:red')
ax5.set_ylabel('Available aFRR (MW)')
ax5.legend(loc='upper left')
ax5.grid(True, axis='y', linestyle=':', alpha=0.7)
ax5.xaxis.set_major_locator(mdates.HourLocator(byhour=range(0,24,2)))
ax5.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
ax5.set_xlabel('Hour of Day')
plt.xticks(rotation=45)
st.subheader("Available aFRR")
st.pyplot(fig5)

# --- PLOT 6: Cap and Floor Price from ods166 ---
fig6, ax6 = plt.subplots(figsize=(12, 4))
ax6.step(df166['datetime'], df166['cap'], where='post', label='Cap', lw=2, color='tab:blue')
ax6.step(df166['datetime'], df166['floorprice'], where='post', label='Floor Price', lw=2, color='tab:red')
ax6.set_ylabel('Cap / Floor Price (€/MWh)')
ax6.set_xlabel('Hour of Day')
ax6.legend(loc='upper left')
ax6.grid(True, axis='y', linestyle=':', alpha=0.7)
ax6.xaxis.set_major_locator(mdates.HourLocator(byhour=range(0,24,2)))
ax6.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
plt.xticks(rotation=45)
st.subheader("Cap and Floor Price (ods166)")
st.pyplot(fig6)
