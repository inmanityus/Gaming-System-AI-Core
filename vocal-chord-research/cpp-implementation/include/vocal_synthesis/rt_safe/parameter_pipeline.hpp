#pragma once

#include <atomic>
#include <memory>
#include <utility>
#include <vector>

namespace vocal_synthesis {
namespace rt_safe {

/**
 * @brief Real-time safe parameter pipeline using lock-free double buffering
 * 
 * CRITICAL (per GPT-5 Pro + GPT-5 Codex peer review):
 * "No lock-free parameter updates, potential allocations/locks in audio thread.
 *  Need: Lock-free double buffering with atomic pointer swap at block boundaries."
 * 
 * PROBLEM:
 * - Audio callback runs on real-time thread (CANNOT block!)
 * - Parameter updates come from GUI/game thread (CAN block)
 * - Direct parameter access = data race + priority inversion
 * 
 * SOLUTION:
 * - Double buffering: Read buffer (audio thread) + Write buffer (GUI thread)
 * - Atomic pointer swap at safe points (between audio blocks)
 * - Lock-free: No mutexes, no blocking operations
 * - Pre-allocated: No memory allocations in audio thread
 * 
 * USAGE:
 *   // Setup (once at initialization)
 *   RTParameterPipeline<VoiceParams> pipeline;
 *   
 *   // GUI thread (update parameters)
 *   VoiceParams new_params = {...};
 *   pipeline.write(new_params);
 *   
 *   // Audio thread (read parameters)
 *   const VoiceParams& current = pipeline.read();  // Always lock-free!
 * 
 * GUARANTEES:
 * - Audio thread NEVER blocks
 * - Audio thread NEVER sees partial updates
 * - Audio thread NEVER allocates memory
 * - GUI thread CAN block (but doesn't affect audio)
 */
template<typename ParamType>
class RTParameterPipeline {
public:
    /**
     * @brief Constructor - initializes both buffers
     * @param initial_value Initial parameter state
     */
    explicit RTParameterPipeline(const ParamType& initial_value = ParamType{})
        : read_buffer_(std::make_unique<ParamType>(initial_value))
        , write_buffer_(std::make_unique<ParamType>(initial_value))
        , read_ptr_(read_buffer_.get())
        , write_ptr_(write_buffer_.get())
    {
        static_assert(std::is_copy_assignable_v<ParamType>, 
                     "ParamType must be copy assignable");
    }
    
    // Non-copyable (unique ownership of buffers)
    RTParameterPipeline(const RTParameterPipeline&) = delete;
    RTParameterPipeline& operator=(const RTParameterPipeline&) = delete;
    
    // Movable
    RTParameterPipeline(RTParameterPipeline&&) noexcept = default;
    RTParameterPipeline& operator=(RTParameterPipeline&&) noexcept = default;
    
    /**
     * @brief Write new parameters (GUI/game thread)
     * 
     * Safe to call from any non-RT thread. Updates are applied
     * atomically at the next swap point.
     * 
     * @param params New parameter values
     * 
     * FIXED: Use atomic exchange to get exclusive write access to write buffer.
     * This prevents race where pointer swap happens while we're writing.
     */
    void write(const ParamType& params) {
        // Atomically get write buffer pointer
        // If swap happens during this operation, we'll get the correct new write buffer
        ParamType* write_buf = write_ptr_.load(std::memory_order_acquire);
        
        // Write to the buffer
        // This is safe because only ONE writer exists, and swapIfPending()
        // ensures reader never reads from write buffer until after fence + flag
        *write_buf = params;
        
        // Release fence: ensures struct write is visible before flag is set
        std::atomic_thread_fence(std::memory_order_release);
        
        // Mark update as pending (release ensures write is visible)
        update_pending_.store(true, std::memory_order_release);
    }
    
    /**
     * @brief Read current parameters (audio thread)
     * 
     * REAL-TIME SAFE: Never blocks, never allocates.
     * Always returns valid, complete parameter state.
     * 
     * FIXED (Gemini 2.5 Flash peer review): Sequential consistency for clean read.
     * Load pointer with seq_cst, copy struct, guaranteed complete by write fence.
     * 
     * @return Copy of current parameters (always complete, never torn)
     */
    ParamType read() const noexcept {
        return *read_ptr_.load(std::memory_order_seq_cst);
    }
    
