"""
╔══════════════════════════════════════════════════════════════════╗
║       BMR & TDEE Calculator + AI Food Analyzer (Streamlit)       ║
║  ใช้สมการ Harris-Benedict + Gemini Vision API วิเคราะห์รูปอาหาร  ║
╚══════════════════════════════════════════════════════════════════╝
วิธีรัน:
    1. pip install streamlit google-generativeai
    2. streamlit run calorie_calculator.py

⚠️  ต้องมี Gemini API Key (ฟรี!) → https://aistudio.google.com/app/apikey
"""

import streamlit as st
import google.generativeai as genai  # Google Gemini SDK — pip install google-generativeai
import base64      # แปลงรูปภาพเป็น base64 string เพื่อส่งให้ API
import json        # แปลง JSON string จาก AI response เป็น Python dict
import re          # Regular Expression — ใช้หา JSON ในข้อความ

# ─────────────────────────────────────────────────────────────
# ⚙️  PAGE CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="BMR & TDEE + AI Food Analyzer",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────
# 🎨  CUSTOM CSS
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Prompt', sans-serif; }

    .result-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        border-radius: 16px; padding: 28px; text-align: center;
        color: white; margin: 8px 0;
        box-shadow: 0 8px 32px rgba(15, 52, 96, 0.4);
    }
    .result-card .label {
        font-size: 0.85rem; letter-spacing: 2px;
        text-transform: uppercase; color: #a8c0e0; margin-bottom: 6px;
    }
    .result-card .value { font-size: 2.6rem; font-weight: 700; color: #e94560; line-height: 1.1; }
    .result-card .unit  { font-size: 0.9rem; color: #a8c0e0; margin-top: 4px; }

    .macro-card { border-radius: 12px; padding: 20px; text-align: center; color: white; margin: 6px 0; }
    .macro-card .macro-label { font-size: 0.8rem; letter-spacing: 1.5px; text-transform: uppercase; opacity: 0.8; margin-bottom: 4px; }
    .macro-card .macro-grams { font-size: 2rem; font-weight: 700; line-height: 1.1; }
    .macro-card .macro-kcal  { font-size: 0.85rem; opacity: 0.75; margin-top: 2px; }

    .app-header { text-align: center; padding: 20px 0 10px 0; }
    .app-header h1 {
        font-size: 2.4rem; font-weight: 700;
        background: linear-gradient(90deg, #e94560, #0f3460);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
    }
    .app-header p { color: #888; font-size: 1rem; margin-top: -8px; }

    .section-title {
        font-size: 1.1rem; font-weight: 600; color: #0f3460;
        border-bottom: 2px solid #e94560; padding-bottom: 6px;
        margin: 20px 0 14px 0; display: inline-block;
    }

    /* Food Analysis Card */
    .food-result-card {
        background: linear-gradient(135deg, #0d2137, #1a3a5c);
        border-radius: 16px; padding: 24px; color: white;
        margin: 12px 0; box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }
    .food-name { font-size: 1.6rem; font-weight: 700; color: #ffd700; margin-bottom: 4px; }
    .food-portion { font-size: 0.85rem; color: #a8c0e0; margin-bottom: 16px; }
    .food-kcal-big { font-size: 3rem; font-weight: 700; color: #e94560; line-height: 1; }
    .food-kcal-label { font-size: 0.85rem; color: #a8c0e0; margin-top: 2px; }
    .confidence-badge {
        display: inline-block; padding: 4px 12px; border-radius: 20px;
        font-size: 0.78rem; font-weight: 600; margin-top: 8px;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# 🧮  CALCULATION FUNCTIONS (เหมือนเดิม)
# ─────────────────────────────────────────────────────────────

def calculate_bmr(gender: str, weight_kg: float, height_cm: float, age: int) -> float:
    """
    คำนวณ BMR ด้วยสมการ Harris-Benedict (Revised)
    ชาย:  BMR = 88.362 + (13.397 × weight) + (4.799 × height) − (5.677 × age)
    หญิง: BMR = 447.593 + (9.247 × weight) + (3.098 × height) − (4.330 × age)
    """
    if gender == "ชาย":
        return 88.362 + (13.397 * weight_kg) + (4.799 * height_cm) - (5.677 * age)
    else:
        return 447.593 + (9.247 * weight_kg) + (3.098 * height_cm) - (4.330 * age)


def calculate_tdee(bmr: float, activity_factor: float) -> float:
    """TDEE = BMR × Activity Factor"""
    return bmr * activity_factor


def calculate_macros(tdee: float) -> dict:
    """
    คำนวณ Macronutrients จาก TDEE
    โปรตีน 25% (4 kcal/g) | คาร์บ 50% (4 kcal/g) | ไขมัน 25% (9 kcal/g)
    """
    return {
        "protein": {"kcal": tdee * 0.25, "grams": (tdee * 0.25) / 4},
        "carbs":   {"kcal": tdee * 0.50, "grams": (tdee * 0.50) / 4},
        "fat":     {"kcal": tdee * 0.25, "grams": (tdee * 0.25) / 9},
    }


def get_calorie_goal(tdee: float) -> dict:
    """แนะนำแคลอรีสำหรับ 3 เป้าหมาย (ขาดดุล/คงที่/เกินดุล)"""
    return {
        "ลดน้ำหนัก (-500 kcal)":   round(tdee - 500),
        "คงน้ำหนักเดิม":            round(tdee),
        "เพิ่มน้ำหนัก (+300 kcal)": round(tdee + 300),
    }


# ─────────────────────────────────────────────────────────────
# 🤖  AI FOOD ANALYSIS FUNCTION (ฟังก์ชันใหม่!)
# ─────────────────────────────────────────────────────────────

def analyze_food_image(image_bytes: bytes, api_key: str) -> dict:
    """
    ส่งรูปภาพอาหารให้ Gemini วิเคราะห์แคลอรีและ Macronutrients

    วิธีทำงาน:
    1. ตั้งค่า Gemini API Key
    2. สร้าง model และส่งรูป + prompt ไปพร้อมกัน (Gemini รับ bytes โดยตรงได้)
    3. Parse JSON ที่ AI ตอบกลับมาเป็น Python dict

    Parameters:
        image_bytes : ข้อมูลรูปภาพในรูปแบบ bytes (จาก st.file_uploader)
        api_key     : Gemini API Key (รับฟรีที่ aistudio.google.com)

    Returns:
        dict ผลวิเคราะห์ มีคีย์: food_name, portion, calories,
             protein_g, carbs_g, fat_g, confidence, notes
    """
    # ── Step 1: ตั้งค่า Gemini API Key ──
    genai.configure(api_key=api_key)

    # ── Step 2: สร้าง Gemini model ที่รองรับ Vision (มองเห็นรูปภาพได้) ──
    # gemini-1.5-flash = รุ่นที่เร็วและฟรี รองรับการวิเคราะห์รูปภาพ
    model = genai.GenerativeModel("gemini-2.0-flash")

    # ── Step 3: เตรียม prompt ──
    prompt = """คุณคือผู้เชี่ยวชาญด้านโภชนาการและวิเคราะห์แคลอรีอาหาร
วิเคราะห์อาหารในรูปนี้แล้วตอบเป็น JSON เท่านั้น ห้ามมีข้อความอื่น ห้ามมี ```json
รูปแบบ JSON ที่ต้องการ:
{
  "food_name": "ชื่ออาหาร (ภาษาไทย)",
  "portion": "ขนาดส่วนที่ประมาณในรูป เช่น 1 จาน / 200g",
  "calories": 000,
  "protein_g": 00.0,
  "carbs_g": 00.0,
  "fat_g": 00.0,
  "confidence": "high/medium/low",
  "notes": "หมายเหตุสั้นๆ เช่น ปัจจัยที่ทำให้แคลอรีแตกต่างกัน"
}"""

    # ── Step 4: สร้าง image part สำหรับส่งให้ Gemini ──
    # Gemini รับรูปในรูปแบบ dict ที่มี mime_type และ data (bytes)
    image_part = {
        "mime_type": "image/jpeg",
        "data": image_bytes,   # ส่ง bytes โดยตรง ไม่ต้องแปลงเป็น base64
    }

    # ── Step 5: เรียก Gemini API พร้อมส่งรูปและ prompt ──
    # generate_content รับ list ของ content (รูป + ข้อความ)
    response = model.generate_content([image_part, prompt])

    # ── Step 6: แปลง response เป็น Python dict ──
    raw_text = response.text

    # ใช้ regex หา JSON ในข้อความ (กรณี AI แนบ markdown หรือข้อความอื่นมาด้วย)
    json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
    if json_match:
        result = json.loads(json_match.group())
    else:
        raise ValueError(f"AI ไม่ได้ตอบเป็น JSON: {raw_text}")

    return result


# ─────────────────────────────────────────────────────────────
# 📋  DATA
# ─────────────────────────────────────────────────────────────
ACTIVITY_LEVELS = {
    "🛋️  ไม่ค่อยขยับ (นั่งทำงาน/เรียนตลอดวัน)":            (1.2,   "Sedentary"),
    "🚶 เคลื่อนไหวเล็กน้อย (ออกกำลังกาย 1–3 วัน/สัปดาห์)":  (1.375, "Lightly Active"),
    "🏃 กลางๆ (ออกกำลังกาย 3–5 วัน/สัปดาห์)":               (1.55,  "Moderately Active"),
    "💪 ขยันมาก (ออกกำลังกาย 6–7 วัน/สัปดาห์)":             (1.725, "Very Active"),
    "🏋️  นักกีฬา/งานหนักมาก (ซ้อมหนักทุกวัน 2 รอบ)":        (1.9,   "Extra Active"),
}

# ─────────────────────────────────────────────────────────────
# 🖥️  UI — Header
# ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
    <h1>🍽️ BMR & TDEE + AI Food Analyzer</h1>
    <p>คำนวณพลังงานด้วย Harris-Benedict · วิเคราะห์แคลอรีอาหารด้วย Claude AI</p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ─────────────────────────────────────────────────────────────
# 📑  TABS — แบ่งเป็น 2 แท็บ
# st.tabs() คืนค่าเป็น context managers ที่ใช้กับ with ได้
# ─────────────────────────────────────────────────────────────
tab_calc, tab_food = st.tabs(["🔥 คำนวณ BMR & TDEE", "📸 วิเคราะห์รูปอาหาร"])


# ══════════════════════════════════════════════════════════════
#  TAB 1 — BMR & TDEE Calculator (เหมือนเวอร์ชันเดิม)
# ══════════════════════════════════════════════════════════════
with tab_calc:
    left_col, right_col = st.columns([1, 1.6], gap="large")

    # ── Left: Input ──
    with left_col:
        st.markdown('<div class="section-title">📝 ข้อมูลส่วนตัว</div>', unsafe_allow_html=True)

        gender = st.radio("เพศ", ["ชาย", "หญิง"], horizontal=True,
                          help="ชาย/หญิงมีสัดส่วนกล้ามเนื้อต่างกัน ส่งผลต่อค่า BMR")
        age    = st.number_input("อายุ (ปี)", 10, 100, 18, 1,
                                 help="อายุมาก → BMR ลดลง เพราะมวลกล้ามเนื้อลดลง")

        w_col, h_col = st.columns(2)
        with w_col:
            weight = st.number_input("น้ำหนัก (กก.)", 20.0, 300.0, 60.0, 0.5, format="%.1f")
        with h_col:
            height = st.number_input("ส่วนสูง (ซม.)", 100.0, 250.0, 170.0, 0.5, format="%.1f")

        st.markdown("---")
        st.markdown('<div class="section-title">🏃 ระดับกิจกรรม</div>', unsafe_allow_html=True)

        activity_label  = st.selectbox("เลือกระดับกิจกรรม", list(ACTIVITY_LEVELS.keys()))
        activity_factor, activity_eng = ACTIVITY_LEVELS[activity_label]
        st.info(f"**Activity Factor:** × {activity_factor}  |  *{activity_eng}*")

        st.markdown("<br>", unsafe_allow_html=True)
        calculate_btn = st.button("🔥 คำนวณเลย!", type="primary", use_container_width=True)

    # ── Right: Results ──
    with right_col:
        bmr  = calculate_bmr(gender, weight, height, age)
        tdee = calculate_tdee(bmr, activity_factor)

        if calculate_btn:
            st.balloons()

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
            </div>""", unsafe_allow_html=True)

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
            </div>""", unsafe_allow_html=True)

        with st.expander("🧮 ดูสมการที่ใช้คำนวณ", expanded=False):
            if gender == "ชาย":
                formula = f"BMR = 88.362 + (13.397 × {weight}) + (4.799 × {height}) − (5.677 × {age}) = {bmr:,.1f} kcal"
            else:
                formula = f"BMR = 447.593 + (9.247 × {weight}) + (3.098 × {height}) − (4.330 × {age}) = {bmr:,.1f} kcal"
            st.code(formula)
            st.code(f"TDEE = {bmr:,.1f} × {activity_factor} = {tdee:,.1f} kcal")

        st.markdown("---")
        st.markdown('<div class="section-title">🥗 สารอาหารที่แนะนำต่อวัน</div>', unsafe_allow_html=True)

        macros   = calculate_macros(tdee)
        p_col, c_col, f_col = st.columns(3)

        with p_col:
            st.markdown(f"""
            <div class="macro-card" style="background:linear-gradient(135deg,#e94560,#c0392b);">
                <div class="macro-label">🥩 โปรตีน</div>
                <div class="macro-grams">{macros['protein']['grams']:.0f} g</div>
                <div class="macro-kcal">{macros['protein']['kcal']:.0f} kcal (25%)</div>
            </div>""", unsafe_allow_html=True)

        with c_col:
            st.markdown(f"""
            <div class="macro-card" style="background:linear-gradient(135deg,#f39c12,#d68910);">
                <div class="macro-label">🍚 คาร์โบไฮเดรต</div>
                <div class="macro-grams">{macros['carbs']['grams']:.0f} g</div>
                <div class="macro-kcal">{macros['carbs']['kcal']:.0f} kcal (50%)</div>
            </div>""", unsafe_allow_html=True)

        with f_col:
            st.markdown(f"""
            <div class="macro-card" style="background:linear-gradient(135deg,#27ae60,#1e8449);">
                <div class="macro-label">🥑 ไขมัน</div>
                <div class="macro-grams">{macros['fat']['grams']:.0f} g</div>
                <div class="macro-kcal">{macros['fat']['kcal']:.0f} kcal (25%)</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>**สัดส่วน Macronutrients:**", unsafe_allow_html=True)
        st.write("🥩 โปรตีน (25%)");      st.progress(0.25)
        st.write("🍚 คาร์โบไฮเดรต (50%)"); st.progress(0.50)
        st.write("🥑 ไขมัน (25%)");       st.progress(0.25)

        st.markdown("---")
        st.markdown('<div class="section-title">🎯 แนะนำแคลอรีตามเป้าหมาย</div>', unsafe_allow_html=True)

        goals      = get_calorie_goal(tdee)
        g1, g2, g3 = st.columns(3)
        emojis  = ["⬇️", "⚖️", "⬆️"]
        colors  = ["#3498db", "#2ecc71", "#e74c3c"]

        for col, (label, kcal), emoji, color in zip([g1, g2, g3], goals.items(), emojis, colors):
            with col:
                st.markdown(f"""
                <div style="background:{color}18; border:2px solid {color}55;
                            border-radius:12px; padding:16px; text-align:center;">
                    <div style="font-size:1.5rem">{emoji}</div>
                    <div style="font-size:1.4rem; font-weight:700; color:{color}">{kcal:,}</div>
                    <div style="font-size:0.72rem; color:#555; margin-top:4px">{label}</div>
                </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
#  TAB 2 — AI Food Analyzer (ฟีเจอร์ใหม่!)
# ══════════════════════════════════════════════════════════════
with tab_food:
    st.markdown('<div class="section-title">🤖 วิเคราะห์แคลอรีอาหารด้วย AI</div>', unsafe_allow_html=True)
    st.write("อัปโหลดรูปอาหาร แล้วให้ Gemini AI บอกชื่ออาหาร แคลอรี และ Macronutrients ให้เลย! (ฟรี 🎉)")

    # ── กรอก API Key ──
    # st.text_input + type="password" ทำให้ข้อความถูกซ่อน (แสดงเป็น ***)
    api_key = st.text_input(
        "🔑 Gemini API Key (ฟรี!)",
        type="password",
        placeholder="AIza...",
        help="รับ API Key ฟรีได้ที่ https://aistudio.google.com/app/apikey",
    )

    # แสดงลิงก์ขอ API Key ถ้ายังไม่มี
    if not api_key:
        st.info("💡 ยังไม่มี API Key? รับฟรีได้ที่ [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) → Sign in → Create API Key")

    st.markdown("---")

    # ── อัปโหลดรูป ──
    food_col, result_col = st.columns([1, 1.2], gap="large")

    with food_col:
        st.markdown('<div class="section-title">📷 อัปโหลดรูปอาหาร</div>', unsafe_allow_html=True)

        # st.file_uploader คืนค่าเป็น UploadedFile object หรือ None ถ้ายังไม่ได้อัปโหลด
        uploaded_file = st.file_uploader(
            "เลือกรูปภาพอาหาร",
            type=["jpg", "jpeg", "png", "webp"],
            help="รองรับไฟล์ .jpg .jpeg .png .webp",
        )

        if uploaded_file is not None:
            # แสดงรูปที่อัปโหลด — st.image() รับ bytes หรือ path ก็ได้
            st.image(uploaded_file, caption="รูปที่อัปโหลด", use_container_width=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # ── ปุ่มวิเคราะห์ ──
            analyze_btn = st.button(
                "🔍 วิเคราะห์แคลอรี!",
                type="primary",
                use_container_width=True,
                disabled=(not api_key),   # ปิดปุ่มถ้ายังไม่มี API Key
            )

            if not api_key:
                st.warning("⚠️ กรุณาใส่ API Key ก่อนวิเคราะห์")
        else:
            analyze_btn = False

    # ── แสดงผลวิเคราะห์ ──
    with result_col:
        st.markdown('<div class="section-title">📊 ผลการวิเคราะห์</div>', unsafe_allow_html=True)

        if uploaded_file is not None and analyze_btn and api_key:
            # แสดง spinner ระหว่างรอ AI ตอบ
            with st.spinner("🤖 Gemini กำลังวิเคราะห์อาหาร..."):
                try:
                    # อ่านไฟล์เป็น bytes
                    # .read() คืนค่าเป็น bytes object
                    image_bytes = uploaded_file.read()

                    # เรียกฟังก์ชันวิเคราะห์รูป
                    result = analyze_food_image(image_bytes, api_key)

                    # ── แสดงผลลัพธ์ ──
                    # Confidence badge สี
                    conf_color = {
                        "high":   ("#27ae60", "✅ ความแม่นยำสูง"),
                        "medium": ("#f39c12", "⚠️ ความแม่นยำปานกลาง"),
                        "low":    ("#e74c3c", "❌ ความแม่นยำต่ำ"),
                    }.get(result.get("confidence", "medium"), ("#888", "❓"))

                    st.markdown(f"""
                    <div class="food-result-card">
                        <div class="food-name">🍽️ {result.get('food_name', 'ไม่ทราบ')}</div>
                        <div class="food-portion">📏 ปริมาณโดยประมาณ: {result.get('portion', '-')}</div>
                        <div class="food-kcal-big">{result.get('calories', 0):,}</div>
                        <div class="food-kcal-label">kcal</div>
                        <div>
                            <span class="confidence-badge"
                                  style="background:{conf_color[0]}33; color:{conf_color[0]}; border:1px solid {conf_color[0]};">
                                {conf_color[1]}
                            </span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # ── Macros จากรูป ──
                    st.markdown("**🥗 Macronutrients (จากรูปอาหาร)**")
                    mp, mc, mf = st.columns(3)

                    with mp:
                        st.markdown(f"""
                        <div class="macro-card" style="background:linear-gradient(135deg,#e94560,#c0392b);">
                            <div class="macro-label">🥩 โปรตีน</div>
                            <div class="macro-grams">{result.get('protein_g', 0):.1f} g</div>
                            <div class="macro-kcal">{result.get('protein_g', 0) * 4:.0f} kcal</div>
                        </div>""", unsafe_allow_html=True)

                    with mc:
                        st.markdown(f"""
                        <div class="macro-card" style="background:linear-gradient(135deg,#f39c12,#d68910);">
                            <div class="macro-label">🍚 คาร์บ</div>
                            <div class="macro-grams">{result.get('carbs_g', 0):.1f} g</div>
                            <div class="macro-kcal">{result.get('carbs_g', 0) * 4:.0f} kcal</div>
                        </div>""", unsafe_allow_html=True)

                    with mf:
                        st.markdown(f"""
                        <div class="macro-card" style="background:linear-gradient(135deg,#27ae60,#1e8449);">
                            <div class="macro-label">🥑 ไขมัน</div>
                            <div class="macro-grams">{result.get('fat_g', 0):.1f} g</div>
                            <div class="macro-kcal">{result.get('fat_g', 0) * 9:.0f} kcal</div>
                        </div>""", unsafe_allow_html=True)

                    # ── หมายเหตุจาก AI ──
                    if result.get("notes"):
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.info(f"💬 **AI หมายเหตุ:** {result['notes']}")

                    # ── เปรียบเทียบกับ TDEE ──
                    st.markdown("---")
                    st.markdown("**📊 เทียบกับ TDEE ของคุณ** *(จากแท็บคำนวณ)*")
                    tdee_for_compare = calculate_tdee(
                        calculate_bmr(gender, weight, height, age), activity_factor
                    )
                    food_kcal   = result.get('calories', 0)
                    percent     = (food_kcal / tdee_for_compare) * 100

                    st.progress(min(percent / 100, 1.0))
                    st.write(f"อาหารจานนี้ = **{food_kcal:,} kcal** = **{percent:.1f}%** ของ TDEE คุณ ({tdee_for_compare:,.0f} kcal)")

                except Exception as e:
                    err = str(e)
                    if "API_KEY_INVALID" in err or "invalid" in err.lower():
                        st.error("❌ API Key ไม่ถูกต้อง กรุณาตรวจสอบอีกครั้ง")
                    elif "quota" in err.lower() or "limit" in err.lower():
                        st.error("❌ เกิน Rate Limit กรุณารอสักครู่แล้วลองใหม่")
                    else:
                        st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")

        elif uploaded_file is None:
            # แสดง placeholder ถ้ายังไม่ได้อัปโหลด
            st.markdown("""
            <div style="border:2px dashed #ccc; border-radius:16px; padding:60px 30px;
                        text-align:center; color:#aaa;">
                <div style="font-size:3rem">📸</div>
                <div style="margin-top:12px; font-size:1rem">อัปโหลดรูปอาหารทางซ้าย<br>เพื่อเริ่มวิเคราะห์</div>
            </div>
            """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# 📌  FOOTER
# ─────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align:center; color:#aaa; font-size:0.8rem; padding:16px 0">
    🔬 ใช้สมการ <b>Harris-Benedict (Revised)</b> | Macro อ้างอิง <b>AMDR</b> | AI วิเคราะห์ภาพด้วย <b>Gemini Vision API</b><br>
    ⚠️ ผลลัพธ์เป็นการประมาณการเท่านั้น ควรปรึกษานักโภชนาการสำหรับแผนที่เหมาะกับคุณ
</div>
""", unsafe_allow_html=True)
