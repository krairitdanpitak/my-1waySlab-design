import streamlit as st
import matplotlib

# ตั้งค่า Backend เป็น Agg เพื่อป้องกันปัญหา Thread ใน Streamlit
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

    /* สไตล์ปุ่ม Print */
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

    /* ตารางรายงาน */
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
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=120)
    buf.seek(0)
    plt.close(fig)  # Memory cleanup
    return f"data:image/png;base64,{base64.b64encode(buf.read()).decode()}"


# ==========================================
# 3. PLOTTING FUNCTION (SCHEMATIC VERSION)
# ==========================================
def plot_slab_section_schematic(Lx_real, h_cm_real, cover_cm, main_key, s_main, temp_key, s_temp, support_type):
    # สร้างรูปภาพ
    fig, ax = plt.subplots(figsize=(10, 5))

    # --- CONSTANTS สำหรับการวาด (Schematic Only) ---
    # ไม่ใช้สเกลจริง เพื่อความสวยงามและเห็นเหล็กชัดเจนตามที่ขอ
    DRAW_L = 5.0  # ความยาวพื้นในรูปวาด (สมมติ)
    DRAW_H = 0.8  # ความหนาพื้นในรูปวาด (หนาพอที่จะใส่เหล็กได้สบายๆ)
    BEAM_W = 0.5  # ความกว้างคาน
    BEAM_D = 1.0  # ความลึกคาน
    PAD = 0.15  # ระยะหุ้มสมมติในรูป (เพื่อให้เหล็กไม่ชนขอบ)

    # สี
    C_CONC = '#FFFFFF'  # สีคอนกรีต (ขาว)
    C_LINE = 'black'  # เส้นขอบ
    C_MAIN = 'blue'  # เหล็กเมน
    C_TEMP = 'red'  # เหล็กกันร้าว

    # 1. วาดคอนกรีต (Concrete)
    # คานซ้าย
    ax.add_patch(patches.Rectangle((-BEAM_W, -BEAM_D), BEAM_W, BEAM_D + DRAW_H, facecolor=C_CONC, edgecolor=C_LINE,
                                   linewidth=1.5))
    # คานขวา
    ax.add_patch(patches.Rectangle((DRAW_L, -BEAM_D), BEAM_W, BEAM_D + DRAW_H, facecolor=C_CONC, edgecolor=C_LINE,
                                   linewidth=1.5))
    # พื้น
    ax.add_patch(patches.Rectangle((0, 0), DRAW_L, DRAW_H, facecolor=C_CONC, edgecolor=C_LINE, linewidth=1.5))

    # 2. วาดเหล็กเสริม (Rebar)
    # ตำแหน่ง Y ของเหล็ก (สมมติให้สวยงาม ไม่ใช่ระยะจริง)
    y_top = DRAW_H - PAD
    y_bot = PAD

    if support_type == "Cantilever":
        # --- พื้นยื่น (Cantilever) ---
        # เหล็กบน (Main Top)
        ax.plot([-BEAM_W / 2, DRAW_L - PAD], [y_top, y_top], color=C_MAIN, linewidth=3)  # เส้นนอน
        ax.plot([DRAW_L - PAD, DRAW_L - PAD], [y_top, y_top - 0.3], color=C_MAIN, linewidth=3)  # งอลงปลาย
        ax.plot([-BEAM_W / 2, -BEAM_W / 2], [y_top, y_top - 0.5], color=C_MAIN, linewidth=3)  # งอลงในคาน

        # เหล็กกันร้าว (Temp) - จุดแดงด้านล่าง
        n_dots = 6
        spacing = DRAW_L / (n_dots + 1)
        for i in range(1, n_dots + 1):
            ax.add_patch(patches.Circle((i * spacing, y_bot), radius=0.06, color=C_TEMP))

        # Label Text
        txt_main = f"Main(Top): {main_key}@{s_main:.0f}cm"
        txt_temp = f"Temp(Bot): {temp_key}@{s_temp:.0f}cm"

    else:
        # --- พื้นช่วงเดียว / ต่อเนื่อง (Simply / Continuous) ---
        # เหล็กบน (Top Bar - เสริมหัวเสา/คาน)
        hook_len = DRAW_L * 0.25
        # ซ้าย
        ax.plot([-BEAM_W / 2, hook_len], [y_top, y_top], color=C_MAIN, linewidth=3)
        ax.plot([-BEAM_W / 2, -BEAM_W / 2], [y_top, y_top - 0.4], color=C_MAIN, linewidth=3)  # Hook ลงคาน
        # ขวา
        ax.plot([DRAW_L - hook_len, DRAW_L + BEAM_W / 2], [y_top, y_top], color=C_MAIN, linewidth=3)
        ax.plot([DRAW_L + BEAM_W / 2, DRAW_L + BEAM_W / 2], [y_top, y_top - 0.4], color=C_MAIN,
                linewidth=3)  # Hook ลงคาน

        # เหล็กล่าง (Bottom Bar - รับโมเมนต์บวก)
        ax.plot([PAD, DRAW_L - PAD], [y_bot, y_bot], color=C_MAIN, linewidth=3)
        # Hook ขึ้น (ดัดคอม้า หรือ งอฉาก)
        ax.plot([PAD, PAD], [y_bot, y_bot + 0.25], color=C_MAIN, linewidth=3)
        ax.plot([DRAW_L - PAD, DRAW_L - PAD], [y_bot, y_bot + 0.25], color=C_MAIN, linewidth=3)

        # เหล็กกันร้าว (Temp) - จุดแดงวางบนเหล็กล่าง
        n_dots = 7
        spacing = DRAW_L / n_dots
        for i in range(1, n_dots):
            # วางจุดเหนือเหล็กล่างเล็กน้อย
            ax.add_patch(patches.Circle((i * spacing, y_bot + 0.15), radius=0.06, color=C_TEMP))

        # Label Text setup
        txt_main = f"Main(Bot): {main_key}@{s_main:.0f}cm"
        txt_temp = f"Temp: {temp_key}@{s_temp:.0f}cm"

        # Label Box Callout (เหมือนรูปตัวอย่าง)
        # Main Bar Label
        bbox_props = dict(boxstyle="round,pad=0.3", fc="white", ec="blue", lw=1)
        ax.annotate(txt_main, xy=(DRAW_L / 2, y_bot), xytext=(DRAW_L / 2, -0.6),
                    ha='center', va='center', color='blue', fontweight='bold',
                    bbox=bbox_props, arrowprops=dict(arrowstyle='->', color='blue'))

        # Temp Bar Label
        bbox_props_red = dict(boxstyle="round,pad=0.3", fc="white", ec="red", lw=1)
        ax.annotate(txt_temp, xy=(DRAW_L / 2 + 0.5, y_bot + 0.15), xytext=(DRAW_L / 2 + 0.5, DRAW_H + 0.4),
                    ha='center', va='center', color='red', fontweight='bold',
                    bbox=bbox_props_red, arrowprops=dict(arrowstyle='->', color='red'))

    # 3. Dimensions (เส้นบอกระยะ)
    # บอกความยาว L (ด้านล่าง)
    ax.annotate(text='', xy=(0, -0.2), xytext=(DRAW_L, -0.2), arrowprops=dict(arrowstyle='<->', color='black'))
    ax.text(DRAW_L / 2, -0.35, f"L = {Lx_real:.2f} m", ha='center', fontsize=12, fontweight='bold')

    # บอกความหนา h (ด้านขวา)
    # วาดเส้นบอกระยะด้านขวาของคานขวา
    dim_x = DRAW_L + BEAM_W + 0.3
    ax.annotate(text='', xy=(dim_x, 0), xytext=(dim_x, DRAW_H), arrowprops=dict(arrowstyle='<->', color='black'))
    # หมุนตัวหนังสือ 90 องศา
    ax.text(dim_x + 0.15, DRAW_H / 2, f"h = {h_cm_real / 100:.2f} m", ha='center', va='center', rotation=90,
            fontsize=12, fontweight='bold')

    # Cleanup Plot Area
    ax.set_xlim(-BEAM_W - 0.5, DRAW_L + BEAM_W + 1.0)
    ax.set_ylim(-BEAM_D - 0.5, DRAW_H + 1.0)
    ax.axis('off')  # ปิดแกนทั้งหมด

    plt.tight_layout()
    return fig


