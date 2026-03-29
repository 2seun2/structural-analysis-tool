import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- 기본 설정 및 스타일 ---
st.set_page_config(page_title="Design Validator Pro", layout="wide")
st.markdown("""
    <style>
    .reportview-container .main .block-container{ max_width: 95%; }
    .stMetric { border: 1px solid #d3d3d3; padding: 10px; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 왼쪽 사이드바: 상세 설계 스펙 입력 ---
with st.sidebar:
    st.header("🛠️ 1. 구조 설계 스펙 (mm)")
    shape = st.selectbox("형상 분류", ["Plate (평판)", "Square Pipe (사각관)", "L-Angle (앵글)"])
    col_l, col_w = st.columns(2)
    with col_l: L = st.number_input("전체 길이 (Length)", value=500, step=10)
    with col_w: W = st.number_input("폭/높이 (Width)", value=60, step=5)
    T = st.number_input("두께 (Thickness)", value=4.0, format="%.1f", step=0.1)

    st.header("🔩 2. 스크류 체결 스펙")
    col_sz, col_qty = st.columns(2)
    with col_sz: bolt_size = st.selectbox("규격", ["M3", "M4", "M5", "M6", "M8", "M10", "M12"])
    with col_qty: bolt_qty = st.number_input("수량 (ea)", min_value=1, max_value=8, value=2)
    
    col_pos, col_grd = st.columns(2)
    with col_pos: screw_pos_x = st.slider("체결 위치 (X축, mm)", 0, int(L*0.2), 20)
    with col_grd: bolt_grade = st.selectbox("등급", ["4.8", "8.8", "10.9 (고장력)"])

    st.header("⚖️ 3. 하중 및 소재")
    mat = st.selectbox("소재 선택", ["SUS304", "SECC (GI)", "AL6061-T6", "PC+ABS", "ABS"])
    load_kg = st.number_input("가압 하중 (Total, kg)", value=150, step=10)
    
    st.divider()
    analyze_btn = st.button("🚀 정밀 해석 시작", type="primary", use_container_width=True)

# --- 2. 물리 계산 및 데이터 준비 ---
# 소재 물성치 (항복강도 MPa, 탄성계수 GPa)
MAT_DB = {
    "SUS304": {"yield": 205, "E": 193}, "SECC (GI)": {"yield": 270, "E": 210},
    "AL6061-T6": {"yield": 275, "E": 69}, "PC+ABS": {"yield": 55, "E": 2.4}, "ABS": {"yield": 40, "E": 2.1}
}
# 볼트 유효 단면적 (mm^2) 및 항복강도 (MPa)
BOLT_AREA = {"M3": 5.03, "M4": 8.78, "M5": 14.2, "M6": 20.1, "M8": 36.6, "M10": 58.0, "M12": 84.3}
BOLT_YIELD = {"4.8": 320, "8.8": 640, "10.9 (고장력)": 940}

y_yield = MAT_DB[mat]["yield"]
e_modulus = MAT_DB[mat]["E"] * 1000 # MPa 변환
force_n = load_kg * 9.81
moment_팔 = L - screw_pos_x

# 구조 계산 (외팔보 단순화 모형)
if shape == "Plate (평판)": I = (W * T**3) / 12; Z = (W * T**2) / 6
elif shape == "Square Pipe (사각관)": I = (W**4 - (W-2*T)**4) / 12; Z = I / (W/2)
else: I = (T * W**3 / 12) + (W * T**3 / 12); Z = I / (W/2)

bending_stress = (force_n * moment_팔) / Z
sf_struct = y_yield / bending_stress if bending_stress > 0 else 99
deflection_max = (force_n * L**3) / (3 * e_modulus * I)

# 전단 계산 (볼트 균일 분산 가정)
bolt_area = BOLT_AREA[bolt_size]
shear_stress = force_n / (bolt_area * bolt_qty)
b_yield = BOLT_YIELD[bolt_grade] * 0.6 # 전단 허용값은 항복의 60%
sf_bolt = b_yield / shear_stress if shear_stress > 0 else 99

# --- 3. 메인 화면: 2분할 (3D 해석 뷰 / 결과 리포트) ---
col_sim, col_rpt = st.columns([2, 1])

with col_sim:
    st.subheader("📦 3D 구조물 해석 뷰 (과장된 변형 표현)")
    st.info("🔵 파란점: 스크류 체결점 | ❌ 빨간점: 하중 가압점")

    # 3D Mesh 생성 및 변형 시뮬레이션
    fig = go.Figure()

    # 원본 형상 (반투명)
    fig.add_trace(go.Mesh3d(
        x=[0, L, L, 0, 0, L, L, 0], y=[0, 0, W, W, 0, 0, W, W], z=[0, 0, 0, 0, T, T, T, T],
        i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2], j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3],
        k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
        opacity=0.1, color='gray', name='Original Shape'
    ))

    # 체결점 및 가압점 표시
    y_bolt_pos = np.linspace(W*0.2, W*0.8, bolt_qty)
    fig.add_trace(go.Scatter3d(x=[screw_pos_x]*bolt_qty, y=y_bolt_pos, z=[T/2]*bolt_qty, 
                                mode='markers', marker=dict(size=8, color='blue', symbol='diamond')))
    fig.add_trace(go.Scatter3d(x=[L], y=[W/2], z=[T], mode='markers', marker=dict(size=10, color='red')))

    # 변형 형상 (과장 표현) - analyze_btn 누르면 활성화
    if analyze_btn:
        x_mesh = np.linspace(0, L, 15)
        y_mesh = np.linspace(0, W, 5)
        X, Y = np.meshgrid(x_mesh, y_mesh)
        # 처짐량 함수 (시각화를 위해 과장됨)
        Deform_vis = - (force_n/1000) * (X/L)**2 * 10
        
        fig.add_trace(go.Surface(x=X, y=Y, z=Deform_vis + T, colorscale='Reds', opacity=0.9))

    fig.update_layout(scene=dict(xaxis=dict(range=[-20, L+50], title="L (mm)"),
                                  yaxis=dict(range=[-10, W+10], title="W (mm)"),
                                  zaxis=dict(range=[-100, T+20], title="H (mm)"),
                                  aspectmode='data'),
                      margin=dict(l=0, r=0, b=0, t=0), height=750)
    st.plotly_chart(fig, use_container_width=True)

with col_rpt:
    st.subheader("📊 설계 검증 리포트")
    
    if analyze_btn:
        c1, c2 = st.columns(2)
        with c1: 
            st.metric("최대 응력", f"{round(bending_stress, 1)} MPa")
            if sf_struct < 1.5: st.error(f"판재 취약 (S.F: {round(sf_struct, 2)})")
            else: st.success(f"판재 안전 (S.F: {round(sf_struct, 2)})")
        with c2: 
            st.metric("볼트 전단 응력", f"{round(shear_stress, 1)} MPa")
            if sf_bolt < 1.5: st.error(f"볼트 파손 위험 (S.F: {round(sf_bolt, 2)})")
            else: st.success(f"볼트 안전 (S.F: {round(sf_bolt, 2)})")
        
        st.divider()
        st.subheader("📐 예상 처짐량 (Deflection)")
        st.metric("끝단 처짐", f"{round(deflection_max, 2)} mm")
        st.info(f"선택하신 {mat} 재질은 {deflection_max}mm 처질 것으로 예상됩니다. 작동성에 문제가 없는지 확인하십시오.")

        st.divider()
        st.markdown(f"""
        **📋 전문가 한마디 (Insight):**
        - 현재 설계는 **{load_kg}kg**의 하중을 받습니다.
        - 구조물({shape})은 **{round(bending_stress, 1)}MPa**의 굽힘을 견뎌야 합니다.
        - **{bolt_size} (등급 {bolt_grade})** 스크류 **{bolt_qty}**개는 전단 파손에 {"취약하므로 수량을 늘리거나 고장력을 사용하십시오." if sf_bolt < 1.5 else "안전합니다."}
        """)

    else:
        st.warning("왼쪽 사이드바에서 치수와 하중을 입력한 후 '정밀 해석 시작' 버튼을 눌러주세요.")
