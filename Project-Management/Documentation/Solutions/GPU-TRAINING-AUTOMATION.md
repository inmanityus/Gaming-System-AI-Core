# GPU Training Automation Script

## One-Command Training

```bash
#!/bin/bash
# train-all-adapters.sh

set -e

echo "Starting vampire adapter training (7 adapters)..."
for task in personality dialogue_style action_policy emotional_response world_knowledge social_dynamics goal_prioritization; do
    echo "Training vampire_${task}..."
    python training/train_lora_adapter.py --archetype vampire --task $task
    echo "✅ vampire_${task} complete"
done

echo "Starting zombie adapter training (7 adapters)..."
for task in personality dialogue_style action_policy emotional_response world_knowledge social_dynamics goal_prioritization; do
    echo "Training zombie_${task}..."
    python training/train_lora_adapter.py --archetype zombie --task $task
    echo "✅ zombie_${task} complete"
done

echo "="
echo "ALL 14 ADAPTERS TRAINED"
echo "Running validation..."
python examples/body_broker_complete_demo.py
```

## Parallel Training (Faster)

```bash
# Train vampire and zombie in parallel on multi-GPU
python training/train_lora_adapter.py --archetype vampire --task personality &
python training/train_lora_adapter.py --archetype zombie --task personality &
wait
# Repeat for all tasks
```

