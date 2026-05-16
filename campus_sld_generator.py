"""
campus_sld_generator.py
=======================
Generates a publication-quality Single-Line Diagram (SLD) of the campus
distribution network using matplotlib. Works WITHOUT PSS®E installed.

Run:
    python campus_sld_generator.py

Outputs:
    campus_sld_academic.png    (300 dpi, ready for report/paper)
    campus_sld_residential.png
    campus_sld_combined.png

Author  : M.Tech Intern
Requires: pip install matplotlib numpy
"""

import math
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch, Arc, Circle, FancyBboxPatch
from matplotlib.lines import Line2D
import numpy as np

matplotlib.rcParams['font.family']  = 'DejaVu Sans'
matplotlib.rcParams['font.size']    = 8
matplotlib.rcParams['axes.linewidth'] = 0.5

# ─── Colour palette ─────────────────────────────────────────────────────────
C_BUS_HV   = '#C0392B'   # 33 kV / 11 kV bus bar (red)
C_BUS_LV   = '#2980B9'   # 0.4 kV bus bar (blue)
C_LINE     = '#2C3E50'   # feeder lines (dark)
C_TX_CORE  = '#E67E22'   # transformer circle (orange)
C_TX_BODY  = '#FDEBD0'   # transformer fill
C_SOLAR    = '#27AE60'   # solar generator (green)
C_LOAD     = '#8E44AD'   # load arrow (purple)
C_GRID     = '#C0392B'   # grid symbol (red)
C_TEXT_DIM = '#7F8C8D'   # dimension labels
C_BG       = '#FAFAFA'


# ─── Drawing primitives ─────────────────────────────────────────────────────

def draw_busbar(ax, x, y, width, color=C_BUS_LV, linewidth=3):
    """Draw a horizontal busbar."""
    ax.plot([x, x + width], [y, y], color=color, linewidth=linewidth,
            solid_capstyle='butt', zorder=3)


def draw_transformer(ax, x, y, label='', kva='', color=C_TX_CORE):
    """Draw two overlapping circles representing a 2-winding transformer."""
    r = 0.18
    # Upper circle (HV winding)
    circ1 = Circle((x, y + r * 0.8), r, fill=True,
                    facecolor=C_TX_BODY, edgecolor=color, linewidth=1.5, zorder=5)
    # Lower circle (LV winding)
    circ2 = Circle((x, y - r * 0.8), r, fill=True,
                    facecolor=C_TX_BODY, edgecolor=color, linewidth=1.5, zorder=5)
    ax.add_patch(circ1)
    ax.add_patch(circ2)
    if label:
        ax.text(x + 0.32, y, label, va='center', ha='left',
                fontsize=7, color=C_LINE, fontweight='bold')
    if kva:
        ax.text(x + 0.32, y - 0.22, kva, va='center', ha='left',
                fontsize=6, color=C_TEXT_DIM)


def draw_load_arrow(ax, x, y, label='', amps=''):
    """Draw a downward-pointing filled arrow representing a load."""
    ax.annotate('', xy=(x, y - 0.3), xytext=(x, y),
                arrowprops=dict(arrowstyle='->', color=C_LOAD,
                                lw=1.5, mutation_scale=10))
    if label:
        ax.text(x + 0.08, y - 0.15, label, va='center', fontsize=6,
                color=C_LOAD)
    if amps:
        ax.text(x - 0.08, y - 0.05, amps, va='center', ha='right',
                fontsize=6, color=C_TEXT_DIM)


def draw_solar_gen(ax, x, y, label='', kw=''):
    """Draw a circle with 'PV' label representing a solar generator."""
    circ = Circle((x, y), 0.16, fill=True,
                   facecolor='#EAFAF1', edgecolor=C_SOLAR, linewidth=1.5, zorder=5)
    ax.add_patch(circ)
    ax.text(x, y, 'PV', va='center', ha='center',
            fontsize=6, color=C_SOLAR, fontweight='bold', zorder=6)
    if label:
        ax.text(x + 0.22, y + 0.1, label, fontsize=6, color=C_SOLAR)
    if kw:
        ax.text(x + 0.22, y - 0.1, kw, fontsize=6, color=C_TEXT_DIM)


