import logging
import http.client
import sys
from typing import Optional
import pandas as pd
import requests
import unittest
import json
from time import sleep
from datetime import datetime as dt


# --- Конфигурация логирования ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("moex_iss")


class MoexISS():

    # Строгий базовый URL для API Мосбиржи
    _BASE_URL = "https://iss.moex.com/iss"

    @staticmethod
    def bond_cf(ticker: str, tables=None
                ) -> dict[str, pd.DataFrame]:

        if not tables:
            tables = {'coupons': pd.DataFrame(),
                      'amortizations': pd.DataFrame(),
                      'offers': pd.DataFrame()}

        url = f"{MoexISS._BASE_URL}/securities/{ticker}/bondization.json"
        params = {
            "iss.meta": "off",
            "start": "0"
        }

        _, df = MoexISS._iss_data(url, params, tables)
        return df

    @staticmethod
    def securities(isin: str, table: pd.DataFrame = pd.DataFrame()) -> pd.DataFrame:
        url = f"{MoexISS._BASE_URL}/securities.json"
        params = {
            "q": isin,
            "iss.meta": "off",
            "start": "0"
        }

        _, df = MoexISS._iss_data(url, params, {'securities': table})
        return df['securities']

    @staticmethod
    def description(ticker: str, table: pd.DataFrame | None) -> pd.DataFrame:

        if table is None:
            table = pd.DataFrame()

        url = f"{MoexISS._BASE_URL}/securities/{ticker}.json"
        params = {
            "iss.meta": "off",
            "start": "0"
            # iss.only
        }

        _, df = MoexISS._iss_data(url, params, {'description': table}, 1)
        return df['description']

    @staticmethod
    def history(ticker: str, from_dt: dt, till_dt: dt = dt.today(), table: pd.DataFrame = pd.DataFrame()) -> pd.DataFrame:
        url = f"{MoexISS._BASE_URL}/history/engines/stock/markets/bonds/securities/{ticker}.json"
        params = {
            "from": from_dt.date().isoformat(),
            "till": till_dt.date().isoformat(),
            "iss.meta": "off",
            "start": "0",
            "limit": "100",
            "marketprice_board": "1"
        }

        _, df = MoexISS._iss_data(url, params, {'history': table})
        return df['history']

    @staticmethod
    def _iss_data(url: str, params: dict, tables: dict[str, pd.DataFrame], limit=0) -> tuple[int, dict[str, pd.DataFrame]]:

        try:

            # always remember about the 'start' argument to get long replies
            start = 0
            cnt = 1
            i = 1
            while cnt > 0:
                cnt = 0

                params["start"] = f"{start}"
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()

                for block_name in tables.keys():
                    if block_name in data:
                        block_data = data[block_name]
                        df = pd.DataFrame(
                            block_data['data'], columns=block_data['columns'])
                        tables[block_name] = pd.concat(
                            [tables[block_name], df], ignore_index=True)
                        cnt = max(cnt, len(df))

                start = start + cnt

                sleep(0.05)
                logger.info(f"start = {start}")
                if limit and i >= limit:
                    break
                else:
                    i = i + 1

            return start, tables

        except requests.exceptions.RequestException as e:
            logger.exception("Сетевое исключение MOEX ISS: %s", e)

        return 0, tables


if __name__ == "__main__":
    # Тестируем на ОФЗ-ПК (флоатере), который обсуждали ранее
    # bond_id = "SU26238RMFS4"

    # securities = MoexISS.securities("RU000A107X96")
    # securities.to_excel('securities.xlsx')

    sec = pd.read_excel('securities.xlsx')

    data = desc = history = None
    for bond_id in sec[sec['isin'].isin(['RU000A105W08'])]['secid']:
        desc = MoexISS.description(bond_id, desc)
        data = MoexISS.bond_cf(bond_id, data)
        history = MoexISS.history(bond_id, dt(2025, 1, 1))

    if data:
        for file_name in data.keys():
            data[file_name].to_excel(f"{file_name}.xlsx")

    if not desc is None:
        desc.to_excel('description.xlsx')

    if not history is None:
        history.to_excel('history.xlsx')
