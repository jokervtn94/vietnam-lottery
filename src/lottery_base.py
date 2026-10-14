import json
import logging
from abc import ABC, abstractmethod
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Type, TypeVar

import pandas as pd
from bs4 import BeautifulSoup # Added this import
from cloudscraper import CloudScraper
from pydantic import BaseModel
from .data_quality import validate_prize_structure

logger = logging.getLogger('vietnam-lottery')

# Define a type variable for Pydantic models
T = TypeVar('T', bound=BaseModel)

class LotteryBase(ABC):
    def __init__(self, data_prefix: str, ResultModel: Type[T], ResultListModel: Type[BaseModel]) -> None:
        self._http = CloudScraper()
        self._data: Dict[date, Any] = {} # Can be ResultModel or List[ResultModel]
        self._raw_data: pd.DataFrame = pd.DataFrame()
        self._2_digits_data: pd.DataFrame = pd.DataFrame()
        self._sparse_data: pd.DataFrame = pd.DataFrame()
        self._begin_date = date.today()
        self._last_date = date.today()
        self._data_prefix = data_prefix
        self._ResultModel = ResultModel
        self._ResultListModel = ResultListModel
        self._init_data_files()

    def _init_data_files(self) -> None:
        """Initialize required data files if they don't exist"""
        data_dir = Path('data')
        data_dir.mkdir(exist_ok=True)
        
        files = [
            (f'{self._data_prefix}.json', '[]'),
            (f'{self._data_prefix}.csv', ''),
            (f'{self._data_prefix}-2-digits.csv', ''),
            (f'{self._data_prefix}-sparse.csv', '')
        ]
        
        for filename, content in files:
            file_path = data_dir / filename
            if not file_path.exists():
                logger.info(f"Creating {filename}")
                file_path.write_text(content, encoding='utf-8')

    def load(self) -> None:
        try:
            file_path = Path('data') / f'{self._data_prefix}.json'
            if not file_path.exists():
                logger.warning(f"Data file {file_path} does not exist. Starting with empty data.")
                return

            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            data = [self._ResultModel.model_validate(item) for item in json_data]

            # Handle both single and list of results per date
            for d in data:
                if isinstance(d, list): # For multi-province results
                    if d[0].date not in self._data:
                        self._data[d[0].date] = []
                    self._data[d[0].date].extend(d)
                else: # For single result per date
                    self._data[d.date] = d
            
            self.generate_dataframes()
            logger.info(f"Successfully loaded existing data from {file_path}")
        except Exception as e:
            logger.warning(f"Could not load existing data from {file_path}: {e}")

    def dump(self) -> None:
        if not self._data:
            logger.info("No data to save")
            return

        # Convert data to list and sort by date
        # Handle both single and list of results per date
        data_list = []
        for val in self._data.values():
            if isinstance(val, list):
                data_list.extend(val)
            else:
                data_list.append(val)
        
        data_list.sort(key=lambda x: x.date)
        
        # Save JSON
        json_file_path = Path('data') / f'{self._data_prefix}.json'
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump([item.model_dump(mode='json') for item in data_list], f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(data_list)} results to {json_file_path}")
        
        # Save DataFrames
        self._dump_dataframe(self._raw_data, self._data_prefix)
        self._dump_dataframe(self._2_digits_data, f'{self._data_prefix}-2-digits')
        self._dump_dataframe(self._sparse_data, f'{self._data_prefix}-sparse')

    def _dump_dataframe(self, df: pd.DataFrame, file_name_prefix: str) -> None:
        if not df.empty:
            csv_path = Path('data') / f'{file_name_prefix}.csv'
            parquet_path = Path('data') / f'{file_name_prefix}.parquet'
            
            df.to_csv(csv_path, index=False)
            df.to_parquet(parquet_path, index=False)
            logger.info(f"Saved {len(df)} records to {csv_path} and {parquet_path}")

    @abstractmethod
    def fetch(self, selected_date: date) -> Any:
        """Abstract method to fetch data for a specific date."""
        pass

    @abstractmethod
    def generate_dataframes(self) -> None:
        """Abstract method to generate pandas DataFrames from fetched data."""
        pass

    def generate_and_dump_sparse_json(self) -> None:
        """Generates a sparse representation of 2-digit number frequencies and saves it to a JSON file."""
        if not self._data:
            logger.info("No data available to generate sparse JSON.")
            return

        sparse_records = []
        
        # Sort dates to ensure chronological order in the output
        sorted_dates = sorted(self._data.keys())

        for selected_date in sorted_dates:
            results = self._data[selected_date]
            
            # Initialize a frequency count for all numbers from 00 to 99
            record = {"date": selected_date.isoformat(), **{str(i): 0 for i in range(100)}}
            
            all_numbers = []
            
            # Handle both single result (MB) and list of results (MN/MT)
            if not isinstance(results, list):
                results = [results]

            for result in results:
                # Iterate through the Pydantic model fields to get all prize numbers
                for field_name, field_value in result:
                    if isinstance(field_value, int) and ('prize' in field_name or 'special' in field_name):
                        all_numbers.append(field_value)

            # Calculate frequency of last two digits
            for number in all_numbers:
                last_two_digits = number % 100
                record[str(last_two_digits)] += 1
            
            sparse_records.append(record)

        # Save to JSON file
        file_path = Path('data') / f'{self._data_prefix}-sparse.json'
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(sparse_records, f, indent=2, ensure_ascii=False)
            logger.info(f"Successfully saved sparse data to {file_path}")
        except Exception as e:
            logger.error(f"Error saving sparse JSON to {file_path}: {e}")

    def get_last_date(self) -> date:
        if not self._data:
            return self._last_date # Returns today's date from init if no data
        
        # Find the maximum date from all entries
        max_date = self._begin_date # Initialize with a default or earliest possible date
        for key, value in self._data.items():
            if isinstance(value, list) and value: # For multi-province results
                max_date = max(max_date, max(d.date for d in value))
            elif isinstance(value, BaseModel): # For single result per date
                max_date = max(max_date, value.date)
            else: # If key is already a date
                max_date = max(max_date, key)
        
        self._last_date = max_date
        return self._last_date

    def get_raw_data(self) -> pd.DataFrame:
        return self._raw_data

    def get_2_digits_data(self) -> pd.DataFrame:
        return self._2_digits_data

    def get_sparse_data(self) -> pd.DataFrame:
        return self._sparse_data

