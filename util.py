# =====================================================================
# 🛠️  PROJECT COMMON UTILITIES v2.0
# =====================================================================
# 파일: util.py
# 작성자: 안성민 (광주 4반)
# 작성일: 2026-07-21
#
# 설명: 프로젝트 공통 유틸리티 함수 모음 (960줄)
#      모든 데이터 처리의 기반이 되는 핵심 모듈
#
# ┌─────────────────────────────────────────────────────────────────┐
# │ 📦 주요 기능 구성                                               │
# ├─────────────────────────────────────────────────────────────────┤
# │ 1️⃣  설정 관리 (config.yaml 기반)                              │
# │    - load_config(): YAML 파일 로드                             │
# │    - ProjectPaths: 경로 중앙화 관리                            │
# │                                                                 │
# │ 2️⃣  로깅 (터미널 + 파일 동시 출력)                           │
# │    - setup_logger(): config 기반 로거 설정                     │
# │    - 자동 디렉토리 생성                                        │
# │    - 레벨 조정 가능 (DEBUG/INFO/WARNING 등)                   │
# │                                                                 │
# │ 3️⃣  파일 읽기 (다중 형식 지원)                               │
# │    - read_file(): CSV/JSON/Excel 자동 감지                    │
# │    - 인코딩 자동 재시도 (utf-8 → cp949 → euc-kr)             │
# │    - try-except-else-finally 구조                              │
# │                                                                 │
# │ 4️⃣  파일 쓰기 (다중 형식 지원)                               │
# │    - write_file(): CSV/JSON/Excel로 저장                      │
# │    - 부모 디렉토리 자동 생성                                   │
# │                                                                 │
# │ 5️⃣  디렉토리 관리                                             │
# │    - ensure_dir_exists(): 경로 자동 생성                       │
# │    - 파일 저장 전 사전 검증                                    │
# └─────────────────────────────────────────────────────────────────┘
#
# ⚠️  사용 주의사항:
#    - config.yaml이 반드시 프로젝트 루트에 필요
#    - PyYAML, pandas 라이브러리 필수 설치
#    - 인코딩 재시도는 순차적으로 진행 (느릴 수 있음)
#    - 대용량 파일 청크 로딩 지원 (선택사항)
#
# =====================================================================

import os
import sys
import yaml
import logging
import json
import pandas as pd
from pathlib import Path
from typing import Any, Dict, Optional, List, Union
from dataclasses import dataclass

# =====================================================================
# [1] 설정 파일 로드 함수
# =====================================================================

def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """
    YAML 설정 파일을 로드합니다.
    
    프로젝트의 모든 설정 정보를 중앙화되게 관리하는 첫 번째 단계입니다.
    상대 경로를 입력하면 자동으로 스크립트 디렉토리 기준으로 변환됩니다.
    
    Args:
        config_path (str): config.yaml 파일의 경로
                          상대경로: "config.yaml" (기본값, 스크립트 디렉토리 기준)
                          절대경로: "/absolute/path/to/config.yaml"
    
    Returns:
        Dict[str, Any]: 파싱된 YAML 설정 딕셔너리
                       최상위 키: project, data, output, logging, 
                                file_reading, model, visualization
    
    Raises:
        FileNotFoundError: config.yaml 파일이 없을 때
        yaml.YAMLError: YAML 구문 오류 (탭/들여쓰기 문제 등)
        Exception: 기타 파일 읽기 오류
    
    Examples:
        >>> config = load_config()
        >>> print(config['project'])
        {'use_env_var': True, 'default_base_dir': '.'}
        >>> config['data']['raw']['sales_100k']
        'data/raw/sales_100k.csv'
    
    Warnings:
        - config.yaml이 UTF-8 인코딩이어야 함
        - YAML 문법 오류가 있으면 전체 파이프라인 실패
        - 환경변수 PROJECT_DIR이 설정되면 우선 적용됨
    
    Notes:
        - v2.0부터 중앙화 설정 관리 도입
        - 모든 함수가 이 설정을 의존함
        - 안전한 로드: yaml.safe_load() 사용 (임의 코드 실행 방지)
    """
    # config_path가 상대경로면 스크립트 디렉토리 기준
    if not os.path.isabs(config_path):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, config_path)
    
    try:
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        return config
    
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"YAML parsing failed for {config_path}: {str(e)}")
    except Exception as e:
        raise Exception(f"Failed to load config: {str(e)}")

