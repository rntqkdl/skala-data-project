"""
=============================================================================
DATA ANALYTICS PIPELINE v2.0
=============================================================================
- 파일명 : 시각화, 통계 검정 및 머신러닝 파이프라인 구축 (실습 4)
- 작성자 : 안성민 (광주 4반)
- 작성일 : 2026-07-21

[프로그램 상세 설명]
  ▶ 데이터 입력 단계
    - 이전 실습에서 정제된 데이터(sales_clean.csv) 및 집계 데이터 활용
    - 원본 데이터(sales_100k.csv)를 모델 학습용으로 활용
  ▶ 처리 단계
    - EDA 시각화: 2x2 서브플롯 (분포, 시계열, 상관계수)
    - 통계 검정: t-test(평균 차이), 카이제곱 검정(독립성)
    - 머신러닝: ColumnTransformer + Ridge 회귀 파이프라인 적용
  ▶ 출력 단계
    - 인사이트 리포트: PNG 이미지 + Plotly 인터랙티브 HTML 웹 차트
    - 재사용 모델: joblib 형식으로 직렬화 및 로그(pipeline_execution.log) 기록
=====================================================================
[💡 실행 결과 및 데이터 해석 요약]
1. 통계 검정 결과
   - t-test (서울 vs 부산) : 두 지역 간 평균 매출은 통계적으로 차이 없음 (p-value 0.4673)
   - 카이제곱 (지역 vs 카테고리) : 지역과 주요 구매 카테고리 간에는 유의미한 연관성이 존재함 (p-value 0.0098)
2. 머신러닝 (Ridge 회귀)
   - R² Score : 0.1890 (추가적인 피처 엔지니어링 필요성 확인)
3. 주요 비즈니스 인사이트
   - 매출은 수량(r=0.63) 및 단가(r=0.66)와 강한 양의 상관관계를 보이나, 고객의 나이와는 무관함.
=====================================================================
"""

import os
import logging
import joblib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from scipy import stats
from typing import Any, Optional

# Scikit-learn 머신러닝 모듈
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score

# 프로젝트 공통 유틸리티 (util.py에서 임포트)
from util import (
    load_config,
    ProjectPaths,
    setup_logger,
    read_file,
    write_file,
    ensure_dir_exists,
    initialize_project
)

# =====================================================================
# [0] 프로젝트 초기화 및 시각화 설정
# =====================================================================
config, paths, logger = initialize_project()

# Mac OS 환경 시각화 한글 깨짐 방지 폰트 설정
vis_config = config.get('visualization', {})
plt.rcParams['font.family'] = vis_config.get('font_family', {}).get('macos', 'AppleGothic')
plt.rcParams['axes.unicode_minus'] = False


# =====================================================================
# [1] EDA 시각화 파이프라인
# =====================================================================
def generate_eda_subplots(clean_csv_path: str, save_path: str) -> None:
    """
    정제된 데이터를 불러와 한 화면에 4개의 주요 분석 차트(2x2)를 구성합니다.
    
    데이터의 전반적인 형태, 이상치, 시계열 추이, 변수 간 상관관계를 
    경영진이 한눈에 파악할 수 있도록 대시보드 형태로 시각화합니다.
    
    Args:
        clean_csv_path (str): 정제된 데이터 CSV 파일 경로 (order_date, amount, category 필수)
        save_path (str): 생성된 차트 이미지 저장 경로 (.png)
    
    Raises:
        ValueError: 데이터를 불러오지 못했거나 빈 파일일 경우 발생
    """
    logger.info("EDA 2x2 서브플롯 시각화 생성 시작")
    df = read_file(clean_csv_path, config=config, logger=logger)
    
    if df is None or df.empty:
        raise ValueError(f"시각화를 위한 데이터를 불러오지 못했습니다: {clean_csv_path}")
    
    df['order_date'] = pd.to_datetime(df['order_date'])
    df['year_month'] = df['order_date'].dt.to_period('M').astype(str)
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('매출 데이터 다각적 EDA 대시보드', fontsize=18, fontweight='bold')
    
    # 1) 히스토그램+KDE (매출 분포)
    sns.histplot(data=df, x='amount', kde=True, ax=axes[0, 0], color='#447adb', bins=40)
    axes[0, 0].set_title('매출액 분포 (Histogram + KDE)')
    
    # 2) 박스플롯 (카테고리별 매출)
    sns.boxplot(data=df, x='category', y='amount', ax=axes[0, 1], hue='category', palette='Set2', legend=False)
    axes[0, 1].set_title('카테고리별 매출액 분포 (Boxplot)')
    
    # 3) 라인 차트 (시계열 추이)
    monthly_sales = df.groupby('year_month')['amount'].sum().reset_index()
    axes[1, 0].plot(monthly_sales['year_month'], monthly_sales['amount'], marker='o', color='#e54e33')
    axes[1, 0].set_title('월별 총매출 추이 (Line Chart)')
    axes[1, 0].tick_params(axis='x', rotation=45)
    
    # 4) 히트맵 (상관관계)
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    corr_matrix = df[numeric_cols].corr()
    sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='Blues', ax=axes[1, 1])
    axes[1, 1].set_title('수치형 변수 상관관계 (Heatmap)')
    
    plt.tight_layout()
    ensure_dir_exists(save_path)
    plt.savefig(save_path, dpi=300)
    plt.close()
    
    logger.info(f"EDA 서브플롯 이미지 저장 완료: {save_path}")


