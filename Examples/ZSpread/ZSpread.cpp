#include <ql/cashflows/arithmeticlookbackoncouponpricer.hpp>
#include <ql/indexes/ibor/sofr.hpp>
#include <ql/instruments/bonds/floatingratebond.hpp>
#include <ql/math/solvers1d/brent.hpp>
#include <ql/pricingengines/bond/discountingbondengine.hpp>
#include <ql/quantlib.hpp>
#include <ql/quotes/simplequote.hpp>
#include <ql/termstructures/yield/zerospreadedtermstructure.hpp>
#include <ql/time/calendars/unitedstates.hpp>
#include <ql/time/daycounters/actual360.hpp>
#include <chrono>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <vector>

using namespace QuantLib;
using std::exp;

// Вспомогательный механизм профессионального логирования
class Logger {
  public:
    static void log(const std::string& level, const std::string& message) {
        auto now = std::chrono::system_clock::now();
        auto in_time_t = std::chrono::system_clock::to_time_t(now);
        std::cout << std::put_time(std::localtime(&in_time_t), "%Y-%m-%d %H:%M:%S") << " [" << level
                  << "] " << message << std::endl;
    }
    static void info(const std::string& msg) { log("INFO", msg); }
    static void warn(const std::string& msg) { log("WARN", msg); }
    static void error(const std::string& msg) { log("ERROR", msg); }
};

// Функция для безопасного перевода QuantLib::Date в строку ISO формата
std::string toISOString(const Date& date) {
    std::ostringstream oss;
    oss << io::iso_date(date);
    return oss.str();
}