def draw_grid_symbol(ax, x, y):
    """Draw utility grid symbol (circle with X)."""
    r = 0.22
    circ = Circle((x, y), r, fill=True,
                   facecolor='#FDEDEC', edgecolor=C_GRID, linewidth=2, zorder=5)
    ax.add_patch(circ)
    ax.plot([x - r*0.6, x + r*0.6], [y + r*0.6, y - r*0.6],
            color=C_GRID, linewidth=1.2, zorder=6)
    ax.plot([x - r*0.6, x + r*0.6], [y - r*0.6, y + r*0.6],
            color=C_GRID, linewidth=1.2, zorder=6)


def draw_breaker(ax, x, y, closed=True):
    """Draw a circuit breaker symbol (small square on line)."""
    sq = FancyBboxPatch((x - 0.05, y - 0.05), 0.1, 0.1,
                          boxstyle="square,pad=0",
                          facecolor='white' if closed else 'white',
                          edgecolor=C_LINE, linewidth=1.0, zorder=7)
    ax.add_patch(sq)
    if not closed:  # open breaker – diagonal line
        ax.plot([x - 0.05, x + 0.05], [y - 0.05, y + 0.05],
                color=C_LINE, linewidth=0.8, zorder=8)


def vline(ax, x, y1, y2, color=C_LINE, lw=1.2, ls='-'):
    ax.plot([x, x], [y1, y2], color=color, linewidth=lw, linestyle=ls, zorder=2)


def hline(ax, x1, x2, y, color=C_LINE, lw=1.2, ls='-'):
    ax.plot([x1, x2], [y, y], color=color, linewidth=lw, linestyle=ls, zorder=2)


# ─── RESIDENTIAL AREA SLD ───────────────────────────────────────────────────

