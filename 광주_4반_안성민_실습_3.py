# =====================================================================
# 파일 명 : 데이터 처리 라이브러리(Pandas, Polars, DuckDB) 성능 비교 분석 및 산출물 저장
# 작 성 자 : 안성민 (광주 4반)
# 작 성 일 : 2026-07-21
# 설 명 : 
#   - 실무 데이터 파이프라인 환경을 가정한 sales_100k.csv 데이터 처리 및 성능 벤치마크 스크립트입니다.
#   - 기초 EDA 수행 및 통계적 기법(IQR)을 적용한 데이터 정제(이상치 제거) 작업을 수행합니다.
#   - 정제된 동일 데이터를 Pandas(Named Aggregation), Polars(Lazy Evaluation), DuckDB(SQL) 엔진으로 집계합니다.
#   - timeit 모듈을 활용하여 각 도구별 메모리 상 연산 속도를 측정하고 비교 분석합니다.
#   - [실습 4 연계] 이상치가 제거된 데이터(sales_clean.csv)와 집계 결과(sales_groupby_summary.csv)를 저장합니다.
# =====================================================================

import os
import io
import timeit
import logging
import pandas as pd
import polars as pl
import duckdb
from dataclasses import dataclass
from typing import Callable, Tuple

# ---------------------------------------------------------------------
# [0] 시스템 기본 설정
# ---------------------------------------------------------------------
# logging 모듈을 사용하여 로그의 타임스탬프와 심각도(INFO, ERROR)를 표준화합니다.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)

@dataclass
class PipelineConfig:
    """프로그램 전역에서 사용되는 하이퍼파라미터 및 환경 변수를 관리하는 데이터 클래스입니다."""
    base_dir: str = os.path.dirname(os.path.abspath(__file__))
    file_path: str = ""
    clean_csv_path: str = ""
    groupby_csv_path: str = ""
    iterations: int = 15  # 공정한 벤치마크 테스트를 위해 세 도구 모두 15회 반복 측정으로 통일합니다.

    def __post_init__(self):
        self.file_path = os.path.join(self.base_dir, "data", "raw", "sales_100k.csv")
        self.clean_csv_path = os.path.join(self.base_dir, "data", "processed", "sales_clean.csv")
        self.groupby_csv_path = os.path.join(self.base_dir, "data", "processed", "sales_groupby_summary.csv")

