#include <ql/cashflows/arithmeticlookbackoncouponpricer.hpp>
#include <ql/errors.hpp>
#include <ql/indexes/iborindex.hpp>

namespace QuantLib {

    ArithmeticLookbackONCouponPricer::ArithmeticLookbackONCouponPricer()
    : ArithmeticAveragedOvernightIndexedCouponPricer(false), coupon_(nullptr) {}

    void ArithmeticLookbackONCouponPricer::initialize(const FloatingRateCoupon& coupon) {
        ArithmeticAveragedOvernightIndexedCouponPricer::initialize(coupon);
        coupon_ = dynamic_cast<const OvernightIndexedCoupon*>(&coupon);
        QL_REQUIRE(coupon_, "Coupon must be of type OvernightIndexedCoupon");
    }

    Rate ArithmeticLookbackONCouponPricer::swapletRate() const {
        QL_REQUIRE(coupon_, "Pricer not initialized");

        auto index = ext::dynamic_pointer_cast<OvernightIndex>(coupon_->index());
        QL_REQUIRE(index, "Index must be an OvernightIndex");

        const std::vector<Date>& fixingDates = coupon_->fixingDates();
        const std::vector<Time>& dt = coupon_->dt();
        Calendar cal = index->fixingCalendar();

        Real accumulatedRate = 0.0;
        Time totalTime = 0.0;

        for (size_t i = 0; i < dt.size(); ++i) {

            Rate r = index->fixing(fixingDates[i]);
            accumulatedRate += r * dt[i];
            totalTime += dt[i];
        }
        // float diff = abs(totalTime - coupon_->accrualPeriod());

        // if (!coupon_->applyObservationShift())
        //     QL_REQUIRE(diff < 1.e-14, std::format("bad convention {} {}",
        //                                         coupon_->accrualStartDate().serialNumber(),
        //                                         diff));
        QL_REQUIRE(totalTime > 0.0, "Total time in coupon period must be positive");
        Rate averagedIndexRate = accumulatedRate / totalTime;

        return coupon_->gearing() * averagedIndexRate + coupon_->spread();
    }

}
