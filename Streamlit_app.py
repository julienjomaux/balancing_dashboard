import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import date, timedelta

# --- Streamlit UI ---
st.set_page_config(page_title="Elia Balancing and Imbalance Data (Opendata)", page_icon="GEM.webp")
st.caption(
    'This app downloads data from [Elia Open Data](https://opendata.elia.be/). It works for dates from 22 May 2024 onwards.'
)
default_date = date(2026, 1, 15)

# Calendar for date input
selected_date = st.date_input("Select a date", value=default_date)
date_str = selected_date.strftime("%Y-%m-%d")
prev_date = selected_date - timedelta(days=1)
prev_date_str = prev_date.strftime("%Y-%m-%d")

@st.cache_data(show_spinner=False)
def fetch(dataset, d):
    u = "https://opendata.elia.be/api/records/1.0/search/"
    p = {"dataset": dataset, "rows": 1000, "refine.datetime": d}
    r = requests.get(u, params=p)
    r.raise_for_status()
    return pd.DataFrame([rec['fields'] for rec in r.json().get("records", [])])

try:
    # Fetch today & previous day's data for all relevant datasets
    df134 = pd.concat([fetch("ods134", prev_date_str), fetch("ods134", date_str)], ignore_index=True)
    df127 = pd.concat([fetch("ods127", prev_date_str), fetch("ods127", date_str)], ignore_index=True)
    df152 = pd.concat([fetch("ods152", prev_date_str), fetch("ods152", date_str)], ignore_index=True)
    df166 = pd.concat([fetch("ods166", prev_date_str), fetch("ods166", date_str)], ignore_index=True)
    df013 = pd.concat([fetch("ods013", prev_date_str), fetch("ods013", date_str)], ignore_index=True)
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

# Convert to datetime and localize & convert to Brussels time
for df in [df134, df127, df152, df166]:
    df['datetime'] = pd.to_datetime(df['datetime'], utc=True).dt.tz_convert('Europe/Brussels')
    df.sort_values('datetime', inplace=True)

# Function to slice relevant range from 00:00 to 23:00 (for 0h–24h plot in localtime)
def slice_df(df, date_sel):
    """Get 00:00 (from previous day), and 01:00–00:00 (from selected date) in Brussels tz."""
    # Build boundaries
    tz = "Europe/Brussels"
    d0 = pd.Timestamp(date_sel, tz=tz)
    d1 = d0 + pd.Timedelta(hours=1)
    d24 = d0 + pd.Timedelta(days=1)
    # Last hour from day before (00:00 at selected date)
    prev_0h = df[df['datetime'] == d0]
    # 01:00–24:00 of selected date
    select_day = df[(df['datetime'] > d0) & (df['datetime'] <= d24)]
    return pd.concat([prev_0h, select_day])

df134p = slice_df(df134, selected_date)
df127p = slice_df(df127, selected_date)
df152p = slice_df(df152, selected_date)
df166p = slice_df(df166, selected_date)

st.write(df134p)

# --- PLOT 1: Imbalance price + alpha ---
fig1, ax1 = plt.subplots(figsize=(12, 4))
ax1.step(df134p['datetime'], df134p['imbalanceprice'], where='post', c='tab:blue', label='Imbalance Price', lw=2)
ax1.step(df134p['datetime'], df134p['alpha'], where='post', c='tab:gray', label='Alpha', lw=2, linestyle='--')
ax1.set_ylabel('Imbalance Price (€/MWh) / Alpha')
ax1.legend(loc='upper left')
ax1.grid(True, axis='y', linestyle=':', alpha=0.7)
ax1.xaxis.set_major_locator(mdates.HourLocator(byhour=range(0,25,2), tz='Europe/Brussels'))
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M', tz='Europe/Brussels'))
plt.xticks(rotation=45)
st.subheader("Imbalance Price and Alpha")
st.pyplot(fig1)

# --- PLOT 2: System imbalance ---
fig2, ax2 = plt.subplots(figsize=(12, 4))
ax2.step(df134p['datetime'], df134p['systemimbalance'], where='post', c='orange', label='System Imbalance', lw=2)
ax2.set_ylabel('System Imbalance')
ax2.legend(loc='upper left')
ax2.grid(True, axis='y', linestyle=':', alpha=0.7)
ax2.xaxis.set_major_locator(mdates.HourLocator(byhour=range(0,25,2), tz='Europe/Brussels'))
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M', tz='Europe/Brussels'))
plt.xticks(rotation=45)
st.subheader("System Imbalance")
st.pyplot(fig2)

# --- PLOT 3: IGCC and aFRR volumes ---
fig3, ax3 = plt.subplots(figsize=(12, 4))
ax3.step(df127p['datetime'], df127p['igccvolumeup'], where='post', label='IGCC +', lw=2)
ax3.step(df127p['datetime'], -df127p['igccvolumedown'], where='post', label='IGCC -', lw=2)
ax3.step(df127p['datetime'], df127p['afrrvolumeup'], where='post', label='aFRR +', lw=2)
ax3.step(df127p['datetime'], -df127p['afrrvolumedown'], where='post', label='aFRR -', lw=2)
ax3.set_ylabel('IGCC / aFRR (+/-)')
ax3.legend(loc='upper left')
ax3.grid(True, axis='y', linestyle=':', alpha=0.7)
ax3.xaxis.set_major_locator(mdates.HourLocator(byhour=range(0,25,2), tz='Europe/Brussels'))
ax3.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M', tz='Europe/Brussels'))
plt.xticks(rotation=45)
st.subheader("IGCC and aFRR Volumes")
st.pyplot(fig3)

