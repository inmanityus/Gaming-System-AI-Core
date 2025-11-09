# 🧬 Expanded Archetype System Roadmap

**Date**: 2025-11-09  
**Story Teller Consultation**: Gemini 2.5 Pro  
**Status**: Complete roadmap for 20+ archetype implementation

---

## 🎯 EXECUTIVE SUMMARY

**Scope Expanded**: From 5 archetypes → 20+ archetypes across two worlds

**Architecture Validated**: Shared base + LoRA adapters scales to expanded scope

**Memory Budget**: 
- Current (5 archetypes): ~15GB (fits g5.2xlarge 24GB)
- Expanded (20 archetypes): ~45-50GB (requires 3× g5.2xlarge OR 1× g5.8xlarge)

---

## 📋 COMPLETE ARCHETYPE LIST

### **PHASE 1: PILOT** (Current - Weeks 1-10)
1. ✅ **Vampire** - Gold-tier dialogue, social dynamics (IMPLEMENTING)
2. ✅ **Zombie** - Scale testing, horde behaviors (IMPLEMENTING)

### **PHASE 2: GHOSTS & SPIRITS** (Weeks 11-15)
3. **Hungry Ghost** - Bronze-tier, ambient audio only, basic melee
4. **Weeping Wraith** - Silver-tier, limited speech, AoE sorrow debuff
5. **Poltergeist** - Bronze-tier, ambient, environmental hazards
6. **Helpful Spirit** - Gold-tier, full dialogue, quest giver

### **PHASE 3: UNDEAD EXPANSION** (Weeks 16-22)
7. **Ghoul** - Silver-tier, limited dialogue, fast/agile/climbing
8. **Skeleton** - Bronze-tier, ambient, resistance mechanics
9. **Wight** - Gold-tier, commander dialogue, weapon use, raises dead

### **PHASE 4: FAE REALM** (Weeks 23-32)
10. **Seelie Fae** (Good) - Gold-tier, complex riddles/bargains
11. **Unseelie Fae** (Bad) - Gold-tier, cruel wordplay
12. **Pixie** - Silver-tier, trickster dialogue
13. **Redcap Goblin** - Bronze-tier, guttural speech
14. **Boggart** - Bronze-tier, ambient sounds

### **PHASE 5: DEMONIC HIERARCHY** (Weeks 33-42)
15. **Imp** - Silver-tier, limited taunts, ranged fire
16. **Hellhound** - Bronze-tier, growls/howls only
17. **Envy Demon** - Gold-tier, full manipulation dialogue
18. **Higher Demon** (Boss) - Gold-tier, bargaining/temptation

### **PHASE 6: UNIQUE MONSTERS** (Weeks 43-48)
19. **Husk-Abomination** - Bronze-tier, ambient horror
20. **Changeling Amalgam** - Bronze-tier, distorted speech
21. **Techno-Geist** - Gold-tier, digital voice, glitches

### **FUTURE PHASES**: Civilized Races (Elves, Trolls, Orcs, Dwarfs, etc.)

---

## 🏗️ ARCHITECTURE SCALING

### Memory Requirements by Phase:

**Phase 1 (Pilot)**: 2 archetypes × 7 adapters × 100MB = **1.4GB adapters**
- Base model (7B, 4-bit): 3.5GB
- Total: ~5GB (fits easily in 24GB)

**Phase 2-3 (Ghosts + Undead)**: 7 archetypes × 7 adapters = **4.9GB adapters**
- Total: ~8.4GB (still fits g5.2xlarge)

**Phase 4-5 (Fae + Demons)**: 14 archetypes × 7 adapters = **9.8GB adapters**
- Total: ~13.3GB (fits g5.2xlarge)

**Phase 6+ (20+ archetypes)**: 20+ archetypes = **14GB+ adapters**
- Total: ~17.5GB+
- **Requires**: g5.4xlarge (48GB) OR multi-server deployment

### Tier-Based Optimization:

**Gold-Tier Archetypes** (Full 7 adapters, ~700MB each):
- Vampire, Wight, Helpful Spirit, Seelie/Unseelie Fae, Envy Demon, Higher Demon, Techno-Geist
- **Total**: ~8 Gold-tier × 700MB = ~5.6GB

**Silver-Tier Archetypes** (Shared bases, ~400MB each):
- Weeping Wraith, Ghoul, Pixie, Imp
- **Total**: ~4 Silver-tier × 400MB = ~1.6GB

