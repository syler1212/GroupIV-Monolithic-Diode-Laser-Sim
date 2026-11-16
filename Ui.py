"""3D layer-stack UI & Publication Figure Generator for GeSn Diode Lasers.

- Large, high-visibility publication fonts (11pt - 14pt+).
- Bandgap energy and classification annotations rendered in bold black.
- Press 'P' or click 'Save Fig (P)' to export a 300 DPI publication figure.
"""

import math
import os
from datetime import datetime

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
from matplotlib.patches import Polygon, FancyBboxPatch, Rectangle
from matplotlib.path import Path

from Device import (
    laser_diode,
    SubstrateLayer,
    BufferLayer,
    GradedBufferLayer,
    ActiveLayer,
    CapLayer,
    TopContactLayer,
)

# --- Publication High-Visibility Palette ---
BG = "#ffffff"
PANEL = "#f8fafc"
EDGE = "#94a3b8"
TEXT_DARK = "#000000"       # Pure black for maximum contrast
TEXT_MUTED = "#334155"

ROLE = {
    SubstrateLayer: ("Substrate", "#475569"),
    BufferLayer: ("Buffer", "#1d4ed8"),
    GradedBufferLayer: ("Graded buffer", "#0f766e"),
    ActiveLayer: ("Active (gain)", "#b45309"),
    CapLayer: ("Cap", "#7e22ce"),
    TopContactLayer: ("Top contact", "#be185d"),
}

ELEMENT_ORDER = {"Si": 0, "Ge": 1, "ASn": 2}


def formula(comp):
    parts = []
    for el in sorted(comp, key=lambda e: ELEMENT_ORDER.get(e, 9)):
        frac = comp[el]
        if frac <= 0:
            continue
        sym = "Sn" if el == "ASn" else el
        parts.append(sym if abs(frac - 1.0) < 1e-9 else f"{sym}$_{{{frac:.2f}}}$")
    return "".join(parts)


def fmt_thickness(nm):
    return f"{nm / 1000:.0f} µm" if nm >= 10000 else f"{nm:.0f} nm"


def display_height(nm):
    return 0.24 + 0.34 * math.log10(1.0 + nm / 40.0)


def strain_word(e):
    if e > 1e-6:
        return "tensile"
    if e < -1e-6:
        return "compressive"
    return "unstrained"


def shade(hex_color, f):
    c = np.array(matplotlib_to_rgb(hex_color))
    return tuple(np.clip(c * f, 0, 1))


def matplotlib_to_rgb(hex_color):
    h = hex_color.lstrip("#")
    return [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]


