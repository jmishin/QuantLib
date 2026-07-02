import logging
from datetime import datetime
import xml.etree.ElementTree as ET
import pandas as pd
import requests

# Настройка логирования для контроля выполнения и отладки
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

URL = "http://www.cbr.ru/DailyInfoWebServ/DailyInfo.asmx"


def fetch_ruonia_data(from_date: str, to_date: str) -> pd.DataFrame:
    """Скачивает данные RUONIA с веб-сервиса ЦБ РФ за указанный период."""
    soap_body = f"""<?xml version="1.0" encoding="utf-8"?>
    <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
      <soap:Body>
        <Ruonia xmlns="http://web.cbr.ru/">
          <fromDate>{from_date}</fromDate>
          <ToDate>{to_date}</ToDate>
        </Ruonia>
      </soap:Body>
    </soap:Envelope>"""

    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        # "SOAPAction": "http://web.cbr.ru/Ruonia",
    }


    try:
        logger.info(
            f"Отправка запроса RUONIA к ЦБ РФ за период: {from_date} - {to_date}")
        response = requests.post(
            URL, data=soap_body, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при выполнении HTTP-запроса RUONIA: {e}")
        raise

    try:
        root = ET.fromstring(response.text)
        records = []

        for ro_node in root.iter("ro"):
            date_node = ro_node.find("D0")
            rate_node = ro_node.find("ruo")
            vol_node = ro_node.find("vol")

            date_str = date_node.text if date_node is not None else None
            rate_str = rate_node.text if rate_node is not None else None
            vol_str = vol_node.text if vol_node is not None else None

            if date_str and rate_str:
                records.append(
                    {"Date": date_str, "Ruonia": rate_str, "Vol": vol_str}
                )

        if not records:
            logger.warning("Данные RUONIA за указанный период не найдены.")
            return pd.DataFrame(columns=["Date", "Ruonia", "Vol"])

        df = pd.DataFrame(records)
        df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None)
        df["Ruonia"] = pd.to_numeric(df["Ruonia"], errors="coerce")
        df["Vol"] = pd.to_numeric(df["Vol"], errors="coerce")
        df = df.sort_values(by="Date", ascending=False).reset_index(drop=True)

        logger.info(f"Успешно обработано строк RUONIA: {len(df)}")
        return df

    except ET.ParseError as e:
        logger.error(f"Ошибка парсинга XML-ответа RUONIA: {e}")
        raise


def fetch_key_rate_data(from_date: str, to_date: str) -> pd.DataFrame:
    """Скачивает историю ключевой ставки с веб-сервиса ЦБ РФ за указанный период."""

    soap_body = f"""<?xml version="1.0" encoding="utf-8"?>
    <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
      <soap:Body>
        <KeyRate xmlns="http://web.cbr.ru/">
          <fromDate>{from_date}</fromDate>
          <ToDate>{to_date}</ToDate>
        </KeyRate>
      </soap:Body>
    </soap:Envelope>"""

    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": "http://web.cbr.ru/KeyRate",
    }


    try:
        logger.info(
            f"Отправка запроса ключевой ставки к ЦБ РФ за период: {from_date} - {to_date}")
        response = requests.post(
            URL, data=soap_body, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(
            f"Ошибка при выполнении HTTP-запроса ключевой ставки: {e}")
        raise

    try:
        root = ET.fromstring(response.text)
        records = []

        for kr_node in root.iter("KR"):
            date_node = kr_node.find("DT")
            rate_node = kr_node.find("Rate")

            date_str = date_node.text if date_node is not None else None
            rate_str = rate_node.text if rate_node is not None else None

            if date_str and rate_str:
                records.append({"Date": date_str, "KeyRate": rate_str})

        if not records:
            logger.warning(
                "Данные ключевой ставки за указанный период не найдены.")
            return pd.DataFrame(columns=["Date", "KeyRate"])

        df = pd.DataFrame(records)
        df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None)
        df["KeyRate"] = pd.to_numeric(df["KeyRate"], errors="coerce")
        df = df.sort_values(by="Date", ascending=False).reset_index(drop=True)

        logger.info(f"Успешно обработано строк ключевой ставки: {len(df)}")
        return df

    except ET.ParseError as e:
        logger.error(f"Ошибка парсинга XML-ответа ключевой ставки: {e}")
        raise


