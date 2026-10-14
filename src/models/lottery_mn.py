from datetime import date
from typing import List
from pydantic import BaseModel

class ResultMN(BaseModel):
    """Kết quả xổ số miền Nam"""
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


class ResultMNList(BaseModel):
    """Danh sách kết quả xổ số miền Nam"""
    root: List[ResultMN]
