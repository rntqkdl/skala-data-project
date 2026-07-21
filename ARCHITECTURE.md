# 🏗️ 시스템 아키텍처 (ARCHITECTURE)

> 이 문서는 전체 시스템의 구조, 데이터 흐름, 모듈 간 의존성을 설명합니다.
> 기술자 대상 상세 문서입니다.

---

## 📊 시스템 전체 구조 (System Overview)

```
┌─────────────────────────────────────────────────────────────────┐
│                    📊 DATA ANALYTICS PIPELINE v2.0              │
│                   (데이터 분석 자동화 시스템)                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1️⃣  INPUT LAYER (입력 계층)                            │  │
│  │  • config.yaml (설정 파일)                               │  │
│  │  • data/raw/*.csv (원본 데이터)                          │  │
│  │  • data/processed/*.csv (정제 데이터)                    │  │
│  └──────────────────────────────────────────────────────────┘  │
│           ↓                                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 2️⃣  INITIALIZATION LAYER (초기화 계층)                │  │
│  │  • initialize_project() : 원스탑 초기화                 │  │
│  │    ├─ load_config() : YAML 로드                          │  │
│  │    ├─ ProjectPaths : 경로 설정                           │  │
│  │    └─ setup_logger() : 로거 구성                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│           ↓                                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 3️⃣  PROCESSING LAYER (처리 계층)                      │  │
│  │                                                          │  │
│  │  ┌─────────────────────────────────────────┐            │  │
│  │  │ A. EDA Visualization                    │            │  │
│  │  │  └─ generate_eda_subplots()             │            │  │
│  │  │    ├─ 히스토그램 + KDE                  │            │  │
│  │  │    ├─ 박스플롯                         │            │  │
│  │  │    ├─ 시계열 라인 차트                  │            │  │
│  │  │    └─ 상관계수 히트맵                   │            │  │
│  │  └─────────────────────────────────────────┘            │  │
│  │  ↓                                                       │  │
│  │  ┌─────────────────────────────────────────┐            │  │
│  │  │ B. Statistical Testing                 │            │  │
│  │  │  └─ perform_statistical_tests()        │            │  │
│  │  │    ├─ t-test (지역 간 매출 차이)       │            │  │
│  │  │    └─ χ² 검정 (지역-카테고리 연관성)  │            │  │
│  │  └─────────────────────────────────────────┘            │  │
│  │  ↓                                                       │  │
│  │  ┌─────────────────────────────────────────┐            │  │
│  │  │ C. Machine Learning Pipeline            │            │  │
│  │  │  └─ build_and_save_pipeline()          │            │  │
│  │  │    ├─ ColumnTransformer (전처리)       │            │  │
│  │  │    │  ├─ StandardScaler (수치형)       │            │  │
│  │  │    │  └─ OneHotEncoder (범주형)        │            │  │
│  │  │    └─ Ridge Regression (모델 학습)     │            │  │
│  │  └─────────────────────────────────────────┘            │  │
│  │  ↓                                                       │  │
│  │  ┌─────────────────────────────────────────┐            │  │
│  │  │ D. Interactive Visualization           │            │  │
│  │  │  └─ create_interactive_chart()         │            │  │
│  │  │    └─ Plotly Bar Chart (HTML)          │            │  │
│  │  └─────────────────────────────────────────┘            │  │
│  └──────────────────────────────────────────────────────────┘  │
│           ↓                                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 4️⃣  OUTPUT LAYER (출력 계층)                          │  │
│  │  • outputs/eda_subplots.png (고해상도 차트)             │  │
│  │  • outputs/sales_region_category.html (인터랙티브)      │  │
│  │  • models/sales_pipeline.joblib (학습 모델)             │  │
│  │  • logs/pipeline_execution.log (실행 로그)              │  │
│  └──────────────────────────────────────────────────────────┘  │
│           ↓                                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 5️⃣  STAKEHOLDER COMMUNICATION                          │  │
│  │  • 기술자: 상세 로그, 모델 평가 지표                     │  │
│  │  • 경영진: 인터랙티브 차트, 요약 보고서                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 데이터 흐름도 (Data Flow Diagram)

```
데이터 입력 단계
═════════════════════════════════════════════════════════════════

  CSV Files              JSON Files             Config
  (sales_100k.csv)   (Python_Practice*.json)   (config.yaml)
       ↓                    ↓                        ↓
       └────────────────────┴────────────────────────┘
                            │
                            ↓
              ┌─────────────────────────────┐
              │   read_file() 함수          │
              │ (CSV/JSON/Excel 자동 감지) │
              │ (자동 인코딩 재시도)        │
              └─────────────────────────────┘
                            │
                            ↓
              ┌─────────────────────────────┐
              │  Pandas DataFrame           │
              │ (in-memory data)            │
              └─────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            ↓               ↓               ↓
         
      [경로 A]         [경로 B]         [경로 C]
    정제 데이터      집계 데이터       원본 데이터
    (sales_clean)  (groupby_summary)  (sales_100k)
         │              │                 │
         ↓              ↓                 ↓

    generate_eda_   perform_         build_and_
    subplots()      statistical_     save_
                    tests()          pipeline()
         │              │                 │
         ├──────────────┼─────────────────┤
         ↓              ↓                 ↓
    PNG 이미지     통계 검정 결과    학습 모델
                       │            (joblib)
                       ↓
                 create_interactive_
                 chart()
                       │
                       ↓
                  HTML 차트