def fetch_ruonia_index_data(from_date: str, to_date: str) -> pd.DataFrame:
    """Скачивает значения Индекса RUONIA и срочных ставок с веб-сервиса ЦБ РФ.

    Args:
        from_date (str): Начальная дата в формате 'YYYY-MM-DD'
        to_date (str): Конечная дата в формате 'YYYY-MM-DD'

    Returns:
        pd.DataFrame: DataFrame с колонками ['Date', 'RUONIA_Index', 'RUONIA_1M', 'RUONIA_3M', 'RUONIA_6M']
    """
    # SOAP XML-пакет для метода RuoniaIndex


    soap_body = f"""<?xml version="1.0" encoding="utf-8"?>
    <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
      <soap:Body>
        <RuoniaSV xmlns="http://web.cbr.ru/">
          <fromDate>{from_date}</fromDate>
          <ToDate>{to_date}</ToDate>
        </RuoniaSV>
      </soap:Body>
    </soap:Envelope>"""

    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        # "SOAPAction": "http://web.cbr.ru/RuoniaIndex",
    }

    try:
        logger.info(
            f"Отправка запроса Индекса RUONIA к ЦБ РФ за период: {from_date} - {to_date}")
        response = requests.post(
            URL, data=soap_body, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при выполнении HTTP-запроса Индекса RUONIA: {e}")
        raise

    try:
        root = ET.fromstring(response.text)
        records = []

        # Данные индекса возвращаются в узлах <roi>
        for roi_node in root.iter("ra"):
            date_node = roi_node.find("DT")        # Дата
            index_node = roi_node.find("RUONIA_Index")  # Значение индекса
            # Срочная версия на 1 мес.
            ave_1m = roi_node.find("RUONIA_AVG_1M")
            # Срочная версия на 3 мес.
            ave_3m = roi_node.find("RUONIA_AVG_3M")
            # Срочная версия на 6 мес.
            ave_6m = roi_node.find("RUONIA_AVG_6M")

            date_str = date_node.text if date_node is not None else None
            index_str = index_node.text if index_node is not None else None

            if date_str and index_str:
                records.append({
                    "Date": date_str,
                    "RUONIA_Index": index_str,
                    "RUONIA_1M": ave_1m.text if ave_1m is not None else None,
                    "RUONIA_3M": ave_3m.text if ave_3m is not None else None,
                    "RUONIA_6M": ave_6m.text if ave_6m is not None else None,
                })

        if not records:
            logger.warning(
                "Данные Индекса RUONIA за указанный период не найдены.")
            return pd.DataFrame(columns=["Date", "RUONIA_Index", "RUONIA_1M", "RUONIA_3M", "RUONIA_6M"])

        df = pd.DataFrame(records)
        df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None)

        # Переводим числовые колонки в float
        num_cols = ["RUONIA_Index", "RUONIA_1M", "RUONIA_3M", "RUONIA_6M"]
        for col in num_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.sort_values(by="Date", ascending=False).reset_index(drop=True)

        logger.info(f"Успешно обработано строк Индекса RUONIA: {len(df)}")
        return df

    except ET.ParseError as e:
        logger.error(f"Ошибка парсинга XML-ответа Индекса RUONIA: {e}")
        raise


def save_to_excel(ruonia_df: pd.DataFrame, key_rate_df: pd.DataFrame, index_df: pd.DataFrame, filename: str = "cbr_data.xlsx"):
    """Сохраняет данные RUONIA, ключевой ставки и индекса RUONIA в один Excel файл на разные листы."""
    if ruonia_df.empty and key_rate_df.empty and index_df.empty:
        logger.warning("Все DataFrame пусты. Файл Excel не будет создан.")
        return

    with pd.ExcelWriter(filename, engine="openpyxl") as writer:

        # Вспомогательная функция стилизации листа
        def format_sheet(df, sheet_name, num_formats):
            if df.empty:
                return
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            ws = writer.sheets[sheet_name]

            # Применение форматов к ячейкам
            for row in range(2, ws.max_row + 1):
                ws.cell(row=row, column=1).number_format = "yyyy-mm-dd"
                for col_idx, fmt in num_formats.items():
                    if ws.cell(row=row, column=col_idx).value is not None:
                        ws.cell(row=row, column=col_idx).number_format = fmt

            # Подгонка ширины колонок
            # for col in ws.columns:
            #     max_len = max(len(str(cell.value or "")) for cell in col)
            #     ws.column_dimensions[col.column_letter].width = max(
            #         max_len + 3, 12)

        # 1. Лист RUONIA
        format_sheet(ruonia_df, "RUONIA", {2: "0.00", 3: "#,##0.00"})

        # 2. Лист Ключевая ставка
        format_sheet(key_rate_df, "KeyRate", {2: "0.00"})

        # 3. Лист Индекс RUONIA (для индекса нужно больше знаков после запятой — обычно 4)
        format_sheet(index_df, "RUONIA_Index", {
                     2: "0.0000", 3: "0.00", 4: "0.00", 5: "0.00"})
        logger.info(f"Данные успешно сохранены в файл: {filename}")


if __name__ == "__main__":  # Метод Индекса RUONIA на стороне ЦБ содержит данные начиная с января 2021 года
    START_DATE = "2015-01-01"
    END_DATE = datetime.now().strftime("%Y-%m-%d")
    OUTPUT_FILE = "cbr.xlsx"

    try:  # Скачиваем все три набора данных
        df_ruonia = fetch_ruonia_data(from_date=START_DATE, to_date=END_DATE)
        df_key_rate = fetch_key_rate_data(
            from_date=START_DATE, to_date=END_DATE)
        # df_ruonia_index = fetch_ruonia_index_data(
        #     from_date=START_DATE, to_date=END_DATE)
        # Сохраняем в один структурированный файл
        df_ruonia_index = pd.DataFrame()
        save_to_excel(df_ruonia, df_key_rate,
                      df_ruonia_index, filename=OUTPUT_FILE)
    except Exception as e:
        logger.critical(f"Критическая ошибка при работе скрипта: {e}")
