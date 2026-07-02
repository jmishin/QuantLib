import QuantLib as ql
from datetime import datetime as dt
from numpy import datetime64
import pandas as pd
import logging

# https://implementingquantlib.substack.com/p/spread-calculations
# https://www.quantlibguide.com/A%20taste%20of%20QuantLib.html
# https://www.quantlibguide.com/Spread%20calculations.html

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("QuantLibBondPricing")


def make_bond(index: ql.OvernightIndex):
    # Россельхозбанк, БO-03-002P (RU000A107S10)

    issue_date = ql.Date(9, ql.February, 2024)
    maturity_date = ql.Date(29, ql.January, 2027)
    settlement_days = 0
    face_amount = 1_000.0
    day_counter = index.dayCounter()
    gearing = 1.0
    spread = 0.013

    schedule = ql.MakeSchedule(
        effectiveDate=issue_date,
        terminationDate=maturity_date,
        tenor=ql.Period("31D"),
        calendar=ql.Russia(),
        convention=ql.Unadjusted,
        # backwards=False,
        # forwards=True,
        rule=ql.DateGeneration.Forward
    )

    leg = ql.Leg()

    for i in range(len(schedule) - 1):
        cp = ql.OvernightIndexedCoupon(
            ql.Russia(ql.Russia.Settlement).adjust(schedule[i + 1]),
            face_amount,
            schedule[i],
            schedule[i + 1],
            index,
            gearing,
            spread,
            ql.Date(),
            ql.Date(),
            day_counter,
            False,
            ql.RateAveraging.Simple,
            31 + 7
        )
        leg.append(cp)

    # Используем стандартный конструктор базового класса Bond
    bond = ql.Bond(settlement_days, ql.Russia(
        ql.Russia.Settlement), issue_date, leg)

    pricer = ql.ArithmeticLookbackONCouponPricer()
    ql.setCouponPricer(bond.cashflows(), pricer)

    logger.info(
        f"Облигация успешно создана. Количество купонов: {len(bond.cashflows())}.")

    return bond


def make_bond_2(index: ql.OvernightIndex):
    # ВЭБ.РФ, ПБО-002Р-40 (RU000A107X96)

    issue_date = ql.Date(9, ql.April, 2024)
    maturity_date = ql.Date(30, ql.March, 2032)
    settlement_days = 0
    face_amount = 1_000.0
    day_counter = index.dayCounter()
    gearing = 1.0
    spread = 0.014

    schedule = ql.MakeSchedule(
        effectiveDate=issue_date,
        terminationDate=maturity_date,
        tenor=ql.Period("91D"),
        calendar=ql.Russia(),
        convention=ql.Unadjusted,
        # backwards=False,
        # forwards=True,
        rule=ql.DateGeneration.Forward
    )

    leg = ql.Leg()

    for i in range(len(schedule) - 1):
        cp = ql.OvernightIndexedCoupon(
            ql.Russia(ql.Russia.Settlement).adjust(schedule[i + 1]),
            face_amount,
            schedule[i],
            schedule[i + 1],
            index,
            gearing,
            spread,
            ql.Date(),
            ql.Date(),
            day_counter,
            False,
            ql.RateAveraging.Simple,
            7
        )
        leg.append(cp)

    # Используем стандартный конструктор базового класса Bond
    bond = ql.Bond(settlement_days, ql.Russia(
        ql.Russia.Settlement), issue_date, leg)

    pricer = ql.ArithmeticLookbackONCouponPricer()
    ql.setCouponPricer(bond.cashflows(), pricer)

    logger.info(
        f"Облигация успешно создана. Количество купонов: {len(bond.cashflows())}.")

    return bond


def make_bond_3(index: ql.OvernightIndex):
    # RU000A105W08
    # МЕТАЛЛОИНВЕСТ 001P-04

    issue_date = ql.Date().from_date(dt.fromisoformat("2023-02-22"))
    maturity_date = ql.Date().from_date(dt.fromisoformat("2027-02-17"))
    settlement_days = 0
    face_amount = 1_000.0
    day_counter = index.dayCounter()
    gearing = 1.0
    spread = 0.013 + 0.0  # spread + KC-RUONIA basis

    schedule = ql.MakeSchedule(
        effectiveDate=issue_date,
        terminationDate=maturity_date,
        tenor=ql.Period("182D"),
        calendar=ql.Russia(),
        convention=ql.Unadjusted,
        # backwards=False,
        # forwards=True,
        rule=ql.DateGeneration.Forward
    )

    leg = ql.Leg()

    for i in range(len(schedule) - 1):
        cp = ql.IborCoupon(
            ql.Russia(ql.Russia.Settlement).adjust(schedule[i + 1]),
            face_amount,
            schedule[i],
            schedule[i + 1],
            5,
            index,
            gearing,
            spread,
            ql.Date(),
            ql.Date(),
            day_counter,
            True
        )
        leg.append(cp)

    # Используем стандартный конструктор базового класса Bond
    bond = ql.Bond(settlement_days, ql.Russia(
        ql.Russia.Settlement), issue_date, leg)

    pricer = ql.BlackIborCouponPricer()
    volatility = 0.0
    vol = ql.OptionletVolatilityStructureHandle(ql.ConstantOptionletVolatility(
        0, ql.Russia(), ql.ModifiedFollowing, volatility, ql.Actual365Fixed()))
    pricer.setCapletVolatility(vol)

    ql.setCouponPricer(bond.cashflows(), pricer)

    logger.info(
        f"Облигация успешно создана. Количество купонов: {len(bond.cashflows())}.")

    return bond


