#include "vocal_synthesis/audio_buffer.hpp"
#include <algorithm>
#include <cmath>
#include <stdexcept>

#ifdef VOCAL_ENABLE_FILE_IO
#include <sndfile.h>
#endif

namespace vocal_synthesis {

namespace {
    // Validate alignment
    constexpr size_t REQUIRED_ALIGNMENT = 32;  // AVX2 requires 32-byte alignment
    
    bool isAligned(const void* ptr, size_t alignment) {
        return (reinterpret_cast<uintptr_t>(ptr) % alignment) == 0;
    }
}

//==============================================================================
// AudioBuffer Implementation
//==============================================================================

AudioBuffer::AudioBuffer()
    : sample_rate_(DEFAULT_SAMPLE_RATE)
    , num_channels_(DEFAULT_NUM_CHANNELS)
{
}

AudioBuffer::AudioBuffer(uint32_t sample_rate, uint32_t num_channels)
    : sample_rate_(sample_rate)
    , num_channels_(num_channels)
{
    if (sample_rate == 0) {
        throw std::invalid_argument("Sample rate must be greater than zero");
    }
    if (num_channels == 0 || num_channels > 16) {
        throw std::invalid_argument("Number of channels must be 1-16");
    }
}

AudioBuffer::AudioBuffer(const std::vector<float>& samples, uint32_t sample_rate, uint32_t num_channels)
    : samples_(samples)
    , sample_rate_(sample_rate)
    , num_channels_(num_channels)
{
    if (sample_rate == 0) {
        throw std::invalid_argument("Sample rate must be greater than zero");
    }
    if (num_channels == 0 || num_channels > 16) {
        throw std::invalid_argument("Number of channels must be 1-16");
    }
    if (samples.size() % num_channels != 0) {
        throw std::invalid_argument("Sample count must be multiple of channel count");
    }
}

AudioBuffer::~AudioBuffer() = default;

void AudioBuffer::resize(size_t num_frames) {
    samples_.resize(num_frames * num_channels_);
}

void AudioBuffer::clear() {
    std::fill(samples_.begin(), samples_.end(), 0.0f);
}

void AudioBuffer::normalize(float peak) {
    if (samples_.empty()) {
        return;
    }
    
    // Find maximum absolute value
    float max_val = 0.0f;
    for (float sample : samples_) {
        max_val = std::max(max_val, std::abs(sample));
    }
    
    // Avoid division by zero
    if (max_val < 1e-10f) {
        return;  // Signal is essentially silent
    }
    
    // Normalize to peak
    const float scale = peak / max_val;
    for (float& sample : samples_) {
        sample *= scale;
    }
}

float AudioBuffer::rms() const {
    if (samples_.empty()) {
        return 0.0f;
    }
    
    float sum_squares = 0.0f;
    for (float sample : samples_) {
        sum_squares += sample * sample;
    }
    
    return std::sqrt(sum_squares / samples_.size());
}

float AudioBuffer::peak() const {
    if (samples_.empty()) {
        return 0.0f;
    }
    
    float peak_val = 0.0f;
    for (float sample : samples_) {
        peak_val = std::max(peak_val, std::abs(sample));
    }
    
    return peak_val;
}

AudioBuffer AudioBuffer::loadFromFile(const std::string& filepath) {
#ifdef VOCAL_ENABLE_FILE_IO
    SF_INFO sf_info;
    std::memset(&sf_info, 0, sizeof(sf_info));
    
    // Open file for reading
    SNDFILE* file = sf_open(filepath.c_str(), SFM_READ, &sf_info);
    if (!file) {
        throw std::runtime_error("Failed to open audio file: " + filepath + 
                               " - " + sf_strerror(nullptr));
    }
    
    // Read all samples
    std::vector<float> samples(sf_info.frames * sf_info.channels);
    sf_count_t read_count = sf_readf_float(file, samples.data(), sf_info.frames);
    
    sf_close(file);
    
    if (read_count != sf_info.frames) {
        throw std::runtime_error("Failed to read all samples from: " + filepath);
    }
    
    // Create AudioBuffer
    return AudioBuffer(samples, sf_info.samplerate, sf_info.channels);
#else
    (void)filepath;
    throw std::runtime_error("File I/O not enabled (rebuild with VOCAL_ENABLE_FILE_IO=ON)");
#endif
}

void AudioBuffer::saveToFile(const std::string& filepath) const {
#ifdef VOCAL_ENABLE_FILE_IO
    SF_INFO sf_info;
    std::memset(&sf_info, 0, sizeof(sf_info));
    
    sf_info.samplerate = sample_rate_;
    sf_info.channels = num_channels_;
    sf_info.format = SF_FORMAT_WAV | SF_FORMAT_PCM_16;  // 16-bit PCM WAV
    
    // Open file for writing
    SNDFILE* file = sf_open(filepath.c_str(), SFM_WRITE, &sf_info);
    if (!file) {
        throw std::runtime_error("Failed to create audio file: " + filepath + 
                               " - " + sf_strerror(nullptr));
    }
    
    // Write all samples
    sf_count_t written_count = sf_writef_float(file, samples_.data(), numFrames());
    
    sf_close(file);
    
    if (written_count != static_cast<sf_count_t>(numFrames())) {
        throw std::runtime_error("Failed to write all samples to: " + filepath);
    }
#else
    (void)filepath;
    throw std::runtime_error("File I/O not enabled (rebuild with VOCAL_ENABLE_FILE_IO=ON)");
#endif
}

void AudioBuffer::mixFrom(const AudioBuffer& other, float gain) {
    if (other.sampleRate() != sample_rate_) {
        throw std::invalid_argument("Sample rates must match for mixing");
    }
    if (other.numChannels() != num_channels_) {
        throw std::invalid_argument("Channel counts must match for mixing");
    }
    
    const size_t samples_to_mix = std::min(samples_.size(), other.samples_.size());
    
    for (size_t i = 0; i < samples_to_mix; ++i) {
        samples_[i] += other.samples_[i] * gain;
    }
}

void AudioBuffer::append(const AudioBuffer& other) {
    if (other.sampleRate() != sample_rate_) {
        throw std::invalid_argument("Sample rates must match for appending");
    }
    if (other.numChannels() != num_channels_) {
        throw std::invalid_argument("Channel counts must match for appending");
    }
    
    samples_.insert(samples_.end(), other.samples_.begin(), other.samples_.end());
}

AudioBuffer AudioBuffer::slice(size_t start_frame, size_t end_frame) const {
    if (start_frame >= numFrames()) {
        // Return empty buffer if range is invalid
        return AudioBuffer(sample_rate_, num_channels_);
    }
    
    // Clamp end_frame to valid range
    end_frame = std::min(end_frame, numFrames());
    
    if (end_frame <= start_frame) {
        // Return empty buffer if range is invalid
        return AudioBuffer(sample_rate_, num_channels_);
    }
    
    const size_t frames_to_extract = end_frame - start_frame;
    const size_t start_sample = start_frame * num_channels_;
    const size_t num_samples = frames_to_extract * num_channels_;
    
    std::vector<float> extracted_samples(
        samples_.begin() + start_sample,
        samples_.begin() + start_sample + num_samples
    );
    
    return AudioBuffer(extracted_samples, sample_rate_, num_channels_);
}

void AudioBuffer::applyGain(float gain) {
    for (float& sample : samples_) {
        sample *= gain;
    }
}

} // namespace vocal_synthesis

