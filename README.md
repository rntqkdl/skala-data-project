# 📊 SKALA 데이터 분석 및 파이프라인 실습 프로젝트

이 프로젝트는 파이썬 핵심 문법 실습부터 데이터 유효성 검증, 다중 데이터 프레임워크(Pandas, Polars, DuckDB) 벤치마킹, 그리고 EDA(탐색적 데이터 분석), 통계 검정, Scikit-Learn 머신러닝 파이프라인 구축 및 시각화까지 포괄하는 데이터 엔지니어링 및 데이터 과학 통합 실습 프로젝트입니다.

## 👤 작성자 정보
- **작성자**: 안성민 (광주 4반)
- **개발 기간**: 2026년 7월 20일 ~ 2026년 7월 21일

---

## 🛠 기술 스택
- **Language**: Python 3.10+
- **Data Frameworks**: `pandas`, `polars`, `duckdb`
- **Machine Learning**: `scikit-learn`, `joblib`
- **Visualization**: `matplotlib`, `seaborn`, `plotly`
- **Statistics**: `scipy`, `numpy`
- **Validation**: `pydantic` (v2), `dataclasses`

---

## 📂 프로젝트 구조
```text
skala-data-project/
├── 광주_4반_안성민_실습_1.py       # [실습 1] 파이썬 핵심 자료구조 및 컴프리헨션, 메모리 비교
├── 광주_4반_안성민_실습_2.py       # [실습 2] Pydantic v2 기반 유효성 검증 및 Two-Phase I/O 파이프라인
├── 광주_4반_안성민_실습_3.py       # [실습 3] Pandas, Polars, DuckDB 성능 벤치마킹 & 데이터 정제(IQR)
├── 광주_4반_안성민_실습.py         # [실습 4] 시각화, 가설 검정 및 Ridge 머신러닝 파이프라인
├── test.py                       # 테스트용 보조 스크립트
├── test2.py                      # 테스트용 보조 스크립트
├── requirements.txt              # 프로젝트 의존성 라이브러리 목록
├── data/
│   ├── raw/                      # 원본 데이터 파일 보관 디렉토리
│   │   ├── Python_Practice1_Data.json
│   │   ├── Python_Practice2_Data.json
│   │   └── sales_100k.csv
│   └── processed/                # 파이프라인에 의해 정제/가공된 데이터 보관 디렉토리
│       ├── error_records.json
│       ├── errors_phase1.json
│       ├── eval_dataset.json
│       ├── sales_clean.csv       # IQR 정제를 마친 Clean 데이터
│       ├── sales_groupby_summary.csv # 각 엔진으로 요약 집계된 매출 데이터
│       ├── valid_phase1.csv
│       └── valid_records.csv
├── logs/                         # 실행 로그 파일
│   └── pipeline_execution.log    # [실습 4] 파이프라인 수행 과정 및 에러 이력 영구 기록
├── models/                       # 학습이 완료된 가중치 및 파이프라인 객체 보관
│   └── sales_pipeline.joblib     # 학습된 Scikit-Learn 전처리 + Ridge 머신러닝 모델
└── outputs/                      # 시각화 리포트 결과물
    └── sales_region_category.html # Plotly 인터랙티브 시각화 리포트
```

---

## 📖 파일별 상세 설명

### 1. `광주_4반_안성민_실습_1.py` (파이썬 자료구조 및 효율성 검증)
- **목적**: 파이썬의 강력한 핵심 문법들을 활용해 대용량 데이터 처리 속도와 메모리를 최적화하는 방안을 배웁니다.
- **주요 기능**:
  - `TypedDict`와 `@dataclass`를 결합하여 데이터를 구조화하고 생성 시점(`__post_init__`)에서 타입 및 정적/런타임 데이터 무결성을 검증합니다.
  - 반복(for) 루프를 배제하고 **리스트/딕셔너리 컴프리헨션** 문법을 적용하여 조건 필터링(`amount >= 1000`) 및 지역별 총합 연산의 속도를 극대화하고 마이크로초(µs) 단위로 실행 시간을 측정합니다.
  - `Counter` 및 `defaultdict` 자료구조를 활용해 중복 연산 코드를 제거하고 카테고리별 건수 세기, 그룹핑 로직을 간결하게 구현합니다.
  - **Generator(yield) 표현식**과 **리스트 컴프리헨션** 간의 메모리 점유율을 `sys.getsizeof`를 통해 직접 비교 검증합니다.
  - 컴프리헨션과 `defaultdict(int)` 조합으로 월별/카테고리별 매출 다중 집계를 수행합니다.