# ---------------------------------------------------------------------
# [1] 데이터 파일 사전 검증 (Fail-fast 패턴)
# ---------------------------------------------------------------------
def validate_environment(filepath: str) -> None:
    """데이터 파이프라인 가동 전, 파일의 존재 여부와 확장자를 사전에 검증합니다."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"지정된 경로에 파일이 존재하지 않습니다: {filepath}")
    
    if not filepath.lower().endswith('.csv'):
        raise TypeError(f"처리할 수 없는 파일 형식입니다. CSV 파일을 준비해주세요: {filepath}")
    
    logging.info("파일 경로 및 확장자 검증 완료.")

# ---------------------------------------------------------------------
# [2] 기초 데이터 탐색(EDA) 및 이상치 처리 + 산출물 저장
# ---------------------------------------------------------------------
def run_pandas_eda_and_get_bounds(config: PipelineConfig) -> Tuple[float, float]:
    """데이터 로드 후 스키마 확인, IQR 기반 이상치 범위 계산, 정제된 데이터(sales_clean.csv) 저장을 수행합니다."""
    logging.info("Pandas 기초 데이터 탐색 및 이상치 범위 계산 시작")
    df = pd.read_csv(config.file_path)
    
    # df.info()는 기본적으로 콘솔에 직접 출력되므로, io.StringIO() 버퍼를 통해 문자열로 캡처한 뒤 로깅 시스템에 통합합니다.
    buffer = io.StringIO()
    df.info(buf=buffer)
    logging.info(f"데이터 프레임 기본 정보:\n{buffer.getvalue()}")
    
    # 결측치(Null) 분포를 확인하여 데이터 품질을 평가합니다.
    logging.info(f"결측치 갯수:\n{df.isnull().sum().to_string()}")
    
    before_count = len(df)
    
    # 통상적인 통계학적 이상치 탐지 기법인 IQR 공식을 적용합니다.
    Q1 = df['amount'].quantile(0.25)
    Q3 = df['amount'].quantile(0.75)
    IQR = Q3 - Q1
    
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    
    # 산출된 정상 범위 내의 데이터만 필터링합니다.
    df_filtered = df[df['amount'].between(lower_bound, upper_bound)].copy()
    after_count = len(df_filtered)
    
    # 극단적인 필터링이나 데이터 오류로 인해 남은 데이터가 없을 경우를 대비한 방어 로직입니다.
    if df_filtered.empty:
        raise ValueError("이상치 제거 후 분석 가능한 데이터가 없습니다.")
        
    logging.info(f"이상치 처리 결과: 제거 전 {before_count:,}건 -> 제거 후 {after_count:,}건 (이상치 {before_count - after_count:,}건 제거)")
    
    # [실습 4 연계용 저장 1] IQR 이상치가 제거된 Clean DataFrame을 CSV 파일로 저장합니다.
    df_filtered.to_csv(config.clean_csv_path, index=False, encoding='utf-8-sig')
    logging.info(f"[산출물 저장 완료] 정제된 데이터 -> {config.clean_csv_path}")
    
    return lower_bound, upper_bound

# ---------------------------------------------------------------------
# [3] 라이브러리별 데이터 집계 파이프라인
# ---------------------------------------------------------------------
def run_pandas_pipeline(filepath: str, lower: float, upper: float) -> pd.DataFrame:
    """[Pandas 집계]""" 
    df = pd.read_csv(filepath, usecols=['region', 'category', 'amount'])
    df_filtered = df[df['amount'].between(lower, upper)]
    
    res = df_filtered.groupby(['region', 'category']).agg(
        total=('amount', 'sum'),
        mean=('amount', 'mean'),
        count=('amount', 'count')
    ).sort_values(by='total', ascending=False).reset_index()
    return res

def run_polars_pipeline(filepath: str, lower: float, upper: float) -> pl.DataFrame:
    """[Polars 집계]"""
    res = (
        pl.scan_csv(filepath)
        .filter(pl.col('amount').is_between(lower, upper))
        .group_by(['region', 'category'])
        .agg([
            pl.col('amount').sum().alias('total'),
            pl.col('amount').mean().alias('mean'),
            pl.col('amount').count().alias('count')
        ])
        .sort('total', descending=True)
        .collect()
    )
    return res

def run_duckdb_pipeline(filepath: str, lower: float, upper: float) -> pd.DataFrame:
    """[DuckDB 집계]"""
    query = f"""
        SELECT 
            region, 
            category, 
            SUM(amount) AS total, 
            AVG(amount) AS mean, 
            COUNT(amount) AS count
        FROM read_csv_auto('{filepath}')
        WHERE amount BETWEEN {lower} AND {upper}
        GROUP BY region, category
        ORDER BY total DESC
    """
    res = duckdb.query(query).df()
    return res

# ---------------------------------------------------------------------
# [4] 성능 측정 및 프로그램 실행 진입점 (Main)
# ---------------------------------------------------------------------
def measure_performance(tool_name: str, config: PipelineConfig, func: Callable, *args) -> float:
    """
    코드 중복 방지(DRY 원칙)를 위한 고차 함수(Wrapper Function)입니다.
    대상 함수와 인자를 동적으로 전달받아 timeit을 실행하고 평균 시간을 로깅합니다.
    """
    total_time = timeit.timeit(lambda: func(*args), number=config.iterations)
    avg_time = total_time / config.iterations
    logging.info(f"[{tool_name}] 평균 실행 시간 : {avg_time:.4f} 초")
    return avg_time

def main():
    config = PipelineConfig()
    
    # try-except-else-finally 구문을 적용하여 엔터프라이즈급 오류 제어 흐름을 구성합니다.
    try:
        logging.info("==================================================")
        logging.info("[실습 3] 데이터 처리 라이브러리 성능 분석 및 산출물 저장 시작")
        logging.info("==================================================")
        
        # 단계 1: 환경 유효성 검증
        validate_environment(config.file_path)
        
        # 단계 2: 기초 통계 및 IQR 정상 범위 산출 (정제된 sales_clean.csv 저장 포함)
        lower_bound, upper_bound = run_pandas_eda_and_get_bounds(config)
        
        # 단계 3: 각 도구별 집계 체인이 정상적으로 구성되었는지 결과물(DataFrame)을 출력하여 교차 검증합니다.
        logging.info("\n--- [결과 확인] Pandas 집계 (총매출 내림차순 정렬) ---")
        pandas_result = run_pandas_pipeline(config.file_path, lower_bound, upper_bound)
        logging.info(f"\n{pandas_result.head().to_string()}\n")
        
        # [실습 4 연계용 저장 2] region, category groupby 집계 결과를 CSV 파일로 저장합니다.
        pandas_result.to_csv(config.groupby_csv_path, index=False, encoding='utf-8-sig')
        logging.info(f"[산출물 저장 완료] Groupby 집계 결과 -> {config.groupby_csv_path}")
        
        logging.info("\n--- [결과 확인] Polars Lazy API 집계 ---")
        polars_result = run_polars_pipeline(config.file_path, lower_bound, upper_bound)
        logging.info(f"\n{str(polars_result.head())}\n")
        
        logging.info("\n--- [결과 확인] DuckDB SQL 집계 (DataFrame 출력) ---")
        duckdb_result = run_duckdb_pipeline(config.file_path, lower_bound, upper_bound)
        logging.info(f"\n{duckdb_result.head().to_string()}\n")
        
        # 단계 4: 제어된 동일 환경(iterations)에서 각 라이브러리의 성능을 프로파일링합니다.
        logging.info(f"--- [성능 비교] 속도 측정 (각 {config.iterations}회 반복) ---")
        measure_performance("Pandas", config, run_pandas_pipeline, config.file_path, lower_bound, upper_bound)
        measure_performance("Polars", config, run_polars_pipeline, config.file_path, lower_bound, upper_bound)
        measure_performance("DuckDB", config, run_duckdb_pipeline, config.file_path, lower_bound, upper_bound)

    # 예측 가능한 예외들을 세분화하여 캐치하고, 트러블슈팅에 용이하도록 명시적 에러 메시지를 제공합니다.
    except FileNotFoundError as e:
        logging.error(str(e))
    except TypeError as e:
        logging.error(str(e))
    except ValueError as e:
        logging.error(f"데이터 처리 중 문제 발생: {str(e)}")
    except Exception as e:
        logging.error(f"시스템 알 수 없는 에러 발생: {str(e)}")
        
    else:
        # try 블록 내의 모든 코드가 단 하나의 예외도 없이 완벽하게 실행되었을 때만 호출됩니다.
        logging.info("==================================================")
        logging.info("실습 3의 모든 데이터 분석, 파일 저장 및 성능 측정이 완벽하게 완료되었습니다.")
        logging.info("==================================================")
        
    finally:
        # 정상 종료 또는 치명적 에러 발생 등 어떠한 상황에서도 실행이 보장되는 블록입니다. 
        logging.info("프로세스를 안전하게 종료합니다.")

if __name__ == "__main__":
    main()