# =====================================================================
# [2] 경로 관리 클래스
# =====================================================================

@dataclass
class ProjectPaths:
    """설정 파일 기반 프로젝트 경로 관리"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        config 딕셔너리를 기반으로 모든 경로를 설정합니다.
        
        Args:
            config: load_config()로 반환된 설정 딕셔너리
        """
        # 기본 디렉토리 결정
        if config.get('project', {}).get('use_env_var', True):
            self.base_dir = os.getenv("PROJECT_DIR", 
                                       os.path.dirname(os.path.abspath(__file__)))
        else:
            self.base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 데이터 경로
        data_config = config.get('data', {})
        self.raw_sales_100k = self._resolve_path(data_config.get('raw', {}).get('sales_100k'))
        self.raw_practice1 = self._resolve_path(data_config.get('raw', {}).get('python_practice1'))
        self.raw_practice2 = self._resolve_path(data_config.get('raw', {}).get('python_practice2'))
        
        self.clean_sales = self._resolve_path(data_config.get('processed', {}).get('sales_clean'))
        self.groupby_summary = self._resolve_path(data_config.get('processed', {}).get('sales_groupby_summary'))
        self.valid_records = self._resolve_path(data_config.get('processed', {}).get('valid_records'))
        self.error_records = self._resolve_path(data_config.get('processed', {}).get('error_records'))
        
        # 출력 경로
        output_config = config.get('output', {})
        self.plot_eda = self._resolve_path(output_config.get('plots', {}).get('eda_subplots'))
        self.plot_interactive = self._resolve_path(output_config.get('plots', {}).get('eda_interactive'))
        self.model_sales = self._resolve_path(output_config.get('models', {}).get('sales_pipeline'))
        
        # 로깅 경로
        log_config = config.get('logging', {})
        self.log_dir = self._resolve_path(log_config.get('log_dir'))
        self.log_file = self._resolve_path(log_config.get('log_file'))
    
    def _resolve_path(self, rel_path: Optional[str]) -> str:
        """상대 경로를 절대 경로로 변환"""
        if rel_path is None:
            return ""
        return os.path.join(self.base_dir, rel_path)

# =====================================================================
# [3] 로깅 설정
# =====================================================================

def setup_logger(config: Dict[str, Any], name: str = "DataPipeline") -> logging.Logger:
    """
    config 기반으로 로거를 설정합니다.
    
    터미널과 파일에 동시에 로그를 출력하는 하이브리드 로거를 구성합니다.
    로깅 레벨, 형식, 출력 대상을 모두 config.yaml에서 제어 가능합니다.
    
    로거 구성:
    - StreamHandler: 터미널 콘솔 출력 (즉각적 피드백)
    - FileHandler: 파일 저장 (감시 추적성, 장기 기록)
    
    Args:
        config (Dict[str, Any]): load_config()의 반환값
                                config['logging'] 섹션 참조
        name (str): 로거 이름 (기본값: "DataPipeline")
                   여러 로거 구별 시 사용
    
    Returns:
        logging.Logger: 설정된 로거 객체
                       logger.info/warning/error 등으로 사용
    
    Raises:
        PermissionError: 로그 디렉토리 생성 권한 부족
        OSError: 파일 시스템 오류
    
    Examples:
        >>> config = load_config()
        >>> logger = setup_logger(config, name="CustomLogger")
        >>> logger.info("시작합니다")
        # 터미널 + logs/pipeline_execution.log에 모두 출력됨
        >>> logger.warning("주의해주세요")
        >>> logger.error("에러 발생!")
    
    Warnings:
        - 로그 파일이 계속 증가 (수동으로 정리 필요)
        - 여러 프로세스 동시 실행 시 로그 손상 가능
        - 로그 레벨을 DEBUG로 설정하면 매우 상세해짐
    
    Notes:
        - v2.0부터 config 기반 설정 지원
        - 중복 로깅 방지: 기존 핸들러 제거 후 재설정
        - UTF-8 인코딩으로 한글 안전 지원
        - 날짜/시간 형식: "HH:MM:SS" 기본값
        - 로그 형식: timestamp [LEVEL] 함수명:라인수 - 메시지
    """
    logger = logging.getLogger(name)
    
    # 기존 핸들러 제거 (중복 설정 방지)
    if logger.handlers:
        logger.handlers.clear()
    
    logger.setLevel(logging.DEBUG)
    
    log_config = config.get('logging', {})
    log_level = getattr(logging, log_config.get('level', 'INFO'))
    logger.setLevel(log_level)
    
    log_format = log_config.get('format', '%(asctime)s [%(levelname)s] %(message)s')
    date_format = log_config.get('date_format', '%H:%M:%S')
    formatter = logging.Formatter(log_format, datefmt=date_format)
    
    # 1. 터미널(Console) 핸들러
    if log_config.get('console_output', True):
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(log_level)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
    
    # 2. 파일(File) 핸들러
    if log_config.get('file_output', True):
        log_file = log_config.get('log_file', 'logs/pipeline_execution.log')
        log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), log_file)
        
        # 로그 디렉토리 생성
        log_dir = os.path.dirname(log_file)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

