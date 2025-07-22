import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')

# 로컬 모듈 import
from real_estate_crawler import HogangnonoCrawler
from hogangnono_real_crawler import HogangnonoRealCrawler
from report_generator import ApartmentReportGenerator

# 한글 폰트 설정
plt.rcParams['font.family'] = 'NanumGothic'
plt.rcParams['axes.unicode_minus'] = False

class ApartmentDataCrawler:
    def __init__(self):
        self.base_url = "https://hogangnono.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
    def crawl_suji_apartments(self, start_date="2022-07-01", end_date="2025-07-21"):
        """용인시 수지구 아파트 데이터 크롤링"""
        try:
            # 실제 크롤링 대신 샘플 데이터 생성 (실제 사이트 구조에 맞게 수정 필요)
            apartments_data = self.generate_sample_data()
            return apartments_data
        except Exception as e:
            st.error(f"데이터 크롤링 중 오류 발생: {e}")
            return self.generate_sample_data()
    
    def generate_sample_data(self):
        """샘플 데이터 생성 (실제 크롤링 데이터로 대체 필요)"""
        np.random.seed(42)
        
        # 용인시 수지구 주요 아파트 단지
        apartments = [
            "수지구청역 푸르지오", "동천역 래미안", "수지구 롯데캐슬", 
            "죽전역 이편한세상", "신분당선 래미안", "수지구 힐스테이트",
            "동천동 푸르지오", "죽전동 자이", "풍덕천동 래미안",
            "상현역 푸르지오", "수지구 센트럴파크", "죽전역 롯데캐슬",
            "동천역 힐스테이트", "수지구 아이파크", "신분당선 자이"
        ]
        
        data = []
        for apt in apartments:
            # 3년간 월별 데이터 생성
            for year in range(2022, 2026):
                for month in range(1, 13):
                    if year == 2022 and month < 7:
                        continue
                    if year == 2025 and month > 7:
                        break
                        
                    date = f"{year}-{month:02d}-01"
                    
                    # 기본 가격 설정 (억원 단위)
                    base_price = np.random.uniform(8, 15)
                    
                    # 평형별 데이터
                    for area_type in ["32평", "39평", "49평", "59평"]:
                        area_multiplier = {"32평": 0.8, "39평": 1.0, "49평": 1.3, "59평": 1.6}
                        
                        # 거래종류별 데이터
                        for deal_type in ["매매", "전세", "월세"]:
                            price_multiplier = {"매매": 1.0, "전세": 0.7, "월세": 0.1}
                            
                            price = base_price * area_multiplier[area_type] * price_multiplier[deal_type]
                            
                            # 시간에 따른 가격 변동 (상승 트렌드)
                            time_factor = 1 + (year - 2022) * 0.05 + np.random.uniform(-0.02, 0.02)
                            price *= time_factor
                            
                            # 거래량 (랜덤)
                            volume = np.random.poisson(15) + 5
                            
                            # 임대수익률 (매매가 기준)
                            if deal_type == "매매":
                                rental_yield = np.random.uniform(2.5, 4.5)
                            else:
                                rental_yield = 0
                            
                            data.append({
                                'date': date,
                                'apartment': apt,
                                'area_type': area_type,
                                'deal_type': deal_type,
                                'price': round(price, 2),
                                'volume': volume,
                                'rental_yield': round(rental_yield, 2)
                            })
        
        return pd.DataFrame(data)

class ApartmentAnalyzer:
    def __init__(self, data):
        self.data = data
        
    def get_top_volume_apartments(self, top_n=15):
        """거래량 상위 아파트 선별"""
        volume_by_apt = self.data.groupby('apartment')['volume'].sum().sort_values(ascending=False)
        return volume_by_apt.head(top_n).index.tolist()
    
    def calculate_cumulative_return(self, apartment, area_type, deal_type):
        """3년 누적 수익률 계산 (자본이득률 + 임대수익률)"""
        filtered_data = self.data[
            (self.data['apartment'] == apartment) & 
            (self.data['area_type'] == area_type) & 
            (self.data['deal_type'] == deal_type)
        ].sort_values('date')
        
        if len(filtered_data) < 2:
            return 0
        
        # 자본이득률 계산
        initial_price = filtered_data.iloc[0]['price']
        final_price = filtered_data.iloc[-1]['price']
        capital_gain = ((final_price - initial_price) / initial_price) * 100
        
        # 임대수익률 계산 (매매만 해당)
        if deal_type == "매매":
            avg_rental_yield = filtered_data['rental_yield'].mean()
            rental_return = avg_rental_yield * 3  # 3년 누적
            total_return = capital_gain + rental_return
        else:
            total_return = capital_gain
        
        return total_return
    
    def get_price_trend(self, apartment, area_type, deal_type):
        """가격 추이 데이터"""
        return self.data[
            (self.data['apartment'] == apartment) & 
            (self.data['area_type'] == area_type) & 
            (self.data['deal_type'] == deal_type)
        ].sort_values('date')

