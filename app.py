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

import Device as D
from Ui import LaserStackApp, ROLE

st.set_page_config(page_title="GeSn Laser Stack Viewer", layout="wide")
st.title("GeSn Diode Laser – Layer Stack & Band Structure")


def build_device(sn_frac, si_frac):
    """Rebuild the layers that sit on/above the active layer for a new composition.

    Substrate, buffer and graded buffer do not depend on the active layer, so the
    originals from Device.py are reused. Cap and top contact are strained against
    the active layer, so they must be recreated.
    """
    comp = {"Ge": round(1.0 - sn_frac - si_frac, 6)}
    if si_frac > 0:
        comp["Si"] = si_frac
    if sn_frac > 0:
        comp["ASn"] = sn_frac

    sub, buf, grd = D.substrate_layer, D.buffer_layer, D.graded_buffer_layer
    active = D.ActiveLayer(
        name="Layer 3", thickness_nm=D.active_layer.thickness_nm,
        material=D.Material(comp),
        underlying_layer_0=sub, underlying_layer_1=buf, underlying_layer_2=grd,
        doping=D.active_layer.doping,
    )
    cap = D.CapLayer(
        name="Layer 4", thickness_nm=D.cap_layer.thickness_nm,
        material=D.cap_layer.material,
        underlying_layer_0=sub, underlying_layer_1=buf, underlying_layer_2=grd,
        underlying_layer_3=active, doping=D.cap_layer.doping,
    )
    top = D.TopContactLayer(
        name="Layer 5", thickness_nm=D.topContact_layer.thickness_nm,
        material=D.topContact_layer.material,
        underlying_layer_0=sub, underlying_layer_1=buf, underlying_layer_2=grd,
        underlying_layer_3=active, underlying_layer_4=cap,
        doping=D.topContact_layer.doping,
    )

    dev = D.Device(D.laser_diode.name)
    dev.add_Substratelayer(sub)
    dev.add_Bufferlayer(buf)
    dev.add_GradedBufferlayer(grd)
    dev.add_Activelayer(active)
    dev.add_Caplayer(cap)
    dev.add_TopContactlayer(top)
    return dev


names = [f"{l.name} · {ROLE[type(l)][0]}" for l in D.laser_diode.layers]

# ---- Sidebar controls (replace click / drag / arrow keys) ----
st.sidebar.header("Controls")
default_idx = next((i for i, n in enumerate(names) if "Active" in n), 0)
choice = st.sidebar.selectbox("Selected layer", names, index=default_idx)
az = st.sidebar.slider("Rotate (azimuth)", -180, 180, -35)
el = st.sidebar.slider("Tilt (elevation)", 4, 80, 24)

st.sidebar.header("Active layer composition")
sn_pct = st.sidebar.slider("Sn (%)", 0.0, 25.0, 11.0, 0.5)
si_pct = st.sidebar.slider("Si (%)", 0.0, 10.0, 0.0, 0.5)
ge_pct = 100.0 - sn_pct - si_pct
st.sidebar.markdown(
    f"**Ge = {ge_pct:.1f} %**  (set automatically)  \n"
    f"Ge$_{{{ge_pct/100:.3f}}}$Sn$_{{{sn_pct/100:.3f}}}$"
    + (f"Si$_{{{si_pct/100:.3f}}}$" if si_pct > 0 else "")
)


@st.cache_data(show_spinner=False)
def render(selected, az, el, sn_pct, si_pct):
    """Draw the figure and return (png_bytes, xlsx_bytes). Cached per input."""
    device = build_device(sn_pct / 100.0, si_pct / 100.0)
    ui = LaserStackApp(device)
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
png_bytes, xlsx_bytes = render(selected, az, el, sn_pct, si_pct)

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