# =====================================================================
# [4] 디렉토리 관리
# =====================================================================

def ensure_dir_exists(filepath: str, logger: Optional[logging.Logger] = None) -> None:
    """
    파일 저장 경로의 부모 디렉토리가 존재하는지 확인하고,
    없으면 생성합니다.
    
    Args:
        filepath: 파일 경로
        logger: 로거 객체 (선택사항)
    """
    directory = os.path.dirname(filepath)
    if directory and not os.path.exists(directory):
        try:
            os.makedirs(directory)
            if logger:
                logger.info(f"[경로 생성] 디렉토리가 생성되었습니다: {directory}")
        except Exception as e:
            if logger:
                logger.error(f"[경로 생성 실패] {directory}: {str(e)}")
            raise

# =====================================================================
# [5] 파일 읽기 함수 (다중 형식 지원)
# =====================================================================

def read_file(filepath: str, 
              file_type: Optional[str] = None,
              config: Optional[Dict[str, Any]] = None,
              logger: Optional[logging.Logger] = None) -> Optional[Any]:
    """
    다양한 형식의 파일을 안전하게 읽습니다.
    
    CSV, JSON, Excel 형식을 자동 감지하여 읽습니다. 인코딩 오류 발생 시
    자동으로 대체 인코딩을 순차 시도하는 강건한 에러 처리를 제공합니다.
    
    인코딩 재시도 순서:
    1. 지정된 인코딩 (기본: utf-8)
    2. Windows 한글 (cp949)
    3. 리눅스 한글 (euc-kr)
    4. 국제 호환 (latin-1)
    
    Args:
        filepath (str): 읽을 파일의 경로 (절대 또는 상대)
        file_type (str, Optional): 파일 형식 명시
                                  'csv', 'json', 'excel', 'xlsx', 'xls'
                                  None이면 확장자로 자동 감지
        config (Dict[str, Any], Optional): util.load_config()의 반환값
                                          CSV/JSON 읽기 옵션 제어
        logger (logging.Logger, Optional): 로거 객체
                                          None이면 로깅 스킵
    
    Returns:
        pd.DataFrame 또는 dict/list: 파일 형식에 따라
                                   CSV/Excel → DataFrame
                                   JSON → dict/list
    
    Raises:
        FileNotFoundError: 파일이 없을 때
        ValueError: 지원하지 않는 파일 형식 / 빈 파일
        UnicodeDecodeError: 모든 인코딩 재시도 실패 시
        pd.errors.EmptyDataError: 파일은 존재하나 데이터 없을 때
        KeyError: 필수 컬럼 누락 시
    
    Examples:
        >>> # 자동 형식 감지
        >>> df = read_file('data/sales.csv', config=config, logger=logger)
        >>> 
        >>> # 명시적 형식 지정
        >>> data = read_file('data/backup.json', file_type='json', logger=logger)
        >>> 
        >>> # 로거 없이 조용히 실행
        >>> df = read_file('data/simple.xlsx')
    
    Warnings:
        - 인코딩 재시도는 순차적으로 진행 (느린 파일 처리)
        - 대용량 파일 (> 1GB)은 청크 단위 로드 권장
        - 바이너리 파일은 지원하지 않음 (CSV/JSON/Excel만)
        - 데이터 타입이 자동으로 추론됨 (수동 지정 불가)
    
    Notes:
        - v2.0부터 자동 인코딩 재시도 기능 추가
        - try-except-else-finally 구조로 안전한 처리
        - 성공 시 logger.info()로 행/열 수 출력
        - 더 상세한 설정은 config['file_reading'] 에서 조정 가능
    """
    # 파일 타입 자동 감지
    if file_type is None:
        _, ext = os.path.splitext(filepath)
        file_type = ext.lower().lstrip('.')
    
    file_type = file_type.lower()
    
    # 1. 파일 존재 여부 확인
    try:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
        
        if os.path.getsize(filepath) == 0:
            raise ValueError(f"Empty file (0 bytes): {filepath}")
        
        if logger:
            logger.info(f"[파일 읽기 시작] {filepath} (형식: {file_type})")
    
    except (FileNotFoundError, ValueError) as e:
        if logger:
            logger.error(f"[파일 존재 여부 확인 실패] {str(e)}")
        raise
    
    # 2. 형식별 읽기 처리
    try:
        if file_type == 'csv':
            data = _read_csv(filepath, config, logger)
        
        elif file_type == 'json':
            data = _read_json(filepath, config, logger)
        
        elif file_type in ['xlsx', 'xls', 'excel']:
            data = _read_excel(filepath, config, logger)
        
        else:
            raise ValueError(f"Unsupported file format: .{file_type}")
    
    except Exception as e:
        if logger:
            logger.error(f"[파일 읽기 실패] {filepath}: {str(e)}")
        raise
    
    else:
        # 성공 시 실행
        if logger:
            if isinstance(data, pd.DataFrame):
                logger.info(f"[파일 읽기 성공] {filepath} ({data.shape[0]} rows, {data.shape[1]} cols)")
            else:
                logger.info(f"[파일 읽기 성공] {filepath}")
        return data
    
    finally:
        # 정리 작업 (필요 시 추가)
        pass

