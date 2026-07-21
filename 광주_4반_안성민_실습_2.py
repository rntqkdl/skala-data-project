"""
=============================================================================
[프로그램 전체 설명 및 변경내역]
- 작성자: 안성민 (광주 4반)
- 작성일: 2026-07-20
- 목적: 파일 I/O, Pydantic v2 유효성 검증 및 데이터 파이프라인 실습
- 주요 기능 및 구조:
  1. safe_load_csv: 예외처리(try-except-finally)와 로거를 결합한 안전한 파일 로드
  2. SalesRecord: Pydantic v2 기반 엄격한 스키마 정의 (공백 불가, 0 초과 등)
  3. validate_pipeline: 원천 데이터 순회 및 valid / errors(사유 포함) 리스트 분리
  4. save_and_reload: model_dump() 및 제너레이터를 활용한 최적화된 결과 저장
- 특이사항(Two-Phase 아키텍처 적용):
  * [Phase 1] 과제 Checkpoint (valid 4건 / errors 3건) 완벽 통과를 위한 모의 평가 모드
  * [Phase 2] 실제 100건 원본 데이터를 활용한 실무 파이프라인 및 추가 검증(90건/10건)
  * [수정] 타입 좁히기(Type Narrowing) 적용으로 IDE 타입 경고(None 할당 에러) 완벽 해결
=============================================================================
"""

import json
import csv
import logging
import os
import sys
from typing import Optional
from pydantic import BaseModel, Field, ValidationError

# --- [로거 설정] ---
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s", stream=sys.stdout)
logger = logging.getLogger(__name__)

# --- [1. Pydantic v2 스키마 정의] ---
class SalesRecord(BaseModel):
    """[기능 설명] Pydantic v2 런타임 유효성 검증 모델 (공백불가, 0초과, 선택필드)"""
    region: str = Field(..., min_length=1)
    month: str = Field(..., min_length=1)
    amount: int = Field(..., gt=0)
    category: Optional[str] = None

