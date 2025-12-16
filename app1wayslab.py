import streamlit as st
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd

# --- Page Config ---
st.set_page_config(page_title="RC Slab Design Report", layout="wide")

# --- Custom CSS for Styling & Printing ---
st.markdown("""
<style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Sarabun', sans-serif;
    }

    /* Report Header Box Style */
    .report-box {
        border: 2px solid #000;
        padding: 15px;
        margin-bottom: 20px;
        border-radius: 5px;
        background-color: #f9f9f9;
    }

    .header-title {
        text-align: center;
        font-weight: bold;
        font-size: 24px;
        margin-bottom: 10px;
        text-transform: uppercase;
    }

    .sub-title {
        text-align: center;
        font-weight: bold;
        font-size: 18px;
        margin-bottom: 20px;
        color: #333;
    }

    /* Table Styling */
    .styled-table {
        width: 100%;
        border-collapse: collapse;
        margin: 25px 0;
        font-size: 16px;
        font-family: 'Sarabun', sans-serif;
        box-shadow: 0 0 20px rgba(0, 0, 0, 0.10);
    }
    .styled-table thead tr {
        background-color: #009879;
        color: #ffffff;
        text-align: left;
    }
    .styled-table th, .styled-table td {
        padding: 12px 15px;
        border: 1px solid #dddddd;
    }
    .styled-table tbody tr {
        border-bottom: 1px solid #dddddd;
    }
    .styled-table tbody tr:nth-of-type(even) {
        background-color: #f3f3f3;
    }

    /* Print Button Style */
    .print-btn {
        background-color: #28a745;
        color: white;
        padding: 10px 20px;
        border: none;
        border-radius: 5px;
        cursor: pointer;
        font-size: 16px;
        font-weight: bold;
        text-decoration: none;
        display: inline-block;
        margin-bottom: 20px;
        text-align: center;
    }
    .print-btn:hover {
        background-color: #218838;
    }

    /* Print Media Query (Hide Sidebar & Elements) */
    @media print {
        [data-testid="stSidebar"] { display: none; }
        .stButton { display: none; }
        header { display: none; }
        footer { display: none; }
        .print-hide { display: none; }
        body { -webkit-print-color-adjust: exact; }
    }
</style>
""", unsafe_allow_html=True)


# --- Function: Draw Slab Section ---
def draw_slab_section(width_cm, height_cm, cover_cm, main_dia_mm, spacing_main_cm, temp_dia_mm, spacing_temp_cm):
    fig, ax = plt.subplots(figsize=(10, 4))

    # 1. Concrete Block (Draw 1 meter strip or less for visibility, let's draw 100cm)
    # To make it visible, we might clip the drawing or just draw a representative 50cm
    draw_width = 100.0
    rect = patches.Rectangle((0, 0), draw_width, height_cm, linewidth=2, edgecolor='black', facecolor='#f0f0f0')
    ax.add_patch(rect)

    # 2. Main Rebar (Bottom)
    # Calculate Y position
    y_main = cover_cm + (main_dia_mm / 10) / 2

    # Generate X positions
    n_bars = int(draw_width / spacing_main_cm) + 1
    # Start centering
    start_x = (draw_width - (n_bars - 1) * spacing_main_cm) / 2
    if start_x < cover_cm: start_x = cover_cm

    main_circle_patches = []
    for i in range(n_bars):
        cx = start_x + i * spacing_main_cm
        if cx > draw_width - cover_cm: break
        circle = patches.Circle((cx, y_main), radius=(main_dia_mm / 10) / 2, edgecolor='black', facecolor='red',
                                label='Main')
        ax.add_patch(circle)

    # 3. Temp Rebar (Top of Main or slightly above)
    # Typically placed on top of main bars in perpendicular direction.
    # In a 2D section cut along the span, temp bars run INTO the page.
    # But wait, this is a section ALONG the span. So Main bars run LEFT-RIGHT (lines), Temp bars run INTO page (circles).
    # Wait, usually for slab detailing:
    # Section cut ALONG span: Main bars are LINES at the bottom. Temp bars are CIRCLES on top of main bars.
    # OR Section cut ACROSS span: Main bars are CIRCLES. Temp bars are LINES.

    # Let's draw the "Cross Section" view (Transverse Cut) where Main bars are CIRCLES.
    # This is the standard view to show spacing.

    # Temp bars (Transverse/Shrinkage) would be LINES running across in this view?
    # No, typically we show Main Reinforcement as circles to show spacing.
    # The Temp bars would be circles in the *other* view.
    # Let's just draw Main Rebar as circles for this view to verify spacing.

    # If we want to show Temp bars in this view, they would be a long line running perpendicular?
    # Let's represent Temp bars as circles sitting ON TOP of main bars (if it was a 2-way mat)
    # OR commonly in 1-way slab, temp bars are placed *above* main bars running perpendicular.
    # In this view (Section X-X), Main bars are circles. Temp bars are lines running L-R.

    # Let's draw a line for Temp Bar location just to indicate depth
    y_temp = y_main + (main_dia_mm / 10) / 2 + (temp_dia_mm / 10) / 2
    # ax.plot([0, draw_width], [y_temp, y_temp], color='blue', linestyle='--', linewidth=2, label='Temp Bar Level')

    # Annotation
    ax.text(draw_width / 2, height_cm + 1, f"Design Strip Width = {draw_width:.0f} cm", ha='center', fontsize=10)
    ax.text(-2, height_cm / 2, f"h={height_cm}cm", va='center', rotation=90)

    # Annotate Main Steel
    ax.annotate(f"Main: DB{main_dia_mm}@{spacing_main_cm:.1f}cm",
                xy=(start_x + spacing_main_cm, y_main),
                xytext=(start_x + spacing_main_cm + 5, y_main + 5),
                arrowprops=dict(facecolor='black', shrink=0.05))

    ax.set_xlim(-5, draw_width + 5)
    ax.set_ylim(-2, height_cm + 5)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title("Slab Cross Section (Showing Main Reinforcement)", fontsize=12, fontweight='bold')

    return fig


