#include "vocal_synthesis/dsp/denormal_handling.hpp"
#include <atomic>
#include <cmath>

// Platform-specific includes
#if defined(_MSC_VER)
    #include <intrin.h>
    #include <xmmintrin.h>  // SSE
    #include <pmmintrin.h>  // SSE3
#elif defined(__GNUC__) || defined(__clang__)
    #include <x86intrin.h>
    #ifdef __ARM_NEON
        #include <arm_neon.h>
    #endif
#endif

namespace vocal_synthesis {
namespace dsp {

namespace {
    // Thread-local state
    thread_local bool g_denormal_handling_enabled = false;
    thread_local DenormalMode g_denormal_mode = DenormalMode::NONE;
    
    // Original FP control state (for restoration)
    thread_local uint32_t g_original_mxcsr = 0;
}

//==============================================================================
// PLATFORM DETECTION
//==============================================================================

bool isHardwareDenormalHandlingSupported() {
#if defined(__SSE__) || defined(__SSE2__) || defined(_M_X64) || (defined(_M_IX86_FP) && _M_IX86_FP >= 1)
    // x86/x64 with SSE support
    return true;
#elif defined(__ARM_NEON)
    // ARM with NEON support
    return true;
#else
    // No hardware support
    return false;
#endif
}

//==============================================================================
// x86/x64 SSE IMPLEMENTATION
//==============================================================================

#if defined(__SSE__) || defined(__SSE2__) || defined(_M_X64) || (defined(_M_IX86_FP) && _M_IX86_FP >= 1)

namespace {
    // SSE MXCSR register bits
    constexpr uint32_t MXCSR_FTZ = 1 << 15;  // Flush-To-Zero
    constexpr uint32_t MXCSR_DAZ = 1 << 6;   // Denormals-Are-Zero
}

static bool enableSSEDenormalHandling() {
    // Save original MXCSR
    g_original_mxcsr = _mm_getcsr();
    
    // Set FTZ and DAZ bits
    uint32_t new_mxcsr = g_original_mxcsr | MXCSR_FTZ | MXCSR_DAZ;
    _mm_setcsr(new_mxcsr);
    
    return true;
}

static void disableSSEDenormalHandling() {
    // Restore original MXCSR
    _mm_setcsr(g_original_mxcsr);
}

//==============================================================================
// ARM NEON IMPLEMENTATION
//==============================================================================

#elif defined(__ARM_NEON)

static bool enableNEONDenormalHandling() {
    // ARM NEON: Set FZ (Flush-to-Zero) bit in FPCR
    // Note: This requires specific ARM instructions and may need inline assembly
    
    #ifdef __aarch64__
        // ARM64: Use mrs/msr instructions
        uint64_t fpcr;
        __asm__ volatile("mrs %0, fpcr" : "=r"(fpcr));
        g_original_mxcsr = static_cast<uint32_t>(fpcr);  // Save original
        
        // Set FZ bit (bit 24)
        fpcr |= (1 << 24);
        __asm__ volatile("msr fpcr, %0" :: "r"(fpcr));
        
        return true;
    #else
        // ARM32: Different instruction
        uint32_t fpscr;
        __asm__ volatile("vmrs %0, fpscr" : "=r"(fpscr));
        g_original_mxcsr = fpscr;  // Save original
        
        // Set FZ bit (bit 24)
        fpscr |= (1 << 24);
        __asm__ volatile("vmsr fpscr, %0" :: "r"(fpscr));
        
        return true;
    #endif
}

static void disableNEONDenormalHandling() {
    #ifdef __aarch64__
        uint64_t fpcr = g_original_mxcsr;
        __asm__ volatile("msr fpcr, %0" :: "r"(fpcr));
    #else
        __asm__ volatile("vmsr fpscr, %0" :: "r"(g_original_mxcsr));
    #endif
}

//==============================================================================
// FALLBACK (NO HARDWARE SUPPORT)
//==============================================================================

#else

static bool enableSSEDenormalHandling() { return false; }
static void disableSSEDenormalHandling() {}

#if !defined(enableNEONDenormalHandling)
static bool enableNEONDenormalHandling() { return false; }
static void disableNEONDenormalHandling() {}
#endif

#endif

//==============================================================================
// PUBLIC API
//==============================================================================

bool enableDenormalHandling(DenormalMode mode) {
    if (g_denormal_handling_enabled && g_denormal_mode == mode) {
        // Already enabled with this mode
        return true;
    }
    
    bool success = false;
    
    switch (mode) {
        case DenormalMode::HARDWARE_FTZ_DAZ:
            #if defined(__SSE__) || defined(__SSE2__) || defined(_M_X64) || (defined(_M_IX86_FP) && _M_IX86_FP >= 1)
                success = enableSSEDenormalHandling();
            #elif defined(__ARM_NEON)
                success = enableNEONDenormalHandling();
            #else
                // No hardware support, fall back to DC offset
                success = true;  // DC offset always "succeeds" (just a convention)
                mode = DenormalMode::DC_OFFSET;
            #endif
            break;
            
        case DenormalMode::DC_OFFSET:
            // DC offset doesn't require hardware setup
            success = true;
            break;
            
        case DenormalMode::NONE:
            // Explicitly disable
            disableDenormalHandling();
            return false;
    }
    
    if (success) {
        g_denormal_handling_enabled = true;
        g_denormal_mode = mode;
    }
    
    return success;
}

void disableDenormalHandling() {
    if (!g_denormal_handling_enabled) {
        return;
    }
    
    if (g_denormal_mode == DenormalMode::HARDWARE_FTZ_DAZ) {
        #if defined(__SSE__) || defined(__SSE2__) || defined(_M_X64) || (defined(_M_IX86_FP) && _M_IX86_FP >= 1)
            disableSSEDenormalHandling();
        #elif defined(__ARM_NEON)
            disableNEONDenormalHandling();
        #endif
    }
    
    g_denormal_handling_enabled = false;
    g_denormal_mode = DenormalMode::NONE;
}

bool isDenormalHandlingEnabled() {
    return g_denormal_handling_enabled;
}

DenormalMode getDenormalMode() {
    return g_denormal_mode;
}

//==============================================================================
// SCOPED DENORMAL HANDLING
//==============================================================================

ScopedDenormalHandling::ScopedDenormalHandling(DenormalMode mode)
    : was_enabled_(isDenormalHandlingEnabled())
    , previous_mode_(getDenormalMode())
{
    enableDenormalHandling(mode);
}

ScopedDenormalHandling::~ScopedDenormalHandling() {
    if (was_enabled_) {
        enableDenormalHandling(previous_mode_);
    } else {
        disableDenormalHandling();
    }
}

//==============================================================================
// DC OFFSET FALLBACK
//==============================================================================

void addDCOffset(float* buffer, size_t num_samples) {
    for (size_t i = 0; i < num_samples; ++i) {
        buffer[i] += DC_OFFSET_DENORMAL;
    }
}

void removeDCOffset(float* buffer, size_t num_samples, float sample_rate) {
    // Simple one-pole high-pass filter to remove DC
    // Cutoff at ~5 Hz (subsonic, inaudible)
    const float fc = 5.0f;
    const float rc = 1.0f / (2.0f * 3.14159265359f * fc);
    const float dt = 1.0f / sample_rate;
    const float alpha = rc / (rc + dt);
    
    float prev_input = 0.0f;
    float prev_output = 0.0f;
    
    for (size_t i = 0; i < num_samples; ++i) {
        const float input = buffer[i];
        const float output = alpha * (prev_output + input - prev_input);
        
        buffer[i] = output;
        
        prev_input = input;
        prev_output = output;
    }
}

} // namespace dsp
} // namespace vocal_synthesis

