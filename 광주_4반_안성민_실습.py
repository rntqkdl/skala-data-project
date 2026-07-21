# =====================================================================
# 파일 명 : 시각화, 통계 검정 및 머신러닝 파이프라인 구축 (실습 4)
# 작 성 자 : 안성민 (광주 4반)
# 작 성 일 : 2026-07-21
# 설 명 : 
#   - 이전 실습에서 정제된 데이터(sales_clean.csv)를 활용하여 2x2 EDA 시각화 및 통계 검정을 수행합니다.
#   - 집계된 데이터(sales_groupby_summary.csv)를 카이제곱 분할표 및 Plotly 인터랙티브 차트에 활용합니다.
#   - 원본 데이터(sales_100k.csv)를 기반으로 Scikit-Learn 전처리+학습 파이프라인을 구축하고 파일로 저장합니다.
#   - 단일 경로 사용 시 발생할 수 있는 파일 누락, 빈 파일, 인코딩 에러 등을 방어하는 I/O 로직을 내장했습니다.
#   - 모든 실행 결과와 에러 이력을 pipeline_execution.log 파일에 영구 기록합니다.
#
# ---------------------------------------------------------------------
# [실행 결과 및 데이터 해석 요약]
# 1. 통계 검정 결과
#    - t-test (서울 vs 부산 매출액) : t-통계량 0.7269, p-value 0.4673
#      -> [해석] p-value가 0.05 이상이므로, 두 지역 간 평균 매출은 통계적으로 유의미한 차이가 없음.
#    - 카이제곱 검정 (지역 vs 카테고리) : 카이제곱 통계량 74.9919, p-value 0.00985
#      -> [해석] p-value가 0.05 미만이므로, 지역과 주로 구매하는 카테고리 간에는 유의미한 연관성(종속성)이 존재함.
#
# 2. 머신러닝 파이프라인 (Ridge 회귀) 평가
#    - R² Score : 0.1890 (동일 스코어로 모델 재로딩 및 검증 성공)
#
# 3. EDA 시각화 (2x2 서브플롯) 주요 인사이트
#    - [매출액 분포] : 오른쪽으로 꼬리가 긴 우상향 비대칭 분포(Right-skewed) 형태. 대부분의 결제액이 0~200만 원 구간에 밀집되어 있음.
#    - [카테고리별 분포] : 카테고리별(전자, 의류, 식품 등) 중앙값은 대체로 유사하나, 상단에 이상치(Outlier) 성향의 고액 결제가 다수 분포함.
#    - [월별 총매출 추이] : 23년 2월, 23년 10월, 24년 1월 등 특정 시점에 매출이 급감하는 형태의 큰 변동성을 보이며 등락을 반복함.
#    - [수치형 상관관계] : 매출액(amount)은 수량(quantity, r=0.63) 및 단가(unit_price, r=0.66)와 강한 양의 상관관계를 가짐. 고객 나이(customer_age)는 매출과 무관함(r=0.00).
# =====================================================================

import os
import logging
import joblib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from scipy import stats
from dataclasses import dataclass, field
from typing import Any, Optional

# Scikit-learn 머신러닝 모듈
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score