int main() {
   
    try {
        // ====================================================================
        // 1. НАСТРОЙКА ВРЕМЕННОГО КОНТЕКСТА
        // ====================================================================
        Date today(17, June, 2026);
        Settings::instance().evaluationDate() = today;
        Logger::info("Системная дата оценки QuantLib установлена на: " + toISOString(today));

        Calendar calendar = UnitedStates(UnitedStates::GovernmentBond);
        DayCounter dayCounter = Actual360();

        // ====================================================================
        // 2. ИНИЦИАЛИЗАЦИЯ ИНДЕКСА И НАПОЛНЕНИЕ ИСТОРИИ
        // ====================================================================
        Logger::info("Построение форвардной кривой и инициализация индекса SOFR...");
        Handle<YieldTermStructure> forecastingCurve(
            ext::make_shared<FlatForward>(today, 0.05, dayCounter));
        auto sofrIndex = ext::make_shared<Sofr>(forecastingCurve);

        Logger::info(
            "Заполнение базы исторических фиксаций SOFR для обеспечения Lookback конвенции...");
        Date startDateHistoric(15, May, 2026);
        Size historicFixingsCount = 0;
        for (Date d = startDateHistoric; d < today; d = calendar.advance(d, 1, Days)) {
            if (calendar.isBusinessDay(d)) {
                sofrIndex->addFixing(d, 0.045); // Историческая ставка 4.5%
                historicFixingsCount++;
            }
        }
        Logger::info("Успешно добавлено " + std::to_string(historicFixingsCount) +
                     " фиксаций в IndexManager.");

        // ====================================================================
        // 3. ГЕНЕРАЦИЯ СТРУКТУРЫ СДЕЛКИ (BOND & STRUCTURED LEG)
        // ====================================================================
        Date issueDate(1, June, 2026);
        Date maturityDate(1, June, 2028);
        Schedule schedule(issueDate, maturityDate, 6 * Months, calendar, ModifiedFollowing,
                          ModifiedFollowing, DateGeneration::Forward, false);

        Logger::info("Ручная сборка купонного Leg (Simple Average + Spread)...");
        Leg customLeg;
        Real nominal = 1000.0;
        Real gearing = 1.0;
        Spread spread = 0.0075; // Спред 75 bps (0.75%)

        for (size_t i = 0; i < schedule.size() - 1; ++i) {
            auto cp = ext::make_shared<OvernightIndexedCoupon>(
                schedule[i + 1], nominal, schedule[i], schedule[i + 1], sofrIndex, gearing, spread,
                Date(), Date(), dayCounter, false, RateAveraging::Simple, 10, 0, false);
            customLeg.push_back(cp);
        }

        Natural settlementDays = 2;
        Bond bond(settlementDays, Russia(), issueDate, customLeg);
        Logger::info("Объект структуры Bond успешно создан. Количество купонных периодов: " +
                     std::to_string(customLeg.size()));

        // ====================================================================
        // 4. ПОДКЛЮЧЕНИЕ КАСТОМНОГО ПРАЙСЕРА
        // ====================================================================
        Logger::info(
            "Интеграция кастомного механизма оценки: "
            "ArithmeticAveragedLookbackOvernightIndexedCouponPricer (Lookback = 5 дней)...");
        auto pricer = ext::make_shared<ArithmeticLookbackONCouponPricer>();
        setCouponPricer(bond.cashflows(), pricer);

        // Поточечный аудит купонных ставок для верификации вычислений прайсера
        for (size_t i = 0; i < bond.cashflows().size(); ++i) {
            auto coupon = ext::dynamic_pointer_cast<OvernightIndexedCoupon>(bond.cashflows()[i]);
            if (coupon) {
                Logger::info(" -> Прогнозная ставка купона №" + std::to_string(i + 1) +
                             " на дату " + toISOString(coupon->date()) + ": " +
                             std::to_string(coupon->rate() * 100.0) + "%");
            }
        }

        // ====================================================================
        // 5. РАСЧЕТ РЫНОЧНЫХ МЕТРИК ОТНОСИТЕЛЬНО КОТИРОВКИ (YIELD & Z-SPREAD)
        // ====================================================================
        Real marketCleanPrice = 101.0;
        Logger::info("Входные параметры оценки: чистая рыночная цена котировки = " +
                     std::to_string(marketCleanPrice) + "%");

        // --- Блок А. Расчет Доходности (Yield to Maturity) ---
        try {
            Logger::info("Запуск вычисления Yield to Maturity...");

            // ИСПРАВЛЕНО: В C++ структура называется Bond::Price
            Bond::Price bondPrice(marketCleanPrice, Bond::Price::Clean);

            Real calculatedYield = bond.yield(bondPrice, dayCounter, Compounded, Semiannual, today);
            Logger::info(">>> Рассчитанная доходность Yield to Maturity: " +
                         std::to_string(calculatedYield * 100.0) + "%");
        } catch (const std::exception& e) {
            Logger::error("Сбой при расчете Yield: " + std::string(e.what()));
        }

        // --- Блок Б. Расчет Z-Спреда через Brent Solver ---
        try {
            Logger::info("Инициализация математического решателя Brent для подбора Z-спреда...");

            auto spreadQuote = ext::make_shared<SimpleQuote>(0.0);
            Handle<Quote> spreadHandle(spreadQuote);

            // Конвенция спреда SimpleThenCompounded с полугодовым шагом дисконтирования
            auto spreadedCurve = ext::make_shared<ZeroSpreadedTermStructure>(
                forecastingCurve, spreadHandle, SimpleThenCompounded, Semiannual);

            auto spreadedEngine =
                ext::make_shared<DiscountingBondEngine>(Handle<YieldTermStructure>(spreadedCurve));
            bond.setPricingEngine(spreadedEngine);

            // Определение лямбда-функции невязки целевой цены
            auto discrepancy = [&](Spread s) -> Real {
                spreadQuote->setValue(s);
                return bond.cleanPrice() - marketCleanPrice;
            };

            Brent solver;
            Real accuracy = 1e-6;
            Real guess = 0.0050; // Начальное смещение 50 bps
            Real step = 0.0001;  // Шаг поиска 1 bp

            Logger::info("Поиск корня уравнения схождения цены...");
            Spread calculatedZSpread = solver.solve(discrepancy, accuracy, guess, step);

            Logger::info(">>> Успешно рассчитан Z-Spread: " +
                         std::to_string(calculatedZSpread * 10000.0) + " bps");
        } catch (const std::exception& e) {
            Logger::error("Сбой при вычислении Z-Spread через Brent Solver: " +
                          std::string(e.what()));
        }

    } catch (const std::exception& e) {
        Logger::error("Глобальный сбой выполнения процесса: " + std::string(e.what()));
        return 1;
    }

    Logger::info("Аналитический расчет успешно завершен.");
    return 0;
}
