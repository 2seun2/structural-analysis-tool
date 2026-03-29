import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- 1. MILL SPEC 데이터 연동 ---
def load_mill_spec(file):
    try:
        df = pd.read_excel(file)
        # 엑셀 첫 번째 행에서 데이터 추출 시도
        return {"name": df.iloc[0,0], "yield_strength": float(df.iloc[0,1])}
    except:
        return None

# --- 2. 구조 해석 및 안전율 계산 ---
def calculate_analysis(L, W, T, load_kg, yield_str):
    force = load_kg * 9.81
    moment = force * L
    i_moment = (W * (T**3)) / 12
    max_stress = (moment * (T/2)) / i_moment / 1e6 # MPa
    sf = yield_str / max_stress if max_stress > 0 else 0
    return round(max_stress, 2), round(sf, 2)

# --- 3. UI 구성 ---
st.set_page_config(page_title="구조해석 시뮬레이터", layout="wide")
st.title("🏗️ 기구개발용 3D 구조해석 툴")

with st.sidebar:
    st.header("1. 재료 및 하중 설정")
    uploaded_file = st.file_uploader("MILL SPEC 업로드 (Excel)", type=["xlsx"])
    y_input = st.number_input("항복강도(MPa) 직접 입력", value=250.0)
    
    st.header("2. 설계 치수 (mm)")
    L = st.slider("길이 (L)", 100, 1000, 500)
    W = st.slider("폭 (W)", 10, 300, 50)
    T = st.slider("두께 (T)", 1, 50, 5)
    load = st.number_input("하중 (kg)", value=165)

# 해석 결과 계산
stress, sf = calculate_analysis(L, W, T, load, y_input)

# --- 4. 메인 화면 ---
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("3D 구조 시각화")
    # Plotly를 이용한 3D 박스 그리기 (에러가 거의 없음)
    fig = go.Figure(data=[go.Mesh3d(
        x=[0, L, L, 0, 0, L, L, 0],
        y=[0, 0, W, W, 0, 0, W, W],
        z=[0, 0, 0, 0, T, T, T, T],
        i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2],
        j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3],
        k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
        intensity=np.linspace(0, stress, 8),
        colorscale='Jet',
        showscale=True
    )])
    fig.update_layout(scene=dict(aspectmode='data'))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("해석 리포트")
    st.metric("최대 응력", f"{stress} MPa")
    if sf < 1.2:
        st.error(f"안전율: {sf} (위험!)")
    elif sf < 2.0:
        st.warning(f"안전율: {sf} (보강 권장)")
    else:
        st.success(f"안전율: {sf} (안전)")
    
    st.write(f"현재 설계는 **{load}kg** 하중에서 **{y_input}MPa**의 재질을 견디도록 계산되었습니다.")