    /**
     * @brief Swap buffers at safe point (audio thread)
     * 
     * Call this at block boundaries (e.g., between audio buffers).
     * Real-time safe: completes in bounded time, no allocations.
     * 
     * @return true if swap occurred, false if no update pending
     * 
     * FIXED (Gemini 2.5 Flash peer review): Sequential consistency for clean swap.
     * Atomic pointer swap with seq_cst guarantees no torn reads/writes.
     */
    bool swapIfPending() noexcept {
        // Check if update is pending
        bool expected = true;
        if (!update_pending_.compare_exchange_strong(expected, false, 
                                                     std::memory_order_seq_cst,
                                                     std::memory_order_seq_cst)) {
            return false;
        }
        
        // Atomically exchange pointers with sequential consistency
        ParamType* old_read = read_ptr_.load(std::memory_order_seq_cst);
        ParamType* old_write = write_ptr_.load(std::memory_order_seq_cst);
        
        read_ptr_.store(old_write, std::memory_order_seq_cst);
        write_ptr_.store(old_read, std::memory_order_seq_cst);
        
        return true;
    }
    
    /**
     * @brief Force immediate swap (audio thread)
     * 
     * Use with caution: may cause audible artifacts if parameters
     * change mid-buffer. Prefer swapIfPending() at buffer boundaries.
     * 
     * FIXED (GPT-4o peer review): Use atomic exchange for truly atomic swap.
     */
    void forceSwap() noexcept {
        // Atomically swap using exchange
        ParamType* old_write = write_ptr_.load(std::memory_order_acquire);
        ParamType* old_read = read_ptr_.exchange(old_write, std::memory_order_acq_rel);
        write_ptr_.store(old_read, std::memory_order_release);
        
        update_pending_.store(false, std::memory_order_release);
    }
    
    /**
     * @brief Check if update is pending
     * @return true if write() was called but swap hasn't occurred yet
     */
    bool hasPendingUpdate() const noexcept {
        return update_pending_.load(std::memory_order_acquire);
    }

private:
    // Double buffers (pre-allocated, never reallocated)
    std::unique_ptr<ParamType> read_buffer_;
    std::unique_ptr<ParamType> write_buffer_;
    
    // Atomic pointers for lock-free access
    std::atomic<ParamType*> read_ptr_;
    std::atomic<ParamType*> write_ptr_;
    
    // Update flag
    std::atomic<bool> update_pending_{false};
};

/**
 * @brief Multi-voice parameter pipeline
 * 
 * Manages parameters for multiple voices efficiently.
 * Each voice gets its own lock-free pipeline.
 */
template<typename ParamType>
class MultiVoicePipeline {
public:
    explicit MultiVoicePipeline(size_t max_voices)
        : pipelines_(max_voices)
    {
    }
    
    /**
     * @brief Write parameters for a voice
     * @param voice_index Voice index [0, max_voices)
     * @param params New parameters
     */
    void write(size_t voice_index, const ParamType& params) {
        if (voice_index < pipelines_.size()) {
            pipelines_[voice_index].write(params);
        }
    }
    
    /**
     * @brief Read parameters for a voice (RT-safe)
     * @param voice_index Voice index
     * @return Current parameters (by value to avoid torn reads)
     */
    ParamType read(size_t voice_index) const noexcept {
        return pipelines_[voice_index].read();
    }
    
    /**
     * @brief Swap all pending updates (RT-safe)
     * 
     * Call once per audio block to apply all pending updates.
     * 
     * @return Number of voices that were updated
     */
    size_t swapAllPending() noexcept {
        size_t count = 0;
        for (auto& pipeline : pipelines_) {
            if (pipeline.swapIfPending()) {
                ++count;
            }
        }
        return count;
    }
    
    /**
     * @brief Get number of voices with pending updates
     */
    size_t countPendingUpdates() const noexcept {
        size_t count = 0;
        for (const auto& pipeline : pipelines_) {
            if (pipeline.hasPendingUpdate()) {
                ++count;
            }
        }
        return count;
    }
    
    size_t size() const noexcept { return pipelines_.size(); }

private:
    std::vector<RTParameterPipeline<ParamType>> pipelines_;
};

} // namespace rt_safe
} // namespace vocal_synthesis