# --- PLOT 4: mFRR & Reserve Sharing ---
fig4, ax4 = plt.subplots(figsize=(12, 4))
ax4.step(df127p['datetime'], df127p['mfrrsaup'], where='post', label='mFRR SA +', lw=2)
ax4.step(df127p['datetime'], -df127p['mfrrsadown'], where='post', label='mFRR SA -', lw=2)
ax4.step(df127p['datetime'], df127p['mfrrdaup'], where='post', label='mFRR DA +', lw=2)
ax4.step(df127p['datetime'], -df127p['mfrrdadown'], where='post', label='mFRR DA -', lw=2)
ax4.step(df127p['datetime'], df127p['reserve_sharing_import'], where='post', label='Reserve +', lw=2)
ax4.step(df127p['datetime'], -df127p['reserve_sharing_export'], where='post', label='Reserve -', lw=2)
ax4.set_ylabel('mFRR / Reserve Sharing')
ax4.legend(loc='upper left', ncol=2)
ax4.grid(True, axis='y', linestyle=':', alpha=0.7)
ax4.xaxis.set_major_locator(mdates.HourLocator(byhour=range(0,25,2), tz='Europe/Brussels'))
ax4.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M', tz='Europe/Brussels'))
plt.xticks(rotation=45)
st.subheader("mFRR and Reserve Sharing")
st.pyplot(fig4)

# --- PLOT 5: Available aFRR ---
fig5, ax5 = plt.subplots(figsize=(12, 4))
ax5.step(df152p['datetime'], df152p['upwardavailableafrrvol'], where='post', label='Available aFRR up', lw=2, c='tab:green')
ax5.step(df152p['datetime'], df152p['downwardavailableafrrvol'], where='post', label='Available aFRR down', lw=2, c='tab:red')
ax5.set_ylabel('Available aFRR (MW)')
ax5.legend(loc='upper left')
ax5.grid(True, axis='y', linestyle=':', alpha=0.7)
ax5.xaxis.set_major_locator(mdates.HourLocator(byhour=range(0,25,2), tz='Europe/Brussels'))
ax5.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M', tz='Europe/Brussels'))
plt.xticks(rotation=45)
st.subheader("Available aFRR")
st.pyplot(fig5)

# --- PLOT 6: Cap and Floor Price from ods166 ---
fig6, ax6 = plt.subplots(figsize=(12, 4))
ax6.step(df166p['datetime'], df166p['cap'], where='post', label='Cap', lw=2, color='tab:blue')
ax6.step(df166p['datetime'], df166p['floorprice'], where='post', label='Floor Price', lw=2, color='tab:red')
ax6.set_ylabel('Cap / Floor Price (€/MWh)')
ax6.legend(loc='upper left')
ax6.grid(True, axis='y', linestyle=':', alpha=0.7)
ax6.xaxis.set_major_locator(mdates.HourLocator(byhour=range(0,25,2), tz='Europe/Brussels'))
ax6.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M', tz='Europe/Brussels'))
plt.xticks(rotation=45)
st.subheader("Cap and Floor Price")
st.pyplot(fig6)

# --- NEW PLOTS: Available Transfer Capacity (ATC) for Import/Export ---
countries_to_plot = ["Germany", "France", "Netherlands"]
ods013_colnames = ['country', 'availabletransfercapacityatlastclosedgate', 'direction', 'datetime', 'resolutioncode']
if all(c in df013.columns for c in ods013_colnames):
    df013['datetime'] = pd.to_datetime(df013['datetime'], utc=True).dt.tz_convert('Europe/Brussels')
    df013.sort_values('datetime', inplace=True)
    df013p = slice_df(df013, selected_date)

    def plot_atc(direction, st_title):
        df_sel = df013p[
            (df013p['direction'].str.lower() == direction.lower()) & 
            (df013p['country'].isin(countries_to_plot))
        ]
        fig, ax = plt.subplots(figsize=(12, 4))
        for country in countries_to_plot:
            df_c = df_sel[df_sel['country'] == country]
            ax.step(df_c['datetime'], df_c['availabletransfercapacityatlastclosedgate'], where='post', label=country)
        ax.set_ylabel('ATC (MW)')
        ax.set_title(f"ATC ({direction}) for {', '.join(countries_to_plot)}")
        ax.legend(loc='upper left')
        ax.grid(True, axis='y', linestyle=':', alpha=0.7)
        ax.xaxis.set_major_locator(mdates.HourLocator(byhour=range(0,25,2), tz='Europe/Brussels'))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M', tz='Europe/Brussels'))
        plt.xticks(rotation=45)
        st.subheader(st_title)
        st.pyplot(fig)

    plot_atc("Import", "Available Transfer Capacity (Import) — DE, FR, NL")
    plot_atc("Export", "Available Transfer Capacity (Export) — DE, FR, NL")
else:
    st.warning("Some required data columns from ods013 are missing for the selected date, ATC plots not generated.")
