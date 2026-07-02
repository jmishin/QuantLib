#ifndef ql_arithmetic_averaged_lookback_overnight_indexed_coupon_pricer_hpp
#define ql_arithmetic_averaged_lookback_overnight_indexed_coupon_pricer_hpp

// Наследуемся от стандартного арифметического прайсера библиотеки
#include <ql/cashflows/overnightindexedcouponpricer.hpp>

namespace QuantLib {

    class ArithmeticLookbackONCouponPricer : public ArithmeticAveragedOvernightIndexedCouponPricer {
      public:
        explicit ArithmeticLookbackONCouponPricer();

        // Переопределяем только инициализацию и саму формулу расчета ставки
        void initialize(const FloatingRateCoupon& coupon) override;
        Rate swapletRate() const override;

      private:
        const OvernightIndexedCoupon* coupon_;
    };

}

#endif