def draw_residential_sld():
    fig, ax = plt.subplots(figsize=(16, 22))
    ax.set_facecolor(C_BG)
    fig.patch.set_facecolor(C_BG)
    ax.set_xlim(-1, 15)
    ax.set_ylim(-1, 22)
    ax.axis('off')
    ax.set_aspect('equal')

    # ── Title ────────────────────────────────────────────────────────────────
    ax.text(7, 21.5, 'CAMPUS DISTRIBUTION NETWORK',
            ha='center', va='center', fontsize=14, fontweight='bold', color=C_LINE)
    ax.text(7, 21.1, 'RESIDENTIAL AREA  —  Single-Line Diagram',
            ha='center', va='center', fontsize=10, color=C_TEXT_DIM)

    # ── 33 kV grid entry (top-centre) ────────────────────────────────────────
    gx, gy = 7.0, 20.5
    draw_grid_symbol(ax, gx, gy)
    ax.text(gx, gy + 0.4, 'UTILITY GRID  33 kV', ha='center',
            fontsize=8, fontweight='bold', color=C_GRID)

    # 33 kV busbar
    vline(ax, gx, gy - 0.22, gy - 0.7)
    draw_busbar(ax, 5.5, 19.1, 3.0, color=C_BUS_HV, linewidth=4)
    vline(ax, gx, gy - 0.7, 19.1)
    ax.text(5.3, 19.1, '33 kV Bus', ha='right', va='center',
            fontsize=7, color=C_BUS_HV, fontweight='bold')

    # 33/11 kV main transformer
    vline(ax, gx, 18.5, 19.1)
    draw_transformer(ax, gx - 0.2, 17.9, label='Main Substation', kva='33/11 kV')
    vline(ax, gx, 17.2, 18.5)

    # 11 kV main busbar
    draw_busbar(ax, 2.0, 16.8, 10.0, color=C_BUS_HV, linewidth=3)
    vline(ax, gx, 16.8, 17.2)
    ax.text(1.8, 16.8, '11 kV  Residential Bus', ha='right', va='center',
            fontsize=7, color=C_BUS_HV, fontweight='bold')

    # ── Define each distribution transformer block ────────────────────────────
    # Each entry: (tap_x, y_start, name, kva, loads_list, solar_kw)
    # tap_x: x position where the 11kV tap connects
    # loads_list: [(label, amps), ...]

    transformers = [
        # Left side (x < 7)
        (3.0, 15.5, 'C-Type\nQuarter',    '250 kVA\n11/0.4 kV',
         [('H-Type H1-H40', '250A'), ('C-Type & MHS', '250A'),
          ('H-Type H41-H52', '250A')],   0),

        (4.5, 13.0, 'Arobindo\nHostel-1', '500 kVA\n11/0.4 kV',
         [('C-Block', '400A'), ('Emergency', '200A'),
          ('A-Block', '200A'), ('C-Block-2', '200A'),
          ('A-Block-2', '630A')],        100),

        (3.0, 10.0, 'Vinodini\nHostel-1', '500 kVA\n11/0.4 kV',
         [('AMF OUT', '400A'), ('SCADA', '250A'),
          ('Old Girls Hostel', '630A')],  50),

        (4.5, 7.5,  'Shopping\nComplex',  '250 kVA\n11/0.4 kV',
         [('Shop-1', '250A'), ('Shop-2', '250A'),
          ('Shop-3', '250A')],            0),

        (3.0, 5.0,  'Aacharya\nBhawan-1', '1000 kVA\n11/0.4 kV',
         [('APFC', '400A'), ('Neelam', '400A'),
          ('Gomed', '400A'), ('Pukhraj', '630A')], 50),

        (4.5, 2.0,  'Aacharya\nBhawan-3', '1000 kVA\n11/0.4 kV',
         [('Manakya', '400A'), ('Moti', '400A'),
          ('Moonga', '400A'), ('Panna', '630A')],  0),

        # Right side (x > 7)
        (9.0, 15.5, 'Hostel-7',           '500 kVA\n11/0.4 kV',
         [('Hostel-1', '250A'), ('Hostel-2', '250A'),
          ('Hostel-3', '250A'), ('Hostel-4', '250A')], 0),

        (10.5, 13.0,'Arobindo\nHostel-2', '500 kVA\n11/0.4 kV',
         [('G-Block', '630A'), ('E-Block', '630A'),
          ('Hostel-6', '200A'), ('G-Block-2', '200A'),
          ('E-Block-2', '400A')],         0),

        (9.0, 10.0, 'Vinodini\nHostel-2', '500 kVA\n11/0.4 kV',
         [('LT Load', '630A'), ('APF', '400A'),
          ('Internal', '400A'), ('Gargi Hostel', '250A')], 0),

        (10.5, 7.5, 'Staff Gate',         '315 kVA\n11/0.4 kV',
         [('Gate-1', '250A'), ('Gate-2', '250A'),
          ('Gate-3', '250A'), ('Gate-4', '250A')],  0),

        (9.0, 5.0,  'Aacharya\nBhawan-2', '1000 kVA\n11/0.4 kV',
         [('AB2-Load1', '630A'), ('AB2-Load2', '630A'),
          ('AB2-Load3', '400A'), ('AB2-Load4', '400A')], 0),
    ]

    for (tap_x, y0, name, kva, loads, solar_kw) in transformers:
        # Vertical drop from 11 kV bus to transformer
        vline(ax, tap_x, 16.8, y0 + 0.8)
        draw_breaker(ax, tap_x, y0 + 0.7)
        vline(ax, tap_x, y0 + 0.3, y0 + 0.6)

        # Transformer symbol
        draw_transformer(ax, tap_x - 0.2, y0, label=name, kva=kva)

        # LV busbar below transformer
        lv_y = y0 - 0.55
        vline(ax, tap_x, lv_y + 0.3, y0 - 0.3)
        lv_width = max(len(loads) * 0.9, 1.5)
        lv_x0    = tap_x - lv_width / 2
        draw_busbar(ax, lv_x0, lv_y, lv_width, color=C_BUS_LV, linewidth=2)

        # Load taps
        load_xs = np.linspace(lv_x0 + 0.2, lv_x0 + lv_width - 0.2, len(loads))
        for i, (ld_name, ld_amps) in enumerate(loads):
            vline(ax, load_xs[i], lv_y, lv_y - 0.2)
            draw_load_arrow(ax, load_xs[i], lv_y - 0.2,
                            label=ld_name, amps=ld_amps)

        # Solar generator (if any)
        if solar_kw > 0:
            sx = lv_x0 - 0.6
            vline(ax, sx, lv_y, lv_y + 0.2, color=C_SOLAR, lw=1)
            hline(ax, sx, lv_x0, lv_y, color=C_SOLAR, lw=1)
            draw_solar_gen(ax, sx, lv_y + 0.38, label='Rooftop PV',
                            kw=f'{solar_kw} kW')

    # ── Legend ────────────────────────────────────────────────────────────────
    legend_x, legend_y = 0.0, 4.0
    items = [
        (C_BUS_HV, '━━', '33/11 kV Busbar'),
        (C_BUS_LV, '━━', '0.4 kV Busbar'),
        (C_LINE,   '—', 'Feeder/Connection'),
        (C_LOAD,   '→', 'Load (feeder)'),
        (C_SOLAR,  '⊙', 'Solar PV Plant'),
        (C_TX_CORE,'○○', 'Transformer'),
        (C_GRID,   '✕', 'Utility Grid'),
    ]
    ax.text(legend_x, legend_y + 0.4, 'LEGEND', fontsize=8,
            fontweight='bold', color=C_LINE)
    for i, (col, sym, desc) in enumerate(items):
        ax.text(legend_x, legend_y - i*0.4,
                f'{sym}  {desc}', fontsize=6.5, color=col)

    # ── Note box ─────────────────────────────────────────────────────────────
    note = ("NOTE: Feeder ampere ratings shown on load arrows.\n"
            "Transformer rated current at 0.4 kV: I = kVA/(√3×0.4).\n"
            "Solar PV plants modelled as negative loads in PSS®E (unity PF).")
    ax.text(7, 0.6, note, ha='center', fontsize=6, color=C_TEXT_DIM,
            style='italic', bbox=dict(boxstyle='round,pad=0.4',
                                      facecolor='#EBF5FB', alpha=0.8))

    plt.tight_layout(pad=0.5)
    out_file = 'campus_sld_residential.png'
    plt.savefig(out_file, dpi=300, bbox_inches='tight',
                facecolor=C_BG)
    print(f"[SAVED] {out_file}")
    return fig


