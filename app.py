import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- 1. 소재 데이터베이스 (Plastic & Press) ---
MATERIAL_DB = {
    "Plastic (사출)": {
        "PC+ABS": {"yield_strength": 50, "modulus": 2400},
        "ABS": {"yield_strength": 40, "modulus": 2100},
        "PA66 (GF30%)": {"yield_strength": 110, "modulus": 6000},
        "HIPS": {"yield_strength": 25, "modulus": 2000},
    },
    "Press (금속)": {
        "SECC (아연도금강판)": {"yield_strength": 270, "modulus": 210000},
        "SUS304": {"yield_strength": 205, "modulus": 193000},
        "SPCC (냉연강판)": {"yield_strength": 240, "modulus": 205000},
        "AL6061-T6": {"yield_strength": 275, "modulus": 68900},
    }
}

# --- 2. 화면 설정 (최대한 크게) ---
st.set_page_config(page_title="Pro-Mech Structure Analyzer", layout="wide")
st.title("🏗️ 기구설계 전문가용 구조해석 시뮬레이터")

# --- 3. 사이드바 설정 ---
with st.sidebar:
    st.header("1. 형상 및 치수 설정")
    shape_type = st.selectbox("형상 선택", ["평판(Plate)", "L-Angle", "사각 파이프(Square Pipe)"])
    
    col_l, col_w = st.columns(2)
    with col_l: L = st.number_input("길이 (L, mm)", value=500)
    with col_w: W = st.number_input("폭/높이 (W, mm)", value=50)
    T = st.number_input("두께 (T, mm)", value=2.0, step=0.1)

    st.header("2. 소재 선택")
    category = st.selectbox("소재 분류", list(MATERIAL_DB.keys()))
    material = st.selectbox("세부 강종", list(MATERIAL_DB[category].keys()))
    selected_yield = MATERIAL_DB[category][material]["yield_strength"]
    
    st.header("3. 구속 및 하중")
    support_type = st.radio("구속 조건", ["외팔보 (Cantilever)", "양단 지지 (Both Ends)"])
    load_kg = st.number_input("적용 하중 (kg)", value=100)
    
    st.divider()
    run_analysis = st.button("🚀 구조해석 시작", use_container_width=True, type="primary")

# --- 4. 구조 계산 로직 ---
def run_fea(L, W, T, load_kg, yield_str, shape, support):
    force = load_kg * 9.81
    
    # 단면계수(Z) 및 관성모멘트(I) 간이 계산 (형상별)
    if shape == "평판(Plate)":
        I = (W * T**3) / 12
        Z = (W * T**2) / 6
    elif shape == "L-Angle":
        # 단순화된 L형강 계산
        I = (T * W**3 / 12) + (W * T**3 / 12) 
        Z = I / (W/2)
    else: # 사각 파이프
        I = (W**4 - (W-2*T)**4) / 12
        Z = I / (W/2)

    # 굽힘 모멘트 및 응력
    if support == "외팔보 (Cantilever)":
        max_moment = force * L
        deflection_factor = (force * L**3) / (3 * 210000 * I) # 간이 변위
    else:
        max_moment = (force * L) / 4
        deflection_factor = (force * L**3) / (48 * 210000 * I)

    max_stress = max_moment / Z / 1e3 # KPa -> MPa 변환 보정
    sf = yield_str / max_stress if max_stress > 0 else 0
    return round(max_stress, 2), round(sf, 2), deflection_factor

# --- 5. 결과 시각화 (Main Area) ---
if run_analysis:
    stress, sf, deform = run_fea(L, W, T, load_kg, selected_yield, shape_type, support_type)
    
    c1, c2, c3 = st.columns(3)
    c1.metric("최대 발생 응력", f"{stress} MPa")
    c2.metric("안전율 (S.F)", f"{sf}")
    c3.metric("선택 소재", material)

    # 3D 시각화 (Bending 시뮬레이션)
    st.subheader(f"📊 {shape_type} 굽힘/변형 시각화")
    
    # 격자 생성 (변형 시각화용)
    x = np.linspace(0, L, 20)
    y = np.linspace(0, W, 5)
    X, Y = np.meshgrid(x, y)
    
    # 구속 조건에 따른 변형 형상 함수 생성
    if support_type == "외팔보 (Cantilever)":
        Z_deform = -(stress/100) * (X**2 / L) # 시각적 과장 포함
    else:
        Z_deform = -(stress/100) * (4 * X * (L - X) / L)

    fig = go.Figure(data=[go.Surface(x=X, y=Y, z=Z_deform, colorscale='Jet', 
                                    colorbar_title="Stress Level")])
    
    fig.update_layout(
        title=f"하중 인가 시 {shape_type} 변형 예상도 (과장 표현됨)",
        scene=dict(
            xaxis_title='Length (mm)',
            yaxis_title='Width (mm)',
            zaxis_title='Deformation',
            aspectratio=dict(x=2, y=0.5, z=0.5)
        ),
        margin=dict(l=0, r=0, b=0, t=40),
        height=600
    )
    st.plotly_chart(fig, use_container_width=True)

    if sf < 1.0:
        st.error("❌ 현재 설계는 파손 위험이 매우 높습니다. 두께를 키우거나 강종을 변경하세요.")
    elif sf < 1.5:
        st.warning("⚠️ 안전율이 낮습니다. 실제 환경에서는 보강이 필요할 수 있습니다.")
    else:
        st.success("✅ 구조적으로 안전한 설계입니다.")

else:
    st.info("왼쪽 사이드바에서 치수와 하중을 입력한 후 '구조해석 시작' 버튼을 눌러주세요.")
