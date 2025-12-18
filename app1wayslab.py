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
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
    buf.seek(0)
    plt.close(fig)  # Memory cleanup
    return f"data:image/png;base64,{base64.b64encode(buf.read()).decode()}"


# ==========================================
# 3. PLOTTING FUNCTION (Updated: Rectangular Beams & Dimensions)
# ==========================================
def plot_slab_section(Lx_m, h_cm, cover_cm, main_key, s_main, temp_key, s_temp, support_type):
    fig, ax = plt.subplots(figsize=(10, 5))

    # Scale setup: Drawing in meters
    h_m = h_cm / 100.0
    beam_w = 0.25  # width of support beam
    beam_d = 0.50  # depth of support beam

    pad = 0.03 + (cover_cm / 100)  # Rebar offset

    # --- 1. Draw Concrete Geometry ---
    if support_type == "Cantilever":
        # Supports: Fixed at Left
        # Beam (Left)
        ax.add_patch(patches.Rectangle((-beam_w, -beam_d), beam_w, beam_d,
                                       facecolor='white', edgecolor='black', linewidth=1.5))
        # Slab (Extending Right)
        ax.add_patch(patches.Rectangle((0, 0), Lx_m, h_m,
                                       facecolor='#f0f0f0', edgecolor='black', linewidth=1.5))

        # Dimension L (Bottom)
        ax.annotate(text='', xy=(0, -0.15), xytext=(Lx_m, -0.15), arrowprops=dict(arrowstyle='<->'))
        ax.text(Lx_m / 2, -0.25, f"L = {Lx_m:.2f} m", ha='center', fontsize=11, fontweight='bold')

        # Rebar (Top Main)
        ax.plot([-beam_w + 0.05, Lx_m - pad], [h_m - pad, h_m - pad], color='blue', linewidth=3)
        # Hook down
        ax.plot([Lx_m - pad, Lx_m - pad], [h_m - pad, h_m - pad - 0.1], color='blue', linewidth=3)

        # Label Main
        ax.annotate(f"Main(Top): {main_key}@{s_main:.0f}cm",
                    xy=(Lx_m / 2, h_m - pad), xytext=(Lx_m / 2, h_m + 0.3),
                    arrowprops=dict(facecolor='blue', arrowstyle='->'),
                    fontsize=10, color='blue', fontweight='bold', ha='center')

        # Limit
        ax.set_xlim(-beam_w - 0.5, Lx_m + 0.5)

    else:
        # Simply / Continuous
        # Beam Left
        ax.add_patch(patches.Rectangle((-beam_w, -beam_d), beam_w, beam_d,
                                       facecolor='white', edgecolor='black', linewidth=1.5))
        # Beam Right
        ax.add_patch(patches.Rectangle((Lx_m, -beam_d), beam_w, beam_d,
                                       facecolor='white', edgecolor='black', linewidth=1.5))
        # Slab
        ax.add_patch(patches.Rectangle((0, 0), Lx_m, h_m,
                                       facecolor='#f0f0f0', edgecolor='black', linewidth=1.5))

        # Dimension L (Bottom) spans between inside faces of supports
        ax.annotate(text='', xy=(0, -0.2), xytext=(Lx_m, -0.2), arrowprops=dict(arrowstyle='<->'))
        ax.text(Lx_m / 2, -0.3, f"L = {Lx_m:.2f} m", ha='center', fontsize=11, fontweight='bold')

        # Rebar (Bottom Main)
        ax.plot([pad, Lx_m - pad], [pad, pad], color='blue', linewidth=3)
        # Hooks
        ax.plot([pad, pad], [pad, pad + 0.1], color='blue', linewidth=3)
        ax.plot([Lx_m - pad, Lx_m - pad], [pad, pad + 0.1], color='blue', linewidth=3)

        # Label Main
        ax.annotate(f"Main(Bot): {main_key}@{s_main:.0f}cm",
                    xy=(Lx_m / 2, pad), xytext=(Lx_m / 2, h_m + 0.3),
                    arrowprops=dict(facecolor='blue', arrowstyle='->'),
                    fontsize=10, color='blue', fontweight='bold', ha='center')

        # Limit
        ax.set_xlim(-beam_w - 0.5, Lx_m + beam_w + 0.5)

    # --- Common Elements ---

    # Dimension Thickness h (Right Side)
    # Find a good X position for the dimension line (slightly to the right of the structure)
    dim_x = Lx_m + 0.1 if support_type == "Cantilever" else Lx_m + beam_w + 0.1
    ax.annotate(text='', xy=(dim_x, 0), xytext=(dim_x, h_m), arrowprops=dict(arrowstyle='<->'))
    ax.text(dim_x + 0.05, h_m / 2, f"h = {h_m:.2f} m", va='center', fontsize=10, rotation=90)

    # Temp Rebar (Dots)
    # Draw dots along the span
    dot_spacing = 0.25  # visual spacing
    n_dots = int(Lx_m / dot_spacing)
    dot_y = h_m - pad - 0.02 if support_type == "Cantilever" else pad + 0.02 + 0.015  # Below top or Above bottom

    for i in range(1, n_dots + 1):
        cx = i * dot_spacing
        if cx < Lx_m:
            ax.add_patch(patches.Circle((cx, dot_y), radius=0.015, color='red'))

    # Label Temp (Just one label)
    lbl_x = dot_spacing * 2
    ax.annotate(f"Temp: {temp_key}@{s_temp:.0f}cm",
                xy=(lbl_x, dot_y), xytext=(lbl_x + 0.5, dot_y + 0.2 if support_type != "Cantilever" else dot_y - 0.2),
                arrowprops=dict(facecolor='red', arrowstyle='->'),
                fontsize=10, color='red', fontweight='bold')

    # Plot Clean up
    ax.set_ylim(-beam_d - 0.2, h_m + 0.6)
    ax.axis('off')
    ax.set_title(f"Cross Section: {support_type} (Not to Scale)", fontsize=12)
    plt.tight_layout()
    return fig


