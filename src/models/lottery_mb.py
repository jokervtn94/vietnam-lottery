from datetime import date
from typing import List
from pydantic import BaseModel

class ResultMB(BaseModel):
    """Kết quả xổ số miền Bắc"""
    date: date
    special: int
    prize1: int
    prize2_1: int
    prize2_2: int
    prize3_1: int
    prize3_2: int
    prize3_3: int
    prize3_4: int
    prize3_5: int
    prize3_6: int
    prize4_1: int
    prize4_2: int
    prize4_3: int
    prize4_4: int
    prize5_1: int
    prize5_2: int
    prize5_3: int
    prize5_4: int
    prize5_5: int
    prize5_6: int
    prize6_1: int
    prize6_2: int
    prize6_3: int
    prize7_1: int
    prize7_2: int
    prize7_3: int
    prize7_4: int


class ResultMBList(BaseModel):
    """Danh sách kết quả xổ số miền Bắc"""
    root: List[ResultMB]
