#pragma once

#include <cstddef>
#include <cmath>

namespace vocal_synthesis {
namespace dsp {

/**
 * @brief Subliminal Audio Layer - Barely perceptible organic sounds
 * 
 * Story Teller refinement: "Subliminal heartbeat/blood flow sounds"
 * 
 * Adds organic, body-related sounds at the threshold of perception:
 * - Heartbeat (0.8-1.5 Hz pulsing)
 * - Blood flow (whooshing, rhythmic)
 * - Breath cycles (slow, organic)
 * 
 * These should be BARELY audible - felt more than heard.
 * Adds to uncanny valley effect for vampire.
 * Creates unease without conscious awareness.
 */
class SubliminalAudio {
public:
    enum class LayerType {
        HEARTBEAT,     ///< Rhythmic pulse (vampire)
        BLOOD_FLOW,    ///< Whooshing rhythm (vampire)
        BREATH_CYCLE,  ///< Slow breathing (all)
        ORGANIC_HUM    ///< Low frequency presence (all)
    };
    
    explicit SubliminalAudio(float sample_rate = 48000.0f);
    
    void setSampleRate(float sample_rate);
    
    /**
     * @brief Enable/disable specific subliminal layer
     * @param layer Layer type to configure
     * @param intensity Intensity [0.0, 1.0] - should be < 0.1 for subliminal
     */
    void setLayer(LayerType layer, float intensity);
    
    /**
     * @brief Set heartbeat rate
     * @param bpm Beats per minute [40, 120] - default 72
     */
    void setHeartbeatRate(float bpm);
    
    /**
     * @brief Process buffer (mixes subliminal layers)
     * @param output Output buffer
     * @param input Input buffer
     * @param num_samples Number of samples
     */
    void processBuffer(
        float* output,
        const float* input,
        size_t num_samples
    );
    
    void processInPlace(float* buffer, size_t num_samples);
    void reset();
    
private:
    float sample_rate_;
    
    // Layer intensities
    float heartbeat_intensity_ = 0.0f;
    float blood_flow_intensity_ = 0.0f;
    float breath_intensity_ = 0.0f;
    float organic_hum_intensity_ = 0.0f;
    
    // Heartbeat parameters
    float heartbeat_bpm_ = 72.0f;
    float heartbeat_phase_ = 0.0f;
    
    // Blood flow parameters
    float blood_flow_phase_ = 0.0f;
    
    // Breath parameters
    float breath_phase_ = 0.0f;
    
    // Generators
    float generateHeartbeat();
    float generateBloodFlow();
    float generateBreath();
    float generateOrganicHum();
};

} // namespace dsp
} // namespace vocal_synthesis

