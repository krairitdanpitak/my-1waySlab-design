import streamlit as st
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# --- 1. Page Configuration ---
st.set_page_config(page_title="RC Slab Design Report", layout="wide")

# --- 2. Custom CSS (Styles for Report & Printing) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Sarabun', sans-serif;
    }

    /* Header Box */
    .header-box {
        border: 2px solid #000;
        padding: 15px;
        margin-bottom: 20px;
        background-color: #ffffff;
    }

    .report-title {
        text-align: center;
        font-weight: 700;
        font-size: 24px;
        margin-bottom: 5px;
        text-transform: uppercase;
    }

    .report-subtitle {
        text-align: center;
        font-weight: 600;
        font-size: 18px;
        margin-bottom: 15px;
        color: #333;
    }

    /* Table Styling */
    .calc-table {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Sarabun', sans-serif;
        font-size: 14px;
        margin-top: 10px;
        color: #000;
    }

    .calc-table th {
        background-color: #e0e0e0; /* Gray Header */
        border: 1px solid #000;
        padding: 8px;
        text-align: center;
        font-weight: bold;
    }

    .calc-table td {
        border: 1px solid #000;
        padding: 6px 8px;
        vertical-align: middle;
    }

    /* Column Widths */
    .col-item { width: 25%; font-weight: 600; }
    .col-formula { width: 20%; font-family: 'Courier New', monospace; font-size: 13px; color: #444; }
    .col-sub { width: 25%; font-family: 'Courier New', monospace; font-size: 13px; color: #222; }
    .col-result { width: 15%; text-align: center; font-weight: bold; }
    .col-unit { width: 8%; text-align: center; }
    .col-status { width: 7%; text-align: center; font-weight: bold; }

    /* Print Button */
    .print-btn-container {
        text-align: right; 
        margin-bottom: 10px;
    }
    .print-btn {
        background-color: #28a745;
        color: white;
        padding: 8px 16px;
        border: none;
        border-radius: 4px;
        text-decoration: none;
        font-weight: bold;
        cursor: pointer;
        font-size: 14px;
    }
    .print-btn:hover { background-color: #218838; }

    /* Print Media Query (Hide Sidebar & Elements) */
    @media print {
        [data-testid="stSidebar"] { display: none; }
        .stButton { display: none; }
        .print-btn-container { display: none; }
        footer { display: none; }
        header { display: none; }
        .block-container { padding-top: 0rem; padding-bottom: 0rem; }
    }
</style>
""", unsafe_allow_html=True)


# --- 3. Helper Function: Draw Slab Section ---
def draw_slab_schematic(L_m, h_cm, cover_cm, main_txt, temp_txt, support_type):
    fig, ax = plt.subplots(figsize=(10, 3.5))

    # Schematic Dimensions
    beam_w = 0.3
    slab_L = 4.0
    slab_h = 0.5

    # 1. Concrete Outline
    # Left Beam
    ax.add_patch(patches.Rectangle((0, -0.8), beam_w, 0.8, facecolor='white', edgecolor='black', linewidth=1.2))
    # Right Beam
    ax.add_patch(
        patches.Rectangle((slab_L + beam_w, -0.8), beam_w, 0.8, facecolor='white', edgecolor='black', linewidth=1.2))
    # Slab
    ax.add_patch(
        patches.Rectangle((0, 0), slab_L + 2 * beam_w, slab_h, facecolor='#f9f9f9', edgecolor='black', linewidth=1.2))

    # 2. Rebar Drawing
    pad = 0.05

    # Bottom Main Steel (Blue Line)
    ax.plot([pad, slab_L + 2 * beam_w - pad], [pad, pad], color='blue', linewidth=2, label='Main Bottom')
    # Hooks up
    ax.plot([pad, pad], [pad, pad + 0.2], color='blue', linewidth=2)
    ax.plot([slab_L + 2 * beam_w - pad, slab_L + 2 * beam_w - pad], [pad, pad + 0.2], color='blue', linewidth=2)

    # Top Steel (Red Line) - Representing Negative Moment or Temp Top
    top_bar_len = slab_L * 0.25

    # Left Top
    ax.plot([pad, beam_w + top_bar_len], [slab_h - pad, slab_h - pad], color='red', linewidth=2)
    ax.plot([pad, pad], [slab_h - pad, slab_h - pad - 0.2], color='red', linewidth=2)

    # Right Top
    ax.plot([slab_L + beam_w - top_bar_len, slab_L + 2 * beam_w - pad], [slab_h - pad, slab_h - pad], color='red',
            linewidth=2)
    ax.plot([slab_L + 2 * beam_w - pad, slab_L + 2 * beam_w - pad], [slab_h - pad, slab_h - pad - 0.2], color='red',
            linewidth=2)

    # Temperature Steel (Dots)
    dot_spacing = 0.25
    n_dots = int((slab_L + 2 * beam_w) / dot_spacing)
    for i in range(1, n_dots):
        cx = i * dot_spacing
        # Dots on top of bottom bar
        circle = patches.Circle((cx, pad + 0.06), radius=0.03, color='black')
        ax.add_patch(circle)

    # 3. Annotations
    # Top/Temp Label
    ax.annotate(f"Top/Temp: {temp_txt}", xy=(beam_w, slab_h - pad), xytext=(beam_w + 0.5, slab_h + 0.3),
                arrowprops=dict(facecolor='black', arrowstyle='->'), fontsize=9, fontweight='bold')

    # Bottom Main Label
    ax.annotate(f"Main Bottom: {main_txt}", xy=(slab_L / 2 + beam_w, pad), xytext=(slab_L / 2, -0.4),
                arrowprops=dict(facecolor='black', arrowstyle='->'), fontsize=9, fontweight='bold')

    # Dimensions
    ax.text((slab_L / 2) + beam_w, slab_h / 2, f"t = {h_cm:.0f} cm", ha='center', va='center', fontsize=10)

    # Span Line
    ax.annotate("", xy=(beam_w, -0.2), xytext=(beam_w + slab_L, -0.2), arrowprops=dict(arrowstyle='<->', color='black'))
    ax.text((slab_L / 2) + beam_w, -0.15, f"Span L = {L_m:.2f} m", ha='center', fontsize=10, backgroundcolor='white')

    ax.set_xlim(-0.5, slab_L + 2 * beam_w + 0.5)
    ax.set_ylim(-1.0, slab_h + 1.0)
    ax.axis('off')
    plt.tight_layout()

    return fig


# --- 4. Main Application ---
def main():
    # ---------------- SIDEBAR INPUTS ----------------
    with st.sidebar:
        st.header("Project Information")
        project_name = st.text_input("Project Name", "อาคารสำนักงาน 2 ชั้น")
        engineer_name = st.text_input("Engineer", "นายไกรฤทธิ์ ด่านพิทักษ์")
        date_str = st.text_input("Date", "16/12/2568")

        st.markdown("---")
        st.header("1. Material Properties")
        fc = st.number_input("Concrete (fc') ksc", value=240, step=10)
        fy = st.number_input("Steel Yield (fy) ksc", value=4000, step=100)

        st.header("2. Geometry & Loads")
        span_L = st.number_input("Span Length (m)", value=4.0, step=0.1)
        slab_t = st.number_input("Thickness (m)", value=0.15, step=0.01)
        cover = st.number_input("Cover (m)", value=0.025, step=0.005)

        sdl = st.number_input("SDL (kg/m2)", value=150.0)
        ll = st.number_input("Live Load (kg/m2)", value=300.0)

        st.header("3. Rebar Selection")
        main_dia = st.selectbox("Main Bar (mm)", [9, 12, 16, 20], index=1)
        temp_dia = st.selectbox("Temp Bar (mm)", [6, 9], index=0)

        support_type = st.selectbox("Support Type",
                                    ["Simply Supported", "Continuous (One End)", "Continuous (Both)", "Cantilever"])

    # ---------------- CALCULATIONS ----------------
    # Units: cm, kg, ksc
    b = 100.0  # Design strip 1m
    L_cm = span_L * 100
    h_cm = slab_t * 100
    cover_cm = cover * 100

    # 1. Load Analysis
    w_sw = 2400 * slab_t  # kg/m2
    w_dead = w_sw + sdl
    wu = 1.2 * w_dead + 1.6 * ll  # kg/m (strip)

    # 2. Moment (Simplified/Coefficients)
    if support_type == "Simply Supported":
        denom = 8.0
    elif "Continuous" in support_type:
        denom = 10.0  # Approx positive moment
    elif support_type == "Cantilever":
        denom = 2.0
    else:
        denom = 8.0

    Mu_kgm = (wu * span_L ** 2) / denom
    Mu = Mu_kgm * 100  # kg-cm

    # 3. Design
    d = h_cm - cover_cm - (main_dia / 20)  # Approx d (using half bar depth)
    Rn = Mu / (0.9 * b * d ** 2)

    rho_min = 0.0018  # ACI for deformed bars < 4200 ksc, or 0.0020 for Grade 40. 0.0018 is standard modern.
    status_flexure = "OK"

    try:
        term = 1 - (2 * Rn) / (0.85 *
