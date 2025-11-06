# Storyteller Enhanced Requirements
**Project**: "The Body Broker" - AI-Driven Gaming Core  
**Date**: January 29, 2025  
**Status**: New Requirements - Pending Implementation  
**Source**: User Requirements (10 Core Rules)

---

## TABLE OF CONTENTS

1. [Content Balance & Centered Approach](#1-content-balance--centered-approach)
2. [Plot Coherence & Navigation](#2-plot-coherence--navigation)
3. [Age-Appropriate Content with User Controls](#3-age-appropriate-content-with-user-controls)
4. [Engagement & Variety](#4-engagement--variety)
5. [Save/Continuation System](#5-savecontinuation-system)
6. [Streaming & Content Creator Features](#6-streaming--content-creator-features)
7. [Splash Page & Marketing](#7-splash-page--marketing)
8. [User Agreement & Legal Protection](#8-user-agreement--legal-protection)
9. [High-End Marketing Website](#9-high-end-marketing-website)
10. [Admin Dashboard & Expert System](#10-admin-dashboard--expert-system)

---

## 1. CONTENT BALANCE & CENTERED APPROACH

### Requirement Overview
The storyteller system must maintain a balanced, centered approach to content generation, avoiding extreme political or ideological positions while allowing natural character diversity.

### Core Rules

#### 1.1 Political/Ideological Balance
- **NEVER** flood the game with DEI/Woke messaging or forced diversity
- **NEVER** include excessive religious preaching or far-right ideology
- **ALLOW** natural character diversity when it serves the story
- **ALLOW** player choices that reflect their preferences (including LGBTQ+ choices if player selects them)
- **MAINTAIN** a centrist, story-first approach

#### 1.2 Character Representation
- Characters should reflect natural diversity without forced messaging
- LGBTQ+ characters can exist if:
  - Player makes choices that lead to such relationships
  - Character background naturally supports it
  - It serves the narrative (not forced)
- Religious elements can exist if:
  - They serve the world-building
  - They're not preachy or forced
  - They respect player agency

#### 1.3 Content Generation Guidelines
- Storyteller must avoid:
  - Political lectures or messaging
  - Forced diversity quotas
  - Religious proselytizing
  - Extreme ideological positions
- Storyteller should:
  - Focus on story and gameplay
  - Allow natural character development
  - Respect player choices
  - Maintain narrative coherence

### Technical Implementation

#### 1.4 Storyteller Prompt Engineering
```python
CONTENT_BALANCE_PROMPT = """
You are a storyteller for an immersive gaming experience. Your role is to create engaging narratives that:

1. Focus on story, gameplay, and player agency
2. Avoid political messaging or ideological extremes
3. Allow natural character diversity when it serves the narrative
4. Respect player choices and preferences
5. Maintain narrative coherence and immersion

DO NOT:
- Include forced diversity messaging
- Include religious preaching
- Include political lectures
- Force ideological positions

DO:
- Create compelling characters that serve the story
- Allow player choices to shape relationships
- Maintain balanced, story-first approach
- Focus on engagement and gameplay
"""
```

#### 1.5 Content Filtering System
- Pre-generation filter: Check prompts for extreme content
- Post-generation filter: Validate output against balance rules
- Player preference integration: Respect player-selected content preferences
- Dynamic adjustment: Learn from player feedback

### Integration Points
- **Storyteller Service**: Core content generation
- **Moderation Service**: Content filtering and validation
- **Player Settings**: User preferences for content types
- **Learning Service**: Feedback loop for content balance

---

## 2. PLOT COHERENCE & NAVIGATION

### Requirement Overview
The storyteller must maintain clear plot progression and prevent players from getting lost or confused about objectives.

### Core Rules

#### 2.1 Main Plot Maintenance
- **ALWAYS** maintain clear main plot objectives
- **NEVER** let side quests obscure main story
- **PROVIDE** clear objectives and next steps
- **ENSURE** players always know what to do next

#### 2.2 Navigation Assistance
- **REQUIRED**: Quest log/journal system
- **REQUIRED**: Companion NPC guidance
- **OPTIONAL**: Visual indicators (light/dark highlighting)
- **OPTIONAL**: Map markers and waypoints
- **OPTIONAL**: Audio cues for important locations

#### 2.3 Side Quest Management
- Side quests are encouraged but must not interfere with main plot
- Side quests should:
  - Be clearly marked as optional
  - Not block main plot progression
  - Provide clear objectives
  - Be completable or abandonable at any time

### Technical Implementation

#### 2.4 Quest System Architecture
```python
class QuestSystem:
    def __init__(self):
        self.main_quests = []  # Priority queue
        self.side_quests = []  # Optional queue
        self.active_quest = None
        self.quest_log = QuestLog()
        self.companion_npc = CompanionNPC()
    
    def update_main_plot(self, player_state):
        """Ensure main plot is always clear"""
        if not self.active_quest or self.active_quest.is_complete():
            self.active_quest = self.get_next_main_quest()
            self.notify_player(self.active_quest)
            self.companion_npc.guide_player(self.active_quest)
    
    def add_side_quest(self, quest):
        """Add side quest without interfering with main plot"""
        self.side_quests.append(quest)
        self.quest_log.add_optional(quest)
```

#### 2.5 Navigation Assistance Systems

**Quest Log/Journal:**
- Persistent quest tracking
- Clear objective descriptions
- Progress indicators
- Next step highlighting
- Searchable/filterable interface

**Companion NPC:**
- Context-aware guidance
- Proactive hints when player is stuck
- Optional detailed explanations
- Can be dismissed but remains available

**Visual Indicators:**
- Light/dark highlighting for important locations
- Glowing objects for quest items
- Path highlighting for navigation
- Color-coded quest markers

**Audio Cues:**
- Ambient sounds for important locations
- Voice cues from companion NPC
- Musical themes for quest types
- Spatial audio for direction

### Integration Points
- **Storyteller Service**: Generates quest objectives
- **Game Engine**: Renders visual/audio indicators
- **State Management**: Tracks quest progress
- **UI System**: Displays quest log and navigation aids

---

## 3. AGE-APPROPRIATE CONTENT WITH USER CONTROLS

### Requirement Overview
The system must provide age-appropriate content filtering with granular user controls for violence, gore, sex, and other mature content.

### Core Rules

#### 3.1 Age Verification
- **REQUIRED**: Age verification during account creation
- **REQUIRED**: Age-based default content settings
- **OPTIONAL**: Parental controls for accounts under 18
- **REQUIRED**: Persistent age verification for sensitive content

#### 3.2 Content Rating System
- **E (Everyone)**: No violence, gore, or sexual content
- **T (Teen)**: Mild violence, no gore, no sexual content
- **M (Mature 17+)**: Violence, gore, sexual content allowed
- **AO (Adults Only 18+)**: Full content access

#### 3.3 Granular Content Controls
Players 18+ can adjust:
- **Violence Level**: None, Mild, Moderate, Extreme
- **Gore Level**: None, Mild, Moderate, Extreme
- **Sexual Content**: None, Implied, Explicit
- **Language**: None, Mild, Strong
- **Drug/Alcohol**: None, Mild, Explicit

### Technical Implementation

#### 3.4 Content Rating System
```python
class ContentRatingSystem:
    def __init__(self):
        self.age_verification = AgeVerification()
        self.content_filters = ContentFilters()
        self.user_preferences = UserPreferences()
    
    def verify_age(self, user_id):
        """Verify user age and set defaults"""
        age = self.age_verification.get_age(user_id)
        if age < 13:
            return ContentRating.EVERYONE
        elif age < 17:
            return ContentRating.TEEN
        elif age < 18:
            return ContentRating.MATURE
        else:
            return ContentRating.ADULTS_ONLY
    
    def filter_content(self, content, user_id):
        """Filter content based on user preferences"""
        rating = self.get_user_rating(user_id)
        preferences = self.user_preferences.get(user_id)
        
        # Apply age-based filters
        if rating == ContentRating.EVERYONE:
            content = self.remove_violence(content)
            content = self.remove_gore(content)
            content = self.remove_sexual_content(content)
        
        # Apply user preferences (18+ only)
        if rating >= ContentRating.ADULTS_ONLY:
            if preferences.violence_level < content.violence_level:
                content = self.reduce_violence(content, preferences.violence_level)
            if preferences.gore_level < content.gore_level:
                content = self.reduce_gore(content, preferences.gore_level)
            if preferences.sexual_content < content.sexual_content:
                content = self.filter_sexual_content(content, preferences.sexual_content)
        
        return content
```

#### 3.5 Storyteller Content Generation
- Storyteller generates content at maximum rating
- Content filtering system applies user preferences
- Dynamic content adjustment based on settings
- Fallback content for filtered scenarios

### Integration Points
- **Storyteller Service**: Generates content (filtered post-generation)
- **Moderation Service**: Validates content against ratings
- **User Settings Service**: Manages user preferences
- **Game Engine**: Applies visual/audio filters

---

## 4. ENGAGEMENT & VARIETY

### Requirement Overview
The storyteller must maintain constant engagement through variety, unpredictability, and emotional range.

### Core Rules

#### 4.1 Engagement Types
- **Jumpscares**: Sudden surprises and scares
- **Drama**: Emotional tension and conflict
- **Dread**: Building suspense and fear
- **Victory**: Triumph and success moments
- **Escapes**: Narrow escapes and close calls
- **Empire Building**: Long-term progression and growth

#### 4.2 Variety Requirements
- **NEVER** be boring, trite, or predictable
- **ALWAYS** maintain player interest
- **ROTATE** engagement types to prevent fatigue
- **BALANCE** intensity levels (high/low tension)

#### 4.3 Engagement Patterns
- Mix of short-term and long-term goals
- Varying intensity levels
- Unpredictable events and outcomes
- Player agency in engagement type selection

### Technical Implementation

#### 4.4 Engagement System
```python
class EngagementSystem:
    def __init__(self):
        self.engagement_types = [
            EngagementType.JUMPSCARE,
            EngagementType.DRAMA,
            EngagementType.DREAD,
            EngagementType.VICTORY,
            EngagementType.ESCAPE,
            EngagementType.EMPIRE_BUILDING
        ]
        self.engagement_history = []
        self.intensity_tracker = IntensityTracker()
    
    def generate_engagement(self, player_state, context):
        """Generate appropriate engagement based on context"""
        # Avoid recent engagement types
        recent_types = self.get_recent_types(5)
        available_types = [t for t in self.engagement_types if t not in recent_types]
        
        # Select based on context and player state
        engagement_type = self.select_engagement_type(
            available_types, player_state, context
        )
        
        # Generate engagement event
        event = self.storyteller.generate_engagement(
            engagement_type, player_state, context
        )
        
        # Track engagement
        self.engagement_history.append(event)
        self.intensity_tracker.update(event.intensity)
        
        return event
    
    def maintain_balance(self):
        """Ensure engagement doesn't become monotonous"""
        if self.intensity_tracker.is_too_high():
            return EngagementType.VICTORY  # Lower intensity
        elif self.intensity_tracker.is_too_low():
            return EngagementType.JUMPSCARE  # Raise intensity
        else:
            return None  # Maintain current level
```

### Integration Points
- **Storyteller Service**: Generates engagement events
- **Game Engine**: Executes engagement events
- **State Management**: Tracks engagement history
- **Learning Service**: Learns from player engagement patterns

---

## 5. SAVE/CONTINUATION SYSTEM

### Requirement Overview
Players must be able to save and continue their game at any time, with the world continuing to evolve during downtime.

### Core Rules

#### 5.1 Save System
- **REQUIRED**: Save at any time (no checkpoints only)
- **REQUIRED**: Multiple save slots
- **REQUIRED**: Auto-save functionality
- **REQUIRED**: Cloud save synchronization

#### 5.2 World Continuity
- World continues to evolve during player absence
- Changes are logical and story-consistent
- Player is not penalized for taking breaks
- World state is preserved accurately

#### 5.3 Continuation Mechanism
- **Sleep System**: Player character "sleeps" in safe location
- **Magical Cocoon**: Player character preserved in stasis
- **Safe Haven**: Player character rests in protected area
- **Relic System**: Special item preserves player state

### Technical Implementation

#### 5.4 Save System Architecture
```python
class SaveSystem:
    def __init__(self):
        self.save_storage = SaveStorage()  # PostgreSQL + S3
        self.world_state = WorldState()
        self.continuation_manager = ContinuationManager()
    
    def save_game(self, player_id, save_slot=None):
        """Save game state"""
        game_state = {
            'player_state': self.get_player_state(player_id),
            'world_state': self.world_state.get_snapshot(),
            'quest_progress': self.get_quest_progress(player_id),
            'inventory': self.get_inventory(player_id),
            'timestamp': datetime.now(),
            'continuation_type': self.continuation_manager.get_type(player_id)
        }
        
        if save_slot:
            self.save_storage.save_to_slot(player_id, save_slot, game_state)
        else:
            self.save_storage.auto_save(player_id, game_state)
        
        # Initiate continuation mechanism
        self.continuation_manager.initiate(player_id, game_state)
    
    def load_game(self, player_id, save_slot=None):
        """Load game state"""
        if save_slot:
            game_state = self.save_storage.load_from_slot(player_id, save_slot)
        else:
            game_state = self.save_storage.load_latest(player_id)
        
        # Calculate world evolution during absence
        absence_duration = datetime.now() - game_state['timestamp']
        evolved_world_state = self.world_state.evolve(
            game_state['world_state'], absence_duration
        )
        
        # Restore player state
        self.restore_player_state(player_id, game_state['player_state'])
        self.restore_world_state(evolved_world_state)
        self.restore_quest_progress(player_id, game_state['quest_progress'])
        
        return game_state
```

#### 5.5 World Evolution System
- Time-based world changes
- Story-consistent evolution
- No player penalty for absence
- Seamless transition on return

### Integration Points
- **State Management Service**: Stores save data
- **Storyteller Service**: Generates world evolution
- **Game Engine**: Handles save/load UI
- **Cloud Storage**: Synchronizes saves across devices

---

## 6. STREAMING & CONTENT CREATOR FEATURES

### Requirement Overview
The system must provide enhanced streaming capabilities for content creators, including multi-angle views and dual microphone support.

### Core Rules

#### 6.1 Enhanced Streaming
- **REQUIRED**: Multi-angle camera views during battles
- **REQUIRED**: Out-of-sight character scenes (non-spoiler)
- **REQUIRED**: Dynamic camera switching
- **REQUIRED**: High-quality video output

#### 6.2 Streamer Subscription Mode
- **REQUIRED**: Dual microphone support (game mic + stream mic)
- **REQUIRED**: Separate audio channels
- **REQUIRED**: Premium pricing tier
- **REQUIRED**: Enhanced streaming features

#### 6.3 Content Protection
- **NEVER** show spoiler content
- **NEVER** reveal plot-critical information
- **ALWAYS** respect player privacy settings
- **ALWAYS** maintain narrative integrity

### Technical Implementation

#### 6.4 Streaming System Architecture
```python
class StreamingSystem:
    def __init__(self):
        self.camera_system = MultiAngleCameraSystem()
        self.audio_system = DualMicrophoneSystem()
        self.content_filter = StreamingContentFilter()
        self.video_encoder = VideoEncoder()
    
    def start_stream(self, user_id, stream_config):
        """Start enhanced streaming session"""
        # Initialize multi-angle cameras
        cameras = self.camera_system.setup_cameras(
            primary_view=stream_config.primary_view,
            battle_angles=stream_config.battle_angles,
            scene_angles=stream_config.scene_angles
        )
        
        # Setup dual microphones
        if stream_config.streamer_mode:
            self.audio_system.setup_dual_mics(
                game_mic=stream_config.game_mic,
                stream_mic=stream_config.stream_mic
            )
        
        # Start streaming
        stream = self.video_encoder.start_stream(
            cameras=cameras,
            audio=self.audio_system.get_audio_channels(),
            quality=stream_config.quality,
            platform=stream_config.platform
        )
        
        return stream
    
    def get_battle_angles(self, battle_state):
        """Get multiple camera angles for battle"""
        angles = [
            self.camera_system.player_perspective(),
            self.camera_system.enemy_perspective(),
            self.camera_system.overhead_view(),
            self.camera_system.cinematic_angle()
        ]
        
        # Filter out spoiler content
        filtered_angles = [
            angle for angle in angles
            if not self.content_filter.is_spoiler(angle, battle_state)
        ]
        
        return filtered_angles
```

### Integration Points
- **Game Engine**: Provides camera and audio systems
- **Streaming Service**: Handles video encoding and delivery
- **Content Filter**: Validates streaming content
- **Payment Service**: Manages streamer subscription

---

## 7. SPLASH PAGE & MARKETING

### Requirement Overview
A compelling splash page is required for Steam and PC distribution to showcase the game at launch.

### Core Rules

#### 7.1 Splash Page Requirements
- **REQUIRED**: Compelling visual design
- **REQUIRED**: Gameplay highlights
- **REQUIRED**: Story teasers
- **REQUIRED**: Unique selling points
- **REQUIRED**: Call-to-action (download/play)

#### 7.2 Platform Distribution
- **PRIMARY**: Steam platform
- **SECONDARY**: PC direct download
- **FUTURE**: Other platforms (TBD)

#### 7.3 Content Requirements
- Showcase game uniqueness
- Highlight AI-driven features
- Display immersive gameplay
- Create excitement and anticipation

### Technical Implementation

#### 7.4 Splash Page Architecture
```python
class SplashPageSystem:
    def __init__(self):
        self.media_assets = MediaAssetManager()
        self.content_curator = ContentCurator()
        self.analytics = SplashPageAnalytics()
    
    def generate_splash_content(self):
        """Generate dynamic splash page content"""
        content = {
            'hero_video': self.media_assets.get_hero_video(),
            'gameplay_highlights': self.content_curator.get_highlights(),
            'story_teasers': self.content_curator.get_teasers(),
            'unique_features': self.get_unique_selling_points(),
            'cta_button': self.generate_cta()
        }
        
        return content
    
    def get_unique_selling_points(self):
        """Get game's unique features"""
        return [
            "AI-Driven Dynamic Storytelling",
            "Infinite Narrative Possibilities",
            "Player Choice Shapes Reality",
            "Unprecedented Immersion",
            "Real-Time World Evolution"
        ]
```

### Integration Points
- **Marketing Website**: Hosts splash page
- **Media Asset System**: Provides game footage
- **Analytics Service**: Tracks engagement
- **Distribution System**: Handles downloads

---

## 8. USER AGREEMENT & LEGAL PROTECTION

### Requirement Overview
Comprehensive user agreement covering US, EU, and Chinese legal requirements with maximum legal protection.

### Core Rules

#### 8.1 Legal Coverage
- **REQUIRED**: US legal compliance
- **REQUIRED**: EU GDPR compliance
- **REQUIRED**: Chinese legal compliance
- **REQUIRED**: Maximum liability protection
- **REQUIRED**: Intellectual property protection

#### 8.2 Agreement Structure
- **FULL AGREEMENT**: Comprehensive legal document
- **IN-GAME AGREEMENT**: Concise version with key points
- **REQUIRED**: Manual checkbox acceptance
- **REQUIRED**: Form submission confirmation

#### 8.3 Key Protections
- Liability limitations
- Intellectual property rights
- User data protection
- Content moderation rights
- Service termination rights

### Technical Implementation

#### 8.4 User Agreement System
```python
class UserAgreementSystem:
    def __init__(self):
        self.full_agreement = LegalDocumentManager()
        self.in_game_agreement = InGameAgreementManager()
        self.acceptance_tracker = AcceptanceTracker()
    
    def present_agreement(self, user_id, locale='en'):
        """Present user agreement based on locale"""
        agreement = self.in_game_agreement.get_concise_version(locale)
        
        # Key points from full agreement
        key_points = [
            "By playing this game, you agree to our terms of service",
            "You grant us rights to user-generated content",
            "We reserve the right to moderate content",
            "Service may be terminated for violations",
            "See full agreement for complete terms"
        ]
        
        return {
            'agreement_text': agreement,
            'key_points': key_points,
            'full_agreement_link': self.full_agreement.get_link(locale),
            'requires_checkbox': True,
            'requires_submission': True
        }
    
    def accept_agreement(self, user_id, agreement_version, ip_address):
        """Record agreement acceptance"""
        acceptance = {
            'user_id': user_id,
            'agreement_version': agreement_version,
            'timestamp': datetime.now(),
            'ip_address': ip_address,
            'locale': self.get_user_locale(user_id)
        }
        
        self.acceptance_tracker.record(acceptance)
        
        # Update user status
        self.update_user_agreement_status(user_id, True)
```

### Integration Points
- **Legal Service**: Manages agreement documents
- **User Service**: Tracks acceptance status
- **Authentication Service**: Enforces agreement requirement
- **Compliance Service**: Validates legal requirements

---

## 9. HIGH-END MARKETING WEBSITE

### Requirement Overview
A polished, immersive marketing website that showcases the game and drives downloads.

### Core Rules

#### 9.1 Website Requirements
- **REQUIRED**: Polished, engaging design
- **REQUIRED**: Immersive experience
- **REQUIRED**: React-based with modern features
- **REQUIRED**: Morphing backgrounds and effects
- **REQUIRED**: Readable, accessible content

#### 9.2 Content Requirements
- Simulated gameplay cutscenes
- Story teasers
- Unique feature highlights
- Download/installer access
- Activation code system (beta testing)

#### 9.3 Design Requirements
- Light/dark themes
- Immersive visuals
- Smooth animations
- Responsive design
- Performance optimized

### Technical Implementation

#### 9.4 Marketing Website Architecture
```python
class MarketingWebsite:
    def __init__(self):
        self.media_manager = MediaAssetManager()
        self.content_curator = ContentCurator()
        self.activation_system = ActivationCodeSystem()
        self.download_manager = DownloadManager()
    
    def generate_homepage(self):
        """Generate immersive homepage"""
        return {
            'hero_section': {
                'video': self.media_manager.get_hero_video(),
                'title': 'The Body Broker',
                'subtitle': 'AI-Driven Immersive Gaming',
                'cta': 'Download Now'
            },
            'gameplay_section': {
                'cutscenes': self.media_manager.get_gameplay_cutscenes(),
                'highlights': self.content_curator.get_highlights()
            },
            'story_section': {
                'teasers': self.content_curator.get_story_teasers(),
                'narrative_preview': self.get_narrative_preview()
            },
            'features_section': {
                'unique_features': self.get_unique_features(),
                'ai_system': self.get_ai_system_info()
            },
            'download_section': {
                'activation_required': True,
                'installer_link': self.download_manager.get_installer_link()
            }
        }
    
    def handle_download_request(self, user_id, activation_code):
        """Handle download request with activation code"""
        if self.activation_system.validate(activation_code):
            download_link = self.download_manager.generate_download_link(
                user_id, activation_code
            )
            return {
                'success': True,
                'download_link': download_link,
                'installer_size': self.download_manager.get_installer_size()
            }
        else:
            return {
                'success': False,
                'error': 'Invalid activation code'
            }
```

### Integration Points
- **Frontend (React)**: Marketing website UI
- **Media Asset System**: Provides game footage
- **Activation System**: Validates beta codes
- **Download System**: Manages installer distribution

---

## 10. ADMIN DASHBOARD & EXPERT SYSTEM

### Requirement Overview
Comprehensive admin dashboard with system monitoring, user management, and AI-powered expert system.

### Core Rules

#### 10.1 Admin Dashboard Features
- **REQUIRED**: System performance metrics (overall, per-user, specific user)
- **REQUIRED**: Cost analysis section
- **REQUIRED**: System stability monitoring
- **REQUIRED**: User complaint handling
- **REQUIRED**: User suggestion submission system

#### 10.2 Expert System Requirements
- **REQUIRED**: Three-model expert system
- **REQUIRED**: Tooled throughout admin section
- **REQUIRED**: On-demand issue resolution
- **REQUIRED**: User communication with learning
- **REQUIRED**: Persona adoption and AI detection prevention

#### 10.3 Expert System Capabilities
- Automated issue resolution
- User communication with human-like responses
- Learning from admin feedback
- Scaling support without large team
- Continuous improvement over time

### Technical Implementation

#### 10.4 Admin Dashboard Architecture
```python
class AdminDashboard:
    def __init__(self):
        self.metrics_system = SystemMetricsSystem()
        self.cost_analyzer = CostAnalyzer()
        self.stability_monitor = StabilityMonitor()
        self.user_support = UserSupportSystem()
        self.expert_system = AdminExpertSystem()
    
    def get_system_metrics(self, scope='overall', user_id=None):
        """Get system performance metrics"""
        if scope == 'overall':
            return self.metrics_system.get_overall_metrics()
        elif scope == 'per_user':
            return self.metrics_system.get_per_user_metrics()
        elif scope == 'specific_user' and user_id:
            return self.metrics_system.get_user_metrics(user_id)
    
    def get_cost_analysis(self, scope='overall', user_id=None):
        """Get cost analysis"""
        if scope == 'overall':
            return self.cost_analyzer.get_overall_costs()
        elif scope == 'per_user':
            return self.cost_analyzer.get_per_user_costs()
        elif scope == 'specific_user' and user_id:
            return self.cost_analyzer.get_user_costs(user_id)
    
    def monitor_stability(self):
        """Monitor system stability"""
        return {
            'bottlenecks': self.stability_monitor.detect_bottlenecks(),
            'failures': self.stability_monitor.detect_failures(),
            'performance_issues': self.stability_monitor.detect_performance_issues(),
            'recommendations': self.stability_monitor.get_recommendations()
        }
    
    def handle_user_complaint(self, complaint_id):
        """Handle user complaint with expert system"""
        complaint = self.user_support.get_complaint(complaint_id)
        
        # Expert system analyzes and responds
        response = self.expert_system.analyze_complaint(complaint)
        
        # Admin can review and approve/modify
        return {
            'complaint': complaint,
            'suggested_response': response,
            'admin_approval_required': True
        }
```

#### 10.5 Expert System Architecture
```python
class AdminExpertSystem:
    def __init__(self):
        self.model1 = ExpertModel1()  # Primary expert
        self.model2 = ExpertModel2()  # Secondary expert
        self.model3 = ExpertModel3()  # Tertiary expert
        self.learning_system = LearningSystem()
        self.persona_manager = PersonaManager()
    
    def analyze_issue(self, issue, context):
        """Analyze issue using three-model system"""
        # Each model provides analysis
        analysis1 = self.model1.analyze(issue, context)
        analysis2 = self.model2.analyze(issue, context)
        analysis3 = self.model3.analyze(issue, context)
        
        # Consensus building
        consensus = self.build_consensus([analysis1, analysis2, analysis3])
        
        # Generate response
        response = self.generate_response(consensus, context)
        
        return response
    
    def communicate_with_user(self, user_id, message, admin_feedback=None):
        """Communicate with user using expert system"""
        # Get persona for communication
        persona = self.persona_manager.get_persona(user_id)
        
        # Generate human-like response
        response = self.generate_human_like_response(
            message, persona, admin_feedback
        )
        
        # Learn from admin feedback
        if admin_feedback:
            self.learning_system.learn_from_feedback(
                message, response, admin_feedback
            )
        
        return response
    
    def prevent_ai_detection(self, response):
        """Ensure response doesn't appear AI-generated"""
        # Apply techniques to make response more human-like
        response = self.add_natural_variations(response)
        response = self.add_personality_traits(response)
        response = self.add_contextual_references(response)
        
        return response
```

### Integration Points
- **Admin Dashboard (React)**: UI for admin interface
- **Metrics Service**: Provides system metrics
- **Cost Analysis Service**: Calculates costs
- **Stability Monitor**: Monitors system health
- **Expert System Service**: AI-powered assistance
- **User Support Service**: Manages complaints and suggestions

---

## INTEGRATION SUMMARY

### Service Integration Points

1. **Storyteller Service**
   - Content balance filtering
   - Plot coherence maintenance
   - Engagement generation
   - World evolution during saves
   - **NEW**: Hybrid Director + LLM architecture
   - **NEW**: Narrative State Database (graph DB)
   - **NEW**: RAG system for plot coherence

2. **Moderation Service**
   - Content rating enforcement
   - Age-appropriate filtering
   - Streaming content validation
   - **NEW**: Multi-layer moderation stack (prompt + post-gen + heuristics)
   - **NEW**: Fallback mechanism for filtered content

3. **User Settings Service**
   - Age verification
   - Content preference management
   - Save/load preferences
   - **NEW**: Platform parental controls integration

4. **Game Engine (UE5)**
   - Quest log/journal UI
   - Navigation assistance rendering
   - Save/load UI
   - Streaming camera system
   - **NEW**: Event bus integration for world state changes

5. **Marketing Website (React)**
   - Splash page
   - Download system
   - Activation code validation
   - **NEW**: WCAG accessibility compliance
   - **NEW**: User persona-based content

6. **Admin Dashboard (React)**
   - System monitoring
   - User management
   - Expert system interface
   - **NEW**: Real-time observability platform
   - **NEW**: AI performance metrics (p50, p90, p99 latency)
   - **NEW**: Narrative health metrics

7. **Streaming Service**
   - Multi-angle camera system
   - Dual microphone support
   - Video encoding and delivery
   - **NEW**: Webhook API for events
   - **NEW**: Viewer interaction API

8. **Legal/Compliance Service**
   - User agreement management
   - Legal document storage
   - Acceptance tracking
   - **NEW**: GDPR/CCPA data management
   - **NEW**: AI-generated content ownership clarification

### Critical Technical Additions (Based on Model Feedback)

#### AI Architecture Definition
- **Hybrid Model (Recommended)**: Director AI (rules-based) + LLM (creative tool)
- **Narrative Memory System**: Vector DB + Structured Narrative State Database
- **RAG System**: Retrieval-Augmented Generation for plot coherence
- **Deterministic Flags**: Critical plot points stored as non-negotiable facts

#### Performance & Latency
- **SLOs**: 95% of dialogue responses < 800ms
- **Caching Strategy**: Response caching for common interactions
- **Model Selection**: Tier-based model selection for cost optimization

#### Data & Telemetry
- **Telemetry Pipeline**: Player choices, AI responses, performance metrics
- **Cost Monitoring**: Per-user, per-hour cost tracking
- **Engagement Analytics**: Session length, choice distribution, progression funnels

#### Human-in-the-Loop
- **Content Pipeline**: Designer tools for steering AI
- **Review Workflow**: Approve/reject AI-generated content
- **Expert System Learning**: Learn from admin feedback on responses

---

## IMPLEMENTATION PRIORITY

### Phase 1: Core Storyteller Rules (Weeks 1-4)
1. Content Balance & Centered Approach
2. Plot Coherence & Navigation
3. Age-Appropriate Content with User Controls
4. Engagement & Variety

### Phase 2: Player Experience (Weeks 5-8)
5. Save/Continuation System
6. Streaming & Content Creator Features

### Phase 3: Marketing & Legal (Weeks 9-12)
7. Splash Page & Marketing
8. User Agreement & Legal Protection
9. High-End Marketing Website

### Phase 4: Admin & Operations (Weeks 13-16)
10. Admin Dashboard & Expert System

---

**END OF REQUIREMENTS DOCUMENT**