### 2. `광주_4반_안성민_실습_2.py` (Pydantic 데이터 검증 및 Two-Phase I/O)
- **목적**: 불완전하거나 비정상적인 원본 데이터를 걸러내는 실무형 데이터 유효성 검증(Validation) 및 I/O 파이프라인을 구축합니다.
- **주요 기능**:
  - **Pydantic v2 스키마 정의**: `SalesRecord(BaseModel)`를 설계하여 공백 문자 제어(`min_length=1`), 매출액 범위(`gt=0`), 옵셔널 필드 할당 등의 엄격한 데이터 품질 규격을 준수합니다.
  - `try-except-finally` 기반의 예외 처리를 로깅(Logging) 모듈과 연계하여 안전한 데이터 리드(`safe_load_csv`)를 구현합니다.
  - 원천 데이터를 무결성 기준에 따라 정상 데이터(`valid`)와 에러 이력 및 사유를 포함한 에러 데이터(`errors`)로 철저하게 분리 및 저장합니다.
  - **Two-Phase 아키텍처**:
    - *Phase 1*: 과제 체크포인트 검증용 Mock 데이터(7건 중 정상 4건, 에러 3건) 완벽 분리 검증
    - *Phase 2*: 실제 원본 데이터를 활용한 유효성 검증(정상 90건, 에러 10건) 파이프라인 수행
  - `model_dump()`와 제너레이터 방식을 활용하여 대용량 파일 쓰기 동작 시의 메모리 사용량을 최소화합니다.

### 3. `광주_4반_안성민_실습_3.py` (멀티엔진 데이터 정제 및 벤치마킹)
- **목적**: 데이터 사이언스 분야에서 널리 활용되는 3대 핵심 라이브러리(Pandas, Polars, DuckDB)의 연산 속도를 벤치마킹하고 데이터를 정제합니다.
- **주요 기능**:
  - **기초 데이터 탐색(EDA)**: 데이터 파일 사전 검증(Fail-fast 패턴)을 수행하고, Null 결측치 분포 탐색 및 통계 분석을 수행합니다.
  - **이상치(Outlier) 제거**: 통계학적 이상치 탐지 기법인 **IQR(Interquartile Range)** 공식을 `amount` 칼럼에 적용하여 정상 결제 범위를 넘어서는 극단적인 이상치를 자동 정제하고 `sales_clean.csv`로 저장합니다.
  - **성능 벤치마크**: 정제된 동일한 데이터셋을 기반으로 세 엔진을 사용해 다중 조건 집계(Group by) 연산을 독립 실행하여 연산 속도를 측정합니다.
    - *Pandas*: Named Aggregation 사용
    - *Polars*: Lazy Evaluation (`lazy()`, `collect()`)을 활용한 최적화 쿼리 계획(Query Plan) 동작
    - *DuckDB*: SQL 쿼리를 활용한 빠른 인메모리 관계형 연산
  - 공정한 벤치마크 테스트를 위해 세 엔진 모두 15회 반복 측정(`timeit.timeit`)하여 성능 비교 보고서를 출력하고, 결과 요약을 `sales_groupby_summary.csv` 파일로 저장합니다.