# ==========================================
# 4. CALCULATION LOGIC (Updated: Auto Thickness)
# ==========================================
def process_slab_calculation(inputs, auto_h_flag):
    rows = []

    def sec(title):
        rows.append(["SECTION", title, "", "", "", "", ""])

    def row(item, formula, subs, result, unit, status=""):
        rows.append([item, formula, subs, result, unit, status])

    # Unpack basic inputs
    fc = inputs['fc'];
    fy = inputs['fy']
    Lx = inputs['Lx'];
    Ly = inputs['Ly']
    # h_cm comes later
    cover_cm = inputs['cover']
    sdl = inputs['sdl'];
    ll = inputs['ll']
    main_key = inputs['mainBar'];
    temp_key = inputs['tempBar']
    support = inputs['support']

    # 1. Geometry Check
    sec("1. GEOMETRY & SLAB TYPE")
    row("Short Span (Lx)", "Input", "-", f"{Lx:.2f}", "m")
    row("Long Span (Ly)", "Input", "-", f"{Ly:.2f}", "m")

    ratio = Ly / Lx
    slab_type = "One-Way Slab" if ratio > 2.0 else "Two-Way Slab"
    status_type = "OK" if ratio > 2.0 else "WARNING"
    row("Ratio Ly/Lx", f"{Ly:.2f} / {Lx:.2f}", "-", f"{ratio:.2f}", "-", status_type)

    if ratio <= 2.0:
        rows.append(
            ["Note", "Ly/Lx ≤ 2.0 acts as Two-Way.", "Design as One-Way is safe but conservative.", "-", "-", "INFO"])

    # 2. Thickness Design (Manual or Auto)
    sec("2. THICKNESS DESIGN (Deflection Control)")

    # Determine Divisor based on support
    if support == "Simply Supported":
        div = 20.0
    elif support == "Continuous (One End)":
        div = 24.0
    elif support == "Continuous (Both)":
        div = 28.0
    elif support == "Cantilever":
        div = 10.0
    else:
        div = 20.0

    # Minimum h formula (ACI/EIT)
    correction_factor = (0.4 + fy / 7000)
    h_min = (Lx * 100 / div) * correction_factor

    if auto_h_flag:
        # Auto calc: Round up to nearest integer
        h_use = math.ceil(h_min)
        calc_note = "Auto-Calculated"
        status_h = "AUTO"
    else:
        # Manual input
        h_use = inputs['h']
        calc_note = "User Input"
        status_h = "CHECK"

    row("Min. Thickness (h_min)", f"L/{div:.0f} · (0.4+fy/7000)", f"{Lx * 100:.0f}/{div:.0f} · {correction_factor:.2f}",
        f"{h_min:.2f}", "cm")

    if not auto_h_flag:
        pass_h = "PASS" if h_use >= h_min else "FAIL (Too Thin)"
        row("Design Thickness (h)", calc_note, f"{h_use} ≥ {h_min:.2f}", f"{h_use:.0f}", "cm", pass_h)
    else:
        row("Design Thickness (h)", f"RoundUp(h_min)", f"Ceil({h_min:.2f})", f"{h_use:.0f}", "cm", "SELECTED")

    # 3. Load Analysis
    sec("3. LOAD ANALYSIS (Design Strip b = 1 m)")
    w_sw = 2400 * (h_use / 100)
    w_dead = w_sw + sdl
    wu = 1.2 * w_dead + 1.6 * ll

    row("Slab Weight (SW)", "2400 · h", f"2400 · {h_use / 100:.2f}", f"{w_sw:.1f}", "kg/m²")
    row("Dead Load (DL)", "SW + SDL", f"{w_sw:.1f} + {sdl}", f"{w_dead:.1f}", "kg/m²")
    row("Factored Load (wu)", "1.2D + 1.6L", f"1.2({w_dead:.0f}) + 1.6({ll})", f"{fmt(wu)}", "kg/m")

    # 4. Flexural Design (Main Steel)
    sec("4. MAIN STEEL DESIGN")

    # Moment Coef
    if support == "Simply Supported":
        coef = 8.0
    elif "Continuous" in support:
        coef = 10.0  # Simplified conservative
    elif support == "Cantilever":
        coef = 2.0
    else:
        coef = 8.0

    Mu_kgm = (wu * Lx ** 2) / coef
    Mu_kgcm = Mu_kgm * 100

    db_main = BAR_INFO[main_key]['d_mm']
    d = h_use - cover_cm - (db_main / 10) / 2

    row("Design Moment (Mu)", f"wu · L² / {coef:.0f}", f"{fmt(wu)}·{Lx}²/{coef:.0f}", f"{fmt(Mu_kgm)}", "kg-m")
    row("Effective Depth (d)", "h - cov - db/2", f"{h_use}-{cover_cm}-{db_main / 20}", f"{d:.2f}", "cm")

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
            status_flex = "FAIL (Section too small)"
        else:
            rho_req = (0.85 * fc / fy) * (1 - math.sqrt(term))
    except:
        rho_req = 0;
        status_flex = "CALC ERROR"

    As_flex_req = rho_req * b * d
    As_min_req = rho_min * b * h_use

    control = "Flexure Controls" if As_flex_req >= As_min_req else "Min Steel Controls"
    As_req_short = max(As_flex_req, As_min_req)

    row("Required As", control, f"max({fmt(As_flex_req)}, {fmt(As_min_req)})", f"{fmt(As_req_short)}", "cm²")

    # Select Main Bar
    Ab_main = BAR_INFO[main_key]['A_cm2']
    s_calc = (Ab_main * 100) / As_req_short
    s_max = min(3 * h_use, 45.0)
    s_main = math.floor(min(s_calc, s_max) * 2) / 2  # Round down to nearest 0.5
    As_prov_main = (Ab_main * 100) / s_main

    row("Provide Main Steel", f"Use {main_key}", f"@{s_main:.1f} cm", f"{fmt(As_prov_main)}", "cm²", status_flex)

    # 5. Temperature Steel
    sec("5. TEMPERATURE STEEL")
    As_req_long = 0.0018 * b * h_use
    row("Required As (Temp)", "0.0018 · b · h", f"0.0018 · 100 · {h_use}", f"{fmt(As_req_long)}", "cm²")

    Ab_temp = BAR_INFO[temp_key]['A_cm2']
    s_t_calc = (Ab_temp * 100) / As_req_long
    s_t_max = min(5 * h_use, 45.0)
    s_temp = math.floor(min(s_t_calc, s_t_max) * 2) / 2
    As_prov_temp = (Ab_temp * 100) / s_temp

    row("Provide Temp Steel", f"Use {temp_key}", f"@{s_temp:.1f} cm", f"{fmt(As_prov_temp)}", "cm²", "OK")

    # 6. Shear Check
    sec("6. SHEAR CHECK")
    Vu = (wu * Lx) / 2 if support != "Cantilever" else wu * Lx
    Vc = 0.53 * math.sqrt(fc) * b * d
    phi_shear = 0.85
    phi_Vc = phi_shear * Vc

    status_shear = "PASS" if phi_Vc >= Vu else "FAIL (Thicken Slab)"
    row("Factored Shear (Vu)", "-", "-", f"{fmt(Vu)}", "kg")
    row("Shear Capacity (φVc)", "0.85 · 0.53√fc · bd", f"0.85 · 0.53√{fc} · 100 · {d:.2f}", f"{fmt(phi_Vc)}", "kg",
        status_shear)

    # Final Return
    return rows, s_main, s_temp, h_use


