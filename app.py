import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- 소재 물성치 DB (항복강도 MPa, 탄성계수 GPa) ---
MATERIAL_DB = {
    "Metal (Press/CNC)": {
        "SUS304": {"yield": 205, "E": 193},
        "SECC (GI)": {"yield": 270, "E": 210},
        "AL6061-T6": {"yield": 275, "E": 69},
        "SPCC": {"yield": 240, "E": 200},
    },
    "Plastic (Injection)": {
        "PC+ABS": {"yield": 55, "E": 2.4},
        "PA66+GF30": {"yield": 110, "E": 6.5},
        "ABS": {"yield": 40, "E": 2.1},
    }
}

st.set_page_config(page_title="Mechanical Design Validator", layout="wide")
st.title("🛡️ 기구 설계 안전성 검증 시스템 (Structure & Fastener)")

# --- 사이드바: 파라미터 입력 ---
with st.sidebar:
    st.header("1. 기본 구조 설계")
    shape = st.selectbox("형상", ["Plate", "Square Pipe", "L-Angle"])
    L = st.number_input("길이 (L, mm)", value=300)
    W = st.number_input("폭/높이 (W, mm)", value=50)
    T = st.number_input("두께 (T, mm)", value=2.0, format="%.2f")
    
    st.header("2. 체결부 설정 (Screw/Bolt)")
    bolt_size = st.selectbox("볼트 규격", ["M3", "M4", "M5", "M6", "M8"])
    bolt_qty = st.number_input("볼트 수량 (ea)", min_value=1, value=2)
    # 볼트 유효 단면적 (mm^2)
    bolt_area_map = {"M3": 5.03, "M4": 8.78, "M5": 14.2, "M6": 20.1, "M8": 36.6}
    
    st.header("3. 소재 및 하중")
    cat = st.selectbox("소재 분류", list(MATERIAL_DB.keys()))
    mat = st.selectbox("상세 강종", list(MATERIAL_DB[cat].keys()))
    load_kg = st.number_input("인가 하중 (Total Load, kg)", value=100)
    
    analyze_btn = st.button("🔍 전단 및 구조 정밀 해석 시작", type="primary", use_container_width=True)

# --- 해석 로직 ---
if analyze_btn:
    yield_str = MATERIAL_DB[cat][mat]["yield"]
    E_modulus = MATERIAL_DB[cat][mat]["E"] * 1000 # MPa 변환
    force_n = load_kg * 9.81
    
    # [1] 구조 굽힘 응력 (Bending Stress)
    # 단순화를 위해 외팔보(Cantilever) 최악 조건 가정
    if shape == "Plate": I = (W * T**3) / 12; Z = (W * T**2) / 6
    elif shape == "Square Pipe": I = (W**4 - (W-2*T)**4) / 12; Z = I / (W/2)
    else: I = (T * W**3 / 12) + (W * T**3 / 12); Z = I / (W/2)
    
    bending_moment = force_n * L
    bending_stress = bending_moment / Z
    
    # [2] 체결부 전단 응력 (Shear Stress)
    # 하중이 볼트에 균일하게 분산된다고 가정 (Shear = Force / (Area * Qty))
    bolt_area = bolt_area_map[bolt_size]
    shear_stress = force_n / (bolt_area * bolt_qty)
    
    # 허용 전단 응력 (보통 항복강도의 60% 수준)
    allowable_shear = yield_str * 0.6
    
    # --- 결과 화면 ---
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📍 구조 해석 결과 (Bending)")
        st.metric("발생 응력", f"{round(bending_stress, 1)} MPa")
        sf_bending = yield_str / bending_stress
        if sf_bending > 2: st.success(f"구조 안전 (S.F: {round(sf_bending, 2)})")
        else: st.error(f"구조 취약 (S.F: {round(sf_bending, 2)})")

    with col2:
        st.subheader("🔩 체결부 해석 결과 (Shear)")
        st.metric("볼트 전단 응력", f"{round(shear_stress, 1)} MPa")
        sf_shear = allowable_shear / shear_stress
        if sf_shear > 2: st.success(f"체결 안전 (S.F: {round(sf_shear, 2)})")
        else: st.error(f"볼트 파손 위험 (S.F: {round(sf_shear, 2)})")

    # [3] 시각화 (Plotly 3D)
    st.divider()
    st.subheader("📊 응력 분포 시각화 (Bending Line)")
    
    # 변형 형상 계산
    x_plot = np.linspace(0, L, 50)
    # y = (F*x^2)/(6*E*I) * (3L - x) -> 외팔보 처짐 공식
    deflection = (force_n * x_plot**2) / (6 * E_modulus * I) * (3*L - x_plot)
    
    fig = go.Figure()
    # 원본 형상
    fig.add_trace(go.Scatter(x=x_plot, y=np.zeros(50), name="Original", line=dict(dash='dash', color='gray')))
    # 변형 형상 (가독성을 위해 5배 과장)
    fig.add_trace(go.Scatter(x=x_plot, y=-deflection * 5, name="Deformed (x5)", 
                             line=dict(width=4, color='red'), mode='lines+markers'))
    
    fig.update_layout(title="하중에 따른 구조물 처짐(Deflection) 예상 라인",
                      xaxis_title="Length (mm)", yaxis_title="Deflection (mm)", height=400)
    st.plotly_chart(fig, use_container_width=True)

    # [4] 전문가 한마디 (Insight)
    st.info(f"""
    **🔍 엔지니어링 검토 의견:**
    1. **구조물:** 현재 {mat} 재질의 {shape} 형상은 하중 지지 시 최대 {round(bending_stress, 1)}MPa의 응력이 발생합니다.
    2. **체결부:** {bolt_size} 볼트 {bolt_qty}개는 {round(shear_stress, 1)}MPa의 전단력을 받습니다. 
    3. **결론:** {"설계 통과" if (sf_bending > 1.5 and sf_shear > 1.5) else "재설계 필요"}. 
       볼트 등급이 4.8일 경우 전단 항복은 낮으므로 8.8 또는 10.9 고장력 볼트 사용을 고려하십시오.
    """)
else:
    st.warning("왼쪽의 파라미터를 확인하고 '해석 시작' 버튼을 눌러주세요.")
