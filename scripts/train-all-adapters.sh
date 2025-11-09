#!/bin/bash
# Train all 14 adapters (7 vampire + 7 zombie)

set -e

echo "Starting Body Broker adapter training..."

for task in personality dialogue_style action_policy emotional_response world_knowledge social_dynamics goal_prioritization; do
    echo "Training vampire_${task}..."
    python training/train_lora_adapter.py --archetype vampire --task $task
    echo "✅ vampire_${task} complete"
done

for task in personality dialogue_style action_policy emotional_response world_knowledge social_dynamics goal_prioritization; do
    echo "Training zombie_${task}..."
    python training/train_lora_adapter.py --archetype zombie --task $task
    echo "✅ zombie_${task} complete"
done

echo "✅ ALL 14 ADAPTERS TRAINED"