# ---------------------------------------------------------------------
# [0] 공통 유틸리티 및 로깅 설정 (내장형)
# ---------------------------------------------------------------------
def setup_logger(name: str = "DataPipeline") -> logging.Logger:
    """터미널 출력과 파일 저장을 동시에 수행하는 하이브리드 로거를 설정합니다."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S')
        
        # 1. 터미널(Console) 출력 핸들러
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
        
        # 2. 파일(File) 저장 핸들러
        default_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.getenv("PROJECT_DIR", default_dir)
        log_file_path = os.path.join(base_dir, "logs", "pipeline_execution.log")
        
        # 디렉토리가 없으면 생성 후 로그 파일 연결
        log_dir = os.path.dirname(log_file_path)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    return logger

logger = setup_logger()

# Mac OS 환경을 고려하여 시각화 차트의 한글 깨짐을 방지하는 폰트 설정입니다.
plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False 

def safe_read_csv(filepath: str, encoding: str = 'utf-8', **kwargs) -> Optional[pd.DataFrame]:
    """
    CSV 파일을 안전하게 읽어오는 공통 함수입니다.
    실무에서 빈번히 발생하는 파일 유실, 빈 파일, 인코딩 에러를 방어합니다.
    """
    if not os.path.exists(filepath):
        logger.error(f"[파일 누락] 경로에 파일이 존재하지 않습니다: {filepath}")
        raise FileNotFoundError(f"Missing file: {filepath}")
    
    if not filepath.lower().endswith('.csv'):
        logger.error(f"[형식 오류] CSV 파일이 아닙니다: {filepath}")
        raise ValueError(f"Invalid file format: {filepath}")

    if os.path.getsize(filepath) == 0:
        logger.error(f"[데이터 오류] 파일 용량이 0 Byte 입니다 (빈 파일): {filepath}")
        raise ValueError(f"Empty file: {filepath}")

    try:
        df = pd.read_csv(filepath, encoding=encoding, **kwargs)
        if df.empty:
            logger.warning(f"[데이터 경고] 파일은 정상이나 데이터 행(Row)이 없습니다: {filepath}")
        return df

    except UnicodeDecodeError:
        logger.error(f"[인코딩 오류] '{encoding}' 인코딩으로 읽을 수 없습니다. (cp949, euc-kr 확인 필요): {filepath}")
        raise
    except pd.errors.EmptyDataError:
        logger.error(f"[파싱 오류] 데이터가 없거나 컬럼 파싱에 실패했습니다: {filepath}")
        raise
    except pd.errors.ParserError as e:
        logger.error(f"[구문 오류] CSV 파일의 형식이 손상되었습니다: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"[알 수 없는 오류] 파일 읽기 중 예기치 못한 에러 발생: {str(e)}")
        raise

def ensure_dir_exists(filepath: str) -> None:
    """
    파일을 저장하기 전, 부모 디렉토리가 존재하는지 확인하고 없다면 생성합니다.
    산출물 저장 시 '경로 없음'으로 인한 에러를 원천 차단합니다.
    """
    directory = os.path.dirname(filepath)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"[경로 생성] 산출물 저장을 위한 디렉토리를 생성했습니다: {directory}")

# ---------------------------------------------------------------------
# [1] 시스템 기본 설정 및 경로 구성
# ---------------------------------------------------------------------
@dataclass
class PipelineConfig:
    """터미널 환경 변수(PROJECT_DIR)를 읽어와 모든 파일 경로를 동적으로 자동 구성합니다."""
    default_dir: str = os.path.dirname(os.path.abspath(__file__))
    base_dir: str = os.getenv("PROJECT_DIR", default_dir)
    
    raw_csv_path: str = field(init=False)
    clean_csv_path: str = field(init=False)
    groupby_csv_path: str = field(init=False)
    plot_img_path: str = field(init=False)
    plotly_html_path: str = field(init=False)
    model_path: str = field(init=False)

    def __post_init__(self):
        self.raw_csv_path = os.path.join(self.base_dir, "data", "raw", "sales_100k.csv")
        self.clean_csv_path = os.path.join(self.base_dir, "data", "processed", "sales_clean.csv")
        self.groupby_csv_path = os.path.join(self.base_dir, "data", "processed", "sales_groupby_summary.csv")
        self.plot_img_path = os.path.join(self.base_dir, "outputs", "eda_subplots.png")
        self.plotly_html_path = os.path.join(self.base_dir, "outputs", "sales_region_category.html")
        self.model_path = os.path.join(self.base_dir, "models", "sales_pipeline.joblib")

# ---------------------------------------------------------------------
# [2] EDA 시각화 4종 (2x2 서브플롯 구성 및 저장)
# ---------------------------------------------------------------------
def generate_eda_subplots(clean_csv_path: str, save_path: str) -> None:
    """정제된 데이터를 불러와 한 화면(Figure)에 4개의 주요 분석 차트를 구성합니다."""
    logger.info("EDA 2x2 서브플롯 시각화 생성 시작")
    df = safe_read_csv(clean_csv_path)
    
    # Pylance None Type 에러 방어 (Guard Clause)
    if df is None or df.empty:
        raise ValueError(f"시각화를 위한 데이터를 불러오지 못했습니다: {clean_csv_path}")
    
    df['order_date'] = pd.to_datetime(df['order_date'])
    df['year_month'] = df['order_date'].dt.to_period('M').astype(str)
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('매출 데이터 다각적 EDA 대시보드', fontsize=18, fontweight='bold')
    
    # 1) 히스토그램+KDE
    sns.histplot(data=df, x='amount', kde=True, ax=axes[0, 0], color='#447adb', bins=40)
    axes[0, 0].set_title('매출액 분포 (Histogram + KDE)')
    
    # 2) 박스플롯 (가독성 향상: Set2 팔레트 적용)
    sns.boxplot(data=df, x='category', y='amount', ax=axes[0, 1], hue='category', palette='Set2', legend=False)
    axes[0, 1].set_title('카테고리별 매출액 분포 (Boxplot)')
    
    # 3) 월별 라인 차트
    monthly_sales = df.groupby('year_month')['amount'].sum().reset_index()
    axes[1, 0].plot(monthly_sales['year_month'], monthly_sales['amount'], marker='o', color='#e54e33')
    axes[1, 0].set_title('월별 총매출 추이 (Line Chart)')
    axes[1, 0].tick_params(axis='x', rotation=45)
    
    # 4) 상관계수 히트맵
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    corr_matrix = df[numeric_cols].corr()
    sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='Blues', ax=axes[1, 1])
    axes[1, 1].set_title('수치형 변수 상관관계 (Heatmap)')
    
    plt.tight_layout()
    ensure_dir_exists(save_path)
    plt.savefig(save_path, dpi=300)
    plt.close()
    logger.info(f"EDA 서브플롯 이미지 저장 완료: {save_path}")

# ---------------------------------------------------------------------
# [3] 통계 검정 (t-test 및 카이제곱 검정)
# ---------------------------------------------------------------------
def perform_statistical_tests(clean_csv_path: str, groupby_csv_path: str) -> None:
    """이상치가 제거된 데이터와 집계 데이터를 바탕으로 통계적 유의성을 검정합니다."""
    logger.info("통계 검정 수행 시작")
    
    # --- 1) t-test ---
    clean_df = safe_read_csv(clean_csv_path)
    if clean_df is None or clean_df.empty:
        raise ValueError("t-test를 위한 데이터를 불러오지 못했습니다.")
        
    seoul_sales = clean_df[clean_df['region'] == '서울']['amount']
    busan_sales = clean_df[clean_df['region'] == '부산']['amount']
    
    ttest_res: Any = stats.ttest_ind(seoul_sales, busan_sales, equal_var=False)
    t_stat: float = float(ttest_res[0])
    p_val_t: float = float(ttest_res[1])
    
    logger.info(f"[t-test 결과] t-통계량: {t_stat:.4f} / p-value: {p_val_t:.4e}")
    if p_val_t < 0.05:
        logger.info("- [해석] p-value가 0.05 미만이므로, 두 지역 간 평균 매출에는 통계적으로 유의미한 차이가 존재합니다.")
    else:
        logger.info("- [해석] p-value가 0.05 이상이므로, 두 지역 간 평균 매출은 통계적으로 차이가 없습니다.")
        
    # --- 2) 카이제곱 검정 ---
    groupby_df = safe_read_csv(groupby_csv_path)
    if groupby_df is None or groupby_df.empty:
        raise ValueError("카이제곱 검정을 위한 집계 데이터를 불러오지 못했습니다.")
        
    contingency_table = groupby_df.pivot(index='region', columns='category', values='count').fillna(0)
    
    chi2_res: Any = stats.chi2_contingency(contingency_table)
    chi2_stat: float = float(chi2_res[0])
    p_val_chi: float = float(chi2_res[1])
    
    logger.info(f"[카이제곱 결과] 카이제곱 통계량: {chi2_stat:.4f} / p-value: {p_val_chi:.4e}")
    if p_val_chi < 0.05:
        logger.info("- [해석] p-value가 0.05 미만이므로, 지역과 주로 구매하는 카테고리 간에는 유의미한 연관성(종속성)이 존재합니다.")
    else:
        logger.info("- [해석] p-value가 0.05 이상이므로, 지역과 카테고리는 서로 독립적입니다.")

# ---------------------------------------------------------------------
# [4] Scikit-Learn Pipeline 구성, 학습 및 저장
# ---------------------------------------------------------------------
def build_and_save_pipeline(raw_csv_path: str, model_path: str) -> None:
    """ColumnTransformer와 Pipeline을 활용해 전처리 및 학습을 수행합니다."""
    logger.info("Scikit-Learn 파이프라인 구축 및 학습 시작")
    df = safe_read_csv(raw_csv_path)
    
    if df is None or df.empty:
        raise ValueError("파이프라인 학습을 위한 데이터를 불러오지 못했습니다.")
        
    df = df.dropna(subset=['amount', 'region', 'category', 'payment_method'])
    
    X = df[['quantity', 'unit_price', 'customer_age', 'region', 'category', 'payment_method']]
    y = df['amount']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), ['quantity', 'unit_price', 'customer_age']),
            ('cat', OneHotEncoder(handle_unknown='ignore'), ['region', 'category', 'payment_method'])
        ]
    )
    
    pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('model', Ridge())
    ])
    
    pipeline.fit(X_train, y_train)
    
    y_pred = pipeline.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    logger.info(f"파이프라인 평가 완료 -> R2 Score: {r2:.4f}")
    
    ensure_dir_exists(model_path)
    joblib.dump(pipeline, model_path)
    logger.info(f"파이프라인 모델 저장 완료: {model_path}")
    
    # 모델 재로딩 검증
    loaded_model = joblib.load(model_path)
    logger.info(f"저장된 모델 재로딩 검증 성공 (동일 R2 Score: {loaded_model.score(X_test, y_test):.4f})")

# ---------------------------------------------------------------------
# [5] Plotly 인터랙티브 차트 작성 및 저장
# ---------------------------------------------------------------------
def create_interactive_chart(groupby_csv_path: str, html_path: str) -> None:
    """집계 데이터를 활용하여 웹 브라우저에서 조작 가능한 Plotly 차트를 HTML로 저장합니다."""
    logger.info("Plotly 인터랙티브 차트 생성 시작")
    df = safe_read_csv(groupby_csv_path)
    
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
    logger.info(f"Plotly HTML 차트 저장 완료: {html_path}")

# ---------------------------------------------------------------------
# [6] 메인 실행 제어부
# ---------------------------------------------------------------------
def main():
    config = PipelineConfig()
    
    try:
        logger.info("==================================================")
        logger.info("[실습 4] 시각화, 통계 검정 및 파이프라인 가동 (안전한 I/O & 영구 로깅 내장)")
        logger.info("==================================================")
        
        generate_eda_subplots(config.clean_csv_path, config.plot_img_path)
        perform_statistical_tests(config.clean_csv_path, config.groupby_csv_path)
        build_and_save_pipeline(config.raw_csv_path, config.model_path)
        create_interactive_chart(config.groupby_csv_path, config.plotly_html_path)

    except FileNotFoundError as e:
        logger.error(f"[프로세스 중단] 필수 파일이 누락되었습니다. 경로를 확인하세요: {str(e)}")
    except ValueError as e:
        logger.error(f"[프로세스 중단] 데이터 검증에 실패했습니다: {str(e)}")
    except Exception as e:
        logger.error(f"[시스템 치명적 에러 발생] {str(e)}")
        
    else:
        logger.info("==================================================")
        logger.info("[완료] 모든 분석 및 파일 저장 프로세스가 에러 없이 성공적으로 끝났습니다.")
        logger.info("==================================================")
        
if __name__ == "__main__":
    main()