def main():
    st.set_page_config(
        page_title="용인시 수지구 아파트 거래 분석 대시보드",
        page_icon="🏠",
        layout="wide"
    )
    
    st.title("🏠 용인시 수지구 아파트 거래 분석 대시보드")
    st.markdown("### 2022년 7월 ~ 2025년 7월 거래량 상위 15개 아파트 분석")
    
    # 데이터 로딩 옵션
    st.sidebar.header("📊 데이터 소스")
    data_source = st.sidebar.radio(
        "데이터 소스 선택",
        ["호갱노노 실제 크롤링", "샘플 데이터 사용"]
    )
    
    # 데이터 로딩
    @st.cache_data
    def load_data(source_type):
        if source_type == "호갱노노 실제 크롤링":
            # 실제 호갱노노 크롤러 사용
            real_crawler = HogangnonoRealCrawler()
            apartments = real_crawler.get_suji_apartments()
            
            # 실제 아파트 데이터로 거래 데이터 생성
            old_crawler = HogangnonoCrawler()
            return old_crawler.generate_realistic_data(apartments)
        else:
            # 기본 샘플 데이터
            crawler = ApartmentDataCrawler()
            return crawler.crawl_suji_apartments()
    
    with st.spinner("데이터를 불러오는 중..."):
        data = load_data(data_source)
    
    analyzer = ApartmentAnalyzer(data)
    top_apartments = analyzer.get_top_volume_apartments(15)
    
    # 사이드바 필터
    st.sidebar.header("🔍 필터 옵션")
    
    selected_apartment = st.sidebar.selectbox(
        "아파트 선택",
        options=top_apartments,
        index=0
    )
    
    area_types = data['area_type'].unique()
    selected_area = st.sidebar.selectbox(
        "평형 선택",
        options=area_types,
        index=0
    )
    
    deal_types = data['deal_type'].unique()
    selected_deal_type = st.sidebar.selectbox(
        "거래종류 선택",
        options=deal_types,
        index=0
    )
    
    # 리포트 생성 옵션
    st.sidebar.header("📄 리포트 생성")
    if st.sidebar.button("PDF 리포트 생성"):
        with st.spinner("PDF 리포트 생성 중..."):
            try:
                report_gen = ApartmentReportGenerator()
                pdf_path = f"{selected_apartment}_{selected_area}_{selected_deal_type}_report.pdf"
                report_gen.generate_apartment_report(
                    data, selected_apartment, selected_area, selected_deal_type, pdf_path
                )
                st.sidebar.success(f"PDF 리포트가 생성되었습니다: {pdf_path}")
                
                # PDF 다운로드 버튼
                with open(pdf_path, "rb") as pdf_file:
                    st.sidebar.download_button(
                        label="📥 PDF 다운로드",
                        data=pdf_file.read(),
                        file_name=pdf_path,
                        mime="application/pdf"
                    )
            except Exception as e:
                st.sidebar.error(f"PDF 생성 오류: {e}")
    
    if st.sidebar.button("엑셀 리포트 생성"):
        with st.spinner("엑셀 리포트 생성 중..."):
            try:
                report_gen = ApartmentReportGenerator()
                excel_path = f"{selected_apartment}_전체분석.xlsx"
                report_gen.generate_excel_report(data, excel_path)
                st.sidebar.success(f"엑셀 리포트가 생성되었습니다: {excel_path}")
                
                # 엑셀 다운로드 버튼
                with open(excel_path, "rb") as excel_file:
                    st.sidebar.download_button(
                        label="📥 엑셀 다운로드",
                        data=excel_file.read(),
                        file_name=excel_path,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            except Exception as e:
                st.sidebar.error(f"엑셀 생성 오류: {e}")
    
    # 메인 대시보드
    col1, col2, col3, col4 = st.columns(4)
    
    # 현재 선택된 조건의 데이터
    current_data = analyzer.get_price_trend(selected_apartment, selected_area, selected_deal_type)
    cumulative_return = analyzer.calculate_cumulative_return(selected_apartment, selected_area, selected_deal_type)
    
    with col1:
        st.metric(
            "3년 누적 수익률",
            f"{cumulative_return:.2f}%",
            delta=f"{cumulative_return:.2f}%"
        )
    
    with col2:
        if not current_data.empty:
            current_price = current_data.iloc[-1]['price']
            st.metric(
                "현재 가격",
                f"{current_price:.2f}억원"
            )
    
    with col3:
        total_volume = current_data['volume'].sum() if not current_data.empty else 0
        st.metric(
            "총 거래량",
            f"{total_volume}건"
        )
    
    with col4:
        avg_rental_yield = current_data['rental_yield'].mean() if not current_data.empty else 0
        st.metric(
            "평균 임대수익률",
            f"{avg_rental_yield:.2f}%"
        )
    
    # 차트 섹션
    st.markdown("---")
    
    # 가격 추이 차트
    st.subheader("📈 가격 추이 분석")
    
    if not current_data.empty:
        fig_price = go.Figure()
        fig_price.add_trace(go.Scatter(
            x=pd.to_datetime(current_data['date']),
            y=current_data['price'],
            mode='lines+markers',
            name='가격',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=6)
        ))
        
        fig_price.update_layout(
            title=f"{selected_apartment} - {selected_area} - {selected_deal_type} 가격 추이",
            xaxis_title="날짜",
            yaxis_title="가격 (억원)",
            hovermode='x unified',
            height=400
        )
        
        st.plotly_chart(fig_price, use_container_width=True)
    
    # 거래량 및 임대수익률 비교
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 월별 거래량")
        if not current_data.empty:
            fig_volume = px.bar(
                current_data,
                x='date',
                y='volume',
                title=f"{selected_apartment} 월별 거래량",
                color='volume',
                color_continuous_scale='Blues'
            )
            fig_volume.update_layout(height=400)
            st.plotly_chart(fig_volume, use_container_width=True)
    
    with col2:
        st.subheader("💰 임대수익률 추이")
        if not current_data.empty and selected_deal_type == "매매":
            fig_yield = px.line(
                current_data,
                x='date',
                y='rental_yield',
                title=f"{selected_apartment} 임대수익률 추이",
                markers=True
            )
            fig_yield.update_layout(height=400)
            st.plotly_chart(fig_yield, use_container_width=True)
        else:
            st.info("임대수익률은 매매 거래에서만 표시됩니다.")
    
    # 상위 15개 아파트 비교 분석
    st.markdown("---")
    st.subheader("🏆 상위 15개 아파트 비교 분석")
    
    # 누적 수익률 비교
    returns_data = []
    for apt in top_apartments:
        for area in area_types:
            for deal in deal_types:
                ret = analyzer.calculate_cumulative_return(apt, area, deal)
                returns_data.append({
                    'apartment': apt,
                    'area_type': area,
                    'deal_type': deal,
                    'cumulative_return': ret
                })
    
    returns_df = pd.DataFrame(returns_data)
    
    # 매매 기준 누적 수익률 상위 10개
    top_returns = returns_df[returns_df['deal_type'] == '매매'].nlargest(10, 'cumulative_return')
    
    fig_returns = px.bar(
        top_returns,
        x='cumulative_return',
        y='apartment',
        color='area_type',
        title="매매 기준 3년 누적 수익률 상위 10개 (평형별)",
        orientation='h',
        height=500
    )
    fig_returns.update_layout(yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig_returns, use_container_width=True)
    
    # 거래량 비교 (히트맵)
    st.subheader("🔥 아파트별 거래량 히트맵")
    
    volume_pivot = data[data['apartment'].isin(top_apartments)].groupby(
        ['apartment', 'deal_type']
    )['volume'].sum().reset_index()
    
    volume_matrix = volume_pivot.pivot(index='apartment', columns='deal_type', values='volume').fillna(0)
    
    fig_heatmap = px.imshow(
        volume_matrix.values,
        x=volume_matrix.columns,
        y=volume_matrix.index,
        color_continuous_scale='YlOrRd',
        title="아파트별 거래종류별 총 거래량"
    )
    fig_heatmap.update_layout(height=600)
    st.plotly_chart(fig_heatmap, use_container_width=True)
    
    # 평형별 평균 가격 비교
    st.subheader("📏 평형별 평균 가격 비교")
    
    avg_price_by_area = data[data['apartment'].isin(top_apartments)].groupby(
        ['area_type', 'deal_type']
    )['price'].mean().reset_index()
    
    fig_area_price = px.box(
        data[data['apartment'].isin(top_apartments)],
        x='area_type',
        y='price',
        color='deal_type',
        title="평형별 가격 분포 (상위 15개 아파트)"
    )
    fig_area_price.update_layout(height=400)
    st.plotly_chart(fig_area_price, use_container_width=True)
    
    # 시계열 분석 - 전체 시장 트렌드
    st.subheader("📅 시장 전체 트렌드 분석")
    
    monthly_trend = data[data['apartment'].isin(top_apartments)].groupby(
        ['date', 'deal_type']
    ).agg({
        'price': 'mean',
        'volume': 'sum'
    }).reset_index()
    
    fig_trend = make_subplots(
        rows=2, cols=1,
        subplot_titles=('평균 가격 추이', '총 거래량 추이'),
        vertical_spacing=0.1
    )
    
    for deal_type in deal_types:
        trend_data = monthly_trend[monthly_trend['deal_type'] == deal_type]
        
        fig_trend.add_trace(
            go.Scatter(
                x=pd.to_datetime(trend_data['date']),
                y=trend_data['price'],
                mode='lines+markers',
                name=f'{deal_type} 평균가격',
                legendgroup=deal_type
            ),
            row=1, col=1
        )
        
        fig_trend.add_trace(
            go.Scatter(
                x=pd.to_datetime(trend_data['date']),
                y=trend_data['volume'],
                mode='lines+markers',
                name=f'{deal_type} 거래량',
                legendgroup=deal_type,
                showlegend=False
            ),
            row=2, col=1
        )
    
    fig_trend.update_layout(height=600, title_text="용인시 수지구 아파트 시장 전체 트렌드")
    fig_trend.update_xaxes(title_text="날짜", row=2, col=1)
    fig_trend.update_yaxes(title_text="가격 (억원)", row=1, col=1)
    fig_trend.update_yaxes(title_text="거래량 (건)", row=2, col=1)
    
    st.plotly_chart(fig_trend, use_container_width=True)
    
    # 데이터 테이블
    st.markdown("---")
    st.subheader("📋 상세 데이터")
    
    # 필터링된 데이터 표시
    filtered_data = data[
        (data['apartment'] == selected_apartment) &
        (data['area_type'] == selected_area) &
        (data['deal_type'] == selected_deal_type)
    ].sort_values('date', ascending=False)
    
    st.dataframe(
        filtered_data[['date', 'apartment', 'area_type', 'deal_type', 'price', 'volume', 'rental_yield']],
        use_container_width=True
    )
    
    # 다운로드 버튼
    csv = filtered_data.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="📥 데이터 다운로드 (CSV)",
        data=csv,
        file_name=f"{selected_apartment}_{selected_area}_{selected_deal_type}_data.csv",
        mime="text/csv"
    )
    
    # 분석 리포트 생성
    st.markdown("---")
    st.subheader("📊 분석 리포트")
    
    with st.expander("상세 분석 리포트 보기"):
        st.markdown(f"""
        ### {selected_apartment} - {selected_area} - {selected_deal_type} 분석 리포트
        
        **기본 정보:**
        - 분석 기간: 2022년 7월 ~ 2025년 7월
        - 총 데이터 포인트: {len(filtered_data)}개
        - 3년 누적 수익률: {cumulative_return:.2f}%
        
        **가격 분석:**
        - 최고가: {filtered_data['price'].max():.2f}억원
        - 최저가: {filtered_data['price'].min():.2f}억원
        - 평균가: {filtered_data['price'].mean():.2f}억원
        - 가격 변동성: {filtered_data['price'].std():.2f}억원
        
        **거래량 분석:**
        - 총 거래량: {filtered_data['volume'].sum()}건
        - 월평균 거래량: {filtered_data['volume'].mean():.1f}건
        - 최대 월거래량: {filtered_data['volume'].max()}건
        
        **투자 수익성:**
        - 평균 임대수익률: {filtered_data['rental_yield'].mean():.2f}%
        - 수익률 안정성: {'높음' if filtered_data['rental_yield'].std() < 0.5 else '보통'}
        
        **투자 추천도:**
        {
            '★★★★★ 매우 추천' if cumulative_return > 20 else
            '★★★★☆ 추천' if cumulative_return > 10 else
            '★★★☆☆ 보통' if cumulative_return > 0 else
            '★★☆☆☆ 신중검토'
        }
        """)

if __name__ == "__main__":
    main()