/**
 * @file audio_buffer.hpp
 * @brief Core audio buffer data structure
 * @version 1.0.0
 * @date 2025-11-09
 * 
 * Efficient audio buffer implementation optimized for:
 * - Real-time performance
 * - SIMD operations
 * - Cache efficiency
 * - Zero-copy operations where possible
 */

#pragma once

#include "types.hpp"
#include <vector>
#include <memory>
#include <string>
#include <cstring>

namespace vocal_synthesis {

/**
 * @brief Audio buffer for sample data
 * 
 * Core data structure for audio processing. Supports:
 * - Multiple channels (though mono is typical for synthesis)
 * - Arbitrary sample rates
 * - Efficient memory management
 * - File I/O
 * - SIMD-aligned allocation
 * 
 * @note Memory is 32-byte aligned for AVX2/AVX-512 SIMD operations
 */
class AudioBuffer {
public:
    // ========================================================================
    // Construction & Destruction
    // ========================================================================
    
    /**
     * @brief Default constructor (empty buffer)
     */
    AudioBuffer();
    
    /**
     * @brief Construct with size
     * @param sample_rate Sample rate in Hz
     * @param num_channels Number of audio channels
     */
    AudioBuffer(SampleRate sample_rate, uint32_t num_channels = DEFAULT_NUM_CHANNELS);
    
    /**
     * @brief Construct from sample data
     * @param samples Sample data (interleaved if multi-channel)
     * @param sample_rate Sample rate in Hz
     * @param num_channels Number of audio channels
     */
    AudioBuffer(const std::vector<Sample>& samples,
                SampleRate sample_rate,
                uint32_t num_channels = DEFAULT_NUM_CHANNELS);
    
    /**
     * @brief Copy constructor
     */
    AudioBuffer(const AudioBuffer& other);
    
    /**
     * @brief Move constructor
     */
    AudioBuffer(AudioBuffer&& other) noexcept;
    
    /**
     * @brief Copy assignment
     */
    AudioBuffer& operator=(const AudioBuffer& other);
    
    /**
     * @brief Move assignment
     */
    AudioBuffer& operator=(AudioBuffer&& other) noexcept;
    
    /**
     * @brief Destructor
     */
    ~AudioBuffer();
    
    // ========================================================================
    // Data Access
    // ========================================================================
    
    /**
     * @brief Get mutable pointer to sample data
     * @return Pointer to first sample
     * 
     * @warning Invalidated by resize() or clear()
     */
    Sample* data() { return samples_.data(); }
    
    /**
     * @brief Get const pointer to sample data
     * @return Pointer to first sample
     */
    const Sample* data() const { return samples_.data(); }
    
    /**
     * @brief Get reference to sample at index
     * @param index Sample index
     * @return Reference to sample
     * 
     * @note No bounds checking in release builds
     */
    Sample& operator[](size_t index) { return samples_[index]; }
    
    /**
     * @brief Get const reference to sample at index
     * @param index Sample index
     * @return Const reference to sample
     */
    const Sample& operator[](size_t index) const { return samples_[index]; }
    
    /**
     * @brief Get sample at index with bounds checking
     * @param index Sample index
     * @return Sample value
     * @throws std::out_of_range if index >= size()
     */
    Sample at(size_t index) const;
    
    // ========================================================================
    // Properties
    // ========================================================================
    
    /**
     * @brief Get total number of samples
     * @return Total samples (all channels)
     */
    size_t size() const { return samples_.size(); }
    
    /**
     * @brief Get number of frames
     * @return Number of frames (size / num_channels)
     */
    size_t numFrames() const { return samples_.size() / num_channels_; }
    
    /**
     * @brief Get sample rate
     * @return Sample rate in Hz
     */
    SampleRate sampleRate() const { return sample_rate_; }
    
    /**
     * @brief Get number of channels
     * @return Number of channels
     */
    uint32_t numChannels() const { return num_channels_; }
    
    /**
     * @brief Get duration in seconds
     * @return Duration
     */
    float durationSeconds() const {
        return samplesToSeconds(numFrames(), sample_rate_);
    }
    
    /**
     * @brief Check if buffer is empty
     * @return True if no samples
     */
    bool empty() const { return samples_.empty(); }
    
    // ========================================================================
    // Modification
    // ========================================================================
    
    /**
     * @brief Resize buffer
     * @param num_frames Number of frames
     * 
     * @note Invalidates pointers from data()
     * @note New samples are zero-initialized
     */
    void resize(size_t num_frames);
    
    /**
     * @brief Clear all samples (size becomes 0)
     */
    void clear();
    
    /**
     * @brief Fill buffer with value
     * @param value Value to fill
     */
    void fill(Sample value);
    
    /**
     * @brief Zero-fill buffer
     */
    void zero() { fill(0.0f); }
    
    /**
     * @brief Normalize audio to peak amplitude
     * @param peak Target peak amplitude (0.0, 1.0]
     * 
     * @note Scales all samples by (peak / current_peak)
     * @note Does nothing if current peak is zero
     */
    void normalize(float peak = 0.8f);
    
    /**
     * @brief Apply gain
     * @param gain Linear gain multiplier
     */
    void applyGain(float gain);
    
