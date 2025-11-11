#include "vocal_synthesis/mid_lod_kernel.hpp"
#include <algorithm>

namespace vocal_synthesis {

MidLODKernel::MidLODKernel(float sample_rate)
    : sample_rate_(sample_rate)
    , formant_bank_(std::make_unique<dsp::TPT_FormantBank>(sample_rate))
    , breathiness_(std::make_unique<dsp::BreathinessEffect>(sample_rate))
    , roughness_(std::make_unique<dsp::RoughnessEffect>(sample_rate))
    , glottal_(std::make_unique<dsp::GlottalIncoherence>(sample_rate))
    , subharmonic_(std::make_unique<dsp::SubharmonicGenerator>(sample_rate))
    , pitch_stabilizer_(std::make_unique<dsp::PitchStabilizer>(sample_rate))
    , corporeal_noise_(std::make_unique<dsp::CorporealNoise>(sample_rate))
{
}

void MidLODKernel::setSampleRate(float sample_rate) {
    sample_rate_ = sample_rate;
    formant_bank_->setSampleRate(sample_rate);
    breathiness_->setSampleRate(sample_rate);
    roughness_->setSampleRate(sample_rate);
    glottal_->setSampleRate(sample_rate);
    subharmonic_->setSampleRate(sample_rate);
    pitch_stabilizer_->setSampleRate(sample_rate);
    corporeal_noise_->setSampleRate(sample_rate);
}

void MidLODKernel::process(
    float* output,
    const float* input,
    const AberrationParams& params,
    size_t num_samples
) {
    // Update all modules from parameters
    updateModulesFromParams(params);
    
    // Copy input to output (processing pipeline)
    std::copy(input, input + num_samples, output);
    
    // Process through DSP chain
    
    // 1. Formant filtering (vocal tract shape)
    formant_bank_->processInPlace(output, num_samples);
    
    // 2. Breathiness (air leakage)
    breathiness_->processInPlace(output, num_samples);
    
    // 3. Roughness (vocal fold irregularity)
    roughness_->processInPlace(output, num_samples);
    
    // 4. Glottal incoherence (Zombie: broken larynx)
    glottal_->processInPlace(output, num_samples);
    
    // 5. Subharmonics (Werewolf: beast undercurrent)
    subharmonic_->processInPlace(output, num_samples);
    
    // 6. Pitch stabilization (Vampire: uncanny stillness)
    pitch_stabilizer_->processInPlace(output, num_samples);
    
    // 7. Corporeal noise (Physical body failures - ADDITIVE!)
    corporeal_noise_->processInPlace(output, num_samples);
}

void MidLODKernel::reset() {
    formant_bank_->reset();
    breathiness_->reset();
    roughness_->reset();
    glottal_->reset();
    subharmonic_->reset();
    pitch_stabilizer_->reset();
    corporeal_noise_->reset();
}

void MidLODKernel::updateModulesFromParams(const AberrationParams& params) {
    // Setup formants (typical human formants, modified by parameters)
    dsp::TPT_FormantBank::Formant formants[3] = {
        {800.0f, 80.0f, 1.0f},   // F1
        {1200.0f, 100.0f, 1.0f}, // F2
        {2500.0f, 120.0f, 1.0f}  // F3
    };
    
    formant_bank_->setFormants(formants, 3);
    formant_bank_->shiftFormants(params.formant_shift.get());
    formant_bank_->scaleFormants(params.formant_scale.get());
    formant_bank_->expandBandwidths(params.bandwidth_expansion.get());
    
    breathiness_->setAmount(params.breathiness.get());
    roughness_->setAmount(params.roughness.get());
    glottal_->setIntensity(params.vocal_fold_irregularity.get());
    subharmonic_->setIntensity(params.growl_harmonics.get());
    pitch_stabilizer_->setStabilization(params.hollow_resonance.get());  // Repurpose hollow for vampire stillness
    
    // Corporeal noise based on archetype
    auto archetype = params.getArchetype();
    if (archetype == AberrationParams::Archetype::ZOMBIE) {
        corporeal_noise_->setZombieProfile(params.wet_sounds.get());
    } else if (archetype == AberrationParams::Archetype::WEREWOLF) {
        corporeal_noise_->setWerewolfProfile(params.growl_harmonics.get());
    }
}

} // namespace vocal_synthesis