class LaserStackApp:
    K_L = 1.0
    K_DELTA = 0.85
    K_MAX = 1.45
    CB_CURVATURE = 1.6
    VB_LH_CURVATURE = 1.8
    VB_HH_CURVATURE = 0.9
    VB_SO_CURVATURE = 1.2

    HALF_WIDTH = 1.15
    DEFAULT_VIEW = (-35.0, 24.0)

    def __init__(self, device):
        self.device = device
        self.layers = device.layers
        self.az, self.el = self.DEFAULT_VIEW

        self.selected = next(
            (i for i, l in enumerate(self.layers) if isinstance(l, ActiveLayer)), 0
        )
        self.hover = None

        self.z_ranges = []
        z = 0.0
        for l in self.layers:
            h = display_height(l.thickness_nm)
            self.z_ranges.append((z, z + h))
            z += h
        self.total_h = z

        self._press = None
        self._dragging = False
        self._faces = []
        self._label_slots = []
        self._label_x = 0.0

        # Balanced aspect ratio for large text
        self.fig = plt.figure(figsize=(14.0, 7.2))
        self.fig.patch.set_facecolor(BG)

        self.ax_stack = self.fig.add_axes((0.005, 0.02, 0.45, 0.94))
        self.ax_band = self.fig.add_axes((0.485, 0.45, 0.50, 0.47))
        self.ax_info = self.fig.add_axes((0.485, 0.03, 0.50, 0.34))

        # Title positioned directly above the band plot (Boosted to 14pt)
        self.title = self.fig.text(0.485, 0.955, "", color=TEXT_DARK, fontsize=13.5,
                                   va="center", ha="left", weight="bold")

        self.ui_prompt = self.fig.text(0.015, 0.97,
                      f"{device.name} · Click layer to inspect · Drag to rotate · 'P' Save Fig",
                      color=TEXT_MUTED, fontsize=9.5, va="center")

        # Export Excel Button
        self.ax_btn_e = self.fig.add_axes((0.36, 0.945, 0.09, 0.04))
        self.btn_export = Button(self.ax_btn_e, "Excel (E)", color="#f1f5f9", hovercolor="#e2e8f0")
        self.btn_export.label.set_color(TEXT_DARK)
        self.btn_export.label.set_fontsize(9.5)
        self.btn_export.on_clicked(lambda _e: self.export_xlsx())

        # Save Publication Figure Button
        self.ax_btn_p = self.fig.add_axes((0.245, 0.945, 0.11, 0.04))
        self.btn_pub = Button(self.ax_btn_p, "Save Fig (P)", color="#f1f5f9", hovercolor="#e2e8f0")
        self.btn_pub.label.set_color(TEXT_DARK)
        self.btn_pub.label.set_fontsize(9.5)
        self.btn_pub.on_clicked(lambda _e: self.save_publication_figure())

        self.status = self.fig.text(0.45, 0.925, "", color="#16a34a", fontsize=9.5,
                                    ha="right", va="top")

        c = self.fig.canvas
        c.mpl_connect("button_press_event", self._on_press)
        c.mpl_connect("button_release_event", self._on_release)
        c.mpl_connect("motion_notify_event", self._on_motion)
        c.mpl_connect("key_press_event", self._on_key)

        self.redraw_all()

    def _project(self, pts):
        pts = np.asarray(pts, dtype=float)
        az, el = np.radians(self.az), np.radians(self.el)
        xr = pts[:, 0] * np.cos(az) - pts[:, 1] * np.sin(az)
        yr = pts[:, 0] * np.sin(az) + pts[:, 1] * np.cos(az)
        sx = xr
        sy = yr * np.sin(el) + pts[:, 2] * np.cos(el)
        return np.column_stack([sx, sy])

    def _rot_normal(self, n):
        az = np.radians(self.az)
        return (n[0] * np.cos(az) - n[1] * np.sin(az),
                n[0] * np.sin(az) + n[1] * np.cos(az),
                n[2])

    def _box_faces(self, z0, z1):
        w = self.HALF_WIDTH
        return [
            ((0, 0, 1),  [(-w, -w, z1), (w, -w, z1), (w, w, z1), (-w, w, z1)]),
            ((1, 0, 0),  [(w, -w, z0), (w, w, z0), (w, w, z1), (w, -w, z1)]),
            ((-1, 0, 0), [(-w, -w, z0), (-w, w, z0), (-w, w, z1), (-w, -w, z1)]),
            ((0, 1, 0),  [(-w, w, z0), (w, w, z0), (w, w, z1), (-w, w, z1)]),
            ((0, -1, 0), [(-w, -w, z0), (w, -w, z0), (w, -w, z1), (-w, -w, z1)]),
        ]

    def draw_stack(self):
        ax = self.ax_stack
        ax.clear()
        ax.set_facecolor(BG)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_xlim(-2.4, 4.9)
        ax.set_ylim(-1.1, self.total_h * np.cos(np.radians(self.DEFAULT_VIEW[1])) + 1.8)

        self._faces = []
        el = np.radians(self.el)
        view = np.array([0.0, -np.cos(el), np.sin(el)])
        light = np.array([-0.5, -0.6, 0.8])
        light /= np.linalg.norm(light)

        sh = self._project([(-1.45, -1.45, 0), (1.45, -1.45, 0), (1.45, 1.45, 0), (-1.45, 1.45, 0)])
        ax.add_patch(Polygon(sh, closed=True, fc="#cbd5e1", ec="none", alpha=0.5, zorder=0))

        selected_faces = []
        for idx, layer in enumerate(self.layers):
            z0, z1 = self.z_ranges[idx]
            base = ROLE[type(layer)][1]
            is_sel = idx == self.selected
            is_hov = idx == self.hover and not is_sel

            for normal, verts in self._box_faces(z0, z1):
                n = self._rot_normal(normal)
                if float(np.dot(n, view)) <= 1e-9:
                    continue
                lam = max(0.0, float(np.dot(n, light)))
                f = 0.55 + 0.45 * lam
                if is_sel:
                    f = min(1.20, f * 1.15)
                elif is_hov:
                    f = min(1.10, f * 1.05)
                elif self.selected is not None:
                    f *= 0.75
                poly = self._project(verts)
                ax.add_patch(Polygon(poly, closed=True, fc=shade(base, f),
                                     ec="#ffffff", lw=1.0, zorder=2 + idx))
                self._faces.append((idx, poly))
                if is_sel:
                    selected_faces.append(poly)

        for poly in selected_faces:
            ax.add_patch(Polygon(poly, closed=True, fill=False, ec=TEXT_DARK,
                                 lw=2.6, zorder=50))

        self._draw_labels(ax)

        ax.annotate("", xy=(-2.1, 1.9), xytext=(-2.1, 0.3),
                    arrowprops=dict(arrowstyle="->", color=TEXT_MUTED, lw=1.5))
        ax.text(-2.1, 2.0, "growth", color=TEXT_MUTED, fontsize=9.5, ha="center", va="bottom", weight="bold")
        ax.text(-2.3, -1.0,
                "Slab heights log-scaled for display\n"
                f"(true total thickness: {self.device.total_thickness() / 1000:.1f} µm)",
                color=TEXT_MUTED, fontsize=8.5, va="bottom", ha="left")

    def _draw_labels(self, ax):
        w = self.HALF_WIDTH
        anchors = []
        for idx in range(len(self.layers)):
            z0, z1 = self.z_ranges[idx]
            zm = 0.5 * (z0 + z1)
            corners = self._project([(w, w, zm), (w, -w, zm), (-w, w, zm), (-w, -w, zm)])
            anchors.append(corners[np.argmax(corners[:, 0])])
        anchors = np.array(anchors)

        self._label_x = float(anchors[:, 0].max()) + 0.35
        gap = 0.63
        ys = anchors[:, 1].copy()
        order = np.argsort(ys)
        for k in range(1, len(order)):
            lo, hi = order[k - 1], order[k]
            if ys[hi] - ys[lo] < gap:
                ys[hi] = ys[lo] + gap

        self._label_slots = []
        for idx, layer in enumerate(self.layers):
            role, color = ROLE[type(layer)]
            is_sel = idx == self.selected
            is_hov = idx == self.hover

            ax.add_patch(Rectangle((self._label_x - 0.16, ys[idx] - 0.22), 0.08, 0.44,
                                   fc=color, ec=TEXT_DARK if is_sel else "none", lw=1.2,
                                   zorder=61))

            comp_txt = formula(layer.material.composition)
            if isinstance(layer, GradedBufferLayer):
                comp_txt = (f"{formula(layer.material_bottom.composition)} → "
                            f"{formula(layer.material_top.composition)}")
            line1 = f"{layer.name} · {role}"
            line2 = f"{comp_txt}   {fmt_thickness(layer.thickness_nm)}   {layer.doping}"

            # Boosted to 11pt and 9.5pt
            ax.text(self._label_x, ys[idx] + 0.10, line1,
                    color="white" if is_sel else TEXT_DARK,
                    fontsize=11.0, weight="bold" if is_sel else "semibold",
                    va="center", ha="left", zorder=62,
                    bbox=dict(boxstyle="round,pad=0.25", fc=color if is_sel else BG,
                              ec=color, lw=1.1, alpha=0.95) if (is_sel or is_hov) else None)
            ax.text(self._label_x + 0.01, ys[idx] - 0.16, line2,
                    color="#334155" if is_sel else TEXT_MUTED, fontsize=9.5,
                    weight="medium", va="center", ha="left", zorder=62)
            self._label_slots.append((idx, float(ys[idx]), gap / 2.0))

    def draw_band(self, L):
        ax = self.ax_band
        ax.clear()
        ax.set_facecolor(BG)
        
        # Boosted Axes Labels and Ticks
        ax.set_xlabel("Crystal Momentum, $k$", color=TEXT_DARK, fontsize=12.0, weight="bold")
        ax.set_ylabel("Energy (eV)  [unstrained VBM = 0]", color=TEXT_DARK, fontsize=11.5, weight="bold")
        ax.tick_params(colors=TEXT_DARK, labelsize=11.0, width=1.2)
        
        for sp in ax.spines.values():
            sp.set_color("#64748b")
            sp.set_linewidth(1.1)
        ax.axhline(0, color="#cbd5e1", lw=1.0, ls=":")
        ax.grid(True, color="#e2e8f0", linestyle="--", linewidth=0.7, alpha=0.9)

        e_gamma = L.gamma_conduction_valley
        e_L = L.L_conduction_valley
        e_delta = L.delta_conduction_valley
        lh, hh, so = (L.delta_E_light_hole_valance_band,
                      L.delta_E_heavy_hole_valance_band,
                      L.delta_E_so_valance_band)

        valleys = [("Γ", e_gamma, 0.0), ("L", e_L, self.K_L), ("Δ", e_delta, self.K_DELTA)]
        low_name, cbm_e, target_k = min(valleys, key=lambda v: v[1])
        top_vb = "LH" if lh >= hh else "HH"
        vbm_e = max(lh, hh)
        eg = cbm_e - vbm_e
        is_direct = low_name == "Γ"
        gap_type = "Direct" if is_direct else f"Indirect ({low_name})"

        k = np.linspace(-self.K_MAX, self.K_MAX, 500)

        for name, e0, curv, col_hi, col_lo, ls_lo in (
            ("LH", lh, self.VB_LH_CURVATURE, "#059669", "#10b981", "--"),
            ("HH", hh, self.VB_HH_CURVATURE, "#be185d", "#ec4899", "--"),
        ):
            top = top_vb == name
            ax.plot(k, e0 - curv * k ** 2, color=col_hi if top else col_lo,
                    lw=2.5 if top else 1.5, ls="-" if top else ls_lo,
                    label=f"{name} ({e0:+.3f} eV)")
        ax.plot(k, so - self.VB_SO_CURVATURE * k ** 2, color="#64748b", lw=1.3, ls=":",
                label=f"SO ({so:+.3f} eV)")

        def valley(name, e0, k0, color, mirror):
            low = name == low_name
            style = dict(color=color if low else "#94a3b8",
                         lw=2.8 if low else 1.3, ls="-" if low else "--")
            ax.plot(k, e0 + self.CB_CURVATURE * (k - k0) ** 2, label=f"{name} ({e0:+.3f} eV)", **style)
            if mirror:
                ax.plot(k, e0 + self.CB_CURVATURE * (k + k0) ** 2, **style)

        valley("Γ", e_gamma, 0.0, "#0284c7", False)
        valley("L", e_L, self.K_L, "#d97706", True)
        valley("Δ", e_delta, self.K_DELTA, "#7c3aed", True)

        # Arrow markers
        arrow = dict(arrowstyle="<->", color="#000000", lw=2.4, shrinkA=0, shrinkB=0)
        if is_direct:
            ax.annotate("", xy=(0, cbm_e), xytext=(0, vbm_e), arrowprops=arrow)
            tx, ha = 0.08, "left"
        else:
            ax.hlines(vbm_e, 0, target_k, colors="#000000", linestyles=":", lw=1.4, alpha=0.8)
            ax.annotate("", xy=(target_k, cbm_e), xytext=(target_k, vbm_e), arrowprops=arrow)
            ax.annotate("", xy=(target_k, cbm_e), xytext=(0, vbm_e),
                        arrowprops=dict(arrowstyle="->", color="#000000", lw=1.4, ls="--", alpha=0.6))
            tx, ha = (target_k - 0.06, "right") if target_k > 0.6 else (target_k + 0.06, "left")

        # BANDGAP ENERGY TEXT CHANGED TO PURE BLACK & 12pt BOLD
        txt = (f"Semimetallic overlap\nΔE = {eg:.3f} eV" if eg <= 0
               else f"E$_g$ = {eg:.3f} eV\n({gap_type}, {top_vb})")
        ax.text(tx, 0.5 * (cbm_e + vbm_e), txt, color="#000000", fontsize=12.0, weight="bold", va="center", ha=ha)

        ax.set_xlim(-self.K_MAX, self.K_MAX)
        ax.set_ylim(min(so - 0.45, -0.9), cbm_e + 2.0)
        ax.set_xticks([-self.K_L, 0, self.K_L])
        ax.set_xticklabels(["L", "Γ", "L"], color=TEXT_DARK, fontsize=12.5, weight="bold")
        
        # Legend font boosted to 9.5pt
        ax.legend(facecolor=PANEL, edgecolor="#94a3b8", labelcolor=TEXT_DARK,
                  loc="upper right", fontsize=9.5, ncol=2, framealpha=0.95)

        role, _ = ROLE[type(L)]
        comp_txt = formula(L.material.composition)
        self.title.set_text(f"{L.name} · {role}:  {comp_txt}   —   "
                            f"{gap_type} bandgap, E$_g$ = {eg:.3f} eV")

    def draw_info(self, L):
        ax = self.ax_info
        ax.clear()
        ax.axis("off")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.add_patch(FancyBboxPatch((0.0, 0.0), 1.0, 1.0, boxstyle="round,pad=0,rounding_size=0.03",
                                    fc=PANEL, ec=EDGE, transform=ax.transAxes))

        is_sub = isinstance(L, SubstrateLayer)
        role, color = ROLE[type(L)]
        hc = "n/a" if is_sub else ("∞ (matched)" if math.isinf(L.hc) else f"{L.hc:.1f} nm")
        ein = L.inplanestrain
        eout = L.outplanestrain

        # Data card body text boosted to 10.5pt bold monospace
        def block(title, rows, x):
            ax.text(x, 0.92, title, color=color, fontsize=11.5, weight="bold", va="top")
            body = "\n".join(f"{k:<13}{v:>14}" for k, v in rows)
            ax.text(x, 0.77, body, color=TEXT_DARK, fontsize=10.2, weight="bold", va="top",
                    family="monospace", linespacing=1.45)

        block("Layer", [
            ("Thickness", fmt_thickness(L.thickness_nm)),
            ("Doping", L.doping),
            ("a relaxed", f"{L.relaxed_lattice_constant:.4f} Å"),
            ("a in-plane", f"{L.final_lattice_constant_In_Plane:.4f} Å"),
            ("a out-plane", f"{L.final_lattice_constant_Out_Plane:.4f} Å"),
            ("C11 / C12", f"{L.C11:.0f}/{L.C12:.0f} GPa"),
        ], 0.02)

        block("Strain & relaxation", [
            ("Crit. thick.", hc),
            ("Relaxation R", f"{L.R * 100:.0f} %"),
            ("ε in-plane", f"{ein * 100:+.3f} %"),
            ("ε out-plane", f"{eout * 100:+.3f} %"),
            ("ε hydro", f"{L.epsilon_hydrostatic * 100:+.3f} %"),
            ("ε shear", f"{L.epsilon_shear * 100:+.3f} %"),
        ], 0.35)
        ax.text(0.35, 0.06, f"state: {strain_word(ein)}", color=TEXT_DARK, fontsize=10.5, weight="bold", va="bottom")

        block("Band edges (eV)", [
            ("Γ valley", f"{L.gamma_conduction_valley:+.3f}"),
            ("L valley", f"{L.L_conduction_valley:+.3f}"),
            ("Δ valley", f"{L.delta_conduction_valley:+.3f}"),
            ("LH", f"{L.delta_E_light_hole_valance_band:+.3f}"),
            ("HH", f"{L.delta_E_heavy_hole_valance_band:+.3f}"),
            ("SO", f"{L.delta_E_so_valance_band:+.3f}"),
        ], 0.68)
        ax.text(0.68, 0.06,
                f"Γ–L = {(L.gamma_conduction_valley - L.L_conduction_valley) * 1e3:+.0f} meV",
                color=TEXT_DARK, fontsize=10.5, weight="bold", va="bottom")

    def redraw_all(self):
        L = self.layers[self.selected]
        self.draw_stack()
        self.draw_band(L)
        self.draw_info(L)
        self.fig.canvas.draw_idle()

    def pick(self, x, y):
        if x is None or y is None:
            return None
        if x >= self._label_x - 0.25:
            for idx, yc, half in self._label_slots:
                if abs(y - yc) <= half:
                    return idx
            return None
        for idx, poly in reversed(self._faces):
            if Path(poly).contains_point((x, y)):
                return idx
        return None

    def _on_press(self, ev):
        if ev.inaxes is not self.ax_stack or ev.button != 1:
            return
        self._press = (ev.x, ev.y, self.az, self.el)
        self._dragging = False

    def _on_motion(self, ev):
        if ev.inaxes is not self.ax_stack:
            if self.hover is not None and self._press is None:
                self.hover = None
                self.draw_stack()
                self.fig.canvas.draw_idle()
            return
        if self._press is not None:
            x0, y0, az0, el0 = self._press
            dx, dy = ev.x - x0, ev.y - y0
            if not self._dragging and math.hypot(dx, dy) > 5:
                self._dragging = True
            if self._dragging:
                self.az = az0 - dx * 0.45
                self.el = float(np.clip(el0 + dy * 0.25, 4.0, 80.0))
                self.draw_stack()
                self.fig.canvas.draw_idle()
            return
        h = self.pick(ev.xdata, ev.ydata)
        if h != self.hover:
            self.hover = h
            self.draw_stack()
            self.fig.canvas.draw_idle()

    def _on_release(self, ev):
        was_drag = self._dragging
        self._press = None
        self._dragging = False
        if was_drag or ev.inaxes is not self.ax_stack or ev.button != 1:
            return
        idx = self.pick(ev.xdata, ev.ydata)
        if idx is not None and idx != self.selected:
            self.selected = idx
            self.redraw_all()

    def _on_key(self, ev):
        n = len(self.layers)
        if ev.key == "up":
            self.selected = min(n - 1, self.selected + 1)
            self.redraw_all()
        elif ev.key == "down":
            self.selected = max(0, self.selected - 1)
            self.redraw_all()
        elif ev.key in ("p", "P"):
            self.save_publication_figure()
        elif ev.key in ("e", "E"):
            self.export_xlsx()
        elif ev.key in ("r", "R"):
            self.az, self.el = self.DEFAULT_VIEW
            self.redraw_all()

    def save_publication_figure(self, filename="fig_solver_ui_2.jpg"):
        """Saves a 300 DPI high-contrast figure with UI buttons cleanly removed."""
        self.ax_btn_e.set_visible(False)
        self.ax_btn_p.set_visible(False)
        self.ui_prompt.set_visible(False)
        self.status.set_visible(False)

        path = os.path.abspath(filename)
        self.fig.savefig(path, dpi=300, facecolor=BG, bbox_inches="tight", pad_inches=0.08)

        self.ax_btn_e.set_visible(True)
        self.ax_btn_p.set_visible(True)
        self.ui_prompt.set_visible(True)
        self.status.set_visible(True)
        self._set_status(f"Exported: {os.path.basename(path)}", ok=True)
        print(f"Publication figure saved: {path}")

    def export_xlsx(self, path=None):
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill, Alignment
            from openpyxl.utils import get_column_letter
        except ImportError:
            self._set_status("Needs openpyxl: pip install openpyxl", ok=False)
            return None

        if path is None:
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe = "".join(ch if ch.isalnum() else "_" for ch in self.device.name)
            path = os.path.abspath(f"{safe}_{stamp}.xlsx")

        base = Font(name="Arial", size=10)
        bold = Font(name="Arial", size=10, bold=True)
        head_font = Font(name="Arial", size=10, bold=True, color="FFFFFF")
        head_fill = PatternFill("solid", fgColor="334155")

        wb = Workbook()
        ws = wb.active
        ws.title = "Layers"

        headers = [
            ("Layer", 10), ("Role", 15), ("Material", 24),
            ("Si fraction", 9), ("Ge fraction", 9), ("Sn fraction", 9),
            ("Thickness (nm)", 13), ("Doping", 11),
            ("Bandgap type", 16), ("Eg (eV)", 9),
            ("Gamma valley (eV)", 13), ("L valley (eV)", 12), ("Delta valley (eV)", 13),
            ("LH (eV)", 9), ("HH (eV)", 9), ("SO (eV)", 9),
            ("Gamma-L (meV)", 12), ("LH-HH (meV)", 12),
            ("a relaxed (A)", 12), ("a in-plane (A)", 12), ("a out-of-plane (A)", 14),
            ("C11 (GPa)", 10), ("C12 (GPa)", 10),
            ("Critical thickness (nm)", 16), ("Relaxation R", 12),
            ("In-plane strain", 13), ("Out-of-plane strain", 14),
            ("Hydrostatic strain", 14), ("Shear strain", 12), ("Strain state", 13),
        ]
        for c, (h, w) in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=c, value=h)
            cell.font, cell.fill = head_font, head_fill
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            ws.column_dimensions[get_column_letter(c)].width = w
        ws.row_dimensions[1].height = 32

        def plain_formula(comp):
            return " ".join(
                f"{'Sn' if el == 'ASn' else el}{frac:.2f}"
                for el, frac in sorted(comp.items(), key=lambda kv: ELEMENT_ORDER.get(kv[0], 9))
                if frac > 0
            )

        for r, L in enumerate(self.layers, start=2):
            comp = L.material.composition
            role = ROLE[type(L)][0]
            mat = plain_formula(comp)
            if isinstance(L, GradedBufferLayer):
                mat = (f"{plain_formula(L.material_bottom.composition)} -> "
                       f"{plain_formula(L.material_top.composition)}")
            if isinstance(L, SubstrateLayer):
                hc = "n/a"
            elif math.isinf(L.hc):
                hc = "inf (matched)"
            else:
                hc = round(L.hc, 3)

            row = [
                L.name, role, mat,
                comp.get("Si", 0.0), comp.get("Ge", 0.0), comp.get("ASn", 0.0),
                L.thickness_nm, L.doping,
                L.bandgap_type,
                f"=MIN(K{r}:M{r})-MAX(N{r}:O{r})",
                L.gamma_conduction_valley, L.L_conduction_valley, L.delta_conduction_valley,
                L.delta_E_light_hole_valance_band, L.delta_E_heavy_hole_valance_band,
                L.delta_E_so_valance_band,
                f"=(K{r}-L{r})*1000",
                f"=(N{r}-O{r})*1000",
                L.relaxed_lattice_constant, L.final_lattice_constant_In_Plane,
                L.final_lattice_constant_Out_Plane,
                L.C11, L.C12,
                hc, L.R,
                L.inplanestrain, L.outplanestrain,
                L.epsilon_hydrostatic, L.epsilon_shear,
                strain_word(L.inplanestrain),
            ]
            for c, v in enumerate(row, start=1):
                cell = ws.cell(row=r, column=c, value=v)
                cell.font = base
                if c in (4, 5, 6):
                    cell.number_format = "0.000"
                elif c == 7:
                    cell.number_format = "#,##0"
                elif c in (10, 11, 12, 13, 14, 15, 16):
                    cell.number_format = "0.000"
                elif c in (17, 18):
                    cell.number_format = "0.0"
                elif c in (19, 20, 21):
                    cell.number_format = "0.0000"
                elif c in (22, 23):
                    cell.number_format = "0.0"
                elif c == 24 and not isinstance(v, str):
                    cell.number_format = "#,##0.0"
                elif c == 25:
                    cell.number_format = "0.0%"
                elif c in (26, 27, 28, 29):
                    cell.number_format = "0.000%"
                if c in (1, 2):
                    cell.font = bold

        n = len(self.layers)
        notes = [
            "Notes",
            "Source: laser_diode in Device.py.",
            "Energies relative to layer unstrained valence-band max (= 0 eV).",
            "Eg = MIN(Gamma, L, Delta) - MAX(LH, HH).",
            "Strains: positive = tensile, negative = compressive.",
        ]
        for i, t in enumerate(notes):
            cell = ws.cell(row=n + 3 + i, column=1, value=t)
            cell.font = bold if i == 0 else Font(name="Arial", size=9, italic=True, color="555555")
        ws.freeze_panes = "B2"

        try:
            wb.save(path)
        except OSError as exc:
            self._set_status(f"Could not save: {exc}", ok=False)
            return None
        print(f"Exported: {path}")
        self._set_status(f"Saved {os.path.basename(path)}", ok=True)
        return path

    def _set_status(self, msg, ok=True):
        self.status.set_text(msg)
        self.status.set_color("#16a34a" if ok else "#dc2626")
        self.fig.canvas.draw_idle()

    def show(self):
        plt.show()


def start_ui():
    LaserStackApp(laser_diode).show()


if __name__ == "__main__":
    start_ui()