# ─── ACADEMIC AREA SLD ──────────────────────────────────────────────────────

def draw_academic_sld():
    fig, ax = plt.subplots(figsize=(16, 18))
    ax.set_facecolor(C_BG)
    fig.patch.set_facecolor(C_BG)
    ax.set_xlim(-1, 15)
    ax.set_ylim(-1, 18)
    ax.axis('off')
    ax.set_aspect('equal')

    ax.text(7, 17.5, 'CAMPUS DISTRIBUTION NETWORK',
            ha='center', va='center', fontsize=14, fontweight='bold', color=C_LINE)
    ax.text(7, 17.1, 'ACADEMIC AREA  —  Single-Line Diagram',
            ha='center', va='center', fontsize=10, color=C_TEXT_DIM)

    # Grid + 33 kV bus
    gx, gy = 7.0, 16.5
    draw_grid_symbol(ax, gx, gy)
    ax.text(gx, gy + 0.4, 'UTILITY GRID  33 kV', ha='center',
            fontsize=8, fontweight='bold', color=C_GRID)
    vline(ax, gx, gy - 0.22, gy - 0.7)
    draw_busbar(ax, 5.5, 15.1, 3.0, color=C_BUS_HV, linewidth=4)
    vline(ax, gx, gy - 0.7, 15.1)

    # 33/11 kV transformer
    vline(ax, gx, 14.5, 15.1)
    draw_transformer(ax, gx - 0.2, 13.9, label='Main Substation', kva='33/11 kV')
    vline(ax, gx, 13.2, 14.5)

    # 11 kV academic bus
    draw_busbar(ax, 1.5, 12.8, 11.0, color=C_BUS_HV, linewidth=3)
    vline(ax, gx, 12.8, 13.2)
    ax.text(1.3, 12.8, '11 kV  Academic Bus', ha='right', va='center',
            fontsize=7, color=C_BUS_HV, fontweight='bold')

    # Distribution transformers
    academic_txs = [
        (2.5, 11.2, 'EE\nDept', '500 kVA\n11/0.4 kV',
         [('EE Main', '400A'), ('EE Labs', '250A'), ('Workshop', '100A')], 50),

        (4.5, 11.2, 'Mech\nDept', '500 kVA\n11/0.4 kV',
         [('Mech Main', '400A'), ('Workshop', '250A'), ('Hydraulics', '100A')], 0),

        (6.5, 11.2, 'CS\nDept', '500 kVA\n11/0.4 kV',
         [('CS Main', '400A'), ('CS Labs', '250A'), ('Infra', '100A')], 50),

        (8.5, 11.2, 'ECE\nDept', '250 kVA\n11/0.4 kV',
         [('ECE Main', '200A'), ('ECE Labs', '150A')], 0),

        (10.5, 11.2, 'Library', '250 kVA\n11/0.4 kV',
         [('Library', '200A'), ('Library AC', '150A')], 100),

        (12.5, 11.2, 'Admin\nBlock', '315 kVA\n11/0.4 kV',
         [('Admin Main', '300A'), ('Admin UPS', '200A')], 0),
    ]

    for (tap_x, y0, name, kva, loads, solar_kw) in academic_txs:
        vline(ax, tap_x, 12.8, y0 + 0.8)
        draw_breaker(ax, tap_x, y0 + 0.7)
        vline(ax, tap_x, y0 + 0.3, y0 + 0.6)
        draw_transformer(ax, tap_x - 0.2, y0, label=name, kva=kva)
        lv_y     = y0 - 0.55
        lv_width = max(len(loads) * 1.0, 1.8)
        lv_x0    = tap_x - lv_width / 2
        vline(ax, tap_x, lv_y + 0.3, y0 - 0.3)
        draw_busbar(ax, lv_x0, lv_y, lv_width, color=C_BUS_LV, linewidth=2)

        load_xs = np.linspace(lv_x0 + 0.2, lv_x0 + lv_width - 0.2, len(loads))
        for i, (ld_name, ld_amps) in enumerate(loads):
            vline(ax, load_xs[i], lv_y, lv_y - 0.2)
            draw_load_arrow(ax, load_xs[i], lv_y - 0.2,
                            label=ld_name, amps=ld_amps)

        if solar_kw > 0:
            sx = lv_x0 - 0.5
            hline(ax, sx, lv_x0, lv_y, color=C_SOLAR, lw=1)
            draw_solar_gen(ax, sx, lv_y + 0.2, kw=f'{solar_kw} kW')

    # ── Scenario annotation box ───────────────────────────────────────────────
    scenarios_txt = (
        "PSS®E Simulation Scenarios:\n"
        "S1 Base Case  │  S2 Peak Solar  │  S3 Peak Load\n"
        "S4 Night      │  S5 Net-Zero    │  S6 Over-Generation"
    )
    ax.text(7, 7.0, scenarios_txt, ha='center', fontsize=7,
            color=C_LINE, family='monospace',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#EBF5FB',
                      edgecolor=C_BUS_HV, alpha=0.9))

    plt.tight_layout(pad=0.5)
    out_file = 'campus_sld_academic.png'
    plt.savefig(out_file, dpi=300, bbox_inches='tight', facecolor=C_BG)
    print(f"[SAVED] {out_file}")
    return fig