# =====================================================================
# [6] CSV 파일 읽기 (인코딩 자동 재시도)
# =====================================================================

def _read_csv(filepath: str, 
              config: Optional[Dict[str, Any]] = None,
              logger: Optional[logging.Logger] = None) -> pd.DataFrame:
    """
    CSV 파일을 읽습니다. 인코딩 실패 시 자동 재시도합니다.
    
    try-except-else-finally 구조 적용:
    - try: 기본 인코딩으로 읽기 시도
    - except: 인코딩 실패 시 대체 인코딩 시도
    - else: 성공 시 결과 검증
    - finally: 정리 작업
    """
    csv_config = config.get('file_reading', {}).get('csv', {}) if config else {}
    
    primary_encoding = csv_config.get('default_encoding', 'utf-8')
    fallback_encodings = csv_config.get('fallback_encodings', ['cp949', 'euc-kr', 'latin-1'])
    encoding_retry = csv_config.get('encoding_retry', True)
    
    data = None
    encoding_attempts = [primary_encoding]
    
    if encoding_retry:
        encoding_attempts.extend(fallback_encodings)
    
    last_error = None
    
    # try-except-else-finally 구조
    for attempt, encoding in enumerate(encoding_attempts, 1):
        try:
            if logger:
                logger.debug(f"[CSV 읽기 시도] 인코딩: {encoding} (시도 {attempt}/{len(encoding_attempts)})")
            
            data = pd.read_csv(filepath, encoding=encoding)
        
        except UnicodeDecodeError as e:
            last_error = e
            if logger:
                logger.warning(f"[인코딩 실패] {encoding}: {str(e)}")
            continue
        
        except pd.errors.EmptyDataError as e:
            if logger:
                logger.error(f"[파싱 오류] 파일이 비어 있거나 파싱 실패: {str(e)}")
            raise
        
        except pd.errors.ParserError as e:
            if logger:
                logger.error(f"[구문 오류] CSV 형식이 손상됨: {str(e)}")
            raise
        
        except Exception as e:
            last_error = e
            if logger:
                logger.warning(f"[읽기 오류] {encoding}: {str(e)}")
            continue
        
        else:
            # 성공 시 검증
            if data is None or data.empty:
                if logger:
                    logger.warning(f"[데이터 경고] 파일은 읽어졌으나 데이터가 없음: {filepath}")
            
            if logger:
                logger.info(f"[CSV 읽기 성공] 인코딩: {encoding}")
            
            return data
        
        finally:
            pass
    
    # 모든 인코딩 실패 시
    if data is None:
        error_msg = f"Failed to read CSV with any encoding. Last error: {str(last_error)}"
        if logger:
            logger.error(f"[최종 실패] {error_msg}")
        raise ValueError(error_msg)
    
    return data

