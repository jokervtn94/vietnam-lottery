import logging
from copy import copy
from datetime import date
from typing import Dict, List

import numpy as np
import pandas as pd
from pydantic import BaseModel

from .lottery_base import LotteryMultiProvinceBase
from .data_quality import validate_prize_structure
from .models.lottery_mt import ResultMT, ResultMTList

logger = logging.getLogger('vietnam-lottery')





class ResultMTList(BaseModel):
    """Danh sách kết quả xổ số miền Trung"""
    root: List[ResultMT]


class LotteryMT(LotteryMultiProvinceBase):
    def __init__(self) -> None:
        super().__init__('xsmt', ResultMT, ResultMTList)

    def _create_result_model(self, selected_date: date, province: str, prizes: Dict[str, List[int]]) -> ResultMT:
        validate_prize_structure(prizes)
        return ResultMT(
            date=selected_date,
            province=province,
            special=prizes.get('ĐB', [0])[0],
            prize1=prizes.get('1', [0])[0],
            prize2=prizes.get('2', [0])[0],
            prize3_1=prizes.get('3', [0, 0])[0],
            prize3_2=prizes.get('3', [0, 0])[1] if len(prizes.get('3', [])) > 1 else 0,
            prize4_1=prizes.get('4', [0]*7)[0],
            prize4_2=prizes.get('4', [0]*7)[1] if len(prizes.get('4', [])) > 1 else 0,
            prize4_3=prizes.get('4', [0]*7)[2] if len(prizes.get('4', [])) > 2 else 0,
            prize4_4=prizes.get('4', [0]*7)[3] if len(prizes.get('4', [])) > 3 else 0,
            prize4_5=prizes.get('4', [0]*7)[4] if len(prizes.get('4', [])) > 4 else 0,
            prize4_6=prizes.get('4', [0]*7)[5] if len(prizes.get('4', [])) > 5 else 0,
            prize4_7=prizes.get('4', [0]*7)[6] if len(prizes.get('4', [])) > 6 else 0,
            prize5=prizes.get('5', [0])[0],
            prize6_1=prizes.get('6', [0, 0, 0])[0],
            prize6_2=prizes.get('6', [0, 0, 0])[1] if len(prizes.get('6', [])) > 1 else 0,
            prize6_3=prizes.get('6', [0, 0, 0])[2] if len(prizes.get('6', [])) > 2 else 0,
            prize7=prizes.get('7', [0])[0],
            prize8=prizes.get('8', [0])[0]
        )

    def generate_dataframes(self) -> None:
        if not self._data:
            logger.info("No data to generate dataframes")
            return

        all_results = []
        for results_in_date in self._data.values():
            all_results.extend([d.model_dump() for d in results_in_date])

        if not all_results:
            logger.info("No results to process")
            return

        self._raw_data = pd.DataFrame(all_results)
        self._raw_data['date'] = pd.to_datetime(self._raw_data['date'])
        numeric_cols = self._raw_data.columns.difference(['date', 'province'])
        self._raw_data[numeric_cols] = self._raw_data[numeric_cols].astype('int64')

        self._2_digits_data = copy(self._raw_data)
        self._2_digits_data[numeric_cols] = self._2_digits_data[numeric_cols].apply(lambda x: x % 100)

        # Generate sparse dataframe
        sparse_records = []
        for record in all_results:
            sparse_record = {'date': record['date'], 'province': record['province'], **{str(i): 0 for i in range(100)}}
            all_numbers = [value for key, value in record.items() if key not in ['date', 'province']]
            for number in all_numbers:
                last_two_digits = number % 100
                sparse_record[str(last_two_digits)] += 1
            sparse_records.append(sparse_record)
            
        self._sparse_data = pd.DataFrame(sparse_records)
        self._sparse_data['date'] = pd.to_datetime(self._sparse_data['date'])
        
        # Set column names for sparse data
        column_names = ['date', 'province'] + [str(i) for i in range(100)]
        self._sparse_data.columns = column_names

        if not self._raw_data.empty:
            begin_date = self._raw_data['date'].min()
            self._begin_date = begin_date.to_pydatetime().date()
            last_date = self._raw_data['date'].max()
            self._last_date = last_date.to_pydatetime().date()
            logger.info(f"Generated dataframes with data from {self._begin_date} to {self._last_date}")