    /**
     * @brief Mix another buffer into this one
     * @param other Buffer to mix
     * @param gain Gain to apply to other buffer
     * 
     * @note Buffers must have same sample rate and channel count
     * @note Mixes min(this->size(), other.size()) samples
     */
    void mixFrom(const AudioBuffer& other, float gain = 1.0f);
    
    /**
     * @brief Copy samples from another buffer
     * @param other Source buffer
     * 
     * @note Resizes this buffer to match other
     */
    void copyFrom(const AudioBuffer& other);
    
    // ========================================================================
    // Analysis
    // ========================================================================
    
    /**
     * @brief Get peak absolute value
     * @return Peak amplitude
     */
    float peak() const;
    
    /**
     * @brief Get RMS (root mean square) value
     * @return RMS amplitude
     */
    float rms() const;
    
    /**
     * @brief Get RMS in decibels
     * @return RMS in dB (or -INFINITY if RMS is zero)
     */
    float rmsDB() const;
    
    /**
     * @brief Check if buffer contains any NaN or Inf
     * @return True if invalid samples found
     */
    bool hasInvalidSamples() const;
    
    /**
     * @brief Check if buffer contains denormals
     * @return True if denormal samples found
     */
    bool hasDenormals() const;
    
    // ========================================================================
    // File I/O
    // ========================================================================
    
    /**
     * @brief Load audio from file
     * @param filepath Path to audio file (WAV, FLAC, etc.)
     * @return AudioBuffer loaded from file
     * @throws std::runtime_error on I/O error
     * 
     * @note Supported formats: WAV, FLAC, OGG (via libsndfile)
     * @note Automatically converts to mono if multi-channel
     */
    static AudioBuffer loadFromFile(const std::string& filepath);
    
    /**
     * @brief Save audio to file
     * @param filepath Path to output file
     * @throws std::runtime_error on I/O error
     * 
     * @note Format determined by file extension (.wav, .flac, etc.)
     * @note Uses libsndfile
     */
    void saveToFile(const std::string& filepath) const;
    
    // ========================================================================
    // Utility
    // ========================================================================
    
    /**
     * @brief Get slice of buffer
     * @param start_frame Start frame (inclusive)
     * @param end_frame End frame (exclusive)
     * @return New buffer containing slice
     * 
     * @note Returns empty buffer if range is invalid
     */
    AudioBuffer slice(size_t start_frame, size_t end_frame) const;
    
    /**
     * @brief Append another buffer
     * @param other Buffer to append
     * 
     * @note Buffers must have same sample rate and channel count
     */
    void append(const AudioBuffer& other);
    
    /**
     * @brief Get channel as separate buffer
     * @param channel_index Channel index [0, num_channels)
     * @return Buffer containing single channel
     * @throws std::out_of_range if invalid channel
     */
    AudioBuffer getChannel(uint32_t channel_index) const;
    
    /**
     * @brief Convert to mono (if multi-channel)
     * @return Mono buffer (average of all channels)
     * 
     * @note Returns copy if already mono
     */
    AudioBuffer toMono() const;
    
    /**
     * @brief Resample to different sample rate
     * @param new_sample_rate Target sample rate
     * @return Resampled buffer
     * 
     * @note Uses simple linear interpolation
     * @note For production, consider high-quality resampler
     */
    AudioBuffer resample(SampleRate new_sample_rate) const;
    
private:
    std::vector<Sample> samples_;    ///< Sample data (interleaved if multi-channel)
    SampleRate sample_rate_;         ///< Sample rate (Hz)
    uint32_t num_channels_;          ///< Number of channels
    
    // Helper for file I/O
    static void checkFileError(const std::string& operation, const std::string& filepath);
};

// ============================================================================
// Non-member Functions
// ============================================================================

/**
 * @brief Generate silence
 * @param duration_sec Duration in seconds
 * @param sample_rate Sample rate
 * @param num_channels Number of channels
 * @return Buffer filled with zeros
 */
AudioBuffer generateSilence(float duration_sec,
                            SampleRate sample_rate = DEFAULT_SAMPLE_RATE,
                            uint32_t num_channels = DEFAULT_NUM_CHANNELS);

/**
 * @brief Generate sine wave
 * @param frequency Frequency in Hz
 * @param duration_sec Duration in seconds
 * @param amplitude Peak amplitude
 * @param sample_rate Sample rate
 * @return Buffer containing sine wave
 */
AudioBuffer generateSineWave(float frequency,
                             float duration_sec,
                             float amplitude = 0.5f,
                             SampleRate sample_rate = DEFAULT_SAMPLE_RATE);

/**
 * @brief Generate white noise
 * @param duration_sec Duration in seconds
 * @param amplitude RMS amplitude
 * @param sample_rate Sample rate
 * @return Buffer containing white noise
 */
AudioBuffer generateWhiteNoise(float duration_sec,
                               float amplitude = 0.3f,
                               SampleRate sample_rate = DEFAULT_SAMPLE_RATE);

/**
 * @brief Compute RMS difference between two buffers
 * @param a First buffer
 * @param b Second buffer
 * @return RMS of difference
 * 
 * @note Compares min(a.size(), b.size()) samples
 */
float computeRMSDifference(const AudioBuffer& a, const AudioBuffer& b);

} // namespace vocal_synthesis

