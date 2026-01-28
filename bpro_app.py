
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Cohort Map", layout="wide")
st.title("Cohort Map")

PASSWORD = "lifefindsaway"  # change this

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        password = st.text_input("Enter password", type="password")

        if password:
            if password == PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect password")
        return False

    return True


if check_password():
    st.success("Welcome 🎉")
    st.write("Your app content goes here")

# --- GitHub raw CSV URL ---
RAW_CSV_URL = "https://raw.githubusercontent.com/ankshah131/biomimicry/main/BPro%202024-2026%20Cohort%20Info%20-%20BPro%20Capstone.csv"

# --- Load data from GitHub ---
@st.cache_data
def load_data(url):
    df = pd.read_csv(url, dtype=str).fillna("")
    return df

df = load_data(RAW_CSV_URL)

# --- Fix coordinate formatting ---
def fix_minus(x: str) -> str:
    return x.replace("−", "-").strip()

df["Latitude"] = pd.to_numeric(df["Latitude"].astype(str).map(fix_minus), errors="coerce")
df["Longitude"] = pd.to_numeric(df["Longitude"].astype(str).map(fix_minus), errors="coerce")
df = df.dropna(subset=["Latitude", "Longitude"])

# --- Dropdown filter for Themes ---
theme_col = "Themes"
themes = sorted([t for t in df.get(theme_col, "").astype(str).unique() if t.strip() != ""])
selected = st.selectbox("Filter by Theme", ["All"] + themes)

if selected != "All":
    df = df[df[theme_col] == selected]

# --- Helper functions ---
def linkify(text: str, url: str) -> str:
    if not url:
        return ""
    return f'<a href="{url}" target="_blank" rel="noopener noreferrer">{text}</a>'

def ig_to_url(handle: str) -> str:
    handle = handle.strip()
    if not handle:
        return ""
    if handle.startswith("@"):
        handle = handle[1:]
    return f"https://www.instagram.com/{handle}"

# --- Build the map ---
if df.empty:
    st.warning("No points match this filter.")
else:
    center = [df["Latitude"].mean(), df["Longitude"].mean()]
    m = folium.Map(location=center, zoom_start=4, tiles="CartoDB positron")

    for _, r in df.iterrows():
        name = f"{r['First Name']} {r['Last Name']}".strip()
        birthday = r.get("Birthday", "").strip()
        city = r.get("City", "").strip()
        state = r.get("State", "").strip()
        country = r.get("Country", "").strip()
        theme = r.get("Themes", "").strip()
        linkedin = r.get("LinkedIn Profile", "").strip()
        ig = r.get("IG Profile", "").strip()
        capstone = r.get("BPro Capstone Project Topic", "").strip()
        support = r.get("Support Request from Cohort", "").strip()

        parts = [f"<b>{name}</b>"]
        if birthday:
            parts.append(f"🎂 {birthday}")
        loc_bits = " • ".join([b for b in [city, state, country] if b])
        if loc_bits:
            parts.append(f"📍 {loc_bits}")
        if theme:
            parts.append(f"🏷️ <i>{theme}</i>")

        links = []
        if linkedin:
            links.append(linkify("LinkedIn", linkedin))
        if ig:
            links.append(linkify("Instagram", ig_to_url(ig)))
        if links:
            parts.append(" | ".join(links))

        if capstone:
            parts.append(f"<b>Capstone:</b> {capstone}")
        if support:
            parts.append(f"<b>Support Request:</b> {support}")

        html = "<br>".join(parts)
        popup = folium.Popup(folium.IFrame(html=html, width=320, height=180), max_width=340)

        folium.Marker(
            location=[r["Latitude"], r["Longitude"]],
            popup=popup,
            tooltip=name or None,
            icon=folium.Icon(color="blue", icon="info-sign")
        ).add_to(m)

    st_folium(m, width=None, height=650)