def avg_ruonia_index(forecast_curve: ql.YieldTermStructureHandle) -> ql.OvernightIndex:

    cal = ql.BespokeCalendar("no_calendar")

    return ql.OvernightIndex("AVG_BOND_RUONIA", 0, ql.RUBCurrency(), cal, ql.Actual365Fixed(), forecast_curve)


def avg_keyrate_index(forecast_curve: ql.YieldTermStructureHandle) -> ql.OvernightIndex:

    cal = ql.Russia()
    return ql.OvernightIndex("AVG_BOND_KEYRATE", 0, ql.RUBCurrency(), cal, ql.Actual365Fixed(), forecast_curve)


def ruonia_index(forecast_curve: ql.YieldTermStructureHandle | None) -> ql.OvernightIndex:

    cal = ql.Russia()  # ql.BespokeCalendar("no_calendar")

    if forecast_curve:
        return ql.OvernightIndex("RUONIA", 0, ql.RUBCurrency(), cal, ql.ActualActual(ql.ActualActual.ISDA), forecast_curve)
    return ql.OvernightIndex("RUONIA", 0, ql.RUBCurrency(), cal, ql.ActualActual(ql.ActualActual.ISDA))


def make_rub_ois(curve_date):
    today = ql.Date().from_date(curve_date)
    ql.Settings.instance().evaluationDate = today

    ois_data = dict(
        [
            ("1D", 16.99),
            ("1W", 16.95),
            ("2W", 16.91),
            ("1M", 17.0),
            ("2M", 17.15),
            ("3M", 17.0),
            ("6M", 16.85),
            ("9M", 16.3),

            ("1Y", 15.73),
            ("2Y", 14.59),
            ("3Y", 14.41),
            ("4Y", 14.24),
            ("5Y", 14.12),
            ("6Y", 14.16),
            ("7Y", 14.15),
            ("8Y", 14.12),
            ("9Y", 14.12),
            ("10Y", 14.14)
        ]
    )

    index = ruonia_index(None)

    settlement_days = 1

    ois_helpers = []
    for tenor in ois_data:
        q = ql.SimpleQuote(ois_data[tenor] / 100)

        if tenor == "1D":
            ois_helpers.append(
                ql.OISRateHelper.forDates(
                    today,
                    ql.Russia().advance(today, 1, ql.Days),
                    ql.QuoteHandle(q),
                    index,
                    # paymentFrequency=ql.Annual,
                )
            )
        else:
            ois_helpers.append(
                ql.OISRateHelper(
                    settlement_days,
                    ql.Period(tenor),
                    ql.QuoteHandle(q),
                    index,
                    # paymentFrequency=ql.Annual,
                )
            )

    curve = ql.PiecewiseNaturalCubicZero(
        0,
        ql.Russia(),
        ois_helpers,
        ql.Actual365Fixed()
    )

    handle = ql.YieldTermStructureHandle(curve)

    return handle


def load_fixings(file_path: str, index: ql.Index, today: dt, index_name: str, sheet_name: str | None = None):
    """Считывает данные RUONIA из Excel и загружает их в QuantLib."""
    try:

        if index_name == "RUONIA":
            rate_col = "Ruonia"
        elif index_name == "KeyRate":
            rate_col = "KeyRate"
        else:
            raise Exception(f"Unknown index{index_name}")

        if sheet_name is None:
            sheet_name = index_name

        df = pd.read_excel(file_path, sheet_name=sheet_name).dropna(
            subset=["Date", rate_col])
        df["Date"] = pd.to_datetime(df["Date"])
        df = df[["Date", rate_col]]

        # df = dt[dt["Date"] < dt]
        # ql_dates = [ql.Date(r.day, r.month, r.year) for r in df["Date"]]
        # fixing_values = [float(rate) / 100.0 for rate in df["Ruonia"]]

        date_range = pd.date_range(start=df["Date"].min(), end=today, freq='D')
        df_daily = df.set_index('Date').reindex(date_range).ffill()
        df_daily.reset_index(level=0, inplace=True)
        df_daily.columns = ['Date', rate_col]
        df = df_daily

        df = df[df["Date"] < pd.to_datetime(today)]

        cal = index.fixingCalendar()

        ql_dates = []

        for _, r in df.iterrows():
            ql_date = ql.Date(r["Date"].day, r["Date"].month, r["Date"].year)
            rate = float(r[rate_col]) / 100.0
            if cal.isBusinessDay(ql_date):
                index.addFixing(ql_date, rate)
                ql_dates.append(ql_date)

        logger.info(f"Успешно загружено {len(ql_dates)} фиксингов")

    except Exception as e:
        logger.error(f"Ошибка при обработке или загрузке данных: {e}")
        raise e


