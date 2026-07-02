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


def fetch_ruonia_data(from_date: str, to_date: str) -> pd.DataFrame:
    """Скачивает данные RUONIA с веб-сервиса ЦБ РФ за указанный период.

    Args:
        from_date (str): Начальная дата в формате 'YYYY-MM-DD'
        to_date (str): Конечная дата в формате 'YYYY-MM-DD'

    Returns:
        pd.DataFrame: DataFrame с колонками ['Date', 'Ruonia', 'Vol']
    """
    url = "http://www.cbr.ru/DailyInfoWebServ/DailyInfo.asmx"

    # Формируем валидный SOAP 1.1 XML-пакет для метода Ruonia
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
        logger.info(f"Отправка запроса к ЦБ РФ за период: {from_date} - {to_date}")
        response = requests.post(url, data=soap_body, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при выполнении HTTP-запроса: {e}")
        raise

    # ПАРСИНГ XML-ОТВЕТА (Изменено под реальную структуру <ro> и <ruo>)
    try:
        root = ET.fromstring(response.text)
        records = []
        
        # Перебираем строки данных, которые ЦБ возвращает в тегах <ro>
        for ro_node in root.iter("ro"):
            date_node = ro_node.find("D0")
            rate_node = ro_node.find("ruo")  # Процентная ставка лежит в теге <ruo>
            vol_node = ro_node.find("vol")

            date_str = date_node.text if date_node is not None else None
            rate_str = rate_node.text if rate_node is not None else None
            vol_str = vol_node.text if vol_node is not None else None

            if date_str and rate_str:
                records.append(
                    {"Date": date_str, "Ruonia": rate_str, "Vol": vol_str}
                )

        if not records:
            logger.warning("Данные за указанный период не найдены.")
            return pd.DataFrame(columns=["Date", "Ruonia", "Vol"])

        # Создаем DataFrame
        df = pd.DataFrame(records)

        # Профессиональная чистка, приведение типов и удаление таймзоны для Excel
        df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None)
        df["Ruonia"] = pd.to_numeric(df["Ruonia"], errors="coerce")
        df["Vol"] = pd.to_numeric(df["Vol"], errors="coerce")

        # Сортируем по дате от свежих к старым
        df = df.sort_values(by="Date", ascending=False).reset_index(drop=True)

        logger.info(f"Успешно обработано строк: {len(df)}")
        return df

    except ET.ParseError as e:
        logger.error(f"Ошибка парсинга XML-ответа: {e}")
        raise


def save_to_excel(df: pd.DataFrame, filename: str = "ruonia_data.xlsx"):
    """Сохраняет DataFrame в Excel с форматированием колонок."""
    if df.empty:
        logger.warning("DataFrame пуст. Файл Excel не будет создан.")
        return

    # Используем openpyxl для продвинутого сохранения
    with pd.ExcelWriter(filename, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="RUONIA", index=False)

        # Стилизация и автоподбор ширины колонок для удобства пользователя
        workbook = writer.book
        worksheet = writer.sheets["RUONIA"]

        # Форматирование даты и числовых значений
        for row in range(2, worksheet.max_row + 1):
            worksheet.cell(row=row, column=1).number_format = "yyyy-mm-dd"
            worksheet.cell(row=row, column=2).number_format = "0.00"
            if worksheet.cell(row=row, column=3).value is not None:
                worksheet.cell(row=row, column=3).number_format = "#,##0.00"

        # Автоматическое выравнивание ширины столбцов
        for col in worksheet.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            col_letter = col[0].column_letter
            worksheet.column_dimensions[col_letter].width = max(max_len + 3, 12)

    logger.info(f"Данные успешно сохранены в файл: {filename}")


if __name__ == "__main__":
    # Пример выгрузки данных за текущий год
    START_DATE = "2015-01-01"
    END_DATE = datetime.now().strftime("%Y-%m-%d")
    OUTPUT_FILE = f"ruonia.xlsx"

    try:
        ruonia_df = fetch_ruonia_data(from_date=START_DATE, to_date=END_DATE)
        save_to_excel(ruonia_df, filename=OUTPUT_FILE)
    except Exception as e:
        logger.critical(f"Критическая ошибка при работе скрипта: {e}")