**Bronze-Tier Archetypes** (Minimal customization, ~200MB each):
- Zombie, Hungry Ghost, Poltergeist, Skeleton, Redcap, Boggart, Hellhound, Husks
- **Total**: ~8 Bronze-tier × 200MB = ~1.6GB

**Optimized Total**: 5.6GB + 1.6GB + 1.6GB = **~8.8GB adapters** (fits g5.2xlarge!)

---

## 🎤 DIALOGUE REQUIREMENTS

### **Gold-Tier** (Full Voice System):
- Complex personalities
- Rich dialogue trees
- Social dynamics
- Emotional nuance
- **Voice**: Anatomically-accurate TTS per archetype
- **Facial**: Full FACS → blendshapes
- **Examples**: Vampire, Fae, Wights, Helpful Spirits, Demons

### **Silver-Tier** (Limited Voice):
- Basic personality
- Short phrases
- Simple reactions
- **Voice**: Simplified TTS or voice clips
- **Facial**: Basic expressions
- **Examples**: Wraiths, Ghouls, Pixies, Imps

### **Bronze-Tier** (Ambient Only):
- No dialogue
- Environmental audio (moans, shrieks, roars)
- Procedural sound generation
- **Voice**: Sound effects only
- **Facial**: Minimal or none
- **Examples**: Zombies, Skeletons, Hungry Ghosts, Hellhounds

---

## 📊 TRAINING DATA ESTIMATES

### Per Archetype (7 Adapters):

**Gold-Tier**: ~1,500-2,000 examples per archetype
- **Vampire**: 1,785 ✅ (complete)
- **Wight**: ~1,500 (needs extraction)
- **Fae**: ~2,000 (high dialogue complexity)
- **Demons**: ~1,800 (bargaining, manipulation)

**Silver-Tier**: ~600-1,000 examples per archetype
- **Ghoul**: ~800
- **Wraith**: ~600
- **Pixie**: ~1,000

**Bronze-Tier**: ~400-600 examples per archetype
- **Zombie**: 686 ✅ (complete)
- **Skeleton**: ~400
- **Hungry Ghost**: ~500

**Total Estimate**: ~18,000-25,000 training examples for full expansion

---

## 🔧 INFRASTRUCTURE SCALING

### Current (Pilot):
- 1× g5.2xlarge: ~$880/mo
- Handles: 100-500 concurrent NPCs (mixed tiers)

### Phase 2-3 (7 archetypes):
- 2× g5.2xlarge: ~$1,760/mo
- Handles: 500-1,000 concurrent NPCs

### Phase 4-5 (14 archetypes):
- 3-4× g5.2xlarge: ~$2,640-3,520/mo
- Handles: 1,000-2,000 concurrent NPCs

### Full Expansion (20+ archetypes):
- 5-7× g5.2xlarge OR 2× g5.8xlarge: ~$4,400-6,160/mo
- Handles: 2,000-5,000 concurrent NPCs (region-wide)

### With Spot Instances (70% savings):
- Full expansion: ~$1,300-1,850/mo

---

## 🚀 IMMEDIATE NEXT STEPS

1. **Complete Vampire + Zombie Pilot** (Weeks 1-10)
   - Train 14 adapters (7 vampire + 7 zombie)
   - Test with 100-500 concurrent NPCs
   - Validate 8-10 min conversations (vampire)
   - Validate horde behaviors (zombie)

2. **Begin Ghost Implementation** (Week 11)
   - Extract ghost lore from narrative docs
   - Design 4 ghost sub-types (Hungry, Wraith, Poltergeist, Helpful)
   - Train adapters with tier-based optimization

3. **Update Story Teller Service**
   - Integrate new faction knowledge (AeternaGen, Sombra, Chrome Skulls, Praetorians)
   - Add storyline tracking (The Bleed, Fae Courts, Ghost in Machine)
   - Implement cross-world consistency checks

---

## 📚 KEY DOCUMENTS

1. **This Roadmap**: Expanded archetype system
2. **Story Teller Design**: `docs/narrative/STORYTELLER-EXPANSION-DESIGN.md`
3. **Original Architecture**: `Project-Management/Documentation/Architecture/ARCHETYPE-MODEL-CHAIN-SYSTEM.md`
4. **Phase 1 Complete**: `Project-Management/PHASE-1-PEER-REVIEWED-COMPLETE.md`

---

**Status**: ✅ Roadmap Complete  
**Next**: Complete pilot, begin ghost implementation  
**Timeline**: 48 weeks for full expansion (1 year)