# =====================================================================
# [2] 통계 검정 파이프라인
# =====================================================================
def perform_statistical_tests(clean_csv_path: str, groupby_csv_path: str) -> None:
    """
    데이터의 패턴이 단순한 우연인지, 통계적으로 유의미한 팩트인지 검증합니다.
    
    1) t-test: 서울과 부산의 평균 매출액 차이 검증 (모수 검정)
    2) 카이제곱 검정: 지역과 주로 구매하는 카테고리 간의 연관성 검증 (비모수 검정)
    
    Args:
        clean_csv_path (str): T-test용 원본 데이터 경로
        groupby_csv_path (str): 카이제곱용 지역/카테고리 집계 데이터 경로
    
    Notes:
        모든 검정 결과(t-stat, p-value)와 비즈니스적 해석은 시스템 로그에 자동 기록됩니다.
    """
    logger.info("통계 검정 수행 시작")
    
    # --- 1) t-test (지역별 매출 차이) ---
    clean_df = read_file(clean_csv_path, config=config, logger=logger)
    if clean_df is None or clean_df.empty:
        raise ValueError("t-test를 위한 데이터를 불러오지 못했습니다.")
        
    seoul_sales = clean_df[clean_df['region'] == '서울']['amount']
    busan_sales = clean_df[clean_df['region'] == '부산']['amount']
    
    ttest_res: Any = stats.ttest_ind(seoul_sales, busan_sales, equal_var=False)
    logger.info(f"[t-test 결과] t-통계량: {float(ttest_res[0]):.4f} / p-value: {float(ttest_res[1]):.4e}")
    if float(ttest_res[1]) < 0.05:
        logger.info("- [해석] p-value < 0.05: 두 지역 간 평균 매출에는 통계적으로 유의미한 차이가 존재합니다.")
    else:
        logger.info("- [해석] p-value >= 0.05: 두 지역 간 평균 매출은 통계적으로 차이가 없습니다.")
        
    # --- 2) 카이제곱 검정 (지역-카테고리 연관성) ---
    groupby_df = read_file(groupby_csv_path, config=config, logger=logger)
    if groupby_df is None or groupby_df.empty:
        raise ValueError("카이제곱 검정을 위한 집계 데이터를 불러오지 못했습니다.")
        
    contingency_table = groupby_df.pivot(index='region', columns='category', values='count').fillna(0)
    chi2_res: Any = stats.chi2_contingency(contingency_table)
    
    logger.info(f"[카이제곱 결과] 카이제곱 통계량: {float(chi2_res[0]):.4f} / p-value: {float(chi2_res[1]):.4e}")
    if float(chi2_res[1]) < 0.05:
        logger.info("- [해석] p-value < 0.05: 지역과 주로 구매하는 카테고리 간 유의미한 연관성이 존재합니다.")
    else:
        logger.info("- [해석] p-value >= 0.05: 지역과 카테고리는 서로 독립적입니다.")


