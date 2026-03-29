import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- 기본 설정 ---
st.set_page_config(page_title="3D Design Validator", layout="wide")
st.title("🔩 3D 기구 체결 및 하중 시각화 해석기")

# --- 사이드바: 엔지니어링 파라미터 ---
with st.sidebar:
    st.header("1. 기구 치수 (mm)")
    L = st.number_input("전체 길이 (Length)", value=300)
    W = st.number_input("폭 (Width)", value=50)
    T = st.number_input("두께 (Thickness)", value=5)
    
    st.header("2. 체결(Screw) 위치")
    st.info("고정단(벽면)에서부터의 거리입니다.")
    screw_pos = st.slider("스크류 체결 위치 (X축)", 0, 50, 10)
    bolt_qty = st.number_input("스크류 수량 (Y축 정렬)", min_value=1, max_value=4, value=2)
    
    st.header("3. 하중(Load) 조건")
    load_kg = st.number_input("가압 하중 (kg)", value=100)
    
    run = st.button("🚀 3D 시뮬레이션 실행", type="primary", use_container_width=True)

# --- 3D 시각화 함수 ---
def draw_3d_simulation(L, W, T, s_pos, b_qty, load):
    fig = go.Figure()

    # 1. 원본 구조물 (반투명 회색)
    fig.add_trace(go.Mesh3d(
        x=[0, L, L, 0, 0, L, L, 0],
        y=[0, 0, W, W, 0, 0, W, W],
        z=[0, 0, 0, 0, T, T, T, T],
        i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2],
        j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3],
        k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
        opacity=0.2, color='gray', name='Original Shape'
    ))

    # 2. 스크류 체결 지점 시각화 (Fixed Points)
    y_points = np.linspace(W*0.2, W*0.8, b_qty)
    fig.add_trace(go.Scatter3d(
        x=[s_pos] * b_qty, y=y_points, z=[T/2] * b_qty,
        mode='markers',
        marker=dict(size=8, color='blue', symbol='diamond'),
        name='Screw Fix Points'
    ))

    # 3. 하중 인가 지점 (Load Point - 끝단 중앙)
    fig.add_trace(go.Scatter3d(
        x=[L], y=[W/2], z=[T],
        mode='markers+text',
        marker=dict(size=10, color='red', symbol='cross'),
        text=["LOAD ↓"], textposition="top center",
        name='Load Point'
    ))

    # 4. 변형 후 형상 (간이 FEA 시각화)
    # 끝단으로 갈수록 처짐(Deflection) 발생
    x_grid = np.linspace(0, L, 10)
    y_grid = np.linspace(0, W, 5)
    X, Y = np.meshgrid(x_grid, y_grid)
    # 처짐량 계산 (시각화를 위해 과장됨)
    Z_deformed = -(load/50) * (X/L)**2 + T 

    fig.add_trace(go.Surface(
        x=X, y=Y, z=Z_deformed,
        colorscale='Reds', opacity=0.8,
        showscale=False, name='Deformed Shape'
    ))

    # 레이아웃 설정
    fig.update_layout(
        scene=dict(
            xaxis=dict(range=[-10, L+50], title="Length (mm)"),
            yaxis=dict(range=[-10, W+10], title="Width (mm)"),
            zaxis=dict(range=[-50, T+20], title="Height (mm)"),
            aspectmode='data'
        ),
        margin=dict(l=0, r=0, b=0, t=0),
        height=700
    )
    return fig

# --- 결과 출력 ---
if run:
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("📦 3D 구조물 분석 뷰")
        st.write("🔵 파란 다이아몬드: 스크류 체결점 | ❌ 빨간 크로스: 하중 가압점")
        fig = draw_3d_simulation(L, W, T, screw_pos, bolt_qty, load_kg)
        st.plotly_chart(fig, use_container_width=True)
        
    with col2:
        st.subheader("📝 설계 검토 리포트")
        # 물리 계산 (기존 로직 활용)
        force = load_kg * 9.81
        moment = force * (L - screw_pos)
        z_mod = (W * T**2) / 6
        stress = moment / z_mod / 1000 # MPa 변환
        
        st.metric("최대 굽힘 응력", f"{round(stress, 1)} MPa")
        
        # 전단 응력 (볼트 하나당 받는 힘)
        bolt_area = 20.1 # M6 기준
        shear = force / (bolt_qty * bolt_area)
        st.metric("볼트 전단 응력", f"{round(shear, 1)} MPa")
        
        if stress > 200:
            st.error("🚨 판재 항복 위험! 두께 증대 필요")
        else:
            st.success("✅ 판재 강성 확보됨")
            
        st.info(f"체결 위치({screw_pos}mm)가 고정단에 가까울수록 모멘트 팔이 길어져 응력이 증가합니다.")

else:
    st.info("사이드바에서 스크류 위치와 하중을 설정한 후 '시뮬레이션 실행'을 눌러주세요.")
