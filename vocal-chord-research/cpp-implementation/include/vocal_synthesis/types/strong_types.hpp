#pragma once

#include <type_traits>
#include <algorithm>
#include <cmath>

namespace vocal_synthesis {
namespace types {

/**
 * @brief Strong typedef pattern for type-safe parameters
 * 
 * CRITICAL (per GPT-5 Codex peer review):
 * "AberrationParams exposes 12 raw floats that are accessed by index/magic strings.
 *  No type-safe envelope. Downstream code will silently break when you insert a new
 *  parameter or change ranges. Introduce explicit fields, enums, or tagged types."
 * 
 * This template creates distinct types for each parameter, preventing accidental
 * mixing of incompatible values (e.g., can't pass frequency where Q is expected).
 * 
 * Example:
 *   using Frequency = StrongType<float, struct FrequencyTag>;
 *   using Q = StrongType<float, struct QTag>;
 *   
 *   void setFilter(Frequency freq, Q q);  // Type-safe!
 *   setFilter(1000.0f, 5.0f);  // Won't compile - must use Frequency{1000.0f}, Q{5.0f}
 */
template<typename T, typename Tag>
class StrongType {
public:
    using ValueType = T;
    
    // Explicit construction (prevents implicit conversions)
    explicit constexpr StrongType(T value) : value_(value) {}
    
    // Default construction
    constexpr StrongType() : value_(T{}) {}
    
    // Get underlying value
    constexpr T get() const { return value_; }
    constexpr operator T() const { return value_; }
    
    // Comparison operators
    constexpr bool operator==(const StrongType& other) const { return value_ == other.value_; }
    constexpr bool operator!=(const StrongType& other) const { return value_ != other.value_; }
    constexpr bool operator<(const StrongType& other) const { return value_ < other.value_; }
    constexpr bool operator<=(const StrongType& other) const { return value_ <= other.value_; }
    constexpr bool operator>(const StrongType& other) const { return value_ > other.value_; }
    constexpr bool operator>=(const StrongType& other) const { return value_ >= other.value_; }
    
    // Arithmetic operators (return StrongType to maintain type safety)
    constexpr StrongType operator+(const StrongType& other) const { return StrongType{value_ + other.value_}; }
    constexpr StrongType operator-(const StrongType& other) const { return StrongType{value_ - other.value_}; }
    constexpr StrongType operator*(T scalar) const { return StrongType{value_ * scalar}; }
    constexpr StrongType operator/(T scalar) const { return StrongType{value_ / scalar}; }
    
    // Compound assignment
    StrongType& operator+=(const StrongType& other) { value_ += other.value_; return *this; }
    StrongType& operator-=(const StrongType& other) { value_ -= other.value_; return *this; }
    StrongType& operator*=(T scalar) { value_ *= scalar; return *this; }
    StrongType& operator/=(T scalar) { value_ /= scalar; return *this; }
    
private:
    T value_;
};

/**
 * @brief Clamped strong type with compile-time range validation
 * 
 * Automatically clamps values to valid range, preventing out-of-range bugs.
 */
template<typename T, typename Tag, T MinValue, T MaxValue>
class ClampedStrongType : public StrongType<T, Tag> {
public:
    explicit constexpr ClampedStrongType(T value) 
        : StrongType<T, Tag>(clamp(value)) {}
    
    constexpr ClampedStrongType() 
        : StrongType<T, Tag>(MinValue) {}
    
    // Set with automatic clamping
    void set(T value) {
        *this = ClampedStrongType{clamp(value)};
    }
    
    // Get valid range
    static constexpr T min() { return MinValue; }
    static constexpr T max() { return MaxValue; }
    
    // Validation
    static constexpr bool isValid(T value) {
        return value >= MinValue && value <= MaxValue;
    }
    
private:
    static constexpr T clamp(T value) {
        return value < MinValue ? MinValue : (value > MaxValue ? MaxValue : value);
    }
};

//==============================================================================
// VOCAL SYNTHESIS STRONG TYPES
//==============================================================================

// Formant parameters
using Frequency = ClampedStrongType<float, struct FrequencyTag, 20.0f, 24000.0f>;
using FrequencyShift = ClampedStrongType<float, struct FrequencyShiftTag, -200.0f, 200.0f>;
using FormantScale = ClampedStrongType<float, struct FormantScaleTag, 0.8f, 1.2f>;
using Bandwidth = ClampedStrongType<float, struct BandwidthTag, 10.0f, 2000.0f>;
using BandwidthExpansion = ClampedStrongType<float, struct BandwidthExpansionTag, 1.0f, 3.0f>;
using Q = ClampedStrongType<float, struct QTag, 0.3f, 30.0f>;

// Spectral parameters (normalized 0-1)
using Breathiness = ClampedStrongType<float, struct BreathinessTag, 0.0f, 1.0f>;
using Roughness = ClampedStrongType<float, struct RoughnessTag, 0.0f, 1.0f>;
using HollowResonance = ClampedStrongType<float, struct HollowResonanceTag, 0.0f, 1.0f>;
using WetSounds = ClampedStrongType<float, struct WetSoundsTag, 0.0f, 1.0f>;
using Irregularity = ClampedStrongType<float, struct IrregularityTag, 0.0f, 1.0f>;
using GrowlAmount = ClampedStrongType<float, struct GrowlAmountTag, 0.0f, 1.0f>;
using WhisperAmount = ClampedStrongType<float, struct WhisperAmountTag, 0.0f, 1.0f>;

// Articulatory parameters
using Tension = ClampedStrongType<float, struct TensionTag, 0.3f, 1.5f>;
using SubglottalPressure = ClampedStrongType<float, struct SubglottalPressureTag, 0.5f, 2.0f>;

// Gain parameters
using GainDB = ClampedStrongType<float, struct GainDBTag, -24.0f, 24.0f>;
using AmplitudeNormalized = ClampedStrongType<float, struct AmplitudeTag, 0.0f, 1.0f>;

// Sample rate and time
using SampleRate = ClampedStrongType<float, struct SampleRateTag, 8000.0f, 192000.0f>;
using TimeConstantMS = ClampedStrongType<float, struct TimeConstantTag, 0.1f, 100.0f>;

//==============================================================================
// UTILITY FUNCTIONS
//==============================================================================

/**
 * @brief Linear interpolation between two strong types
 */
template<typename StrongT>
constexpr StrongT lerp(const StrongT& a, const StrongT& b, float t) {
    t = std::clamp(t, 0.0f, 1.0f);
    return StrongT{a.get() + t * (b.get() - a.get())};
}

/**
 * @brief Convert dB to linear amplitude
 */
inline float dbToLinear(GainDB db) {
    return std::pow(10.0f, db.get() / 20.0f);
}

/**
 * @brief Convert linear amplitude to dB
 */
inline GainDB linearToDb(float linear) {
    return GainDB{20.0f * std::log10(std::max(linear, 1.0e-10f))};
}

/**
 * @brief Convert bandwidth to Q factor
 */
inline Q bandwidthToQ(Frequency freq, Bandwidth bw) {
    return Q{freq.get() / std::max(bw.get(), 1.0f)};
}

/**
 * @brief Convert Q factor to bandwidth
 */
inline Bandwidth qToBandwidth(Frequency freq, Q q) {
    return Bandwidth{freq.get() / std::max(q.get(), 0.3f)};
}

} // namespace types
} // namespace vocal_synthesis

