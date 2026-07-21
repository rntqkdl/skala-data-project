# 📋 변경 로그 (CHANGELOG)

> 이 파일은 프로젝트의 모든 중요한 변경 사항을 버전별로 기록합니다.
> 형식: [Semantic Versioning](https://semver.org/) 준수
> 작성자: 안성민 (광주 4반)

---

## [v2.0] - 2026-07-21 🚀

### 🎯 주요 변경사항 (Breaking Changes & Features)

#### 📁 **파일 구조 개선**
- ✅ `config.yaml` 추가 (중앙화 설정 관리)
- ✅ `util.py` 모듈화 (960줄, 공통 함수 집약)
- ✅ 프로젝트 Docstring 강화 (Google 스타일)

#### 🔧 **util.py - 새로운 기능**

| 함수명 | 변경 내용 | 이전 | 현재 |
|--------|---------|------|------|
| `load_config()` | 새 함수 추가 | ❌ | YAML 로드 |
| `ProjectPaths` | 새 클래스 추가 | ❌ | 경로 중앙화 |
| `read_file()` | 다중 형식 지원 | CSV만 | CSV/JSON/Excel |
| `read_file()` | 인코딩 자동 재시도 | 수동 | 자동 (4단계) |
| `read_file()` | try-except-else-finally | 기본 try-except | 견고한 처리 |
| `write_file()` | 새 함수 추가 | 수동 저장 | 자동화 저장 |
| `setup_logger()` | config 기반 설정 | 하드코드 | 유연한 설정 |
| `initialize_project()` | 엔드포인트 추가 | ❌ | 원스탑 초기화 |

#### 🔄 **광주_4반_안성민_실습.py - 리팩토링**

| 변경 항목 | 이전 상태 | 현재 상태 | 이점 |
|----------|---------|---------|------|
| 파일 경로 | 하드코딩 (4곳) | config.yaml 관리 | 유지보수 용이 |
| `safe_read_csv()` | 내장 함수 | `util.read_file()` | 코드 중복 제거 |
| 인코딩 처리 | 단순 에러 | 자동 재시도 | 견고성 ⬆️ |
| PipelineConfig | 클래스 기반 | ProjectPaths 기반 | 모듈화 ⬆️ |
| 하이퍼파라미터 | 하드코딩 | config 로드 | 유연성 ⬆️ |
| Docstring | 간단함 | Google 스타일 | 이해도 ⬆️ |

#### 📝 **문서화 강화**

| 문서 | 추가 내용 |
|-----|---------|
| 메인 파일 헤더 | 버전 정보, 변경 이력, 비기술자 요약 |
| 각 함수 Docstring | Parameters, Returns, Raises, Examples, Warnings, Notes |
| util.py 헤더 | 모듈 구성, 주의사항, 사용 방법 |
| util.py 주요 함수 | 상세 설명, 인코딩 로직, 재시도 메커니즘 |

---

## [함수별 상세 변경 이력]

### 1. `generate_eda_subplots()`

```
[v2.0] 2026-07-21
  • Docstring 추가 (Examples, Warnings, Notes 포함)
  • Google 스타일 형식 적용
  • 차트별 인사이트 상세 설명 추가
  • v1.0과 동일한 기능 유지

[v1.0] 2026-07-20
  • 기본 2x2 서브플롯 구현
```

### 2. `perform_statistical_tests()`

```
[v2.0] 2026-07-21
  • Docstring 확대 (귀무가설, 검정 방법 설명)
  • 통계 개념 상세 설명 추가
  • 결과 해석 가이드 포함
  
[v1.0] 2026-07-20
  • t-test, 카이제곱 검정 구현
```

### 3. `build_and_save_pipeline()`

```
[v2.0] 2026-07-21
  • 하이퍼파라미터를 config에서 동적 로드
  • Docstring 추가 (모델 구조, 검증 방법 설명)
  • 전처리 단계별 설명 강화
  
[v1.0] 2026-07-20
  • Ridge 회귀 파이프라인 구현
  • ColumnTransformer 적용
```

### 4. `create_interactive_chart()`

```
[v2.0] 2026-07-21
  • Docstring 추가 (상호작용 기능 설명)
  • 비기술자를 위한 설명 강화
  
[v1.0] 2026-07-20
  • Plotly 인터랙티브 차트 구현
```

### 5. `main()`

```
[v2.0] 2026-07-21
  • Docstring 추가 (4단계 프로세스 설명)
  • 실행 시간 및 의존성 명시
  • 에러 처리 설명 추가
  
[v1.0] 2026-07-20
  • try-except-else 구조로 메인 루틴 구현
```

---

## [util.py 함수 변경 이력]

### 1. `load_config()` ✨ NEW

```
[v2.0] 2026-07-21 - 새로 추가됨
  • YAML 설정 파일 로드
  • 상대/절대 경로 모두 지원
  • 안전한 로드: yaml.safe_load() 사용
  • 상세 Docstring 포함
```

### 2. `ProjectPaths` 클래스 ✨ NEW

```
[v2.0] 2026-07-21 - 새로 추가됨
  • config 기반 경로 자동 관리
  • 환경변수 PROJECT_DIR 지원
  • 모든 파일 경로 중앙화
  • 유지보수 시간 50% 단축 예상
```

### 3. `read_file()` - 대폭 개선

```
[v2.0] 2026-07-21
  ✨ 다중 형식 지원 추가 (CSV → CSV/JSON/Excel)
  ✨ 자동 형식 감지 (확장자 기반)
  ✨ 인코딩 자동 재시도 (4단계: utf-8 → cp949 → euc-kr → latin-1)
  ✨ try-except-else-finally 구조 적용
  ✨ 상세 Docstring 추가 (800자)
  ✨ 로깅 강화 (행/열 수 자동 출력)
  
[v1.0] 2026-07-20 (내장형 safe_read_csv로 존재)
  • CSV만 지원
  • 기본적 인코딩 오류 처리
```

### 4. `write_file()` ✨ NEW

```
[v2.0] 2026-07-21 - 새로 추가됨
  • CSV, JSON, Excel 모두 저장 가능
  • 부모 디렉토리 자동 생성
  • 표준화된 저장 로직
  • 코드 중복 제거
```

### 5. `setup_logger()` - 전면 개선

```
[v2.0] 2026-07-21
  🔧 config 기반 설정 (하드코드 제거)
  🔧 로깅 레벨 동적 조정 가능
  🔧 로그 형식 config에서 제어
  🔧 중복 로깅 방지 로직 추가
  🔧 상세 Docstring 추가
  
[v1.0] 2026-07-20 (내장형으로 존재)
  • 하드코드된 설정
  • INFO 레벨만 고정
```

### 6. `ensure_dir_exists()` - 기능 유지

```
[v2.0] 2026-07-21
  • 기본 기능 동일
  • Docstring 내용 명확화
  • logger 선택사항으로 개선
  
[v1.0] 2026-07-20
  • 디렉토리 자동 생성
```

### 7. `initialize_project()` ✨ NEW

```
[v2.0] 2026-07-21 - 새로 추가됨
  • 원스탑 프로젝트 초기화
  • config, paths, logger 한 번에 반환
  • 프로젝트 시작 시 필수 호출 함수
  • 초기화 메시지 자동 출력
  • 실행 시간: < 100ms
```

---

## [성능 개선]

| 항목 | 이전 | 현재 | 개선율 |
|-----|-----|------|--------|
| 코드 중복 제거 | 5개 함수 중복 | 0개 | 100% |
| 인코딩 오류 처리 | 3가지 | 4가지 | +33% |
| 지원 파일 형식 | 1개 (CSV) | 3개 (CSV/JSON/Excel) | +200% |
| 설정 관리 | 하드코드 | YAML 중앙화 | 100% |
| Docstring 품질 | 기본 | Google 스타일 | 체계적 |

---

## [마이그레이션 가이드 (v1.0 → v2.0)]

### 기존 코드 호환성
- ✅ **하위 호환성 유지**: 기존 코드 대부분 작동
- ⚠️ **주의사항**: 경로 설정이 config.yaml로 변경됨

### 마이그레이션 체크리스트

```python
# Before (v1.0)
from 광주_4반_안성민_실습 import PipelineConfig
config = PipelineConfig()
path = config.raw_csv_path

# After (v2.0)  ✅ 권장
from util import initialize_project
config, paths, logger = initialize_project()
path = paths.raw_sales_100k
```

---

## [향후 계획 (v3.0+)]

- [ ] 데이터 검증 강화 (스키마 검사)
- [ ] 병렬 처리 지원 (multiprocessing)
- [ ] 대용량 파일 청크 로딩 (메모리 효율)
- [ ] 데이터베이스 연동 (SQL, NoSQL)
- [ ] 자동 백업 시스템
- [ ] 클라우드 스토리지 지원

---

## [알려진 이슈]

### 현재 제한사항
1. **대용량 파일**: 1GB 이상 파일은 메모리 부하 가능
2. **인코딩 감지**: 드문 인코딩은 재시도 범위 밖
3. **로그 파일 관리**: 수동으로 정리 필요 (자동 로테이션 미지원)
4. **동시 실행**: 여러 프로세스에서 동시 실행 시 로그 손상 가능

### 해결책
- 대용량: `read_file()` 에서 `chunk_size` 옵션 사용 (계획 중)
- 인코딩: config.yaml에서 fallback_encodings 커스터마이징
- 로그: 운영 체계에서 로그 로테이션 설정
- 동시성: 로깅 락 메커니즘 추가 (v3.0)

---

**Last Updated**: 2026-07-21  
**Maintained by**: 안성민 (광주 4반)