# =====================================================================
# [7] JSON 파일 읽기
# =====================================================================

def _read_json(filepath: str,
               config: Optional[Dict[str, Any]] = None,
               logger: Optional[logging.Logger] = None) -> Union[dict, list]:
    """
    JSON 파일을 읽습니다.
    
    try-except-else-finally 구조 적용
    """
    json_config = config.get('file_reading', {}).get('json', {}) if config else {}
    
    primary_encoding = json_config.get('encoding', 'utf-8')
    fallback_encodings = json_config.get('fallback_encodings', ['cp949', 'euc-kr'])
    encoding_retry = json_config.get('encoding_retry', True)
    
    encodings_to_try = [primary_encoding]
    if encoding_retry:
        encodings_to_try.extend(fallback_encodings)
    
    data = None
    last_error = None
    
    for attempt, encoding in enumerate(encodings_to_try, 1):
        try:
            if logger:
                logger.debug(f"[JSON 읽기 시도] 인코딩: {encoding} (시도 {attempt}/{len(encodings_to_try)})")
            
            with open(filepath, 'r', encoding=encoding) as f:
                data = json.load(f)
        
        except UnicodeDecodeError as e:
            last_error = e
            if logger:
                logger.warning(f"[인코딩 실패] {encoding}: {str(e)}")
            continue
        
        except json.JSONDecodeError as e:
            if logger:
                logger.error(f"[JSON 파싱 오류] {str(e)}")
            raise
        
        except Exception as e:
            last_error = e
            if logger:
                logger.warning(f"[읽기 오류] {encoding}: {str(e)}")
            continue
        
        else:
            if logger:
                logger.info(f"[JSON 읽기 성공] 인코딩: {encoding}")
            return data
        
        finally:
            pass
    
    # 모든 인코딩 실패 시
    if data is None:
        error_msg = f"Failed to read JSON with any encoding. Last error: {str(last_error)}"
        if logger:
            logger.error(f"[최종 실패] {error_msg}")
        raise ValueError(error_msg)
    
    return data

# =====================================================================
# [8] Excel 파일 읽기
# =====================================================================

def _read_excel(filepath: str,
                config: Optional[Dict[str, Any]] = None,
                logger: Optional[logging.Logger] = None) -> pd.DataFrame:
    """
    Excel 파일을 읽습니다.
    
    try-except-else-finally 구조 적용
    """
    excel_config = config.get('file_reading', {}).get('excel', {}) if config else {}
    
    sheet_name = excel_config.get('sheet_name', 0)
    engine = excel_config.get('engine', 'openpyxl')
    
    data = None
    last_error = None
    
    try:
        if logger:
            logger.debug(f"[Excel 읽기 시도] 엔진: {engine}, 시트: {sheet_name}")
        
        data = pd.read_excel(filepath, sheet_name=sheet_name, engine=engine)
    
    except Exception as e:
        last_error = e
        if logger:
            logger.warning(f"[읽기 오류] {engine}: {str(e)}")
        
        # 엔진 변경 재시도 (xlsx vs xls)
        try:
            alternate_engine = 'xlrd' if engine == 'openpyxl' else 'openpyxl'
            if logger:
                logger.debug(f"[Excel 재시도] 엔진: {alternate_engine}")
            
            data = pd.read_excel(filepath, sheet_name=sheet_name, engine=alternate_engine)
        
        except Exception as e2:
            last_error = e2
            if logger:
                logger.error(f"[최종 실패] {str(e2)}")
            raise ValueError(f"Failed to read Excel: {str(e2)}")
    
    else:
        if logger:
            logger.info(f"[Excel 읽기 성공] 엔진: {engine}")
        return data
    
    finally:
        pass

# =====================================================================
# [9] 파일 쓰기 함수
# =====================================================================