# =====================================================================
# [3] 머신러닝(ML) 학습 및 저장 파이프라인
# =====================================================================
def build_and_save_pipeline(raw_csv_path: str, model_path: str) -> None:
    """
    향후 매출액 예측을 위한 Scikit-Learn 전처리 및 Ridge 회귀 파이프라인을 구축합니다.
    
    수치형(StandardScaler) 및 범주형(OneHotEncoder) 데이터 전처리와 모델 학습을
    하나의 파이프라인으로 결합하여, 새로운 데이터 입력 시 즉시 예측 가능하도록 만듭니다.
    
    Args:
        raw_csv_path (str): 학습을 위한 원본 데이터 CSV 경로
        model_path (str): 학습이 완료된 모델이 저장될 경로 (.joblib)
    """
    logger.info("Scikit-Learn ML 파이프라인 구축 및 학습 시작")
    df = read_file(raw_csv_path, config=config, logger=logger)
    
    if df is None or df.empty:
        raise ValueError("파이프라인 학습을 위한 데이터를 불러오지 못했습니다.")
        
    df = df.dropna(subset=['amount', 'region', 'category', 'payment_method'])
    X = df[['quantity', 'unit_price', 'customer_age', 'region', 'category', 'payment_method']]
    y = df['amount']
    
    # Config 기반 하이퍼파라미터 동적 할당
    test_size = config.get('model', {}).get('train_test_split', {}).get('test_size', 0.2)
    random_state = config.get('model', {}).get('train_test_split', {}).get('random_state', 42)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state)
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), ['quantity', 'unit_price', 'customer_age']),
            ('cat', OneHotEncoder(handle_unknown='ignore'), ['region', 'category', 'payment_method'])
        ]
    )
    
    ridge_config = config.get('model', {}).get('ridge_regression', {})
    pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('model', Ridge(
            alpha=ridge_config.get('alpha', 1.0), 
            random_state=ridge_config.get('random_state', 42)
        ))
    ])
    
    pipeline.fit(X_train, y_train)
    r2 = r2_score(y_test, pipeline.predict(X_test))
    logger.info(f"파이프라인 평가 완료 -> 예측 설명력(R2 Score): {r2:.4f}")
    
    ensure_dir_exists(model_path)
    joblib.dump(pipeline, model_path)
    logger.info(f"파이프라인 모델 직렬화(저장) 완료: {model_path}")


# =====================================================================
# [4] Plotly 웹 대시보드 리포팅
# =====================================================================
def create_interactive_chart(groupby_csv_path: str, html_path: str) -> None:
    """
    웹 브라우저에서 실시간으로 필터링 및 조작 가능한 인터랙티브 차트를 생성합니다.
    
    단순 정적 이미지가 아닌, 경영진이 직접 마우스 오버 및 카테고리 클릭을 통해
    데이터를 깊이 있게 탐색할 수 있는 HTML 포맷의 리포트를 제공합니다.
    
    Args:
        groupby_csv_path (str): 차트에 매핑될 지역/카테고리별 집계 데이터 경로
        html_path (str): 출력될 HTML 파일 경로
    """
    logger.info("Plotly 인터랙티브 차트 생성 시작")
    df = read_file(groupby_csv_path, config=config, logger=logger)
    
    if df is None or df.empty:
        raise ValueError("Plotly 차트 생성을 위한 데이터를 불러오지 못했습니다.")
    
    fig = px.bar(
        df, x='region', y='total', color='category', barmode='group',
        color_discrete_sequence=px.colors.qualitative.Set2,
        title='지역 및 카테고리별 총매출 현황',
        labels={'total': '총 매출액', 'region': '지역', 'category': '카테고리'}
    )
    
    ensure_dir_exists(html_path)
    fig.write_html(html_path)
    logger.info(f"Plotly HTML 차트 렌더링 완료: {html_path}")


# =====================================================================
# [5] 메인 컨트롤러
# =====================================================================
def main():
    """
    전체 데이터 분석 파이프라인의 실행 흐름을 제어합니다.
    
    순차적 실행 보장:
    [EDA 시각화] → [통계 검정] → [머신러닝 모델 학습] → [인터랙티브 웹 차트 생성]
    
    예기치 않은 시스템 에러 발생 시 프로그램 강제 종료를 방지하고,
    안전하게 원인을 추적할 수 있도록 try-except-else 구조로 설계되었습니다.
    """
    try:
        logger.info("==================================================")
        logger.info("[실습 4] 시각화, 통계 검정 및 ML 파이프라인 가동 시작")
        logger.info("==================================================")
        
        generate_eda_subplots(paths.clean_sales, paths.plot_eda)
        perform_statistical_tests(paths.clean_sales, paths.groupby_summary)
        build_and_save_pipeline(paths.raw_sales_100k, paths.model_sales)
        create_interactive_chart(paths.groupby_summary, paths.plot_interactive)

    except FileNotFoundError as e:
        logger.error(f"[프로세스 중단] 필수 데이터 파일이 누락되었습니다: {str(e)}")
    except ValueError as e:
        logger.error(f"[프로세스 중단] 데이터 검증에 실패했습니다: {str(e)}")
    except Exception as e:
        logger.error(f"[치명적 오류] 알 수 없는 시스템 에러 발생: {str(e)}")
    else:
        logger.info("==================================================")
        logger.info("[완료] 모든 분석 및 리포팅 프로세스가 성공적으로 종료되었습니다.")
        logger.info("==================================================")
        
if __name__ == "__main__":
    main()