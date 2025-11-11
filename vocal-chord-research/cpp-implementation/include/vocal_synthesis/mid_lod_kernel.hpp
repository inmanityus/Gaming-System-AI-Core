#pragma once

#include "vocal_synthesis/audio_buffer.hpp"
#include "vocal_synthesis/aberration_params_v2.hpp"
#include "vocal_synthesis/dsp/tpt_svf.hpp"
#include "vocal_synthesis/dsp/breathiness.hpp"
#include "vocal_synthesis/dsp/roughness.hpp"
#include "vocal_synthesis/dsp/glottal_incoherence.hpp"
#include "vocal_synthesis/dsp/subharmonic_generator.hpp"
#include "vocal_synthesis/dsp/pitch_stabilizer.hpp"
#include "vocal_synthesis/dsp/corporeal_noise.hpp"
#include <memory>

namespace vocal_synthesis {

/**
 * @brief Mid LOD Kernel - Simplified voice synthesis for medium distance
 * 
 * TARGET: <0.5ms per voice (128 voices = <64ms total = 60fps compatible)
 * 
 * COMPONENTS:
 * - TPT/SVF formant bank (3-5 formants)
 * - Breathiness effect
 * - Roughness effect
 * - Glottal incoherence (Zombie)
 * - Subharmonic generator (Werewolf)
 * - Pitch stabilizer (Vampire)
 * - Corporeal noise layers (All)
 * 
 * INTEGRATION:
 * - All modules peer-reviewed
 * - Type-safe parameters
 * - Real-time safe
 * - SIMD-ready
 */
class MidLODKernel {
public:
    explicit MidLODKernel(float sample_rate = 48000.0f);
    
    void setSampleRate(float sample_rate);
    
    /**
     * @brief Process audio with aberration parameters
     * @param output Output buffer
     * @param input Input (anchor audio)
     * @param params Aberration parameters
     * @param num_samples Number of samples
     */
    void process(
        float* output,
        const float* input,
        const AberrationParams& params,
        size_t num_samples
    );
    
    void reset();
    
private:
    float sample_rate_;
    
    // DSP modules
    std::unique_ptr<dsp::TPT_FormantBank> formant_bank_;
    std::unique_ptr<dsp::BreathinessEffect> breathiness_;
    std::unique_ptr<dsp::RoughnessEffect> roughness_;
    std::unique_ptr<dsp::GlottalIncoherence> glottal_;
    std::unique_ptr<dsp::SubharmonicGenerator> subharmonic_;
    std::unique_ptr<dsp::PitchStabilizer> pitch_stabilizer_;
    std::unique_ptr<dsp::CorporealNoise> corporeal_noise_;
    
    void updateModulesFromParams(const AberrationParams& params);
};

} // namespace vocal_synthesis