# ==========================================
# 5. HTML REPORT GENERATOR
# ==========================================
def generate_report(inputs, rows, img_base64, h_final):
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
                <strong>Date:</strong> 18/12/2568
            </div>
            <div class="info-box">
                <strong>Panel Size:</strong> {inputs['Lx']} x {inputs['Ly']} m ({inputs['support']})<br>
                <strong>Thickness:</strong> {h_final:.0f} cm (Cover {inputs['cover']} cm)<br>
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

    # --- UPDATED: Auto Thickness Feature ---
    st.subheader("Thickness Design")
    auto_thick = st.checkbox("✅ Auto-calculate Slab Thickness", value=True,
                             help="Calculate minimum thickness for deflection control automatically")

    c3, c4 = st.columns(2)
    if auto_thick:
        h_input = c3.number_input("Manual Thickness (Ignored)", value=0.0, disabled=True)
    else:
        h_input = c3.number_input("Thickness (cm)", value=12.0, step=1.0)

    cover = c4.number_input("Cover (cm)", value=2.5, step=0.5)

    st.header("2. Materials")
    c1, c2 = st.columns(2)
    fc = c1.number_input("fc' (ksc)", value=240)
    fy = c2.number_input("fy (ksc)", value=4000)

    st.header("3. Loads & Support")
    c1, c2 = st.columns(2)
    sdl = c1.number_input("SDL (kg/m²)", value=150.0)
    ll = c2.number_input("LL (kg/m²)", value=300.0)

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
    # Logic to ensure Lx is actually the shorter side (Unless Cantilever)
    if support != "Cantilever" and Lx > Ly:
        st.warning(f"⚠️ Warning: Input Lx ({Lx}m) is greater than Ly ({Ly}m). Swapping values automatically.")
        Lx, Ly = Ly, Lx

    inputs = {
        'project': project, 'slab_id': slab_id, 'engineer': engineer,
        'Lx': Lx, 'Ly': Ly, 'h': h_input, 'cover': cover,
        'fc': fc, 'fy': fy, 'sdl': sdl, 'll': ll,
        'support': support, 'mainBar': mainBar, 'tempBar': tempBar
    }

    # 1. Calculate (Pass Auto Flag)
    rows, s_main, s_temp, h_final = process_slab_calculation(inputs, auto_thick)

    # 2. Draw (Use h_final)
    img_base64 = fig_to_base64(plot_slab_section(Lx, h_final, cover, mainBar, s_main, tempBar, s_temp, support))

    # 3. Report
    html_report = generate_report(inputs, rows, img_base64, h_final)

    st.success("✅ Auto-Design Complete!")
    components.html(html_report, height=1200, scrolling=True)

else:
    st.info("👈 Please enter slab dimensions (Lx, Ly) and properties to design.")