def calculate_zspread_brent(today: ql.Date, bond: ql.Bond, base_curve: ql.YieldTermStructureHandle,
                            market_clean_price: float) -> float:
    """Рассчитывает Z-спред флоатера методом Brent через ZeroSpreadedTermStructure."""
    logger.info(
        f"Запуск численного решателя Brent для поиска Z-спреда при цене {market_clean_price}...")

    spread_quote = ql.SimpleQuote(0.0)
    spread_handle = ql.QuoteHandle(spread_quote)

    # Строим spreaded-структуру (рыночный стандарт SimpleThenCompounded + Semiannual)
    spreaded_curve = ql.ZeroSpreadedTermStructure(
        base_curve, spread_handle, ql.Compounded, ql.Annual
    )

    spreaded_engine = ql.DiscountingBondEngine(
        ql.YieldTermStructureHandle(spreaded_curve))
    bond.setPricingEngine(spreaded_engine)

    # Целевая функция невязки для Brent: (Текущая чистая цена - Рыночная чистая цена)
    def objective_function(s: float) -> float:
        try:
            spread_quote.setValue(s)
            return bond.cleanPrice() - market_clean_price
        except Exception as e:
            logger.error(e)
        return 0.0

    solver = ql.Brent()
    accuracy = 1e-6
    guess = 0.0050  # Стартовое предположение: 50 bps
    step = 0.0001   # Шаг: 1 bp

    # Решаем уравнение objective_function(s) = 0
    z_spread = solver.solve(objective_function, accuracy, guess, step)
    return z_spread