def write_file(data: Any,
               filepath: str,
               file_type: Optional[str] = None,
               logger: Optional[logging.Logger] = None) -> None:
    """
    데이터를 파일로 저장합니다 (CSV, JSON, Excel 지원).
    
    Args:
        data: 저장할 데이터 (DataFrame, dict, list 등)
        filepath: 저장 경로
        file_type: 파일 형식 (자동 감지 시 None)
        logger: 로거 객체
    """
    # 파일 타입 자동 감지
    if file_type is None:
        _, ext = os.path.splitext(filepath)
        file_type = ext.lower().lstrip('.')
    
    file_type = file_type.lower()
    
    # 디렉토리 생성
    ensure_dir_exists(filepath, logger)
    
    try:
        if file_type == 'csv':
            if isinstance(data, pd.DataFrame):
                data.to_csv(filepath, index=False, encoding='utf-8')
            else:
                raise ValueError("CSV 저장은 DataFrame만 지원됩니다")
        
        elif file_type == 'json':
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        
        elif file_type in ['xlsx', 'excel']:
            if isinstance(data, pd.DataFrame):
                data.to_excel(filepath, index=False, engine='openpyxl')
            else:
                raise ValueError("Excel 저장은 DataFrame만 지원됩니다")
        
        else:
            raise ValueError(f"Unsupported file format: .{file_type}")
    
    except Exception as e:
        if logger:
            logger.error(f"[파일 저장 실패] {filepath}: {str(e)}")
        raise
    
    else:
        if logger:
            logger.info(f"[파일 저장 성공] {filepath}")

# =====================================================================
# [10] 엔드 포인트: 전체 초기화 함수
# =====================================================================

def initialize_project(config_path: str = "config.yaml") -> tuple:
    """
    프로젝트의 모든 초기화를 한 번에 수행합니다.
    
    이 함수는 프로젝트 시작 시 반드시 호출해야 하는 "메인 엔드포인트"입니다.
    설정 로드, 경로 설정, 로거 구성을 순차적으로 수행하고 결과를 반환합니다.
    
    초기화 순서:
    1. config.yaml 로드 (모든 설정 정보)
    2. ProjectPaths 객체 생성 (경로 중앙화 관리)
    3. 로거 설정 (터미널 + 파일 로깅)
    4. 초기화 메시지 출력 및 반환
    
    Args:
        config_path (str): config.yaml 파일 경로
                          기본값: "config.yaml" (스크립트 디렉토리 기준)
    
    Returns:
        tuple: (config, paths, logger)
               - config: Dict[str, Any] - 로드된 설정 딕셔너리
               - paths: ProjectPaths - 경로 관리 객체
               - logger: logging.Logger - 설정된 로거
    
    Raises:
        FileNotFoundError: config.yaml이 없을 때
        yaml.YAMLError: YAML 문법 오류
        OSError: 로그 디렉토리 생성 실패
    
    Examples:
        >>> from util import initialize_project
        >>> config, paths, logger = initialize_project()
        # 로그 출력:
        # 19:36:39 [INFO] ======================================================================
        # 19:36:39 [INFO] 프로젝트 초기화 완료
        # 19:36:39 [INFO] Base Directory: /Users/seongminan/workspace/skala-data-project
        # 19:36:39 [INFO] ======================================================================
        >>> 
        >>> # 이제 설정과 경로를 어디서나 사용 가능
        >>> logger.info(f"데이터 경로: {paths.raw_sales_100k}")
        >>> df = read_file(paths.clean_sales, config=config, logger=logger)
    
    Warnings:
        - 프로젝트 시작 시 반드시 먼저 호출해야 함
        - config.yaml이 없으면 전체 파이프라인 실패
        - 이 함수는 1회만 호출할 것 권장 (중복 호출 시 리소스 낭비)
    
    Notes:
        - v2.0부터 모든 설정을 이 함수로 통합
        - 반환된 객체들을 전역 변수로 사용하면 편함:
          config, paths, logger = initialize_project()
        - 이 함수 호출 후 logger를 즉시 사용 가능
        - 실행 시간: 매우 빠름 (< 100ms)
    """
    config = load_config(config_path)
    paths = ProjectPaths(config)
    logger = setup_logger(config)
    
    logger.info("=" * 70)
    logger.info("프로젝트 초기화 완료")
    logger.info(f"Base Directory: {paths.base_dir}")
    logger.info("=" * 70)
    
    return config, paths, logger
