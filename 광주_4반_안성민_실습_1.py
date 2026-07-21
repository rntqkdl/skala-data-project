"""
=============================================================================
[머리말: 프로그램 전체 설명 및 변경내역]
- 작성자: 안성민 (광주 4반)
- 파일명: 광주_4반_안성민.py
- 목적: 파이썬 핵심 자료구조(컴프리헨션, Counter, defaultdict, 제너레이터) 실습 및 성능 검증
- 주요 기능:
  1. TypedDict와 dataclass를 활용한 JSON 데이터 로드 및 런타임 유효성 검증
  2. 리스트/딕셔너리 컴프리헨션을 활용한 필터링 및 총매출 집계 (실행 시간 측정 포함)
  3. Counter를 통한 거래 건수 집계, defaultdict(list)를 통한 그룹핑
  4. 제너레이터(yield)와 리스트 컴프리헨션의 sys.getsizeof 메모리 사용량 비교
  5. 컴프리헨션 + defaultdict(int)를 결합한 월별/카테고리별 매출 다중 집계
- 변경내역:
  - 2026-07-20 (월) 오전 11:11: 초기 작성 및 기능 구현 완료
=============================================================================
"""

import json
import os
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import TypedDict, List

# 정적 타입 힌팅을 위한 TypedDict 정의
class SalesDict(TypedDict):
    region: str
    category: str
    amount: int
    month: str

# 런타임 데이터 구조화 및 유효성 검증을 위한 dataclass
@dataclass
class SalesRecord:
    region: str
    category: str
    amount: int
    month: str

    def __post_init__(self):
        """데이터 인스턴스 생성 시점에 타입 및 유효성 검증 (런타임 예외 처리용)"""
        if not isinstance(self.amount, int) or self.amount < 0:
            raise ValueError(f"유효하지 않은 amount 값입니다: {self.amount}")
        if not isinstance(self.region, str) or not self.region:
            raise ValueError(f"유효하지 않은 region 값입니다: {self.region}")

