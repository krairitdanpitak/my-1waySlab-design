import streamlit as st
import matplotlib

# Set backend to Agg to prevent thread issues in Streamlit
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import math
import io
import base64
import streamlit.components.v1 as components

# ==========================================
# 1. SETUP & CSS
# ==========================================
st.set_page_config(page_title="RC One-Way Slab Design (Auto Check)", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@400;700&display=swap');

    /* Print Button Style */
    .print-btn-internal {
        background-color: #4CAF50;
        border: none;
        color: white !important;
        padding: 12px 24px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 10px 0px;
        cursor: pointer;
        border-radius: 5px;
        font-family: 'Sarabun', sans-serif;
        font-weight: bold;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    .print-btn-internal:hover { background-color: #45a049; }

    /* Report Table Style */
    .report-table {width: 100%; border-collapse: collapse; font-family: 'Sarabun', sans-serif; font-size: 14px;}
    .report-table th, .report-table td {border: 1px solid #ddd; padding: 8px;}
    .report-table th {background-color: #f2f2f2; text-align: center; font-weight: bold;}

    .pass-ok {color: green; font-weight: bold;}
    .pass-no {color: red; font-weight: bold;}
    .pass-warn {color: #ff9800; font-weight: bold;} 

    .sec-row {background-color: #e0e0e0; font-weight: bold; font-size: 15px;}
    .load-value {color: #D32F2F !important; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATABASE & HELPERS
# ==========================================
BAR_INFO = {
    'RB6': {'A_cm2': 0.283, 'd_mm': 6},
    'RB9': {'A_cm2': 0.636, 'd_mm': 9},
    'DB10': {'A_cm2': 0.785, 'd_mm': 10},
    'DB12': {'A_cm2': 1.131, 'd_mm': 12},
    'DB16': {'A_cm2': 2.011, 'd_mm': 16},
    'DB20': {'A_cm2': 3.142, 'd_mm': 20},
    'DB25': {'A_cm2': 4.909, 'd_mm': 25}
}


def fmt(n, digits=2):
    try:
        val = float(n)
        if math.isnan(val): return "-"
        return f"{val:,.{digits}f}"
    except:
        return "-"


def fig_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)  # Memory cleanup
    return f"data:image/png;base64,{base64.b64encode(buf.read()).decode()}"


# ==========================================
# 3. PLOTTING FUNCTION (Updated for Cantilever)
# ==========================================
def plot_slab_section(h_cm, cover_cm, main_key, s_main, temp_key, s_temp, support_type):
    fig, ax = plt.subplots(figsize=(8, 4))

    # Common parameters
    pad = 0.03 + (cover_cm / 100)  # visual padding + cover

    if support_type == "Cantilever":
        # --- DRAWING FOR CANTILEVER (พื้นยื่น) ---
        slab_len_draw = 1.5  # Fixed visual length
        beam_w = 0.30  # Visual beam width
        beam_d = 0.50  # Visual beam depth
        slab_h_draw = h_cm / 100

        # 1. Concrete
        # Beam (Left support)
        ax.add_patch(patches.Rectangle((-beam_w, -beam_d), beam_w, beam_d,
                                       facecolor='white', edgecolor='black', linewidth=1.5))
        # Slab (Cantilever part)
        ax.add_patch(patches.Rectangle((0, -slab_h_draw), slab_len_draw, slab_h_draw,
                                       facecolor='#f9f9f9', edgecolor='black', linewidth=1.5))

        # 2. Main Rebar (Top Steel - Tension) -> Blue Line
        # Path: Hook in beam -> Top of slab -> Hook down at end
        bar_y = -pad

        # Points: [Start(in beam), Corner(in beam), End(slab tip), Hook(down)]
        x_pts = [-beam_w + pad, -beam_w + pad, slab_len_draw - pad, slab_len_draw - pad]
        y_pts = [-beam_d + pad, bar_y, bar_y, bar_y - 0.10]

        ax.plot(x_pts, y_pts, color='blue', linewidth=3.0)

        # 3. Temp Rebar (Distribution - Under Main) -> Red Dots
        dist_y = bar_y - 0.02 - 0.012  # slightly below main bar
        dot_spacing = 0.20
        n_dots = int((slab_len_draw) / dot_spacing)

        for i in range(n_dots):
            cx = (i * dot_spacing) + 0.1
            if cx < slab_len_draw - pad:
                ax.add_patch(patches.Circle((cx, dist_y), radius=0.015, color='red'))

        # 4. Dimensions & Text
        # Beam Dimension
        ax.annotate(f"{beam_w:.2f}m", xy=(-beam_w / 2, -beam_d - 0.05), ha='center', fontsize=9, color='brown')

        # Slab Thickness
        ax.text(slab_len_draw / 2, -slab_h_draw / 2, f"t = {h_cm:.0f} cm", ha='center', va='center', fontsize=10)

        # Rebar Labels
        ax.annotate(f"Main (Top): {main_key}@{s_main:.0f}cm",
                    xy=(slab_len_draw / 3, bar_y), xytext=(slab_len_draw / 3, 0.2),
                    arrowprops=dict(facecolor='blue', arrowstyle='->'), fontsize=10, color='blue', fontweight='bold')

        ax.annotate(f"Temp (Dist.): {temp_key}@{s_temp:.0f}cm",
                    xy=(0.1 + dot_spacing, dist_y), xytext=(0.5, 0.4),
                    arrowprops=dict(facecolor='red', arrowstyle='->'), fontsize=10, color='red', fontweight='bold')

        ax.set_xlim(-beam_w - 0.2, slab_len_draw + 0.2)
        ax.set_ylim(-beam_d - 0.2, 0.6)

    else:
        # --- DRAWING FOR STANDARD (Simply / Continuous) ---
        slab_len_draw = 4.0
        beam_w = 0.3
        slab_h_draw = 0.4  # Visual relative height

        # Concrete
        ax.add_patch(patches.Rectangle((0, -0.6), beam_w, 0.6, facecolor='white', edgecolor='black', linewidth=1.5))
        ax.add_patch(
            patches.Rectangle((slab_len_draw + beam_w, -0.6), beam_w, 0.6, facecolor='white', edgecolor='black',
                              linewidth=1.5))
        ax.add_patch(
            patches.Rectangle((0, 0), slab_len_draw + 2 * beam_w, slab_h_draw, facecolor='#f9f9f9', edgecolor='black',
                              linewidth=1.5))

        # Main Rebar (Bottom Steel - Tension) -> Blue Line
        ax.plot([pad, slab_len_draw + 2 * beam_w - pad], [pad, pad], color='blue', linewidth=2.5)
        # Hooks
        ax.plot([pad, pad], [pad, pad + 0.15], color='blue', linewidth=2.5)
        ax.plot([slab_len_draw + 2 * beam_w - pad, slab_len_draw + 2 * beam_w - pad], [pad, pad + 0.15], color='blue',
                linewidth=2.5)

        # Temp Rebar (Top of Bottom) -> Red Dots
        dot_spacing = 0.25
        n_dots = int((slab_len_draw + 2 * beam_w) / dot_spacing)
        for i in range(1, n_dots):
            cx = i * dot_spacing
            ax.add_patch(patches.Circle((cx, pad + 0.07), radius=0.04, color='red'))

        # Labels
        ax.text((slab_len_draw / 2) + beam_w, slab_h_draw / 2, f"Thickness t = {h_cm:.0f} cm", ha='center', va='center',
                fontsize=11)

        ax.annotate(f"Main (Bottom): {main_key}@{s_main:.0f}cm",
                    xy=(slab_len_draw / 2 + beam_w, pad), xytext=(slab_len_draw / 2, -0.4),
                    arrowprops=dict(facecolor='blue', arrowstyle='->'), fontsize=10, color='blue', fontweight='bold')

        ax.annotate(f"Temp (Long): {temp_key}@{s_temp:.0f}cm",
                    xy=(slab_len_draw / 2 + beam_w + 0.2, pad + 0.07),
                    xytext=(slab_len_draw / 2 + 1.5, slab_h_draw + 0.3),
                    arrowprops=dict(facecolor='red', arrowstyle='->'), fontsize=10, color='red', fontweight='bold')

        ax.set_xlim(-0.2, slab_len_draw + 2 * beam_w + 0.2)
        ax.set_ylim(-0.8, slab_h_draw + 0.6)

    ax.axis('off')
    plt.tight_layout()
    return fig


# ==========================================
# 4. CALCULATION LOGIC
# ==========================================
def process_slab_calculation(inputs):
    rows = []

    def sec(title):
        rows.append(["SECTION", title, "", "", "", "", ""])

    def row(item, formula, subs, result, unit, status=""):
        rows.append([item, formula, subs, result, unit, status])

    # Unpack
    fc = inputs['fc'];
    fy = inputs['fy']
    Lx = inputs['Lx'];
    Ly = inputs['Ly']
    h_cm = inputs['h'];
    cover_cm = inputs['cover']
    sdl = inputs['sdl'];
    ll = inputs['ll']
    main_key = inputs['mainBar'];
    temp_key = inputs['tempBar']
    support = inputs['support']

    # 1. Geometry & Type Check
    sec("1. GEOMETRY & SLAB TYPE")
    row("Short Span", "Lx", "-", f"{Lx:.2f}", "m")
    row("Long Span", "Ly", "-", f"{Ly:.2f}", "m")

    ratio = Ly / Lx
    slab_type = "One-Way Slab" if ratio > 2.0 else "Two-Way Slab"
    status_type = "OK" if ratio > 2.0 else "WARNING"

    row("Ratio Ly/Lx", f"{Ly:.2f} / {Lx:.2f}", "-", f"{ratio:.2f}", "-", status_type)
    row("Slab Type Check", "Ratio > 2.0?", "-", slab_type, "-", status_type)

    if ratio <= 2.0:
        rows.append(
            ["Note", "Since Ly/Lx ≤ 2.0, it behaves as Two-Way.", "Design as One-Way is Conservative.", "-", "-",
             "INFO"])

    # 2. Load Analysis
    sec("2. LOAD ANALYSIS (Design Strip b = 1 m)")
    w_sw = 2400 * (h_cm / 100)
    w_dead = w_sw + sdl
    wu = 1.2 * w_dead + 1.6 * ll

    row("Factored Load (wu)", "1.2D + 1.6L", f"1.2({w_dead:.0f}) + 1.6({ll})", f"{fmt(wu)}", "kg/m")

    # 3. Flexural Design (Short Span - Lx)
    sec("3. SHORT SPAN DESIGN (MAIN STEEL)")

    # Coef
    if support == "Simply Supported":
        coef = 8.0
    elif "Continuous" in support:
        coef = 10.0
    elif support == "Cantilever":
        coef = 2.0
    else:
        coef = 8.0

    Mu_kgm = (wu * Lx ** 2) / coef
    Mu_kgcm = Mu_kgm * 100

    db_main = BAR_INFO[main_key]['d_mm']
    d = h_cm - cover_cm - (db_main / 10) / 2

    row("Design Moment (Mu)", f"wu · Lx² / {coef:.0f}", f"{fmt(wu)}·{Lx}²/{coef:.0f}", f"{fmt(Mu_kgm)}", "kg-m")
    row("Effective Depth (d)", "h - cov - db/2", f"{h_cm}-{cover_cm}-{db_main / 20}", f"{d:.2f}", "cm")

    # Rn & Rho
    phi = 0.90;
    b = 100
    Rn = Mu_kgcm / (phi * b * d ** 2)

    rho_min = 0.0018
    status_flex = "OK"
    try:
        term = 1 - (2 * Rn) / (0.85 * fc)
        if term < 0:
            rho_req = 0;
            status_flex = "FAIL (Thicken Slab)"
        else:
            rho_req = (0.85 * fc / fy) * (1 - math.sqrt(term))
    except:
        rho_req = 0;
        status_flex = "CALC ERROR"

    As_flex_req = rho_req * b * d
    As_min_req = rho_min * b * h_cm

    # Determine Control
    if As_flex_req >= As_min_req:
        As_req_short = As_flex_req
        control = "Flexure Controls"
    else:
        As_req_short = As_min_req
        control = "Min Steel Controls"

    row("Required As (Short)", control, f"max(ρbd, 0.0018bh)", f"{fmt(As_req_short)}", "cm²")

    # Select Main Bar
    Ab_main = BAR_INFO[main_key]['A_cm2']
    s_calc = (Ab_main * 100) / As_req_short
    s_max = min(3 * h_cm, 45.0)
    s_main = math.floor(min(s_calc, s_max) * 2) / 2
    As_prov_main = (Ab_main * 100) / s_main

    row("Provide Main Steel", f"Use {main_key}", f"@{s_main:.1f} cm", f"{fmt(As_prov_main)}", "cm²", status_flex)

    # 4. Temperature Steel (Long Span - Ly)
    sec("4. LONG SPAN DESIGN (TEMP STEEL)")
    As_req_long = 0.0018 * b * h_cm
    row("Required As (Long)", "0.0018 · b · h", f"0.0018 · 100 · {h_cm}", f"{fmt(As_req_long)}", "cm²")

    Ab_temp = BAR_INFO[temp_key]['A_cm2']
    s_t_calc = (Ab_temp * 100) / As_req_long
    s_t_max = min(5 * h_cm, 45.0)
    s_temp = math.floor(min(s_t_calc, s_t_max) * 2) / 2
    As_prov_temp = (Ab_temp * 100) / s_temp

    row("Provide Temp Steel", f"Use {temp_key}", f"@{s_temp:.1f} cm", f"{fmt(As_prov_temp)}", "cm²", "OK")

    # 5. Shear & Deflection (UPDATED ACI/EIT)
    sec("5. CHECKS")

    # --- Shear Check ---
    Vu = (wu * Lx) / 2 if support != "Cantilever" else wu * Lx
    Vc = 0.53 * math.sqrt(fc) * b * d
    phi_shear = 0.85
    phi_Vc = phi_shear * Vc

    status_shear = "PASS" if phi_Vc >= Vu else "FAIL"
    row("Shear Check", "φVc ≥ Vu", f"{fmt(phi_Vc)} ≥ {fmt(Vu)}", status_shear, "kg", status_shear)

    # --- Deflection Check (h_min) ---
    if support == "Simply Supported":
        ratio_def = 20.0
    elif support == "Continuous (One End)":
        ratio_def = 24.0
    elif support == "Continuous (Both)":
        ratio_def = 28.0
    elif support == "Cantilever":
        ratio_def = 10.0
    else:
        ratio_def = 20.0

    correction_factor = (0.4 + fy / 7000)
    h_min = (Lx * 100 / ratio_def) * correction_factor

    status_defl = "PASS" if h_cm >= h_min else "CHECK"
    row("Deflection Check", f"L/{ratio_def:.0f} · (0.4+fy/7000)", f"{h_cm} ≥ {fmt(h_min)}", status_defl, "cm",
        status_defl)

    if status_defl == "CHECK":
        rows.append(["Note", f"Req h_min = {fmt(h_min)} cm", "Consider increasing thickness", "-", "-", "WARNING"])

    # Final
    sec("6. CONCLUSION")
    final_status = "COMPLETE" if status_flex == "OK" and status_shear == "PASS" else "REVIEW"
    row("Design Status", "-", "-", final_status, "-", final_status)

    return rows, s_main, s_temp


# ==========================================
# 5. HTML REPORT GENERATOR
# ==========================================
def generate_report(inputs, rows, img_base64):
    table_html = ""
    for r in rows:
        if r[0] == "SECTION":
            table_html += f"<tr class='sec-row'><td colspan='6'>{r[1]}</td></tr>"
        else:
            st_val = r[5]
            cls = "pass-ok"
            if "FAIL" in st_val:
                cls = "pass-no"
            elif "WARNING" in st_val or "CHECK" in st_val:
                cls = "pass-warn"
            elif "INFO" in st_val:
                cls = ""

            val_cls = "load-value" if "Factored" in str(r[0]) else ""

            table_html += f"<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td><td class='{val_cls}'>{r[3]}</td><td>{r[4]}</td><td class='{cls}'>{st_val}</td></tr>"

    html = f"""
    <!DOCTYPE html>
    <html lang="th">
    <head>
        <meta charset="UTF-8">
        <title>One-Way Slab Design Report</title>
        <link href="https://fonts.googleapis.com/css2?family=Sarabun:wght@400;700&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Sarabun', sans-serif; padding: 20px; color: black; }}
            h1, h3 {{ text-align: center; margin: 5px; }}
            .header {{ border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 20px; position: relative; }}
            .id-box {{ position: absolute; top:0; right:0; border: 2px solid #000; padding: 5px 15px; font-weight: bold; font-size: 18px; }}
            .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 20px; }}
            .info-box {{ border: 1px solid #ddd; padding: 10px; }}
            .img-container {{ text-align: center; margin: 20px 0; border: 1px solid #eee; padding: 10px; }}
            img {{ max-width: 80%; height: auto; }}
            table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
            th, td {{ border: 1px solid #444; padding: 6px; }}
            th {{ background-color: #eee; }}
            .sec-row {{ background-color: #ddd; font-weight: bold; }}
            .pass-ok {{ color: green; font-weight: bold; }}
            .pass-no {{ color: red; font-weight: bold; }}
            .pass-warn {{ color: orange; font-weight: bold; }}
            .load-value {{ color: #D32F2F; font-weight: bold; }}

            .footer {{ margin-top: 40px; page-break-inside: avoid; }}
            .sign-box {{ width: 250px; text-align: center; margin-top: 20px; }}
            .line {{ border-bottom: 1px solid #000; margin: 30px 0 5px 0; }}

            /* Print Button Internal */
            .print-btn-internal {{
                background-color: #4CAF50; border: none; color: white; padding: 10px 20px;
                text-align: center; display: inline-block; font-size: 16px; margin-bottom: 20px;
                cursor: pointer; border-radius: 4px; font-family: 'Sarabun'; font-weight: bold;
            }}
            @media print {{ .no-print {{ display: none !important; }} }}
        </style>
    </head>
    <body>
        <div class="no-print" style="text-align: center;">
            <button onclick="window.print()" class="print-btn-internal">🖨️ Print Report</button>
        </div>

        <div class="header">
            <div class="id-box">{inputs['slab_id']}</div>
            <h1>ENGINEERING DESIGN REPORT</h1>
            <h3>RC One-Way Slab Design (ACI 318/EIT)</h3>
        </div>

        <div class="info-grid">
            <div class="info-box">
                <strong>Project:</strong> {inputs['project']}<br>
                <strong>Engineer:</strong> {inputs['engineer']}<br>
                <strong>Date:</strong> 16/12/2568
            </div>
            <div class="info-box">
                <strong>Panel Size:</strong> {inputs['Lx']} x {inputs['Ly']} m ({inputs['support']})<br>
                <strong>Thickness:</strong> {inputs['h']} cm (Cover {inputs['cover']} cm)<br>
                <strong>Materials:</strong> fc'={inputs['fc']}, fy={inputs['fy']} ksc
            </div>
        </div>

        <h3>Design Visualization</h3>
        <div class="img-container">
            <img src="{img_base64}" />
        </div>

        <h3>Calculation Details</h3>
        <table>
            <thead>
                <tr>
                    <th width="25%">Item</th><th width="20%">Formula</th><th width="25%">Substitution</th>
                    <th width="15%">Result</th><th width="8%">Unit</th><th width="7%">Status</th>
                </tr>
            </thead>
            <tbody>
                {table_html}
            </tbody>
        </table>

        <div class="footer">
            <div class="sign-box">
                <div style="text-align: left; font-weight: bold;">Designed by:</div>
                <div class="line"></div>
                <div>({inputs['engineer']})</div>
                <div>Civil Engineer</div>
            </div>
        </div>
    </body>
    </html>
    """
    return html


# ==========================================
# 6. UI MAIN
# ==========================================
st.title("RC Slab Design SDM (One-Way Auto)")

with st.sidebar.form("input_form"):
    st.header("Project Info")
    project = st.text_input("Project Name", "อาคารพักอาศัย 2 ชั้น")
    slab_id = st.text_input("Slab Mark", "S-01")
    engineer = st.text_input("Engineer", "นายไกรฤทธิ์ ด่านพิทักษ์")

    st.header("1. Geometry (Dimensions)")
    c1, c2 = st.columns(2)
    Lx = c1.number_input("Short Span: Lx (m)", value=3.0, step=0.1, min_value=0.1)
    Ly = c2.number_input("Long Span: Ly (m)", value=7.0, step=0.1, min_value=0.1)

    c3, c4 = st.columns(2)
    h = c3.number_input("Thickness (cm)", value=12.0, step=1.0)
    cover = c4.number_input("Cover (cm)", value=2.0, step=0.5)

    st.header("2. Materials")
    c1, c2 = st.columns(2)
    fc = c1.number_input("fc' (ksc)", value=240)
    fy = c2.number_input("fy (ksc)", value=4000)

    st.header("3. Loads & Support")
    c1, c2 = st.columns(2)
    sdl = c1.number_input("SDL (kg/m²)", value=150.0)
    ll = c2.number_input("LL (kg/m²)", value=300.0)

    # Updated Support List
    support = st.selectbox("Support Type", [
        "Simply Supported",
        "Continuous (One End)",
        "Continuous (Both)",
        "Cantilever"
    ])

    st.header("4. Bar Selection")
    st.caption("Select preferred bar size. Spacing will be auto-calculated.")
    mainBar = st.selectbox("Main Bar (Lx)", list(BAR_INFO.keys()), index=3)  # Default DB12
    tempBar = st.selectbox("Temp Bar (Ly)", ['RB6', 'RB9', 'DB10'], index=1)  # Default RB9

    run_btn = st.form_submit_button("Run Auto Design")

if run_btn:
    # Logic to ensure Lx is actually the shorter side (Unless Cantilever which has distinct direction)
    # Note: For Cantilever, Lx is usually the Overhang Length.
    if support != "Cantilever" and Lx > Ly:
        st.warning(f"⚠️ Warning: Input Lx ({Lx}m) is greater than Ly ({Ly}m). Swapping values automatically.")
        Lx, Ly = Ly, Lx

    inputs = {
        'project': project, 'slab_id': slab_id, 'engineer': engineer,
        'Lx': Lx, 'Ly': Ly, 'h': h, 'cover': cover,
        'fc': fc, 'fy': fy, 'sdl': sdl, 'll': ll,
        'support': support, 'mainBar': mainBar, 'tempBar': tempBar
    }

    # 1. Calculate
    rows, s_main, s_temp = process_slab_calculation(inputs)

    # 2. Draw (Pass support type)
    img_base64 = fig_to_base64(plot_slab_section(h, cover, mainBar, s_main, tempBar, s_temp, support))

    # 3. Report
    html_report = generate_report(inputs, rows, img_base64)

    st.success("✅ Auto-Design Complete!")
    components.html(html_report, height=1200, scrolling=True)

else:
    st.info("👈 Please enter slab dimensions (Lx, Ly) and properties to design.")