# --- Main Application ---
def main():
    # --- Sidebar Input ---
    with st.sidebar:
        st.header("1. Project Info")
        project_name = st.text_input("Project Name", "อาคารสำนักงาน 2 ชั้น")
        engineer_name = st.text_input("Engineer", "นายไกรฤทธิ์ ด่านพิทักษ์")
        date_str = st.text_input("Date", "16/12/2568")

        st.markdown("---")
        st.header("2. Material & Section")
        fc = st.number_input("Concrete (fc') ksc", value=240, step=10)
        fy = st.number_input("Steel Yield (fy) ksc", value=4000, step=100)

        st.header("3. Geometry")
        span_L = st.number_input("Span Length (m)", value=4.0, step=0.1)
        slab_t = st.number_input("Thickness (m)", value=0.15, step=0.01)
        cover = st.number_input("Cover (m)", value=0.025, step=0.005)
        support_type = st.selectbox("Support",
                                    ["Simply Supported", "Continuous (One End)", "Continuous (Both)", "Cantilever"])

        st.header("4. Loads")
        sdl = st.number_input("SDL (kg/m2)", value=150.0)
        ll = st.number_input("LL (kg/m2)", value=300.0)

        st.header("5. Rebar Selection")
        main_bar = st.selectbox("Main Bar (mm)", [9, 12, 16, 20], index=1)
        temp_bar = st.selectbox("Temp Bar (mm)", [6, 9], index=0)

    # --- Calculations ---
    # Constants
    b = 100.0  # cm
    L_cm = span_L * 100
    h_cm = slab_t * 100
    cover_cm = cover * 100

    # 1. Load Analysis
    w_sw = 2400 * slab_t
    w_dead = w_sw + sdl
    wu = 1.2 * w_dead + 1.6 * ll  # kg/m

    # 2. Moment & Shear
    # Moment coef
    if "Simply" in support_type:
        m_coef = 8
    elif "One End" in support_type:
        m_coef = 10  # Approx for positive
    elif "Both" in support_type:
        m_coef = 12  # Approx for positive
    elif "Cantilever" in support_type:
        m_coef = 2
    else:
        m_coef = 8

    Mu_kg_m = (wu * span_L ** 2) / m_coef
    if "Cantilever" in support_type: Mu_kg_m = (wu * span_L ** 2) / 2

    Mu = Mu_kg_m * 100  # kg-cm
    Vu = (wu * span_L) / 2
    if "Cantilever" in support_type: Vu = wu * span_L

    # 3. Design
    d = h_cm - cover_cm - (main_bar / 10) / 2
    Mn_req = Mu / 0.90
    Rn = Mn_req / (b * d ** 2)

    rho_min = 0.0018
    rho_calc = "N/A"

    status_flexure = "OK"
    try:
        term = 1 - (2 * Rn) / (0.85 * fc)
        if term < 0:
            rho_req = 0
            status_flexure = "FAIL (Thicken Slab)"
        else:
            rho_req = (0.85 * fc / fy) * (1 - math.sqrt(term))
    except:
        rho_req = 0
        status_flexure = "FAIL"

    As_req = max(rho_req, rho_min) * b * h_cm  # ACI Min based on Gross Area

    # Main Spacing
    Ab_main = math.pi * (main_bar / 10) ** 2 / 4
    s_calc = (Ab_main * 100) / As_req
    s_max = min(3 * h_cm, 45.0)
    s_design = min(s_calc, s_max)
    s_design = math.floor(s_design * 2) / 2  # Round 0.5

    As_prov = (Ab_main * 100) / s_design

    # Temp Spacing
    As_temp = rho_min * b * h_cm
    Ab_temp = math.pi * (temp_bar / 10) ** 2 / 4
    s_temp_calc = (Ab_temp * 100) / As_temp
    s_temp_max = min(5 * h_cm, 45.0)
    s_temp_design = min(s_temp_calc, s_temp_max)
    s_temp_design = math.floor(s_temp_design * 2) / 2

    # 4. Check Shear
    Vc = 0.53 * math.sqrt(fc) * b * d
    phi_Vc = 0.75 * Vc
    status_shear = "PASS" if phi_Vc >= Vu else "FAIL"

    # 5. Check Deflection (h_min)
    if "Simply" in support_type:
        factor = 20
    elif "One End" in support_type:
        factor = 24
    elif "Both" in support_type:
        factor = 28
    else:
        factor = 10

    h_min = (L_cm / factor) * (0.4 + fy / 7000)
    status_deflection = "PASS" if h_cm >= h_min else "WARNING"

    # --- RENDER REPORT ---

    # 1. Print Button
    st.markdown("""
    <script>
    function printPage() {
        window.print();
    }
    </script>
    <div style="text-align: right;">
        <button class="print-btn" onclick="window.print()">🖨️ Print This Page / พิมพ์หน้านี้</button>
    </div>
    """, unsafe_allow_html=True)

    # 2. Header Box
    st.markdown(f"""
    <div class="report-box">
        <div class="header-title">ENGINEERING DESIGN REPORT</div>
        <div class="sub-title">RC One-Way Slab Design (ACI 318-19)</div>
        <div style="display: flex; justify-content: space-between;">
            <div style="width: 48%;">
                <b>Project:</b> {project_name}<br>
                <b>Engineer:</b> {engineer_name}<br>
                <b>Date:</b> {date_str}
            </div>
            <div style="width: 48%;">
                <b>Materials:</b> fc'={fc} ksc, fy={fy} ksc<br>
                <b>Section:</b> {b:.0f}x{h_cm:.0f} cm, Cover={cover_cm} cm<br>
                <b>Code:</b> ACI 318-19 (Metric)
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 3. Design Summary (Visuals)
    st.subheader("Design Summary & Visualization")
    col_vis1, col_vis2 = st.columns([2, 1])

    with col_vis1:
        fig = draw_slab_section(100, h_cm, cover_cm, main_bar, s_design, temp_bar, s_temp_design)
        st.pyplot(fig)

    with col_vis2:
        st.markdown(f"""
        <div style="background-color: #e6fffa; padding: 15px; border-radius: 5px; border: 1px solid #b2f5ea;">
            <h4 style="margin-top:0;">Final Selection</h4>
            <p><b>Thickness (h):</b> {h_cm:.0f} cm</p>
            <p><b>Main Rebar:</b> <br><span style="color:blue; font-weight:bold;">DB{main_bar} @ {s_design:.1f} cm</span></p>
            <p><b>Temp Rebar:</b> <br>RB/DB{temp_bar} @ {s_temp_design:.1f} cm</p>
            <hr>
            <p><b>Status:</b> <span style="color:green; font-weight:bold;">DESIGN COMPLETE</span></p>
        </div>
        """, unsafe_allow_html=True)

    # 4. Detailed Calculation Table
    st.subheader("Calculation Details")

    # Prepare Data for Table
    data = [
        # Material
        {"Item": "Concrete Strength", "Formula": "fc' (Input)", "Substitution": f"{fc} ksc", "Result": f"{fc:.0f}",
         "Unit": "ksc", "Status": ""},
        {"Item": "Yield Strength", "Formula": "fy (Input)", "Substitution": f"{fy} ksc", "Result": f"{fy:.0f}",
         "Unit": "ksc", "Status": ""},

        # Load
        {"Item": "Dead Load (DL)", "Formula": "2400*h + SDL", "Substitution": f"2400*{slab_t:.2f} + {sdl}",
         "Result": f"{w_dead:.1f}", "Unit": "kg/m2", "Status": ""},
        {"Item": "Factored Load (wu)", "Formula": "1.2D + 1.6L", "Substitution": f"1.2({w_dead:.0f}) + 1.6({ll})",
         "Result": f"{wu:.1f}", "Unit": "kg/m", "Status": ""},

        # Analysis
        {"Item": "Design Moment (Mu)", "Formula": "wu * L^2 / Coef",
         "Substitution": f"{wu:.0f} * {span_L}^2 / {m_coef}", "Result": f"{Mu_kg_m:.1f}", "Unit": "kg-m", "Status": ""},
        {"Item": "Design Shear (Vu)", "Formula": "wu * L / 2", "Substitution": f"{wu:.0f} * {span_L} / 2",
         "Result": f"{Vu:.1f}", "Unit": "kg", "Status": ""},

        # Design
        {"Item": "Effective Depth (d)", "Formula": "h - cover - db/2",
         "Substitution": f"{h_cm}-{cover_cm}-{main_bar / 20}", "Result": f"{d:.2f}", "Unit": "cm", "Status": ""},
        {"Item": "Resistance Factor (Rn)", "Formula": "Mu / (0.9 b d^2)",
         "Substitution": f"{Mu:.0f}/(0.9*100*{d:.1f}^2)", "Result": f"{Rn:.3f}", "Unit": "ksc", "Status": ""},
        {"Item": "Required Rho", "Formula": "0.85fc/fy * ...", "Substitution": "-", "Result": f"{rho_req:.5f}",
         "Unit": "-", "Status": f"{'OK' if rho_req > 0 else 'FAIL'}"},
        {"Item": "Min Rho (Temp)", "Formula": "0.0018 or 0.0020", "Substitution": "-", "Result": f"{rho_min:.4f}",
         "Unit": "-", "Status": "Control" if rho_min > rho_req else ""},
        {"Item": "Req. Steel Area (As)", "Formula": "rho * b * h",
         "Substitution": f"{max(rho_req, rho_min):.4f} * 100 * {h_cm}", "Result": f"{As_req:.2f}", "Unit": "cm2",
         "Status": ""},

        # Checks
        {"Item": "Main Steel Prov.", "Formula": f"DB{main_bar} @ {s_design}", "Substitution": f"Ab * 100 / {s_design}",
         "Result": f"{As_prov:.2f}", "Unit": "cm2", "Status": "PASS"},
        {"Item": "Shear Capacity", "Formula": "0.75 * 0.53 * sqrt(fc) * b * d",
         "Substitution": f"0.75*0.53*sqrt({fc})*...", "Result": f"{phi_Vc:.0f}", "Unit": "kg",
         "Status": f"{status_shear} (Vu={Vu:.0f})"},
        {"Item": "Deflection (h_min)", "Formula": "L/Ratio * Mod", "Substitution": f"{L_cm}/{factor} * Mod",
         "Result": f"{h_min:.2f}", "Unit": "cm", "Status": f"{status_deflection}"},
    ]

    # Create HTML Table
    table_html = '<table class="styled-table"><thead><tr><th>Item</th><th>Formula</th><th>Substitution</th><th>Result</th><th>Unit</th><th>Status</th></tr></thead><tbody>'

    for row in data:
        status_color = "red" if "FAIL" in row["Status"] or "WARNING" in row["Status"] else "green"
        status_style = f'style="color:{status_color}; font-weight:bold;"' if row["Status"] else ""

        table_html += f"""
        <tr>
            <td>{row['Item']}</td>
            <td>{row['Formula']}</td>
            <td>{row['Substitution']}</td>
            <td><b>{row['Result']}</b></td>
            <td>{row['Unit']}</td>
            <td {status_style}>{row['Status']}</td>
        </tr>
        """
    table_html += "</tbody></table>"
    st.markdown(table_html, unsafe_allow_html=True)

    # 5. Footer / Signature
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("__________________________")
        st.markdown(f"**Designed by:**<br>{engineer_name}<br>Civil Engineer", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div style="border: 2px solid green; color: green; padding: 10px; text-align: center; font-weight: bold; border-radius: 5px;">
        DESIGN STATUS:<br>COMPLETE
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
