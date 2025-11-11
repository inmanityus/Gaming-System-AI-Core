#pragma once

#include <cstdint>

/**
 * @file denormal_handling.hpp
 * @brief Platform-specific denormal handling (FTZ/DAZ)
 * 
 * CRITICAL (per GPT-5 Pro peer review):
 * "Denormal handling: Adding a tiny DC is insufficient alone and costs CPU;
 *  you must enable FTZ/DAZ at audio thread start."
 * 
 * PROBLEM:
 * - Denormal (subnormal) floating-point numbers cause 10-100x CPU slowdown
 * - Occur when filter states decay to near-zero values
 * - Common in audio DSP (reverbs, delays, filters with long decay)
 * 
 * SOLUTION:
 * - FTZ (Flush-To-Zero): Treat denormal results as zero
 * - DAZ (Denormals-Are-Zero): Treat denormal inputs as zero
 * - Enable at audio thread startup (NOT per-sample!)
 * 
 * PLATFORM SUPPORT:
 * - x86/x64: SSE/AVX (FTZ + DAZ)
 * - ARM: NEON (FZ bit in FPCR)
 * - Fallback: DC offset injection
 */

namespace vocal_synthesis {
namespace dsp {

/**
 * @brief Denormal handling mode
 */
enum class DenormalMode {
    HARDWARE_FTZ_DAZ,  ///< Use hardware FTZ/DAZ (fastest, platform-specific)
    DC_OFFSET,         ///< Add DC offset (portable, slight CPU cost)
    NONE               ///< No denormal protection (debugging only!)
};

/**
 * @brief Enable denormal handling for current thread
 * 
 * USAGE:
 *   void audioThreadInit() {
 *       enableDenormalHandling();  // Call ONCE at thread start
 *       // ... rest of audio thread setup ...
 *   }
 * 
 * CRITICAL: Call this at the START of your audio thread, not per-sample!
 * 
 * @param mode Denormal handling mode (defaults to hardware if available)
 * @return true if denormals are now handled, false if unsupported
 */
bool enableDenormalHandling(DenormalMode mode = DenormalMode::HARDWARE_FTZ_DAZ);

/**
 * @brief Disable denormal handling (restore default FP behavior)
 * 
 * USE CASE: Testing, debugging, or when leaving audio thread
 */
void disableDenormalHandling();

/**
 * @brief Check if denormal handling is currently enabled
 */
bool isDenormalHandlingEnabled();

/**
 * @brief Get current denormal mode
 */
DenormalMode getDenormalMode();

/**
 * @brief Check if hardware FTZ/DAZ is supported on this platform
 */
bool isHardwareDenormalHandlingSupported();

/**
 * @brief RAII wrapper for automatic denormal handling
 * 
 * USAGE:
 *   void audioThread() {
 *       ScopedDenormalHandling denormals;  // Enabled for scope
 *       // ... audio processing ...
 *   }  // Automatically restored on scope exit
 */
class ScopedDenormalHandling {
public:
    explicit ScopedDenormalHandling(DenormalMode mode = DenormalMode::HARDWARE_FTZ_DAZ);
    ~ScopedDenormalHandling();
    
    // Non-copyable, movable
    ScopedDenormalHandling(const ScopedDenormalHandling&) = delete;
    ScopedDenormalHandling& operator=(const ScopedDenormalHandling&) = delete;
    ScopedDenormalHandling(ScopedDenormalHandling&&) noexcept = default;
    ScopedDenormalHandling& operator=(ScopedDenormalHandling&&) noexcept = default;
    
private:
    bool was_enabled_;
    DenormalMode previous_mode_;
};

//==============================================================================
// DC OFFSET INJECTION (Fallback Method)
//==============================================================================

/**
 * @brief DC offset for denormal protection (fallback method)
 * 
 * Add this to signals to prevent denormals when hardware FTZ/DAZ unavailable.
 * Value: 1.0e-25f (inaudible, prevents denormals)
 * 
 * USAGE:
 *   float output = input * gain + DC_OFFSET_DENORMAL;
 * 
 * NOTE: Hardware FTZ/DAZ is preferred (zero CPU cost)
 */
constexpr float DC_OFFSET_DENORMAL = 1.0e-25f;

/**
 * @brief Add DC offset to buffer (in-place)
 * @param buffer Audio buffer
 * @param num_samples Number of samples
 */
void addDCOffset(float* buffer, size_t num_samples);

/**
 * @brief Remove DC offset from buffer (in-place, high-pass filter)
 * @param buffer Audio buffer
 * @param num_samples Number of samples
 * @param sample_rate Sample rate in Hz
 */
void removeDCOffset(float* buffer, size_t num_samples, float sample_rate = 48000.0f);

} // namespace dsp
} // namespace vocal_synthesis

