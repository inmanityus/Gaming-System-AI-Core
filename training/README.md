# Archetype LoRA Adapter Training

Training pipeline for archetype-specific LoRA adapters.

## Overview

Trains 7 LoRA adapters per archetype:
1. **personality** - Behavioral response patterns
2. **dialogue_style** - Speech patterns and vocabulary
3. **action_policy** - Decision-making and behavior selection
4. **emotional_response** - Reactions to events
5. **world_knowledge** - Lore-specific information
6. **social_dynamics** - Relationship management
7. **goal_prioritization** - Planning and goal hierarchy

## Directory Structure

```
training/
├── data/                    # Training data (extracted from docs/narrative/)
│   ├── vampire_*_training.json  # 1,785 examples across 7 tasks
│   └── zombie_*_training.json   # 686 examples across 7 tasks
├── adapters/                # Trained adapter weights
│   ├── vampire/             # 7 adapters for vampire
│   └── zombie/              # 7 adapters for zombie
├── curate_archetype_data.py # Data extraction script
├── train_lora_adapter.py    # Training pipeline
└── requirements.txt         # Dependencies
```

## Training Data

**Extracted**: 2,471 total examples
- **Vampire**: 1,785 examples (255 per adapter task)
- **Zombie**: 686 examples (98 per adapter task)

**Source**: 22 narrative documents in `docs/narrative/`

## Training Pipeline

### 1. Install Dependencies

```bash
pip install -r training/requirements.txt
```

### 2. Train Adapters

**Train single adapter**:
```bash
python training/train_lora_adapter.py --archetype vampire --task personality
```

**Train all adapters for archetype**:
```bash
python training/train_lora_adapter.py --archetype vampire
python training/train_lora_adapter.py --archetype zombie
```

**Train everything**:
```bash
python training/train_lora_adapter.py --archetype all
```

### 3. Training Configuration

Default settings (can be modified in code):
- Base model: Qwen/Qwen2.5-7B-Instruct
- LoRA rank: 32
- LoRA alpha: 16.0
- Training epochs: 3
- Batch size: 4
- Learning rate: 2e-4
- Quantization: 4-bit (QLoRA)

### 4. GPU Requirements

- **Minimum**: NVIDIA GPU with 16GB VRAM
- **Recommended**: A10G (24GB) or better
- **Training time**: ~2-4 hours per adapter

## Integration

See `examples/archetype_system_demo.py` for complete integration example.

## Next Steps

1. Train vampire + zombie adapters
2. Test with evaluation harness
3. Deploy to vLLM server
4. Validate with 100+ concurrent NPCs

---

**Status**: Phase 1 infrastructure complete, ready for training