### 4. `광주_4반_안성민_실습.py` (시각화, 통계 검정, 머신러닝 예측 모델 파이프라인)
- **목적**: 실무 데이터 분석 과정의 종착지인 시각화 보고서, 가설 검정을 통한 비즈니스 인사이트 도출, Scikit-Learn 머신러닝 파이프라인 서빙을 포함하는 종합 데이터 분석 스크립트입니다.
- **주요 기능 및 분석 결과**:
  - **통계적 가설 검정**:
    - **두 집단 평균 차이 검정 (Independent Two-Sample t-test)**: 서울 매출액 vs 부산 매출액
      - *통계량*: `0.7269`, *p-value*: `0.4673`
      - *해석*: p-value가 유의수준 0.05 이상이므로 귀무가설을 기각하지 못함. 즉, 두 지역 간 평균 매출은 통계적으로 유의미한 차이가 없습니다.
    - **범주형 독립성 검정 (Chi-Square Test of Independence)**: 지역(Region) vs 주로 구매하는 상품 카테고리(Category)
      - *통계량*: `74.9919`, *p-value*: `0.00985`
      - *해석*: p-value가 유의수준 0.05 미만이므로 귀무가설을 기각함. 즉, 지역과 구매 카테고리 간에는 유의미한 연관성(종속성)이 존재합니다.
  - **EDA 시각화 (2x2 서브플롯)**:
    1. *매출액 분포*: 오른쪽으로 긴 꼬리를 갖는 우상향 비대칭 분포(Right-skewed)를 보이며 대다수 결제가 0~200만 원 사이에 밀집됨.
    2. *카테고리별 매출 분포*: 카테고리별 중앙값은 유사하나, 고액 Outlier 결제가 다수 상단에 포진함.
    3. *월별 총매출 추이*: 2023년 2월, 10월, 2024년 1월 등 특정 시점에 매출이 급등락하는 변동성이 포착됨.
    4. *수치형 상관관계 Heatmap*: 매출액(`amount`)은 수량(`quantity`, r=0.63), 단가(`unit_price`, r=0.66)와 매우 강한 정적 상관관계를 지님. 반면, 고객 연령(`customer_age`)은 매출과 연관성이 없음(r=0.00).
  - **Plotly 인터랙티브 HTML 리포트**: 지역별 및 카테고리별 다차원 매출액을 3D 형태에 가깝게 대화형으로 탐색할 수 있는 `sales_region_category.html` 시각화 결과물을 저장합니다.
  - **Scikit-Learn 머신러닝 파이프라인**:
    - 데이터 전처리 파이프라인(`ColumnTransformer`): 수치형 데이터에 대해 `StandardScaler`, 범주형 데이터에 대해 `OneHotEncoder`를 유기적으로 바인딩합니다.
    - Ridge Regression(리지 회귀) 알고리즘을 연결하여 예측 성능 $R^2 = 0.1890$을 기록하였으며, 모델 학습 후 `models/sales_pipeline.joblib` 파일로 완전하게 직렬화해 보존합니다.
  - **하이브리드 로깅**: 터미널 출력과 함께 `logs/pipeline_execution.log` 파일에 전 처리 이력과 에러 로그를 영구 기록합니다.

---

## 🚀 시작하기

### 1. 가상환경 및 의존성 설치
본 프로젝트를 구동하기 위한 가상환경 설정 및 패키지 설치 방법입니다.
```bash
# 가상환경 생성 (선택 사항)
python -m venv venv
source venv/bin/activate  # macOS / Linux
# venv\Scripts\activate  # Windows

# 필수 라이브러리 일괄 설치
pip install -r requirements.txt
```

### 2. 실행 순서 및 방법
각 실습 단계별 스크립트는 모듈별로 격리되어 있어 독립적으로도 실행 가능합니다.

```bash
# 1. 파이썬 문법 및 제너레이터 성능 검증
python 광주_4반_안성민_실습_1.py

# 2. Mock & Real 데이터 유효성 검증 파이프라인
python 광주_4반_안성민_실습_2.py

# 3. Pandas vs Polars vs DuckDB 벤치마킹 및 IQR 정제
python 광주_4반_안성민_실습_3.py

# 4. EDA 시각화, 통계 검정 및 예측 모델링 수행
python 광주_4반_안성민_실습.py
```

---

## 🎯 주요 산출물
파이프라인 실행이 완료되면 프로젝트 폴더 내에 다음과 같은 산출물이 저장됩니다:
1. `data/processed/sales_clean.csv` : IQR 기반 이상치가 성공적으로 정제된 정규 데이터셋
2. `data/processed/sales_groupby_summary.csv` : 지역/카테고리별 다중 집계 결과 테이블
3. `logs/pipeline_execution.log` : 분석 파이프라인의 에러 예외 사항 및 실행 기록
4. `models/sales_pipeline.joblib` : Scikit-Learn 전처리 스케일러와 Ridge 모델 파이프라인 덤프본
5. `outputs/sales_region_category.html` : Plotly를 통한 반응형 웹 시각화 대시보드 리포트