```

---

## 📦 모듈 구조 (Module Structure)

```
프로젝트 루트
├── config.yaml                    ← 중앙 설정 파일
├── util.py                        ← 공통 유틸리티 (960줄)
│   ├── load_config()
│   ├── ProjectPaths (클래스)
│   ├── setup_logger()
│   ├── read_file() (다중 형식)
│   ├── write_file()
│   ├── ensure_dir_exists()
│   └── initialize_project()
│
├── 광주_4반_안성민_실습.py         ← 메인 분석 스크립트
│   ├── generate_eda_subplots()
│   ├── perform_statistical_tests()
│   ├── build_and_save_pipeline()
│   ├── create_interactive_chart()
│   └── main()
│
├── data/
│   ├── raw/                       ← 원본 데이터
│   │   ├── sales_100k.csv
│   │   ├── Python_Practice1_Data.json
│   │   └── Python_Practice2_Data.json
│   └── processed/                 ← 정제된 데이터
│       ├── sales_clean.csv
│       ├── sales_groupby_summary.csv
│       └── *.json (에러 기록)
│
├── outputs/                       ← 분석 결과
│   ├── eda_subplots.png          ← 2x2 차트 (PNG)
│   └── sales_region_category.html ← 인터랙티브 차트
│
├── models/                        ← 저장된 모델
│   └── sales_pipeline.joblib      ← Ridge 회귀 모델
│
├── logs/                          ← 실행 로그
│   └── pipeline_execution.log
│
└── [문서]
    ├── README_FOR_STAKEHOLDERS.md
    ├── CHANGELOG.md
    └── ARCHITECTURE.md (현재 파일)
```

---

## 🔗 모듈 간 의존성 (Module Dependencies)

```
의존성 다이어그램 (Dependency Diagram)
═════════════════════════════════════════════════════════════════

        config.yaml
            ↑
            │ (yaml.load)
            │
        ┌───────────────┐
        │  util.py      │  ← PyYAML, pandas, logging 의존
        └───────────────┘
            ↑
            │ (import)
            │
            ├─ initialize_project()
            ├─ read_file()
            ├─ ProjectPaths
            └─ setup_logger()
                    │
                    ↓
        ┌────────────────────────────┐
        │ 광주_4반_안성민_실습.py    │ ← scikit-learn, matplotlib, plotly 의존
        └────────────────────────────┘
            │
            ├─ generate_eda_subplots()
            ├─ perform_statistical_tests()
            ├─ build_and_save_pipeline()
            ├─ create_interactive_chart()
            └─ main()


의존성 정리:
────────────────────────────────────────────────────────────────

util.py 의존성:
  • os, sys, yaml, logging, json, pandas, dataclasses

광주_4반_안성민_실습.py 의존성:
  • util.py (import)
  • os, logging, joblib, pandas, numpy
  • matplotlib, seaborn
  • plotly.express
  • scipy.stats
  • sklearn (model_selection, compose, preprocessing, pipeline, linear_model, metrics)

