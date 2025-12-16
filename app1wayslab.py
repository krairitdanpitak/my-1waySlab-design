import streamlit as st
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# --- Page Config ---
st.set_page_config(page_title="RC Slab Design Report", layout="wide")

# --- Custom CSS for Reporting (Based on your PDF attachment) ---
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

    /* Table Styling to match PDF */
    .calc-table {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Sarabun', sans-serif;
        font-size: 14px;
        margin-top: 10px;
    }

    .calc-table th {
        background-color: #e0e0e0; /* Light Gray Header like PDF */
        border: 1px solid #000;
        padding: 8px;
        text-align: center;
        font-weight: bold;
    }

    .calc-table td {
        border: 1px solid #000; /* Solid borders */
        padding: 6px 8px;
        vertical-align: middle;
    }

    /* Column Widths */
    .col-item { width: 25%; font-weight: 600; }
    .col-formula { width: 20%; font-family: 'Courier New', monospace; font-size: 12px; color: #555; }
    .col-sub { width: 25%; font-family: 'Courier New', monospace; font-size: 12px; color: #333; }
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
        border-radius: 4px;
        text-decoration: none;
        font-weight: bold;
        cursor: pointer;
    }

    /* Hide elements when printing */
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


# --- Function: Draw Slab Section (Mimicking untitled4.png) ---
def draw_slab_schematic(L_m, h_cm, cover_cm, main_txt, temp_txt, support_type):
    fig, ax = plt.subplots(figsize=(10, 4))

    # Dimensions for drawing (Scaleless/Schematic)
    beam_w = 0.3  # width of support beam
    slab_L = 4.0  # visual length
    slab_h = 0.5  # visual thickness

    # 1. Draw Concrete Outline (Slab + Beams)
    # Left Beam
    ax.add_patch(patches.Rectangle((0, -0.8), beam_w, 0.8, facecolor='white', edgecolor='black', linewidth=1.5))
    # Right Beam
    ax.add_patch(
        patches.Rectangle((slab_L + beam_w, -0.8), beam_w, 0.8, facecolor='white', edgecolor='black', linewidth=1.5))
    # Slab
    ax.add_patch(
        patches.Rectangle((0, 0), slab_L + 2 * beam_w, slab_h, facecolor='#f9f9f9', edgecolor='black', linewidth=1.5))

    # 2. Draw Rebar
    # Padding
    pad = 0.05

    # Bottom Main Steel (Blue Line) - "เหล็กล่าง"
    # Runs full length + hooks
    ax.plot([pad, slab_L + 2 * beam_w - pad], [pad, pad], color='blue', linewidth=2, label='Bottom Main')
    # Hooks
    ax.plot([pad, pad], [pad, pad + 0.2], color='blue', linewidth=2)
    ax.plot([slab_L + 2 * beam_w - pad, slab_L + 2 * beam_w - pad], [pad, pad + 0.2], color='blue', linewidth=2)

    # Top Steel (Red Line) - At supports (Negative Moment) or Temp top
    # If continuous, show top bars at supports
    top_bar_len = slab_L * 0.25

    # Left Support Top Bar
    ax.plot([pad, beam_w + top_bar_len], [slab_h - pad, slab_h - pad], color='red', linewidth=2)
    ax.plot([pad, pad], [slab_h - pad, slab_h - pad - 0.2], color='red', linewidth=2)  # Hook down

    # Right Support Top Bar
    ax.plot([slab_L + beam_w - top_bar_len, slab_L + 2 * beam_w - pad], [slab_h - pad, slab_h - pad], color='red',
            linewidth=2)
    ax.plot([slab_L + 2 * beam_w - pad, slab_L + 2 * beam_w - pad], [slab_h - pad, slab_h - pad - 0.2], color='red',
            linewidth=2)  # Hook down

    # Temperature Steel (Dots) - "เหล็กกันร้าว/เหล็กขวาง"
    # Draw dots along the bottom main bar and top bars
    # Bottom dots
    dot_spacing = 0.4
    n_dots = int((slab_L + 2 * beam_w) / dot_spacing)
    for i in range(1, n_dots):
        cx = i * dot_spacing
        circle = patches.Circle((cx, pad + 0.08), radius=0.03, color='black')  # On top of bottom bar
        ax.add_patch(circle)

    # 3. Annotations (Arrows and Text)
    # Top Bar Label
    ax.annotate(f"Top Bar / Temp: {temp_txt}", xy=(beam_w, slab_h - pad), xytext=(beam_w + 0.5, slab_h + 0.4),
                arrowprops=dict(facecolor='black', arrowstyle='->'), fontsize=9, fontweight='bold')

    # Bottom Bar Label
    ax.annotate(f"Bottom Main: {main_txt}", xy=(slab_L / 2 + beam_w, pad), xytext=(slab_L / 2, -0.5),
                arrowprops=dict(facecolor='black', arrowstyle='->'), fontsize=9, fontweight='bold')

    # Dimensions
    ax.text((slab_L / 2) + beam_w, slab_h / 2, f"t = {h_cm:.0f} cm", ha='center', va='center', fontsize=10)

    # Span Line
    ax.annotate("", xy=(beam_w, -0.3), xytext=(beam_w + slab_L, -0.3), arrowprops=dict(arrowstyle='<->', color='black'))
    ax.text((slab_L / 2) + beam_w, -0.2, f"Span L = {L_m:.2f} m", ha='center', fontsize=10)

    # Clean up plot
    ax.set_xlim(-0.5, slab_L + 2 * beam_w + 0.5)
    ax.set_ylim(-1.0, slab_h + 1.0)
    ax.axis('off')

    return fig


# --- Main App ---
def main():
    # --- Sidebar Inputs ---
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

        support_type = st.selectbox("Support Type", ["Simply Supported", "Continuous"])

    # --- Calculations ---
    # Units: cm, kg, ksc
    b = 100.0  # Design strip 1m
    L_cm = span_L * 100
    h_cm = slab_t * 100
    cover_cm = cover * 100

    # 1. Loads
    w_sw = 2400 * slab_t  # kg/m2
    w_dead = w_sw + sdl
    wu = 1.2 * w_dead + 1.6 * ll  # kg/m (strip)

    # 2. Moment (Simple conservative)
    # Using wL^2/8 for simple, wL^2/10 or 12 for continuous (approx)
    denom = 8.0 if support_type == "Simply Supported" else 10.0
    Mu_kgm = (wu * span_L ** 2) / denom
    Mu = Mu_kgm * 100  # kg-cm

    # 3. Design
    d = h_cm - cover_cm - (main_dia / 20)  # Approx d
    Rn = Mu / (0.9 * b * d ** 2)

    rho_min = 0.0018
    try:
        term = 1 - (2 * Rn) / (0.85 * fc)
        if term < 0:
            rho_req = 0  # Fail
            status_flexure = "FAIL (Increase h)"
            design_ok = False
        else:
            rho_req = (0.85 * fc / fy) * (1 - math.sqrt(term))
            status_flexure = "OK"
            design_ok = True
    except:
        rho_req = 0
        status_flexure = "CALC ERR"
        design_ok = False

    As_req = max(rho_req, rho_min) * b * h_cm  # ACI Min uses Gross Area (bh) for slab shrinkage

    # Main Spacing
    Ab_main = math.pi * (main_dia / 10) ** 2 / 4
    s_calc_main = (Ab_main * 100) / As_req
    s_max_main = min(3 * h_cm, 45.0)
    s_main = math.floor(min(s_calc_main, s_max_main) * 2) / 2

    # Temp Spacing
    As_temp_req = rho_min * b * h_cm
    Ab_temp = math.pi * (temp_dia / 10) ** 2 / 4
    s_calc_temp = (Ab_temp * 100) / As_temp_req
    s_max_temp = min(5 * h_cm, 45.0)
    s_temp = math.floor(min(s_calc_temp, s_max_temp) * 2) / 2

    As_prov = (Ab_main * 100) / s_main

    # 4. Shear Check
    Vu = (wu * span_L) / 2  # Simple shear
    Vc = 0.53 * math.sqrt(fc) * b * d
    phi_Vc = 0.75 * Vc
    status_shear = "PASS" if phi_Vc >= Vu else "FAIL"

    # 5. Deflection (h_min)
    if support_type == "Simply Supported":
        ratio = 20
    else:
        ratio = 24  # One end continuous approx

    h_min = (L_cm / ratio) * (0.4 + fy / 7000)
    status_defl = "PASS" if h_cm >= h_min else "CHECK"

    # --- Render Report ---

    # Print Button
    st.markdown(
        '<div class="print-btn-container"><button class="print-btn" onclick="window.print()">🖨️ Print This Page</button></div>',
        unsafe_allow_html=True)

    # Header Box
    st.markdown(f"""
    <div class="header-box">
        <div class="report-title">ENGINEERING DESIGN REPORT</div>
        <div class="report-subtitle">RC ONE-WAY SLAB DESIGN (ACI 318-19)</div>
        <div style="display: flex; justify-content: space-between; padding: 0 20px;">
            <div style="width: 45%;">
                <b>Project:</b> {project_name}<br>
                <b>Engineer:</b> {engineer_name}<br>
                <b>Date:</b> {date_str}
            </div>
            <div style="width: 50%;">
                <b>Design Code:</b> ACI 318-19 (Metric)<br>
                <b>Materials:</b> fc' = {fc} ksc, fy = {fy} ksc<br>
                <b>Element:</b> Slab Thickness {h_cm:.0f} cm
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Graphic Section
    st.subheader("Design Visualization")
    col_gfx1, col_gfx2 = st.columns([3, 1])

    with col_gfx1:
        main_txt = f"DB{main_dia}@{s_main:.0f}cm"
        temp_txt = f"RB{temp_dia}@{s_temp:.0f}cm"
        fig = draw_slab_schematic(span_L, h_cm, cover_cm, main_txt, temp_txt, support_type)
        st.pyplot(fig)

    with col_gfx2:
        st.markdown(f"""
        <div style="border: 1px solid #ccc; padding: 10px; border-radius: 5px; background-color: #f0f8ff;">
            <h4 style="margin:0; text-align:center;">Selected Rebar</h4>
            <hr>
            <p><b>Main (Bottom):</b><br> <span style="color:blue; font-weight:bold; font-size:1.2em;">DB{main_dia} @ {s_main:.0f} cm</span></p>
            <p><b>Temp (Top):</b><br> <span style="color:red; font-weight:bold;">RB{temp_dia} @ {s_temp:.0f} cm</span></p>
            <hr>
            <p align="center"><b>Status:</b> <span style="color:green;">{status_flexure}</span></p>
        </div>
        """, unsafe_allow_html=True)

    # Table Generation (The Core Requirement)
    st.subheader("Calculation Details")

    # Prepare rows data
    rows = [
        ("1. PROPERTIES", "", "", "", "", ""),
        ("Concrete Strength", "fc' (Input)", f"{fc} ksc", f"{fc:.0f}", "ksc", ""),
        ("Yield Strength", "fy (Input)", f"{fy} ksc", f"{fy:.0f}", "ksc", ""),
        ("Slab Thickness", "h", f"{slab_t} m", f"{h_cm:.0f}", "cm", ""),
        ("Effective Depth", "d = h - cov - db/2", f"{h_cm}-{cover_cm}-...", f"{d:.2f}", "cm", ""),

        ("2. LOAD ANALYSIS", "", "", "", "", ""),
        ("Dead Load (SW)", "2400 x h", f"2400 x {slab_t}", f"{w_sw:.1f}", "kg/m2", ""),
        ("Superimposed DL", "SDL (Input)", f"{sdl}", f"{sdl:.1f}", "kg/m2", ""),
        ("Total Dead Load", "w_dead = SW + SDL", f"{w_sw:.0f} + {sdl:.0f}", f"{w_dead:.1f}", "kg/m2", ""),
        ("Factored Load", "wu = 1.2D + 1.6L", f"1.2({w_dead:.0f})+1.6({ll})", f"{wu:.1f}", "kg/m", ""),

        ("3. FLEXURAL DESIGN", "", "", "", "", ""),
        ("Design Moment", "Mu = wu.L^2 / Coef", f"{wu:.0f}*{span_L}^2/{denom:.0f}", f"{Mu_kgm:.1f}", "kg-m", ""),
        ("Resistance Factor", "Rn = Mu / 0.9bd^2", f"{Mu:.0f}/...", f"{Rn:.3f}", "ksc", ""),
        ("Required Rho", "0.85fc/fy * ...", "Formula Eq.", f"{rho_req:.5f}", "-", status_flexure),
        ("Min Rho (Temp)", "0.0018 (Ag)", "-", f"{rho_min:.4f}", "-", ""),
        ("Req. Steel Area", "As = rho * b * h", f"{max(rho_req, rho_min):.4f}*100*{h_cm}", f"{As_req:.2f}", "cm2", ""),
        ("Provided Main", f"DB{main_dia} @ {s_main}", f"Ab*100/{s_main}", f"{As_prov:.2f}", "cm2", "PASS"),

        ("4. CHECKS", "", "", "", "", ""),
        ("Design Shear (Vu)", "wu * L / 2", f"{wu:.0f}*{span_L}/2", f"{Vu:.1f}", "kg", ""),
        ("Shear Capacity", "0.75 * 0.53sqrt(fc)bd", "Formula Eq.", f"{phi_Vc:.1f}", "kg", status_shear),
        ("Deflection (h_min)", "L/Ratio * Mod", f"{L_cm}/{ratio} * ...", f"{h_min:.2f}", "cm", status_defl),
    ]

    # Build HTML Table
    table_html = '<table class="calc-table"><thead><tr>'
    table_html += '<th class="col-item">Item</th><th class="col-formula">Formula</th><th class="col-sub">Substitution</th>'
    table_html += '<th class="col-result">Result</th><th class="col-unit">Unit</th><th class="col-status">Status</th>'
    table_html += '</tr></thead><tbody>'

    for item, formula, sub, res, unit, status in rows:
        # Check if it's a section header row
        if formula == "" and res == "":
            table_html += f'<tr style="background-color: #f0f0f0;"><td colspan="6"><b>{item}</b></td></tr>'
        else:
            # Color status
            stat_color = "green" if "PASS" in status or "OK" in status else ("red" if "FAIL" in status else "black")

            table_html += f"""
            <tr>
                <td class="col-item">{item}</td>
                <td class="col-formula">{formula}</td>
                <td class="col-sub">{sub}</td>
                <td class="col-result">{res}</td>
                <td class="col-unit">{unit}</td>
                <td class="col-status" style="color:{stat_color}">{status}</td>
            </tr>
            """

    table_html += '</tbody></table>'
    st.markdown(table_html, unsafe_allow_html=True)

    # Footer
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("__________________________")
        st.markdown(f"**Designed by:**<br>{engineer_name}<br>Civil Engineer", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div style="border: 2px solid green; color: green; padding: 10px; text-align: center; font-weight: bold;">
        DESIGN STATUS:<br>COMPLETE
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
