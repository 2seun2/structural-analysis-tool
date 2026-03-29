import streamlit as st
import pandas as pd
import numpy as np
import pyvista as pv
from stpyvista import stpyvista

# --- 1. MILL SPEC 데이터 연동 모듈 ---
def load_mill_spec(file):
    try:
        # 엑셀 파일에서 Yield Strength(항복강도)와 Material Name을 읽어옴
        df = pd.read_excel(file)
        # 예: 엑셀에 'Material', 'Yield_Strength_MPa' 컬럼이 있다고 가정
        material_info = {
            "name": df['Material'].iloc[0],
            "yield_strength": float(df['Yield_Strength_MPa'].iloc[0])
        }
        return material_info
    except Exception as e:
        st.error(f"MILL SPEC 파일 형식 확인 필요: {e}")
        return None

# --- 2. 3D 구조 설계 및 해석 시뮬레이션 (FEA 로직 대용) ---
def perform_structural_analysis(length, width, thickness, load_kg, yield_strength):
    # 하중 계산 (N = kg * 9.81)
    force = load_kg * 9.81
    
    # 단순 보(Cantilever) 모델 기준 최대 응력 계산 (예시 수식)
    # sigma = M * y / I
    moment = force * length
    i_moment = (width * (thickness**3)) / 12
    max_stress = (moment * (thickness/2)) / i_moment / 1e6 # MPa 단위 변환
    
    safety_factor = yield_strength / max_stress if max_stress > 0 else 0
    return round(max_stress, 2), round(safety_factor, 2)

# --- 3. Streamlit UI 구성 ---
st.set_page_config(layout="wide")
st.title("🏗️ Pro-Grade 3D 구조해석 & MILL SPEC 연동 툴")

with st.sidebar:
    st.header("1. 재료 정보 입력 (MILL SPEC)")
    uploaded_file = st.file_uploader("제작처 성적서 업로드 (Excel)", type=["xlsx"])
    
    if uploaded_file:
        mat_data = load_mill_spec(uploaded_file)
        if mat_data:
            st.success(f"재질 확인: {mat_data['name']}")
            yield_str = st.number_input("항복강도(MPa)", value=mat_data['yield_strength'])
        else:
            yield_str = st.number_input("항복강도(MPa) 수동 입력", value=250.0)
    else:
        yield_str = st.number_input("항복강도(MPa) 수동 입력", value=250.0)

    st.header("2. 기구 설계 파라미터 (mm)")
    L = st.slider("길이 (L)", 100, 2000, 500)
    W = st.slider("폭 (W)", 10, 500, 50)
    T = st.slider("두께 (T)", 1, 100, 5)
    
    st.header("3. 구속 및 하중 조건")
    load = st.number_input("적용 하중 (kg)", value=165)

# --- 4. 메인 화면: 3D 시각화 및 결과 ---
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("3.D 구조 설계 Preview (Von-Mises Stress Distribution)")
    
    # PyVista를 이용한 3D 모델 생성
    mesh = pv.Box(bounds=(0, L, 0, W, 0, T))
    
    # 해석 결과 계산
    stress, sf = perform_structural_analysis(L, W, T, load, yield_str)
    
    # 가상의 응력 분포 데이터 생성 (끝단으로 갈수록 응력이 높아지는 시각화)
    stress_values = np.linspace(0, stress, mesh.n_points)
    mesh.point_data["Stress (MPa)"] = stress_values
    
    # 3D 렌더링 설정
    plotter = pv.Plotter(window_size=[600, 400])
    plotter.add_mesh(mesh, scalars="Stress (MPa)", cmap="jet", show_edges=True)
    plotter.add_scalar_bar(title="Stress (MPa)")
    plotter.background_color = "white"
    plotter.view_isometric()
    
    # Streamlit에 3D 모델 표시
    stpyvista(plotter)

with col2:
    st.subheader("해석 결과 요약")
    st.metric("최대 발생 응력", f"{stress} MPa")
    
    if sf < 1.0:
        st.error(f"안전율: {sf} (위험: 설계 변경 권장)")
    elif sf < 1.5:
        st.warning(f"안전율: {sf} (주의: 보강 필요 가능성)")
    else:
        st.success(f"안전율: {sf} (안전)")

    st.info(f"계산 근거: {yield_str}MPa 항복강도 대비 하중 {load}kg 적용 시 굽힘 응력 해석 결과")