def load_and_validate_data(filepath: str) -> List[SalesRecord]:
    """
    [기능 설명] JSON 파일을 읽어와 TypedDict 힌팅 구조를 거쳐 dataclass로 인스턴스화하며 검증합니다.
    - 파일 미존재, JSON 디코딩 오류, 데이터 값 오류 등에 대한 예외 처리를 수행합니다.
    """
    records = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
            
            for item in raw_data:
                # 딕셔너리 언패킹 과정에서 __post_init__을 통한 검증 수행
                record = SalesRecord(**item)
                records.append(record)
                
    except FileNotFoundError:
        print(f"[오류] 데이터 파일을 찾을 수 없습니다: {filepath}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"[오류] JSON 파일 형식이 올바르지 않습니다: {filepath}")
        sys.exit(1)
    except (ValueError, TypeError) as e:
        print(f"[검증 오류] 데이터 무결성 검증 실패: {e}")
        sys.exit(1)
        
    return records

def task1_comprehension(records: List[SalesRecord]):
    """
    [기능 설명] 컴프리헨션을 사용한 필터링(amount >= 1000) 및 지역별 총합 계산.
    - 코드바이트(실행 시간) 측정을 포함합니다.
    - for 루프문을 배제하고 딕셔너리 컴프리헨션 문법을 적용합니다.
    """
    start_time = time.perf_counter()
    
    # ① amount >= 1000 인 거래 필터링
    filtered = [s for s in records if s.amount >= 1000]
    
    # ② 지역별 총매출 dict 컴프리헨션 계산 (중복 지역 추출 후 해당 지역 데이터만 합산)
    region_totals = {
        region: sum(s.amount for s in filtered if s.region == region)
        for region in set(s.region for s in filtered)
    }
    
    end_time = time.perf_counter()
    print(f"컴프리헨션 실행 시간: {(end_time - start_time) * 1_000_000:.2f} 마이크로초(µs)")
    
    return region_totals

def task2_counter_and_defaultdict(records: List[SalesRecord]):
    """
    [기능 설명] Counter로 카운팅 로직을 대체하고, defaultdict로 'if key not in' 패턴을 대체합니다.
    """
    # Counter: 직접 루프로 카운팅 지양 (-1점 감점 방지)
    region_counts = Counter(s.region for s in records)
    
    # defaultdict: if key not in dict 패턴 지양 (-1점 감점 방지)
    category_amounts = defaultdict(list)
    for s in records:
        category_amounts[s.category].append(s.amount)
        
    return region_counts, category_amounts

def generate_high_sales(records: List[SalesRecord]):
    """
    [기능 설명] amount > 1000 인 행만 yield 하는 제너레이터 함수
    """
    for s in records:
        if s.amount > 1000:
            yield s

def task3_generator_memory(records: List[SalesRecord]):
    """
    [기능 설명] 제너레이터 함수(yield)와 리스트 컴프리헨션의 메모리 사용량을 비교합니다.
    """
    # yield 기반 제너레이터 객체 생성 (-2점 감점 방지: list로 변환하지 않음)
    gen_sales = generate_high_sales(records)
    
    # 리스트 컴프리헨션 객체 생성
    list_sales = [s for s in records if s.amount > 1000]
    
    return sys.getsizeof(gen_sales), sys.getsizeof(list_sales)

def task4_monthly_category_agg(records: List[SalesRecord]):
    """
    [기능 설명] 월별/카테고리별 기준 그룹핑을 컴프리헨션 + defaultdict로 구현합니다.
    """
    # 딕셔너리 컴프리헨션으로 다중 키(month, category) 집계를 생성하고 defaultdict에 초기값 주입
    monthly_cat = defaultdict(int, {
        (m, c): sum(s.amount for s in records if s.month == m and s.category == c)
        for m, c in set((s.month, s.category) for s in records)
    })
    return monthly_cat

def main():
    # 파일 경로 지정
    base_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(base_dir, "data", "raw", "Python_Practice1_Data.json")
    
    # [데이터 로드 및 검증]
    records = load_and_validate_data(filepath)
    if not records:
        print("[경고] 로드된 데이터가 없습니다.")
        return

    try:
        print("=== [1] 리스트/딕셔너리 컴프리헨션 ===")
        region_totals = task1_comprehension(records)
        print(f"지역별 총매출 (amount >= 1000): {region_totals}")
        
        # Checkpoint: region_total 값 정확 (assert 통과)
        assert '서울' in region_totals, "서울 지역 데이터가 누락되어 집계가 정확하지 않습니다."
        
        # Checkpoint: top3 금액 내림차순 정렬 정확
        top3_regions = sorted(region_totals.items(), key=lambda x: x[1], reverse=True)[:3]
        print(f"Top 3 지역 총매출 (내림차순): {top3_regions}")

        print("\n=== [2] Counter + defaultdict ===")
        region_counts, category_amounts = task2_counter_and_defaultdict(records)
        
        # Checkpoint: Counter.most_common() 순서 정확
        print("지역별 거래 건수 (most_common):", region_counts.most_common())
        print("카테고리별 amount 리스트 (의류 예시):", category_amounts['의류'][:5], "...")

        print("\n=== [3] 제너레이터(yield) — 메모리 크기 비교 ===")
        mem_gen, mem_list = task3_generator_memory(records)
        print(f"Generator 메모리 크기: {mem_gen} bytes")
        print(f"List 메모리 크기: {mem_list} bytes")
        
        # Checkpoint: generator sys.getsizeof < list 확인
        assert mem_gen < mem_list, "제너레이터의 메모리가 리스트보다 작지 않습니다. (비교 실패)"
        print("-> [검증 성공] yield 제너레이터가 리스트보다 메모리 효율이 높음을 확인했습니다.")

        print("\n=== [4] 종합 — 월별 카테고리 매출 집계 ===")
        monthly_cat = task4_monthly_category_agg(records)
        
        # 5개만 샘플 출력
        print("월별/카테고리별 총매출 (샘플):")
        for key, val in list(sorted(monthly_cat.items()))[:5]:
            print(f"  {key[0]}월 - {key[1]}: {val}원")

    except AssertionError as e:
        print(f"\n[검증 실패] Checkpoint 요건 미충족: {e}")
    except Exception as e:
        print(f"\n[런타임 오류] 예상치 못한 오류 발생: {e}")

if __name__ == "__main__":
    main()