class LotteryMultiProvinceBase(LotteryBase):
    def __init__(self, data_prefix: str, ResultModel: Type[T], ResultListModel: Type[BaseModel]) -> None:
        super().__init__(data_prefix, ResultModel, ResultListModel)
        # Override _data to specifically store list of results per date
        self._data: Dict[date, List[ResultModel]] = {}

    def load(self) -> None:
        try:
            file_path = Path('data') / f'{self._data_prefix}.json'
            if not file_path.exists():
                logger.warning(f"Data file {file_path} does not exist. Starting with empty data.")
                return

            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)

            data = [self._ResultModel.model_validate(item) for item in json_data]

            for d in data:
                if d.date not in self._data:
                    self._data[d.date] = []
                self._data[d.date].append(d)
            
            self.generate_dataframes()
            logger.info(f"Successfully loaded existing data from {file_path}")
        except Exception as e:
            logger.warning(f"Could not load existing data from {file_path}: {e}")

    def dump(self) -> None:
        if not self._data:
            logger.info("No data to save")
            return

        root = [item for sublist in self._data.values() for item in sublist]
        root.sort(key=lambda x: x.date) # Ensure sorted for consistent output

        json_file_path = Path('data') / f'{self._data_prefix}.json'
        with open(json_file_path, 'w', encoding='utf-8') as f:
            # Use model_dump() for each item and then json.dump for the list
            json_data = [item.model_dump(mode='json') for item in root]
            # import json # Import json here to avoid circular dependency if pydantic uses it
            json.dump(json_data, f, indent=2, ensure_ascii=False) # default=str for date objects
        logger.info(f"Saved {len(root)} results to {json_file_path}")

        self._dump_dataframe(self._raw_data, self._data_prefix)
        self._dump_dataframe(self._2_digits_data, f'{self._data_prefix}-2-digits')
        self._dump_dataframe(self._sparse_data, f'{self._data_prefix}-sparse')

    def fetch(self, selected_date: date) -> List[T]:
        url = f'https://xoso.com.vn/{self._data_prefix}-{selected_date:%d-%m-%Y}.html'
        logger.info(f"Fetching URL: {url}")
        
        try:
            resp = self._http.get(url)
            logger.info(f"Response status: {resp.status_code}")
            
            if resp.status_code != 200:
                logger.error(f"Failed to fetch URL {url}, status code: {resp.status_code}")
                return []

            soup = BeautifulSoup(resp.text, 'lxml')
            table = soup.find('table', class_='table-result')
            
            if not table:
                logger.error(f"Could not find result table for date {selected_date} at {url}")
                return []
                
            header = table.find('tr')
            if not header:
                logger.error("No header row found in result table.")
                return []
            
            provinces = [th.text.strip() for th in header.find_all('th')[1:]]
            if not provinces:
                logger.warning("No provinces found in header.")
                return []
            
            logger.info(f"Found provinces: {', '.join(provinces)}")

            province_results: Dict[str, Dict[str, List[int]]] = {province: {} for province in provinces}
            
            rows = table.find_all('tr')[1:]
            for row in rows:
                cells = row.find_all(['th', 'td'])
                if len(cells) < 2:
                    continue
                
                prize_type = cells[0].text.strip()
                
                for i, (province, cell) in enumerate(zip(provinces, cells[1:])):
                    numbers_str = cell.get_text(' ', strip=True).split()
                    # Check for '...' or empty strings before conversion
                    if not numbers_str or any('...' in n for n in numbers_str):
                        logger.warning(f"Skipping {province} for {selected_date} due to incomplete data: {numbers_str}")
                        return [] # Return empty list to signal incomplete data for the day
                    try:
                        numbers = [int(n) for n in numbers_str]
                        province_results[province][prize_type] = numbers
                    except ValueError as e:
                        logger.error(f"Error converting numbers for {province}, prize {prize_type}: {e}. Numbers: {numbers_str}")
                        return []  # malformed input must never become a fabricated 00

            for province in provinces:
                validate_prize_structure(province_results[province])

            results: List[T] = []
            for province in provinces:
                try:
                    prizes = province_results[province]
                    # This part needs to be implemented by the concrete class
                    # as prize mapping is specific to each lottery type (MN/MT)
                    result_instance = self._create_result_model(selected_date, province, prizes)
                    results.append(result_instance)
                    logger.info(f"Successfully processed data for {province} on {selected_date}")
                except Exception as e:
                    logger.error(f"Error creating result for {province} on {selected_date}: {e}")

            if results:
                self._data[selected_date] = results
                logger.info(f"Successfully fetched {len(results)} results for date {selected_date}")
                return results
            else:
                logger.warning(f"No valid results found for date {selected_date}")
                return []
            
        except Exception as e:
            logger.error(f"Error fetching data for {self._data_prefix} on {selected_date}: {e}")
            return []

    @abstractmethod
    def _create_result_model(self, selected_date: date, province: str, prizes: Dict[str, List[int]]) -> T:
        """Abstract method to create a specific ResultModel instance."""
        pass
