from datetime import date
from typing import List
from pydantic import BaseModel

class ResultMT(BaseModel):
    """Kết quả xổ số miền Trung"""
    date: date
    province: str
    special: int
    prize1: int
    prize2: int
    prize3_1: int
    prize3_2: int
    prize4_1: int
    prize4_2: int
    prize4_3: int
    prize4_4: int
    prize4_5: int
    prize4_6: int
    prize4_7: int
    prize5: int
    prize6_1: int
    prize6_2: int
    prize6_3: int
    prize7: int
    prize8: int


class ResultMTList(BaseModel):
    """Danh sách kết quả xổ số miền Trung"""
    root: List[ResultMT]