데이터 의존성:
  • data/raw/*.csv (필수)
  • data/processed/*.csv (필수)
```

---

## 🔐 데이터 흐름 보안 (Data Security)

```
민감 정보 처리 흐름
═════════════════════════════════════════════════════════════════

입력
  ↓
[접근 제어]
  • config.yaml: 로컬 파일만 (환경변수 검증)
  • 데이터 파일: 프로젝트 디렉토리 내만 접근
  ↓
[데이터 검증]
  • 파일 존재 여부 확인
  • 파일 크기 검증 (0 바이트 제외)
  • 컬럼 이름 검증
  ↓
[처리]
  • 인메모리 처리 (외부 저장 금지)
  • 임시 파일 미사용
  ↓
[출력]
  • outputs/: 일반인 접근 가능
  • logs/: 비기술자 접근 제한 권장
  • models/: 모델 공개 시 주의
  ↓
[감사]
  • pipeline_execution.log: 모든 작업 기록
```

---

## ⚙️ 실행 흐름 (Execution Flow)

```
메인 실행 흐름 (Main Execution Flow)
═════════════════════════════════════════════════════════════════

1. 프로젝트 초기화
   ┌──────────────────────────────────────┐
   │ config, paths, logger =              │
   │   initialize_project()               │
   │                                      │
   │ • config.yaml 로드 (모든 설정)      │
   │ • 경로 객체 생성                     │
   │ • 로거 구성 (터미널 + 파일)         │
   │ • 초기화 메시지 출력                │
   └──────────────────────────────────────┘
   실행 시간: < 100ms

2. 데이터 분석 (순차 실행)
   ┌──────────────────────────────────────┐
   │ ① EDA 시각화 생성 (2-3초)           │
   │   • read_file() 호출 (자동 감지)    │
   │   • 4개 차트 그리기                  │
   │   • PNG 저장                         │
   └──────────────────────────────────────┘
            ↓
   ┌──────────────────────────────────────┐
   │ ② 통계 검정 (< 1초)                 │
   │   • t-test 수행                      │
   │   • 카이제곱 검정                    │
   │   • 결과 해석 출력                   │
   └──────────────────────────────────────┘
            ↓
   ┌──────────────────────────────────────┐
   │ ③ ML 파이프라인 구축 (2-4초)        │
   │   • 전처리 파이프라인 생성           │
   │   • 데이터 분할 (80:20)             │
   │   • Ridge 회귀 학습                 │
   │   • R² 평가                          │
   │   • 모델 저장 (joblib)              │
   │   • 재로드 검증                      │
   └──────────────────────────────────────┘
            ↓
   ┌──────────────────────────────────────┐
   │ ④ 인터랙티브 차트 생성 (< 1초)     │
   │   • Plotly 차트 구성                 │
   │   • HTML 저장                        │
   └──────────────────────────────────────┘

3. 종료
   ┌──────────────────────────────────────┐
   │ 모든 작업 완료 메시지 출력           │
   │ (또는 에러 메시지)                   │
   │                                      │
   │ 전체 실행 시간: 5-10초              │
   └──────────────────────────────────────┘

에러 처리:
   try
    ├→ FileNotFoundError: 파일 누락
    ├→ ValueError: 데이터 검증 실패
    └→ Exception: 예기치 않은 에러
   else
    └→ 모든 작업 완료
```

---

## 🔄 에러 처리 전략 (Error Handling Strategy)

```
3계층 에러 처리 아키텍처
═════════════════════════════════════════════════════════════════

[계층 1] 파일 입출력 레벨
  read_file() 함수 내부:
    try:
      1. 파일 존재 여부 확인
      2. 주 인코딩으로 읽기 시도 (utf-8)
    except UnicodeDecodeError:
      3. 대체 인코딩 재시도 (cp949 → euc-kr → latin-1)
    else:
      4. 데이터 검증 (empty, 컬럼 확인)
    finally:
      5. 정리 작업

  write_file() 함수 내부:
    1. 디렉토리 자동 생성
    2. 형식별 저장 로직
    3. 에러 로깅


[계층 2] 함수 레벨
  각 분석 함수:
    try:
      데이터 로드 및 처리
    except [SpecificError]:
      에러 로깅 및 메시지
    raise


[계층 3] 메인 함수 레벨
  main() 함수:
    try:
      4개 분석 함수 순차 실행
    except FileNotFoundError:
      파일 누락 에러 처리
    except ValueError:
      데이터 검증 에러 처리
    except Exception:
      시스템 에러 처리
    else:
      성공 메시지 출력


로깅 수준:
  DEBUG    : 개발자 디버깅 (상세)
  INFO     : 일반 정보 (진행 상황)
  WARNING  : 주의 필요 (계속 진행)
  ERROR    : 오류 발생 (일부 기능 미작동)
  CRITICAL : 심각한 오류 (전체 중단)
```

---

## 🎯 성능 최적화 지점 (Performance Optimization Points)

| 구간 | 병목 | 최적화 | 우선순위 |
|------|------|--------|---------|
| 데이터 로드 | CSV 읽기 (대용량) | 청크 단위 로드 | 🔴 높음 |
| 인코딩 재시도 | 순차 재시도 | 병렬 시도 | 🟡 중간 |
| 시각화 | 고해상도 저장 | 비동기 저장 | 🟡 중간 |
| 모델 학습 | 대용량 데이터 | GPU 가속 | 🔴 높음 |
| 로깅 | 디스크 I/O | 버퍼링 | 🟢 낮음 |

---

## 🚀 확장성 가이드 (Scalability Guide)

### 수평 확장 (Horizontal Scaling)
```
현재: 단일 파이프라인
→ 미래: 병렬 파이프라인 (여러 데이터셋 동시 처리)
  방법: multiprocessing.Pool 사용
```

### 수직 확장 (Vertical Scaling)
```
현재: 메모리 기반 (< 1GB)
→ 미래: 스트리밍 처리 (무제한)
  방법: Dask, Spark 통합
```

### 기능 확장
```
현재: EDA + 통계 + ML (기본)
→ 미래: 심화 분석
  • 시계열 분석 (ARIMA, Prophet)
  • 클러스터링 (K-means, DBSCAN)
  • 이상 탐지 (Isolation Forest)
  • 자연어 처리 (TF-IDF, Word2Vec)
```

---

**Last Updated**: 2026-07-21  
**Maintained by**: 안성민 (광주 4반)