# ─── COMBINED / OVERVIEW SLD ────────────────────────────────────────────────

def draw_combined_overview():
    """Simple overview showing both feeders from the 33 kV grid."""
    fig, ax = plt.subplots(figsize=(18, 10))
    ax.set_facecolor(C_BG)
    fig.patch.set_facecolor(C_BG)
    ax.set_xlim(-1, 18)
    ax.set_ylim(-1, 11)
    ax.axis('off')
    ax.set_aspect('equal')

    ax.text(8.5, 10.5, 'CAMPUS POWER DISTRIBUTION — OVERVIEW SLD',
            ha='center', fontsize=14, fontweight='bold', color=C_LINE)
    ax.text(8.5, 10.0, 'For PSS®E Load Flow Model  |  33 kV → 11 kV → 0.4 kV',
            ha='center', fontsize=9, color=C_TEXT_DIM)

    # ── Grid + 33 kV bus (centre-top) ────────────────────────────────────────
    gx, gy = 8.5, 9.0
    draw_grid_symbol(ax, gx, gy)
    ax.text(gx, gy + 0.5, 'UTILITY GRID (33 kV)', ha='center',
            fontsize=9, fontweight='bold', color=C_GRID)

    vline(ax, gx, gy - 0.22, gy - 0.6)
    draw_busbar(ax, 4.5, 7.8, 8.0, color=C_BUS_HV, linewidth=5)
    vline(ax, gx, 7.8, 8.4)
    ax.text(4.2, 7.8, '33 kV PCC', ha='right', va='center',
            fontsize=8, color=C_BUS_HV, fontweight='bold')

    # ── Academic feeder ──────────────────────────────────────────────────────
    ax_x = 5.5
    hline(ax, ax_x, ax_x, 7.8, color=C_BUS_HV)
    vline(ax, ax_x, 5.9, 7.8)
    draw_transformer(ax, ax_x - 0.2, 5.3, label='Academic\nSubstation',
                     kva='5 MVA  33/11 kV')
    vline(ax, ax_x, 4.1, 5.0)
    draw_busbar(ax, 1.0, 4.1, 5.5, color=C_BUS_HV, linewidth=3)
    ax.text(0.7, 4.1, '11 kV\nAcademic', ha='right', va='center',
            fontsize=7, color=C_BUS_HV, fontweight='bold')

    dept_labels = ['EE Dept\n500 kVA', 'Mech Dept\n500 kVA', 'CS Dept\n500 kVA',
                   'Library\n250 kVA', 'ECE Dept\n250 kVA', 'Admin\n315 kVA']
    dept_xs = np.linspace(1.3, 6.3, len(dept_labels))
    for dx, dlabel in zip(dept_xs, dept_labels):
        vline(ax, dx, 3.3, 4.1)
        draw_transformer(ax, dx - 0.2, 2.7, kva=dlabel)
        vline(ax, dx, 1.8, 2.3)
        draw_load_arrow(ax, dx, 1.8)

    # ── Residential feeder ───────────────────────────────────────────────────
    rx_x = 11.5
    vline(ax, rx_x, 5.9, 7.8)
    draw_transformer(ax, rx_x - 0.2, 5.3, label='Residential\nSubstation',
                     kva='5 MVA  33/11 kV')
    vline(ax, rx_x, 4.1, 5.0)
    draw_busbar(ax, 8.5, 4.1, 5.5, color=C_BUS_HV, linewidth=3)
    ax.text(8.3, 4.1, '11 kV\nResidential', ha='right', va='center',
            fontsize=7, color=C_BUS_HV, fontweight='bold')

    resi_labels = ["C-Type\n250kVA", "Arobindo1\n500kVA", "Hostel7\n500kVA",
                   "Vinodini1\n500kVA", "Arobindo2\n500kVA", "Aacharya1\n1000kVA",
                   "Aacharya2\n1000kVA"]
    resi_xs = np.linspace(8.8, 15.5, len(resi_labels))
    for dx, dlabel in zip(resi_xs, resi_labels):
        vline(ax, dx, 3.3, 4.1)
        draw_transformer(ax, dx - 0.2, 2.7, kva=dlabel)
        vline(ax, dx, 1.8, 2.3)
        draw_load_arrow(ax, dx, 1.8)

    # ── Solar PV symbols at select buses ─────────────────────────────────────
    for sx in [dept_xs[0], dept_xs[2], dept_xs[3]]:    # EE, CS, Library
        draw_solar_gen(ax, sx - 0.5, 4.1, kw='50–100 kW')
    for sx in [resi_xs[1], resi_xs[3]]:                # Arobindo, Vinodini
        draw_solar_gen(ax, sx - 0.5, 4.1, kw='50–100 kW')

    # ── Stats box ────────────────────────────────────────────────────────────
    stats = [
        "Model Statistics",
        f"Total Buses      : 25 (within 50-bus demo limit)",
        f"Transformers     : 2 × 5 MVA + 17 distribution",
        f"Load Buses       : 17 (at 0.4 kV)",
        f"Solar PV Plants  : 6 (distributed)",
        f"Scenarios Solved : 6",
    ]
    for i, s in enumerate(stats):
        ax.text(0.0, 0.8 - i * 0.4, s, fontsize=7,
                color=C_LINE if i == 0 else C_TEXT_DIM,
                fontweight='bold' if i == 0 else 'normal')

    plt.tight_layout(pad=0.5)
    out_file = 'campus_sld_combined.png'
    plt.savefig(out_file, dpi=300, bbox_inches='tight', facecolor=C_BG)
    print(f"[SAVED] {out_file}")
    return fig


# ─── MAIN ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Generating campus SLD diagrams...")
    print("-" * 45)

    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        print("[ERROR] Install dependencies:  pip install matplotlib numpy")
        raise

    draw_residential_sld()
    plt.close('all')

    draw_academic_sld()
    plt.close('all')

    draw_combined_overview()
    plt.close('all')

    print("\nAll SLD images generated at 300 dpi.")
    print("Open PNG files in any image viewer or include in your report.")
