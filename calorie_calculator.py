"""
╔══════════════════════════════════════════════════════════════╗
║          BMR & TDEE Calorie Calculator  (Streamlit)          ║
║    ใช้สมการ Harris-Benedict และการวิเคราะห์ Macronutrients   ║
╚══════════════════════════════════════════════════════════════╝
วิธีรัน:
    1. ติดตั้ง Streamlit:  pip install streamlit
    2. รันแอป:             streamlit run calorie_calculator.py
"""

import streamlit as st

# ─────────────────────────────────────────────────────────────
# ⚙️  PAGE CONFIG  (ต้องเรียกก่อน Streamlit command อื่นๆ ทั้งหมด)
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="BMR & TDEE Calculator",
    page_icon="🔥",
    layout="wide",          # ใช้พื้นที่หน้าจอเต็มความกว้าง
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────
# 🎨  CUSTOM CSS  (จัด UI ให้สวยงาม)
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Prompt', sans-serif;
    }

    /* กล่องผลลัพธ์หลัก */
    .result-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        border-radius: 16px;
        padding: 28px;
        text-align: center;
        color: white;
        margin: 8px 0;
        box-shadow: 0 8px 32px rgba(15, 52, 96, 0.4);
    }

    .result-card .label {
        font-size: 0.85rem;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: #a8c0e0;
        margin-bottom: 6px;
    }

    .result-card .value {
        font-size: 2.6rem;
        font-weight: 700;
        color: #e94560;
        line-height: 1.1;
    }

    .result-card .unit {
        font-size: 0.9rem;
        color: #a8c0e0;
        margin-top: 4px;
    }

    /* กล่อง Macronutrient */
    .macro-card {
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        color: white;
        margin: 6px 0;
    }

    .macro-card .macro-label {
        font-size: 0.8rem;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        opacity: 0.8;
        margin-bottom: 4px;
    }

    .macro-card .macro-grams {
        font-size: 2rem;
        font-weight: 700;
        line-height: 1.1;
    }

    .macro-card .macro-kcal {
        font-size: 0.85rem;
        opacity: 0.75;
        margin-top: 2px;
    }

    /* Header */
    .app-header {
        text-align: center;
        padding: 20px 0 10px 0;
    }

    .app-header h1 {
        font-size: 2.4rem;
        font-weight: 700;
        background: linear-gradient(90deg, #e94560, #0f3460);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .app-header p {
        color: #888;
        font-size: 1rem;
        margin-top: -8px;
    }

    /* ข้อความอธิบายสมการ */
    .formula-box {
        background: #f8f9ff;
        border-left: 4px solid #0f3460;
        border-radius: 0 8px 8px 0;
        padding: 14px 18px;
        font-size: 0.88rem;
        color: #333;
        margin: 10px 0;
    }

    /* Divider แบบ custom */
    .section-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #0f3460;
        border-bottom: 2px solid #e94560;
        padding-bottom: 6px;
        margin: 20px 0 14px 0;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# 🧮  FUNCTIONS  (ฟังก์ชันคำนวณหลักทั้งหมด)
# ─────────────────────────────────────────────────────────────

def calculate_bmr(gender: str, weight_kg: float, height_cm: float, age: int) -> float:
    """
    คำนวณ BMR (Basal Metabolic Rate) ด้วยสมการ Harris-Benedict (ฉบับปรับปรุง)
    BMR = พลังงานขั้นต่ำที่ร่างกายต้องการต่อวัน ถ้านอนนิ่งๆ ตลอดเวลา

    สมการ Harris-Benedict:
    ─────────────────────────────────────────────────────────
    ชาย:   BMR = 88.362 + (13.397 × น้ำหนักกก.)
                        + (4.799  × ส่วนสูงซม.)
                        − (5.677  × อายุปี)

    หญิง:  BMR = 447.593 + (9.247  × น้ำหนักกก.)
                          + (3.098  × ส่วนสูงซม.)
                          − (4.330  × อายุปี)
    ─────────────────────────────────────────────────────────
    ค่าคงที่แต่ละตัวมาจากการวิจัยทางสถิติ (regression analysis)
    บนกลุ่มตัวอย่างประชากร ไม่ใช่ค่าที่คำนวณเองได้ทางตรง

    Parameters:
        gender    : "ชาย" หรือ "หญิง"
        weight_kg : น้ำหนัก (กิโลกรัม)
        height_cm : ส่วนสูง (เซนติเมตร)
        age       : อายุ (ปี)

    Returns:
        bmr (float): ค่า BMR หน่วย kcal/วัน
    """
    if gender == "ชาย":
        bmr = 88.362 + (13.397 * weight_kg) + (4.799 * height_cm) - (5.677 * age)
    else:  # หญิง
        bmr = 447.593 + (9.247 * weight_kg) + (3.098 * height_cm) - (4.330 * age)
    return bmr


def calculate_tdee(bmr: float, activity_factor: float) -> float:
    """
    คำนวณ TDEE (Total Daily Energy Expenditure)
    TDEE = พลังงานรวมที่ร่างกายต้องการต่อวัน รวมกิจกรรมที่ทำจริงๆ

    สมการ:
        TDEE = BMR × Activity Factor

    Activity Factor คือตัวคูณที่สะท้อนความเข้มข้นของกิจกรรมในชีวิตประจำวัน
    ยิ่งออกกำลังกายมาก ค่า Factor ยิ่งสูง → ต้องการพลังงานมากขึ้น

    Parameters:
        bmr             : ค่า BMR (kcal/วัน)
        activity_factor : ตัวคูณกิจกรรม (ดู ACTIVITY_LEVELS ด้านล่าง)

    Returns:
        tdee (float): ค่า TDEE หน่วย kcal/วัน
    """
    return bmr * activity_factor


def calculate_macros(tdee: float) -> dict:
    """
    คำนวณปริมาณ Macronutrients (สารอาหารหลัก 3 ชนิด) จาก TDEE

    สัดส่วนที่แนะนำทั่วไป (อ้างอิง AMDR — Acceptable Macronutrient Distribution Range):
    ──────────────────────────────────────────────────────────
    | สารอาหาร     | % ของพลังงานรวม | พลังงาน/กรัม |
    |──────────────|────────────────|────────────|
    | โปรตีน       |      25%       |   4 kcal/g  |
    | คาร์โบไฮเดรต |      50%       |   4 kcal/g  |
    | ไขมัน        |      25%       |   9 kcal/g  |
    ──────────────────────────────────────────────────────────

    วิธีคำนวณกรัม:
        กรัม = (TDEE × เปอร์เซ็นต์) ÷ พลังงานต่อกรัม
    ตัวอย่าง โปรตีน:
        กรัม = (TDEE × 0.25) ÷ 4

    Parameters:
        tdee : ค่า TDEE (kcal/วัน)

    Returns:
        dict ที่มีคีย์ protein, carbs, fat
        แต่ละคีย์มีค่า kcal และ grams
    """
    # ─── สัดส่วนพลังงาน (ปรับได้ตามเป้าหมาย) ───
    PROTEIN_RATIO = 0.25   # 25% ของ TDEE
    CARBS_RATIO   = 0.50   # 50% ของ TDEE
    FAT_RATIO     = 0.25   # 25% ของ TDEE

    # ─── ค่าพลังงานต่อกรัม (ค่าคงที่ทางชีวเคมี) ───
    PROTEIN_KCAL_PER_G = 4   # โปรตีน 1 กรัม = 4 kcal
    CARBS_KCAL_PER_G   = 4   # คาร์โบไฮเดรต 1 กรัม = 4 kcal
    FAT_KCAL_PER_G     = 9   # ไขมัน 1 กรัม = 9 kcal (มากกว่าเพราะโครงสร้างโมเลกุลซับซ้อนกว่า)

    protein_kcal = tdee * PROTEIN_RATIO
    carbs_kcal   = tdee * CARBS_RATIO
    fat_kcal     = tdee * FAT_RATIO

    return {
        "protein": {
            "kcal":  protein_kcal,
            "grams": protein_kcal / PROTEIN_KCAL_PER_G,
        },
        "carbs": {
            "kcal":  carbs_kcal,
            "grams": carbs_kcal / CARBS_KCAL_PER_G,
        },
        "fat": {
            "kcal":  fat_kcal,
            "grams": fat_kcal / FAT_KCAL_PER_G,
        },
    }


def get_calorie_goal(tdee: float) -> dict:
    """
    แนะนำแคลอรีสำหรับเป้าหมายต่างๆ

    หลักการ (Energy Balance):
    ─────────────────────────────────────────────────────────
    ลดน้ำหนัก  : กินน้อยกว่า TDEE → ร่างกายดึงไขมันสำรองมาใช้
                ขาดดุล 500 kcal/วัน ≈ ลด ~0.5 กก./สัปดาห์
    คงน้ำหนัก  : กิน = TDEE → น้ำหนักคงที่
    เพิ่มน้ำหนัก: กินมากกว่า TDEE → ร่างกายสะสมมวลกล้ามเนื้อ/ไขมัน
                เกิน 300 kcal/วัน ≈ เพิ่ม ~0.3 กก./สัปดาห์
    ─────────────────────────────────────────────────────────
    """
    return {
        "ลดน้ำหนัก (-500 kcal)":  round(tdee - 500),
        "คงน้ำหนักเดิม":           round(tdee),
        "เพิ่มน้ำหนัก (+300 kcal)": round(tdee + 300),
    }


# ─────────────────────────────────────────────────────────────
# 📋  DATA  (ข้อมูลระดับกิจกรรม — Activity Factor)
# ─────────────────────────────────────────────────────────────

# Dictionary: key = ชื่อระดับกิจกรรม, value = (factor, คำอธิบาย)
# Activity Factor มาจากการวิจัยของ Harris & Benedict (1919) และปรับปรุงโดย McArdle et al.
ACTIVITY_LEVELS = {
    "🛋️  ไม่ค่อยขยับ (นั่งทำงาน/เรียนตลอดวัน)":           (1.2,  "Sedentary"),
    "🚶 เคลื่อนไหวเล็กน้อย (ออกกำลังกาย 1–3 วัน/สัปดาห์)": (1.375, "Lightly Active"),
    "🏃 กลางๆ (ออกกำลังกาย 3–5 วัน/สัปดาห์)":              (1.55,  "Moderately Active"),
    "💪 ขยันมาก (ออกกำลังกาย 6–7 วัน/สัปดาห์)":            (1.725, "Very Active"),
    "🏋️  นักกีฬา/งานหนักมาก (ซ้อมหนักทุกวัน 2 รอบ)":       (1.9,   "Extra Active"),
}


# ─────────────────────────────────────────────────────────────
# 🖥️  UI LAYOUT
# ─────────────────────────────────────────────────────────────

# ── Header ──
st.markdown("""
<div class="app-header">
    <h1>🔥 BMR & TDEE Calculator</h1>
    <p>คำนวณความต้องการพลังงานและสารอาหารด้วยสมการ Harris-Benedict</p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ── แบ่งหน้าจอเป็น 2 ส่วน: ซ้าย = กรอกข้อมูล, ขวา = ผลลัพธ์ ──
left_col, right_col = st.columns([1, 1.6], gap="large")


# ════════════════════════════════════════════
#  LEFT COLUMN — ส่วนกรอกข้อมูล
# ════════════════════════════════════════════
with left_col:
    st.markdown('<div class="section-title">📝 ข้อมูลส่วนตัว</div>', unsafe_allow_html=True)

    # ── เพศ ──
    gender = st.radio(
        "เพศ",
        options=["ชาย", "หญิง"],
        horizontal=True,
        help="สมการ Harris-Benedict ใช้เพศในการปรับค่าคงที่ เพราะชาย/หญิงมีสัดส่วนกล้ามเนื้อต่างกัน",
    )

    # ── อายุ ──
    age = st.number_input(
        "อายุ (ปี)",
        min_value=10,
        max_value=100,
        value=18,
        step=1,
        help="อายุยิ่งมาก BMR ยิ่งลดลง เพราะมวลกล้ามเนื้อมักลดลงตามอายุ",
    )

    # ── แบ่งน้ำหนักและส่วนสูงเป็น 2 คอลัมน์ย่อย ──
    w_col, h_col = st.columns(2)

    with w_col:
        weight = st.number_input(
            "น้ำหนัก (กก.)",
            min_value=20.0,
            max_value=300.0,
            value=60.0,
            step=0.5,
            format="%.1f",
        )

    with h_col:
        height = st.number_input(
            "ส่วนสูง (ซม.)",
            min_value=100.0,
            max_value=250.0,
            value=170.0,
            step=0.5,
            format="%.1f",
        )

    st.markdown("---")
    st.markdown('<div class="section-title">🏃 ระดับกิจกรรม</div>', unsafe_allow_html=True)

    # ── ระดับกิจกรรม (Selectbox แสดงเป็น dropdown) ──
    activity_label = st.selectbox(
        "เลือกระดับกิจกรรมที่ตรงกับชีวิตประจำวันมากที่สุด",
        options=list(ACTIVITY_LEVELS.keys()),
        index=0,
    )

    # ดึงค่า factor และชื่อ eng จาก dict
    activity_factor, activity_eng = ACTIVITY_LEVELS[activity_label]

    # แสดง Factor ที่เลือก
    st.info(f"**Activity Factor:** × {activity_factor}  |  *{activity_eng}*")

    # ── ปุ่มคำนวณ ──
    st.markdown("<br>", unsafe_allow_html=True)
    calculate_btn = st.button("🔥 คำนวณเลย!", type="primary", use_container_width=True)


# ════════════════════════════════════════════
#  RIGHT COLUMN — ส่วนแสดงผลลัพธ์
# ════════════════════════════════════════════
with right_col:
    # คำนวณเสมอ (ไม่ต้องรอกดปุ่ม ก็แสดงผล real-time)
    # แต่ถ้ากดปุ่มจะ highlight ด้วย st.balloons()
    bmr  = calculate_bmr(gender, weight, height, age)
    tdee = calculate_tdee(bmr, activity_factor)

    if calculate_btn:
        st.balloons()

    # ── BMR & TDEE Cards ──
    st.markdown('<div class="section-title">📊 ผลการคำนวณ</div>', unsafe_allow_html=True)

    bmr_col, tdee_col = st.columns(2)

    with bmr_col:
        st.markdown(f"""
        <div class="result-card">
            <div class="label">⚡ BMR</div>
            <div class="value">{bmr:,.0f}</div>
            <div class="unit">kcal / วัน</div>
            <hr style="border-color:#ffffff22; margin:12px 0">
            <div style="font-size:0.78rem; color:#a8c0e0; line-height:1.5">
                พลังงานขั้นต่ำของร่างกาย<br>ถ้านอนนิ่งๆ ไม่ทำอะไรเลย
            </div>
        </div>
        """, unsafe_allow_html=True)

    with tdee_col:
        st.markdown(f"""
        <div class="result-card">
            <div class="label">🔥 TDEE</div>
            <div class="value">{tdee:,.0f}</div>
            <div class="unit">kcal / วัน</div>
            <hr style="border-color:#ffffff22; margin:12px 0">
            <div style="font-size:0.78rem; color:#a8c0e0; line-height:1.5">
                พลังงานรวมที่ต้องการ<br>ตามกิจกรรมจริงของคุณ
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── แสดงสมการที่ใช้ ──
    with st.expander("🧮 ดูสมการที่ใช้คำนวณ", expanded=False):
        if gender == "ชาย":
            formula_text = (
                f"BMR = 88.362 + (13.397 × {weight}) + (4.799 × {height}) − (5.677 × {age})"
                f"\n     = **{bmr:,.1f} kcal**"
            )
        else:
            formula_text = (
                f"BMR = 447.593 + (9.247 × {weight}) + (3.098 × {height}) − (4.330 × {age})"
                f"\n     = **{bmr:,.1f} kcal**"
            )
        tdee_formula = f"TDEE = {bmr:,.1f} × {activity_factor} = **{tdee:,.1f} kcal**"

        st.markdown(f"**สมการ Harris-Benedict ({gender}):**")
        st.code(formula_text, language="")
        st.markdown("**สมการ TDEE:**")
        st.code(tdee_formula, language="")

    st.markdown("---")

    # ── Macronutrients ──
    st.markdown('<div class="section-title">🥗 สารอาหารที่แนะนำต่อวัน</div>', unsafe_allow_html=True)

    macros = calculate_macros(tdee)

    p_col, c_col, f_col = st.columns(3)

    with p_col:
        st.markdown(f"""
        <div class="macro-card" style="background: linear-gradient(135deg, #e94560, #c0392b);">
            <div class="macro-label">🥩 โปรตีน</div>
            <div class="macro-grams">{macros['protein']['grams']:.0f} g</div>
            <div class="macro-kcal">{macros['protein']['kcal']:.0f} kcal (25%)</div>
        </div>
        """, unsafe_allow_html=True)

    with c_col:
        st.markdown(f"""
        <div class="macro-card" style="background: linear-gradient(135deg, #f39c12, #d68910);">
            <div class="macro-label">🍚 คาร์โบไฮเดรต</div>
            <div class="macro-grams">{macros['carbs']['grams']:.0f} g</div>
            <div class="macro-kcal">{macros['carbs']['kcal']:.0f} kcal (50%)</div>
        </div>
        """, unsafe_allow_html=True)

    with f_col:
        st.markdown(f"""
        <div class="macro-card" style="background: linear-gradient(135deg, #27ae60, #1e8449);">
            <div class="macro-label">🥑 ไขมัน</div>
            <div class="macro-grams">{macros['fat']['grams']:.0f} g</div>
            <div class="macro-kcal">{macros['fat']['kcal']:.0f} kcal (25%)</div>
        </div>
        """, unsafe_allow_html=True)

    # ── Progress bars แสดงสัดส่วน ──
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**สัดส่วน Macronutrients:**")

    # Streamlit's progress bar รับค่า 0.0–1.0
    st.write("🥩 โปรตีน (25%)")
    st.progress(0.25)
    st.write("🍚 คาร์โบไฮเดรต (50%)")
    st.progress(0.50)
    st.write("🥑 ไขมัน (25%)")
    st.progress(0.25)

    st.markdown("---")

    # ── Calorie Goals ──
    st.markdown('<div class="section-title">🎯 แนะนำแคลอรีตามเป้าหมาย</div>', unsafe_allow_html=True)

    goals = get_calorie_goal(tdee)

    g1, g2, g3 = st.columns(3)
    cols_goals = [g1, g2, g3]
    emojis      = ["⬇️", "⚖️", "⬆️"]
    colors      = ["#3498db", "#2ecc71", "#e74c3c"]

    for col, (label, kcal), emoji, color in zip(cols_goals, goals.items(), emojis, colors):
        with col:
            st.markdown(f"""
            <div style="background:{color}18; border:2px solid {color}55;
                        border-radius:12px; padding:16px; text-align:center;">
                <div style="font-size:1.5rem">{emoji}</div>
                <div style="font-size:1.4rem; font-weight:700; color:{color}">{kcal:,}</div>
                <div style="font-size:0.72rem; color:#555; margin-top:4px">{label}</div>
            </div>
            """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# 📌  FOOTER
# ─────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align:center; color:#aaa; font-size:0.8rem; padding:16px 0">
    🔬 ใช้สมการ <b>Harris-Benedict (Revised)</b> | สัดส่วน Macro อ้างอิง <b>AMDR Guidelines</b><br>
    ⚠️ ผลลัพธ์เป็นการประมาณการเท่านั้น ควรปรึกษานักโภชนาการสำหรับแผนที่เหมาะกับคุณโดยเฉพาะ
</div>
""", unsafe_allow_html=True)
