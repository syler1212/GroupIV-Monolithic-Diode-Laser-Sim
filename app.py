"""Streamlit web front-end for the GeSn diode laser stack viewer.

Reuses LaserStackApp from Ui.py (the matplotlib drawing code) unchanged:
the desktop mouse/keyboard controls are replaced by sidebar widgets.
"""

import os
import tempfile

import matplotlib

matplotlib.use("Agg")  # headless backend: required on a server
import matplotlib.pyplot as plt
import streamlit as st

from Device import laser_diode
from Ui import LaserStackApp, ROLE

st.set_page_config(page_title="GeSn Laser Stack Viewer", layout="wide")
st.title("GeSn Diode Laser – Layer Stack & Band Structure")

layers = laser_diode.layers
names = [f"{l.name} · {ROLE[type(l)][0]}" for l in layers]

# ---- Sidebar controls (replace click / drag / arrow keys) ----
st.sidebar.header("Controls")
default_idx = next((i for i, n in enumerate(names) if "Active" in n), 0)
choice = st.sidebar.selectbox("Selected layer", names, index=default_idx)
az = st.sidebar.slider("Rotate (azimuth)", -180, 180, -35)
el = st.sidebar.slider("Tilt (elevation)", 4, 80, 24)


@st.cache_data(show_spinner=False)
def render(selected, az, el):
    """Draw the figure and return (png_bytes, xlsx_bytes). Cached per input."""
    ui = LaserStackApp(laser_diode)
    ui.selected, ui.az, ui.el = selected, float(az), float(el)
    ui.redraw_all()

    with tempfile.TemporaryDirectory() as tmp:
        png_path = os.path.join(tmp, "fig.png")
        ui.save_publication_figure(png_path)  # 300 DPI, buttons hidden
        with open(png_path, "rb") as f:
            png = f.read()

        xlsx_path = ui.export_xlsx(os.path.join(tmp, "stack.xlsx"))
        xlsx = None
        if xlsx_path:
            with open(xlsx_path, "rb") as f:
                xlsx = f.read()

    plt.close(ui.fig)
    return png, xlsx


selected = names.index(choice)
png_bytes, xlsx_bytes = render(selected, az, el)

st.image(png_bytes, use_container_width=True)

c1, c2 = st.columns(2)
c1.download_button("Download figure (PNG)", png_bytes, "laser_stack.png", "image/png")
if xlsx_bytes:
    c2.download_button(
        "Download data (Excel)",
        xlsx_bytes,
        "laser_stack.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