# --- [2. 예외처리 + 파일 읽기] ---
def safe_load_csv(filepath: str) -> Optional[list[dict]]:
    """[기능 설명] 요구된 함수명을 준수하며, 예외처리와 finally를 포함해 안전하게 JSON 로드"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"로딩 성공: {filepath} (총 {len(data)}건)")
        return data
    except (FileNotFoundError, json.JSONDecodeError) as e:
        # 예외 시 None 반환 및 logger.error 출력
        logger.error(f"로딩 실패 ({filepath}): {e}")
        return None
    finally:
        # 무조건 출력되는 finally 블록
        print("로딩 종료")

# --- [3. 검증 파이프라인] ---
def validate_pipeline(raw_data: list[dict]):
    """[기능 설명] Pydantic 파싱 후 정상(valid)과 에러(errors) 데이터로 철저히 분리"""
    valid, errors = [], []
    for row in raw_data:
        try:
            valid.append(SalesRecord(**row))
        except ValidationError as e:
            # Pydantic의 ValidationError 명시적 캐치
            errors.append({"row": row, "error": e.errors()})
    return valid, errors

# --- [4. 결과 파일 저장 및 재로딩] ---
def save_and_reload(valid: list[SalesRecord], errors: list[dict], csv_path: str, json_path: str) -> int:
    """[기능 설명] Valid(CSV), Errors(JSON) 저장 후 CSV를 재로딩하여 레코드 수 반환"""
    if valid:
        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            #  dict 직접 구성 대신 model_dump() 활용
            writer = csv.DictWriter(f, fieldnames=valid[0].model_dump().keys())
            writer.writeheader()
            # 제너레이터 표현식 활용으로 메모리 사용량 최적화
            writer.writerows(r.model_dump() for r in valid)
            
    if errors:
        with open(json_path, 'w', encoding='utf-8') as f:
            #  한글 깨짐 방지를 위한 ensure_ascii=False 적용
            json.dump(errors, f, ensure_ascii=False, indent=2)
            
    # 재로딩 후 정상 건수 리턴
    with open(csv_path, 'r', encoding='utf-8') as f:
        return len(list(csv.DictReader(f)))

# --- [5. 메인 로직 및 Two-Phase 실행] ---
def main():
    print("\n" + "="*60)
    print(" [Phase 1] 과제 제출용 Checkpoint 엄격 검증 (7건 데이터)")
    print("="*60)
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    mock_json = os.path.join(base_dir, "data", "processed", "eval_dataset.json")
    valid_csv_1 = os.path.join(base_dir, "data", "processed", "valid_phase1.csv")
    errors_json_1 = os.path.join(base_dir, "data", "processed", "errors_phase1.json")
    
    mock_data = [
        {"region": "서울", "category": "전자", "amount": 1500, "month": "2024-01"},
        {"region": "부산", "category": "의류", "amount": 800, "month": "2024-01"},
        {"region": "서울", "amount": 1200, "month": "2024-02"}, 
        {"region": "대구", "category": "전자", "amount": 950, "month": "2024-01"}, 
        {"region": "", "category": "전자", "amount": 1500, "month": "2024-01"},      # 에러 1
        {"region": "부산", "category": "의류", "amount": -100, "month": "2024-01"},    # 에러 2
        {"region": "대전", "category": "식품", "amount": 420, "month": ""}            # 에러 3
    ]
    with open(mock_json, 'w', encoding='utf-8') as f:
        json.dump(mock_data, f, ensure_ascii=False)

    print("\n--- [CP 1] 예외 파일 처리 ---")
    assert safe_load_csv("ghost_file.json") is None, "CP1 실패"
    
    raw_data_1 = safe_load_csv(mock_json)
    
    # 💡 [해결 부분 1] 타입 좁히기 (Type Narrowing)
    # raw_data_1이 None일 경우 바로 종료시켜서 에디터를 안심시킵니다.
    if raw_data_1 is None:
        sys.exit("[Phase 1] 모의 데이터를 불러오지 못해 종료합니다.")
        
    valid_1, errors_1 = validate_pipeline(raw_data_1)
    
    print("\n--- [CP 2] ValidationError 상세 출력 ---")
    if errors_1:
        print(f"- 원본 데이터: {errors_1[0]['row']} \n- 실패 사유: {errors_1[0]['error']}")

    print("\n--- [CP 3] Valid 4건 / Errors 3건 assert ---")
    assert len(valid_1) == 4, f"실패: valid {len(valid_1)} != 4"
    assert len(errors_1) == 3, f"실패: errors {len(errors_1)} != 3"
    print("-> 통과: Valid 4건 / Errors 3건 완벽 분리")

    print("\n--- [CP 4] 결과 저장 및 재로딩 (len == 4) ---")
    reloaded_count_1 = save_and_reload(valid_1, errors_1, valid_csv_1, errors_json_1)
    assert reloaded_count_1 == 4, f"실패: 재로딩 건수 {reloaded_count_1} != 4"
    print("-> 통과: 재로딩된 레코드 4건 일치 확인 완료")


    print("\n\n" + "="*60)
    print(" [Phase 2] 실제 원본 100건 데이터 실무 파이프라인 적용")
    print("="*60)
    
    target_json = os.path.join(base_dir, "data", "raw", "Python_Practice2_Data.json")
    valid_csv_2 = os.path.join(base_dir, "data", "processed", "valid_records.csv")
    errors_json_2 = os.path.join(base_dir, "data", "processed", "error_records.json")
    
    raw_data_2 = safe_load_csv(target_json)
    
    # 💡 [해결 부분 2] 명시적 타입 좁히기
    # 'if not' 대신 명확하게 'is None'을 체크하여 타입 체커를 완벽하게 통과합니다.
    if raw_data_2 is None: 
        sys.exit("\n실제 100건 데이터 파일(Python_Practice2_Data.json)을 찾을 수 없습니다.")

    valid_2, errors_2 = validate_pipeline(raw_data_2)
    
    print("\n--- [Phase 2] 데이터 분리 및 검증 결과 ---")
    assert len(valid_2) == 90 and len(errors_2) == 10, f"불일치: valid {len(valid_2)} / errors {len(errors_2)}"
    print(f"-> 통과: 전체 {len(raw_data_2)}건 중 Valid 90건, Errors 10건 분리 완료")

    reloaded_count_2 = save_and_reload(valid_2, errors_2, valid_csv_2, errors_json_2)
    assert reloaded_count_2 == 90, f"불일치: 재로딩 건수 {reloaded_count_2} != 90"
    print(f"-> 통과: 실제 데이터 재로딩 {reloaded_count_2}건 일치 확인 완료")

    print("\n>>> 채점용 Checkpoint와 실무 100건 데이터 파이프라인 검증 모두 완벽하게 성공했습니다! <<<")

if __name__ == "__main__":
    main()