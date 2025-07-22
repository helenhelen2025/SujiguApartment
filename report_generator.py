from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime
import os

class ApartmentReportGenerator:
    def __init__(self):
        # 한글 폰트 등록
        try:
            pdfmetrics.registerFont(TTFont('NanumGothic', 'NanumGothic-Regular.ttf'))
            pdfmetrics.registerFont(TTFont('NanumGothic-Bold', 'NanumGothic-Bold.ttf'))
            self.font_name = 'NanumGothic'
            self.font_bold = 'NanumGothic-Bold'
        except:
            self.font_name = 'Helvetica'
            self.font_bold = 'Helvetica-Bold'
        
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """커스텀 스타일 설정"""
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontName=self.font_bold,
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontName=self.font_bold,
            fontSize=14,
            spaceAfter=12,
            textColor=colors.darkblue
        )
        
        self.normal_style = ParagraphStyle(
            'CustomNormal',
            parent=self.styles['Normal'],
            fontName=self.font_name,
            fontSize=10,
            spaceAfter=6
        )
    
    def generate_apartment_report(self, data, apartment_name, area_type, deal_type, output_path):
        """아파트 분석 리포트 생성"""
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        story = []
        
        # 제목
        title = f"{apartment_name} 부동산 분석 리포트"
        story.append(Paragraph(title, self.title_style))
        story.append(Spacer(1, 12))
        
        # 기본 정보
        info_text = f"""
        <b>분석 대상:</b> {apartment_name}<br/>
        <b>평형:</b> {area_type}<br/>
        <b>거래종류:</b> {deal_type}<br/>
        <b>분석 기간:</b> 2022년 7월 ~ 2025년 7월<br/>
        <b>리포트 생성일:</b> {datetime.now().strftime('%Y년 %m월 %d일')}
        """
        story.append(Paragraph(info_text, self.normal_style))
        story.append(Spacer(1, 20))
        
        # 필터링된 데이터
        filtered_data = data[
            (data['apartment'] == apartment_name) &
            (data['area_type'] == area_type) &
            (data['deal_type'] == deal_type)
        ].sort_values('date')
        
        if filtered_data.empty:
            story.append(Paragraph("해당 조건의 데이터가 없습니다.", self.normal_style))
        else:
            # 요약 통계
            story.append(Paragraph("1. 요약 통계", self.heading_style))
            
            summary_stats = self.calculate_summary_stats(filtered_data)
            summary_table = self.create_summary_table(summary_stats)
            story.append(summary_table)
            story.append(Spacer(1, 20))
            
            # 가격 분석
            story.append(Paragraph("2. 가격 분석", self.heading_style))
            price_analysis = self.analyze_price_trend(filtered_data)
            story.append(Paragraph(price_analysis, self.normal_style))
            story.append(Spacer(1, 20))
            
            # 거래량 분석
            story.append(Paragraph("3. 거래량 분석", self.heading_style))
            volume_analysis = self.analyze_volume_trend(filtered_data)
            story.append(Paragraph(volume_analysis, self.normal_style))
            story.append(Spacer(1, 20))
            
            # 투자 수익성 분석
            if deal_type == "매매":
                story.append(Paragraph("4. 투자 수익성 분석", self.heading_style))
                investment_analysis = self.analyze_investment_return(filtered_data)
                story.append(Paragraph(investment_analysis, self.normal_style))
                story.append(Spacer(1, 20))
            
            # 상세 거래 데이터
            story.append(Paragraph("5. 상세 거래 데이터", self.heading_style))
            data_table = self.create_data_table(filtered_data.tail(20))  # 최근 20건
            story.append(data_table)
        
        # PDF 생성
        doc.build(story)
        return output_path
    
    def calculate_summary_stats(self, data):
        """요약 통계 계산"""
        return {
            '총 거래건수': len(data),
            '평균 가격': f"{data['price'].mean():.2f}억원",
            '최고 가격': f"{data['price'].max():.2f}억원",
            '최저 가격': f"{data['price'].min():.2f}억원",
            '가격 표준편차': f"{data['price'].std():.2f}억원",
            '총 거래량': f"{data['volume'].sum()}건",
            '월평균 거래량': f"{data['volume'].mean():.1f}건",
            '평균 임대수익률': f"{data['rental_yield'].mean():.2f}%" if data['rental_yield'].mean() > 0 else "N/A"
        }
    
    def create_summary_table(self, stats):
        """요약 통계 테이블 생성"""
        table_data = [['항목', '값']]
        for key, value in stats.items():
            table_data.append([key, value])
        
        table = Table(table_data, colWidths=[3*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), self.font_bold),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTNAME', (0, 1), (-1, -1), self.font_name),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        return table
    
    def analyze_price_trend(self, data):
        """가격 추이 분석"""
        if len(data) < 2:
            return "분석할 데이터가 부족합니다."
        
        initial_price = data.iloc[0]['price']
        final_price = data.iloc[-1]['price']
        price_change = ((final_price - initial_price) / initial_price) * 100
        
        trend = "상승" if price_change > 0 else "하락" if price_change < 0 else "보합"
        
        analysis = f"""
        분석 기간 동안 가격은 {initial_price:.2f}억원에서 {final_price:.2f}억원으로 변동하여 
        {abs(price_change):.2f}% {trend}했습니다. 
        
        가격 변동성(표준편차)은 {data['price'].std():.2f}억원으로 
        {'높은' if data['price'].std() > 1.0 else '보통' if data['price'].std() > 0.5 else '낮은'} 
        수준입니다.
        
        최근 6개월 평균 가격은 {data.tail(6)['price'].mean():.2f}억원으로 
        전체 평균 {data['price'].mean():.2f}억원 대비 
        {'높은' if data.tail(6)['price'].mean() > data['price'].mean() else '낮은'} 수준입니다.
        """
        
        return analysis
    
    def analyze_volume_trend(self, data):
        """거래량 추이 분석"""
        total_volume = data['volume'].sum()
        avg_volume = data['volume'].mean()
        max_volume = data['volume'].max()
        
        analysis = f"""
        총 거래량은 {total_volume}건이며, 월평균 {avg_volume:.1f}건의 거래가 발생했습니다.
        최대 월거래량은 {max_volume}건입니다.
        
        거래량 변동성은 {'높은' if data['volume'].std() > avg_volume * 0.5 else '보통'} 수준으로,
        시장 활성도가 {'불안정한' if data['volume'].std() > avg_volume * 0.5 else '안정적인'} 편입니다.
        
        최근 6개월 평균 거래량은 {data.tail(6)['volume'].mean():.1f}건으로 
        전체 평균 대비 {'활발한' if data.tail(6)['volume'].mean() > avg_volume else '저조한'} 상황입니다.
        """
        
        return analysis
    
    def analyze_investment_return(self, data):
        """투자 수익성 분석"""
        if len(data) < 2:
            return "투자 수익성 분석을 위한 데이터가 부족합니다."
        
        initial_price = data.iloc[0]['price']
        final_price = data.iloc[-1]['price']
        capital_gain = ((final_price - initial_price) / initial_price) * 100
        
        avg_rental_yield = data['rental_yield'].mean()
        total_return = capital_gain + (avg_rental_yield * 3)  # 3년 누적
        
        analysis = f"""
        <b>투자 수익성 분석 (3년 기준)</b><br/>
        
        • 자본이득률: {capital_gain:.2f}%<br/>
        • 평균 임대수익률: {avg_rental_yield:.2f}%/년<br/>
        • 3년 누적 임대수익: {avg_rental_yield * 3:.2f}%<br/>
        • 총 예상 수익률: {total_return:.2f}%<br/>
        
        <b>투자 등급:</b> {
            'A+ (매우 우수)' if total_return > 30 else
            'A (우수)' if total_return > 20 else
            'B+ (양호)' if total_return > 15 else
            'B (보통)' if total_return > 10 else
            'C (신중검토)'
        }<br/>
        
        <b>투자 의견:</b> {
            '적극 매수 추천' if total_return > 25 else
            '매수 추천' if total_return > 15 else
            '보유 추천' if total_return > 5 else
            '신중한 검토 필요'
        }
        """
        
        return analysis
    
    def create_data_table(self, data):
        """상세 데이터 테이블 생성"""
        table_data = [['날짜', '가격(억원)', '거래량(건)', '임대수익률(%)']]
        
        for _, row in data.iterrows():
            table_data.append([
                row['date'][:7],  # YYYY-MM 형식
                f"{row['price']:.2f}",
                str(row['volume']),
                f"{row['rental_yield']:.2f}" if row['rental_yield'] > 0 else "-"
            ])
        
        table = Table(table_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), self.font_bold),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTNAME', (0, 1), (-1, -1), self.font_name),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))
        
        return table
    
    def generate_excel_report(self, data, output_path):
        """엑셀 리포트 생성"""
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # 전체 데이터
            data.to_excel(writer, sheet_name='전체데이터', index=False)
            
            # 아파트별 요약
            apartment_summary = data.groupby('apartment').agg({
                'price': ['mean', 'min', 'max', 'std'],
                'volume': ['sum', 'mean'],
                'rental_yield': 'mean'
            }).round(2)
            apartment_summary.to_excel(writer, sheet_name='아파트별요약')
            
            # 평형별 요약
            area_summary = data.groupby('area_type').agg({
                'price': ['mean', 'min', 'max'],
                'volume': ['sum', 'mean'],
                'rental_yield': 'mean'
            }).round(2)
            area_summary.to_excel(writer, sheet_name='평형별요약')
            
            # 거래종류별 요약
            deal_summary = data.groupby('deal_type').agg({
                'price': ['mean', 'min', 'max'],
                'volume': ['sum', 'mean'],
                'rental_yield': 'mean'
            }).round(2)
            deal_summary.to_excel(writer, sheet_name='거래종류별요약')
            
            # 월별 트렌드
            monthly_trend = data.groupby('date').agg({
                'price': 'mean',
                'volume': 'sum'
            }).round(2)
            monthly_trend.to_excel(writer, sheet_name='월별트렌드')
        
        return output_path

def main():
    """테스트용 메인 함수"""
    # 샘플 데이터 생성
    import numpy as np
    np.random.seed(42)
    
    sample_data = pd.DataFrame({
        'date': pd.date_range('2022-07-01', '2025-07-01', freq='M').strftime('%Y-%m-%d'),
        'apartment': ['테스트 아파트'] * 37,
        'area_type': ['39평'] * 37,
        'deal_type': ['매매'] * 37,
        'price': np.random.uniform(10, 15, 37),
        'volume': np.random.poisson(10, 37),
        'rental_yield': np.random.uniform(3, 5, 37)
    })
    
    # 리포트 생성기 초기화
    generator = ApartmentReportGenerator()
    
    # PDF 리포트 생성
    pdf_path = generator.generate_apartment_report(
        sample_data, '테스트 아파트', '39평', '매매', 'test_report.pdf'
    )
    print(f"PDF 리포트 생성 완료: {pdf_path}")
    
    # 엑셀 리포트 생성
    excel_path = generator.generate_excel_report(sample_data, 'test_report.xlsx')
    print(f"엑셀 리포트 생성 완료: {excel_path}")

if __name__ == "__main__":
    main()