def get_instruments_cashflows_df(instruments) -> pd.DataFrame:
    """Строит детальный DataFrame по денежным потокам для любых объектов QuantLib.

    Добавлены поля:
        - fixing_weights: список весов (дней/долей) для каждого фиксинга в купоне.
    """
    # 1. Приводим входные данные к единому формату словаря {deal_id: instrument}
    if isinstance(instruments, dict):
        instruments_dict = instruments
    elif isinstance(instruments, (list, tuple)):
        instruments_dict = {f"deal_{i}": inst for i,
                            inst in enumerate(instruments, start=1)}
    else:
        instruments_dict = {"deal_1": instruments}

    records = []

    # 2. Основной цикл по всем объектам
    for deal_id, obj in instruments_dict.items():

        # Разворачиваем хелпер в базовый инструмент, если необходимо
        if hasattr(obj, "instrument"):
            instrument = obj.instrument()
        else:
            instrument = obj

        # Определяем структуру ног (Legs) для текущего инструмента
        if hasattr(instrument, "legs"):
            legs = [instrument.leg(i) for i in range(len(instrument.legs()))]
        elif hasattr(instrument, "cashflows"):
            legs = [instrument.cashflows()]
        else:
            continue  # Пропускаем неподдерживаемые объекты

        # Итерируемся по каждой ноге инструмента
        for leg_idx, leg in enumerate(legs, start=1):
            for cf in leg:
                coupon = ql.as_coupon(cf)
                fl_coupon = ql.as_overnight_indexed_coupon(cf)
                if fl_coupon is None:
                    fl_coupon = ql.as_floating_rate_coupon(cf)
                    is_overnight = False
                else:
                    is_overnight = True

                # Определяем купонные свойства
                if coupon is not None:
                    cf_type = "interest"
                    rate_type = "float" if fl_coupon is not None else "fix"
                    accrual_start = coupon.accrualStartDate().to_date()
                    accrual_end = coupon.accrualEndDate().to_date()
                    days = accrual_end - accrual_start
                    dcf = coupon.accrualPeriod()
                    convention = coupon.dayCounter().name()
                    rate = coupon.rate() * 100

                else:
                    cf_type = "principal"
                    rate_type = None
                    accrual_start = accrual_end = days = dcf = rate = convention = None

                # Инициализируем поля фиксингов и весов
                first_fixing_date = last_fixing_date = None
                fixing_dates = fixing_rates = fixing_weights = None
                spread = None

                if fl_coupon is not None:
                    # Пробуем привести к типу OvernightIndexedCoupon для извлечения весов

                    spread = fl_coupon.spread() * 100

                    try:
                        # Попытка работы со специфичным интерфейсом Overnight купонов

                        fixing_dates = [d.to_date().isoformat()[:10]
                                        for d in fl_coupon.fixingDates()]
                        fixing_rates = [fl_coupon.index().fixing(d)
                                        for d in fl_coupon.fixingDates()]

                        if (len(fixing_dates)):
                            first_fixing_date = fixing_dates[0]
                            last_fixing_date = fixing_dates[-1]

                        # Извлекаем веса фиксингов (число дней действия ставки)
                        if hasattr(fl_coupon, "fixingWeights"):
                            fixing_weights = list(
                                fl_coupon.fixingWeights())
                        elif hasattr(fl_coupon, "dt"):
                            fixing_weights = list(fl_coupon.dt())

                    except AttributeError:
                        pass

                    # Если это обычный флоатер (не овернайт) — у него 1 дата и вес равен 1 купонному периоду/дню
                    if not is_overnight:
                        try:
                            fix_date = fl_coupon.fixingDate()
                            first_fixing_date = last_fixing_date = fix_date.to_date()
                            fixing_dates = [fix_date.to_date()]
                            fixing_rates = [fl_coupon.index().fixing(fix_date)]
                            # Для классического купона вес единичный
                            fixing_weights = [1]
                        except Exception:
                            pass

                # Собираем финальную запись
                records.append(
                    {
                        "deal_id": deal_id,
                        "leg": leg_idx,
                        "type": cf_type,
                        "rate_type": rate_type,
                        "accrual_start": accrual_start,
                        "accrual_end": accrual_end,
                        "days": days,
                        "payment_date": cf.date().to_date(),
                        "dcf": dcf,
                        "convention": convention,
                        "rate": rate,
                        "spread": spread,
                        "amount": cf.amount(),
                        "first_fixing_date": first_fixing_date,
                        "last_fixing_date": last_fixing_date,
                        "fixing_dates": fixing_dates,
                        "fixing_rates": fixing_rates,
                        "fixing_weights": fixing_weights,
                    }
                )

    # 3. Формируем DataFrame и сортируем данные
    df = pd.DataFrame(records)
    if not df.empty:
        df = df.sort_values(
            by=["deal_id", "leg", "payment_date"]).reset_index(drop=True)

    return df


def main():
    try:
        logger.info(f'ql.__version__ = {ql.__version__}')

        bps = 1e-4
        curve_date = dt(2025, 9, 30)
        today = ql.Date().from_date(curve_date)

        ql.Settings.instance().evaluationDate = today

        forecast_curve = make_rub_ois(curve_date)

        avg_index = avg_keyrate_index(forecast_curve)
        load_fixings(r'cbr.xlsx', avg_index, curve_date, "KeyRate")

        bond = make_bond_3(avg_index)

        base_curve = avg_index.forwardingTermStructure()
        pricing_engine = ql.DiscountingBondEngine(base_curve)
        bond.setPricingEngine(pricing_engine)

        market_price = ql.BondPrice(99.51, ql.BondPrice.Clean)

        ytm = bond.bondYield(
            market_price, ql.Actual365Fixed(), ql.Compounded, ql.Annual) * 100

        logger.info(f"Теоретическая грязная цена (NPV): {bond.NPV():.6f}")
        logger.info(
            f"Накопленный купонный доход (Accrued): {bond.accruedAmount(today):.6f}")
        logger.info(
            f"Теоретическая чистая цена (Clean): {bond.cleanPrice():.6f}")
        logger.info(
            f"YTM: {ytm:.6f}")

        cf_table = get_instruments_cashflows_df(bond)
        cf_table['fdays'] = cf_table['last_fixing_date'].astype(
            "datetime64[s]") - cf_table['first_fixing_date'].astype("datetime64[s]")
        # logger.info(cf_table[['accrual_start', 'accrual_end', 'rate',
        #             'spread', 'first_fixing_date', 'last_fixing_date', 'fdays']])
        cf_table.to_excel('bond_3.xlsx')

        # # Логирование прогнозных ставок по купонам
        # for cf in bond.cashflows():
        #     c = ql.as_overnight_indexed_coupon(cf)
        #     if c:
        #         logger.info(f" Прогноз купона {c.date().ISO()}: {c.rate() * 100:.4f}%")

        z_spread = calculate_zspread_brent(
            today, bond, forecast_curve, market_price.amount())
        logger.info(
            f"Z-Spread (через Brent Solver): {z_spread * 10000.0:.4f} bps")
    except Exception as e:
        logger.error(e)


if __name__ == "__main__":
    main()