# ==========================================
# 4. CALCULATION LOGIC
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

    # 2. Thickness Design (Manual or Auto)
    sec("2. THICKNESS DESIGN (Deflection Control)")

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

    correction_factor = (0.4 + fy / 7000)
    h_min = (Lx * 100 / div) * correction_factor

    if auto_h_flag:
        h_use = math.ceil(h_min)
        calc_note = "Auto-Calculated"
        pass_h = "SELECTED"
    else:
        h_use = inputs['h']
        calc_note = "User Input"
        pass_h = "PASS" if h_use >= h_min else "FAIL (Too Thin)"

    row("Min. Thickness (h_min)", f"L/{div:.0f} · (0.4+fy/7000)", f"{Lx * 100:.0f}/{div:.0f} · {correction_factor:.2f}",
        f"{h_min:.2f}", "cm")
    row("Design Thickness (h)", calc_note, f"{h_use} ≥ {h_min:.2f}", f"{h_use:.0f}", "cm", pass_h)

    # 3. Load Analysis
    sec("3. LOAD ANALYSIS (Design Strip b = 1 m)")
    w_sw = 2400 * (h_use / 100)
    w_dead = w_sw + sdl
    wu = 1.2 * w_dead + 1.6 * ll

    row("Factored Load (wu)", "1.2D + 1.6L", f"1.2({w_dead + w_sw:.0f}) + 1.6({ll})", f"{fmt(wu)}", "kg/m")

    # 4. Flexural Design
    sec("4. MAIN STEEL DESIGN")

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
    d = h_use - cover_cm - (db_main / 10) / 2

    row("Design Moment (Mu)", f"wu · L² / {coef:.0f}", f"{fmt(wu)}·{Lx}²/{coef:.0f}", f"{fmt(Mu_kgm)}", "kg-m")

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
    As_req_short = max(As_flex_req, As_min_req)

    # Main Bar Selection
    Ab_main = BAR_INFO[main_key]['A_cm2']
    s_calc = (Ab_main * 100) / As_req_short
    s_max = min(3 * h_use, 45.0)
    s_main = math.floor(min(s_calc, s_max) * 2) / 2
    As_prov_main = (Ab_main * 100) / s_main

    row("Provide Main Steel", f"Use {main_key}", f"@{s_main:.1f} cm", f"{fmt(As_prov_main)}", "cm²", status_flex)

    # 5. Temp Steel
    sec("5. TEMPERATURE STEEL")
    As_req_long = 0.0018 * b * h_use
    Ab_temp = BAR_INFO[temp_key]['A_cm2']
    s_t_calc = (Ab_temp * 100) / As_req_long
    s_t_max = min(5 * h_use, 45.0)
    s_temp = math.floor(min(s_t_calc, s_t_max) * 2) / 2
    As_prov_temp = (Ab_temp * 100) / s_temp

    row("Provide Temp Steel", f"Use {temp_key}", f"@{s_temp:.1f} cm", f"{fmt(As_prov_temp)}", "cm²", "OK")

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
            elif "WARNING" in st_val:
                cls = "pass-warn"
            elif "SELECTED" in st_val:
                cls = "pass-ok"

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
            .footer {{ margin-top: 40px; }}
            .sign-box {{ width: 250px; text-align: center; margin-top: 20px; }}
            .line {{ border-bottom: 1px solid #000; margin: 30px 0 5px 0; }}
            .print-btn-internal {{ background-color: #4CAF50; border: none; color: white; padding: 10px 20px; cursor: pointer; border-radius: 4px; font-family: 'Sarabun'; }}
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

        <h3>Design Visualization (Schematic)</h3>
        <div class="img-container">
            <img src="{img_base64}" />
        </div>

        <h3>Calculation Details</h3>
        <table>
            <thead>
                <tr><th width="25%">Item</th><th width="20%">Formula</th><th width="25%">Substitution</th><th width="15%">Result</th><th width="8%">Unit</th><th width="7%">Status</th></tr>
            </thead>
            <tbody>{table_html}</tbody>
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

    st.subheader("Thickness Design")
    auto_thick = st.checkbox("✅ Auto-calculate Thickness", value=True)

    c3, c4 = st.columns(2)
    if auto_thick:
        h_input = c3.number_input("Manual Thickness", value=0.0, disabled=True)
    else:
        h_input = c3.number_input("Thickness (cm)", value=12.0, step=1.0)

    cover = c4.number_input("Cover (cm)", value=2.5, step=0.5)

    st.header("2. Materials & Loads")
    fc = st.number_input("fc' (ksc)", value=240)
    fy = st.number_input("fy (ksc)", value=4000)
    sdl = st.number_input("SDL (kg/m²)", value=150.0)
    ll = st.number_input("LL (kg/m²)", value=300.0)

    support = st.selectbox("Support Type",
                           ["Simply Supported", "Continuous (One End)", "Continuous (Both)", "Cantilever"])

    st.header("3. Bar Selection")
    # Updated: Temp Bar uses full list like Main Bar
    mainBar = st.selectbox("Main Bar (Lx)", list(BAR_INFO.keys()), index=3)
    tempBar = st.selectbox("Temp Bar (Ly)", list(BAR_INFO.keys()), index=1)

    run_btn = st.form_submit_button("Run Auto Design")

if run_btn:
    if support != "Cantilever" and Lx > Ly:
        st.warning(f"⚠️ Warning: Input Lx ({Lx}m) > Ly ({Ly}m). Swapping automatically.")
        Lx, Ly = Ly, Lx

    inputs = {
        'project': project, 'slab_id': slab_id, 'engineer': engineer,
        'Lx': Lx, 'Ly': Ly, 'h': h_input, 'cover': cover,
        'fc': fc, 'fy': fy, 'sdl': sdl, 'll': ll,
        'support': support, 'mainBar': mainBar, 'tempBar': tempBar
    }

    # Calculate
    rows, s_main, s_temp, h_final = process_slab_calculation(inputs, auto_thick)

    # Draw (Schematic)
    img_base64 = fig_to_base64(
        plot_slab_section_schematic(Lx, h_final, cover, mainBar, s_main, tempBar, s_temp, support))

    # Report
    html_report = generate_report(inputs, rows, img_base64, h_final)

    st.success("✅ Design Complete!")
    components.html(html_report, height=1200, scrolling=True)
else:
    st.info("👈 Please enter data on the sidebar to start design.")
