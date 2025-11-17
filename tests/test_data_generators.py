"""
Test data generators for creating realistic test scenarios.
Generates audio files, localization content, and session data.
"""
import numpy as np
import soundfile as sf
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
import random
from typing import Dict, List, Tuple, Optional, Any


class AudioTestDataGenerator:
    """Generate various types of audio test data."""
    
    @staticmethod
    def generate_clean_speech(
        duration: float = 3.0,
        sample_rate: int = 48000,
        pitch_hz: float = 150
    ) -> Tuple[np.ndarray, int]:
        """Generate clean speech-like audio."""
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Varying pitch to simulate natural speech
        pitch_variation = pitch_hz + 30 * np.sin(2 * np.pi * 0.5 * t)
        
        # Generate harmonics
        signal = np.zeros_like(t)
        for harmonic in range(1, 8):
            amplitude = 1.0 / (harmonic ** 0.8)  # Natural harmonic rolloff
            phase = np.random.random() * 2 * np.pi
            signal += amplitude * np.sin(2 * np.pi * pitch_variation * harmonic * t + phase)
        
        # Add formants
        formants = [
            (700, 100, 0.8),   # F1
            (1220, 150, 0.6),  # F2
            (2600, 200, 0.4),  # F3
            (3500, 250, 0.3)   # F4
        ]
        
        for freq, bandwidth, amplitude in formants:
            # Formant filter simulation
            resonance = np.exp(-bandwidth * t / sample_rate)
            formant_signal = amplitude * np.sin(2 * np.pi * freq * t) * resonance
            signal += formant_signal
        
        # Add slight breathiness
        breathiness = np.random.normal(0, 0.02, signal.shape)
        signal += breathiness
        
        # Normalize
        signal = signal / np.max(np.abs(signal)) * 0.9
        
        return signal, sample_rate
    
    @staticmethod
    def generate_noisy_speech(
        duration: float = 3.0,
        sample_rate: int = 48000,
        snr_db: float = 5.0
    ) -> Tuple[np.ndarray, int]:
        """Generate speech with controlled noise level."""
        # Start with clean speech
        speech, sr = AudioTestDataGenerator.generate_clean_speech(duration, sample_rate)
        
        # Calculate noise level based on SNR
        speech_power = np.mean(speech ** 2)
        noise_power = speech_power / (10 ** (snr_db / 10))
        
        # Generate noise
        noise = np.random.normal(0, np.sqrt(noise_power), speech.shape)
        
        # Mix speech and noise
        noisy_speech = speech + noise
        
        # Normalize to prevent clipping
        max_val = np.max(np.abs(noisy_speech))
        if max_val > 1.0:
            noisy_speech = noisy_speech / max_val * 0.95
        
        return noisy_speech, sample_rate
    
    @staticmethod
    def generate_archetype_voice(
        archetype: str,
        duration: float = 3.0,
        sample_rate: int = 48000
    ) -> Tuple[np.ndarray, int]:
        """Generate voice matching specific archetype characteristics."""
        archetypes = {
            'vampire_alpha': {
                'pitch': 100,
                'pitch_variation': 20,
                'roughness': 0.7,
                'breathiness': 0.3,
                'formant_shift': 0.9
            },
            'human_agent': {
                'pitch': 140,
                'pitch_variation': 40,
                'roughness': 0.3,
                'breathiness': 0.2,
                'formant_shift': 1.0
            },
            'corpse_tender': {
                'pitch': 80,
                'pitch_variation': 10,
                'roughness': 0.9,
                'breathiness': 0.6,
                'formant_shift': 0.8
            }
        }
        
        profile = archetypes.get(archetype, archetypes['human_agent'])
        
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Base pitch with variation
        pitch = profile['pitch'] + profile['pitch_variation'] * np.sin(2 * np.pi * 0.3 * t)
        
        # Generate base voice
        signal = np.zeros_like(t)
        for harmonic in range(1, 10):
            amplitude = 1.0 / (harmonic ** 1.2)
            signal += amplitude * np.sin(2 * np.pi * pitch * harmonic * t)
        
        # Apply formant shift
        formants = [
            700 * profile['formant_shift'],
            1220 * profile['formant_shift'],
            2600 * profile['formant_shift']
        ]
        
        for i, freq in enumerate(formants):
            formant_signal = 0.5 * np.sin(2 * np.pi * freq * t) * np.exp(-0.5 * t)
            signal += formant_signal / (i + 1)
        
        # Add roughness (jitter)
        if profile['roughness'] > 0:
            jitter = np.random.normal(0, profile['roughness'] * 0.01, signal.shape)
            rough_t = t + jitter
            signal = np.interp(t, rough_t[rough_t >= 0], signal[rough_t >= 0])
        
        # Add breathiness
        if profile['breathiness'] > 0:
            breath_noise = np.random.normal(0, profile['breathiness'] * 0.1, signal.shape)
            # High-pass filter simulation for breathy quality
            breath_noise = np.diff(breath_noise, prepend=breath_noise[0])
            signal += breath_noise
        
        # Normalize
        signal = signal / np.max(np.abs(signal)) * 0.85
        
        return signal, sample_rate
    
    @staticmethod
    def generate_test_audio_files(output_dir: Path):
        """Generate a comprehensive set of test audio files."""
        output_dir.mkdir(exist_ok=True)
        
        test_cases = [
            ('clean_speech_high_snr.wav', lambda: AudioTestDataGenerator.generate_clean_speech()),
            ('noisy_speech_5db.wav', lambda: AudioTestDataGenerator.generate_noisy_speech(snr_db=5)),
            ('noisy_speech_0db.wav', lambda: AudioTestDataGenerator.generate_noisy_speech(snr_db=0)),
            ('very_noisy_speech_-5db.wav', lambda: AudioTestDataGenerator.generate_noisy_speech(snr_db=-5)),
            ('vampire_alpha_voice.wav', lambda: AudioTestDataGenerator.generate_archetype_voice('vampire_alpha')),
            ('human_agent_voice.wav', lambda: AudioTestDataGenerator.generate_archetype_voice('human_agent')),
            ('corpse_tender_voice.wav', lambda: AudioTestDataGenerator.generate_archetype_voice('corpse_tender')),
            ('short_audio.wav', lambda: AudioTestDataGenerator.generate_clean_speech(duration=0.5)),
            ('long_audio.wav', lambda: AudioTestDataGenerator.generate_clean_speech(duration=10.0)),
        ]
        
        generated_files = []
        
        for filename, generator in test_cases:
            audio, sr = generator()
            filepath = output_dir / filename
            sf.write(filepath, audio, sr)
            generated_files.append(filepath)
            print(f"Generated: {filepath}")
        
        # Also generate edge cases
        
        # Empty audio
        empty_audio = np.array([], dtype=np.float32)
        empty_path = output_dir / 'empty_audio.wav'
        sf.write(empty_path, empty_audio, 48000)
        generated_files.append(empty_path)
        
        # Single sample
        single_sample = np.array([0.5], dtype=np.float32)
        single_path = output_dir / 'single_sample.wav'
        sf.write(single_path, single_sample, 48000)
        generated_files.append(single_path)
        
        # Silent audio
        silent = np.zeros(48000 * 2)  # 2 seconds of silence
        silent_path = output_dir / 'silent_audio.wav'
        sf.write(silent_path, silent, 48000)
        generated_files.append(silent_path)
        
        return generated_files


class LocalizationTestDataGenerator:
    """Generate comprehensive localization test data."""
    
    @staticmethod
    def generate_ui_content() -> Dict[str, Dict[str, Any]]:
        """Generate UI localization content."""
        languages = ['en-US', 'ja-JP', 'es-ES', 'zh-CN', 'ko-KR', 'ar-SA', 'fr-FR', 'de-DE']
        
        content = {
            'ui.button.start': {
                'en-US': 'Start',
                'ja-JP': '開始',
                'es-ES': 'Iniciar',
                'zh-CN': '开始',
                'ko-KR': '시작',
                'ar-SA': 'ابدأ',
                'fr-FR': 'Démarrer',
                'de-DE': 'Starten'
            },
            'ui.button.continue': {
                'en-US': 'Continue',
                'ja-JP': '続ける',
                'es-ES': 'Continuar',
                'zh-CN': '继续',
                'ko-KR': '계속',
                'ar-SA': 'استمر',
                'fr-FR': 'Continuer',
                'de-DE': 'Fortfahren'
            },
            'ui.menu.settings': {
                'en-US': 'Settings',
                'ja-JP': '設定',
                'es-ES': 'Configuración',
                'zh-CN': '设置',
                'ko-KR': '설정',
                'ar-SA': 'الإعدادات',
                'fr-FR': 'Paramètres',
                'de-DE': 'Einstellungen'
            },
            'ui.dialog.confirm': {
                'en-US': 'Are you sure?',
                'ja-JP': 'よろしいですか？',
                'es-ES': '¿Está seguro?',
                'zh-CN': '您确定吗？',
                'ko-KR': '확실합니까?',
                'ar-SA': 'هل أنت متأكد؟',
                'fr-FR': 'Êtes-vous sûr?',
                'de-DE': 'Sind Sie sicher?'
            }
        }
        
        # Convert to proper format
        formatted_content = {}
        for key, translations in content.items():
            formatted_content[key] = {}
            for lang, text in translations.items():
                formatted_content[key][lang] = {
                    'text': text,
                    'validated': True,
                    'last_modified': datetime.utcnow().isoformat(),
                    'translator': 'test_system'
                }
        
        return formatted_content
    
    @staticmethod
    def generate_dialogue_content() -> Dict[str, Dict[str, Any]]:
        """Generate dialogue localization content."""
        dialogues = {
            'dialogue.intro.greeting': {
                'en-US': {
                    'text': 'Welcome to the world of shadows, {player_name}.',
                    'speaker': 'narrator',
                    'audio_file': 'intro_greeting_en.ogg',
                    'duration_ms': 3500
                },
                'ja-JP': {
                    'text': 'ようこそ、影の世界へ、{player_name}さん。',
                    'speaker': 'narrator',
                    'tts_enabled': True,
                    'tts_voice': 'ja-JP-Standard-A'
                },
                'es-ES': {
                    'text': 'Bienvenido al mundo de las sombras, {player_name}.',
                    'speaker': 'narrator',
                    'tts_enabled': True,
                    'tts_voice': 'es-ES-Standard-A'
                }
            },
            'dialogue.vampire.threat': {
                'en-US': {
                    'text': 'Your blood smells... exquisite. Come closer.',
                    'speaker': 'vampire_lord',
                    'audio_file': 'vampire_threat_en.ogg',
                    'emotion': 'menacing'
                },
                'ja-JP': {
                    'text': 'お前の血の匂い...絶妙だ。近くに来い。',
                    'speaker': 'vampire_lord',
                    'tts_enabled': True,
                    'emotion': 'menacing'
                }
            }
        }
        
        return dialogues
    
    @staticmethod
    def generate_edge_case_content() -> Dict[str, Dict[str, Any]]:
        """Generate edge case content for testing."""
        return {
            # Very long text
            'ui.tooltip.help': {
                'en-US': {
                    'text': 'This is a very long tooltip that contains detailed information about the game mechanics. ' * 10,
                    'validated': True
                },
                'ja-JP': {
                    'text': 'これは非常に長いツールチップで、ゲームメカニクスに関する詳細情報が含まれています。' * 10,
                    'validated': True
                }
            },
            # Text with many placeholders
            'ui.stats.summary': {
                'en-US': {
                    'text': 'Player: {name}, Level: {level}, HP: {hp}/{max_hp}, XP: {xp}/{xp_needed}',
                    'validated': True,
                    'placeholders': ['name', 'level', 'hp', 'max_hp', 'xp', 'xp_needed']
                }
            },
            # RTL text with special formatting
            'ui.achievement.unlock': {
                'ar-SA': {
                    'text': '\u200Fلقد فتحت الإنجاز: {achievement_name}',
                    'validated': True,
                    'direction': 'rtl'
                }
            },
            # Text with special characters
            'ui.special.characters': {
                'en-US': {
                    'text': 'Special chars: <>&"\'©®™€¥£',
                    'validated': True
                }
            }
        }
    
    @staticmethod
    def generate_localization_files(output_dir: Path):
        """Generate localization test files."""
        output_dir.mkdir(exist_ok=True)
        
        # Generate UI content
        ui_content = LocalizationTestDataGenerator.generate_ui_content()
        ui_path = output_dir / 'ui_content.json'
        with open(ui_path, 'w', encoding='utf-8') as f:
            json.dump(ui_content, f, ensure_ascii=False, indent=2)
        
        # Generate dialogue content
        dialogue_content = LocalizationTestDataGenerator.generate_dialogue_content()
        dialogue_path = output_dir / 'dialogue_content.json'
        with open(dialogue_path, 'w', encoding='utf-8') as f:
            json.dump(dialogue_content, f, ensure_ascii=False, indent=2)
        
        # Generate edge cases
        edge_cases = LocalizationTestDataGenerator.generate_edge_case_content()
        edge_path = output_dir / 'edge_cases.json'
        with open(edge_path, 'w', encoding='utf-8') as f:
            json.dump(edge_cases, f, ensure_ascii=False, indent=2)
        
        return [ui_path, dialogue_path, edge_path]


class EngagementTestDataGenerator:
    """Generate engagement and session test data."""
    
    @staticmethod
    def generate_session_data(
        num_users: int = 10,
        days: int = 14
    ) -> List[Dict[str, Any]]:
        """Generate realistic session data."""
        sessions = []
        base_date = datetime.utcnow() - timedelta(days=days)
        
        for user_id in range(num_users):
            user_sessions = EngagementTestDataGenerator._generate_user_sessions(
                f'test_user_{user_id}',
                base_date,
                days
            )
            sessions.extend(user_sessions)
        
        return sessions
    
    @staticmethod
    def _generate_user_sessions(
        user_id: str,
        base_date: datetime,
        days: int
    ) -> List[Dict[str, Any]]:
        """Generate sessions for a single user."""
        sessions = []
        
        # Determine user behavior pattern
        patterns = ['casual', 'regular', 'intensive', 'addictive']
        pattern = random.choice(patterns)
        
        for day in range(days):
            current_date = base_date + timedelta(days=day)
            
            # Skip some days for casual players
            if pattern == 'casual' and random.random() > 0.3:
                continue
            
            # Generate sessions based on pattern
            if pattern == 'casual':
                num_sessions = random.randint(0, 1)
            elif pattern == 'regular':
                num_sessions = random.randint(1, 2)
            elif pattern == 'intensive':
                num_sessions = random.randint(2, 4)
            else:  # addictive
                num_sessions = random.randint(3, 6)
            
            for _ in range(num_sessions):
                session = EngagementTestDataGenerator._generate_session(
                    user_id,
                    current_date,
                    pattern
                )
                sessions.append(session)
        
        return sessions
    
    @staticmethod
    def _generate_session(
        user_id: str,
        date: datetime,
        pattern: str
    ) -> Dict[str, Any]:
        """Generate a single gaming session."""
        # Session start times based on pattern
        if pattern == 'addictive':
            # More likely to play at night
            hour = random.choices(
                range(24),
                weights=[1,1,1,1,1,1,2,3,4,5,5,4,4,5,5,6,7,8,9,10,10,9,8,5]
            )[0]
        else:
            # Normal distribution
            hour = random.choices(
                range(24),
                weights=[1,1,1,1,1,1,2,3,5,7,8,7,6,7,8,9,10,10,9,7,5,4,3,2]
            )[0]
        
        start_time = date.replace(hour=hour, minute=random.randint(0, 59))
        
        # Session duration based on pattern
        if pattern == 'casual':
            duration_minutes = random.randint(15, 60)
        elif pattern == 'regular':
            duration_minutes = random.randint(30, 120)
        elif pattern == 'intensive':
            duration_minutes = random.randint(60, 240)
        else:  # addictive
            duration_minutes = random.randint(120, 360)
        
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        # Generate events
        events = EngagementTestDataGenerator._generate_session_events(
            start_time,
            end_time,
            pattern
        )
        
        return {
            'user_id': user_id,
            'session_id': f'{user_id}_{start_time.timestamp()}',
            'session_start': start_time.isoformat(),
            'session_end': end_time.isoformat(),
            'duration_minutes': duration_minutes,
            'events': events,
            'pattern': pattern
        }
    
    @staticmethod
    def _generate_session_events(
        start_time: datetime,
        end_time: datetime,
        pattern: str
    ) -> List[Dict[str, Any]]:
        """Generate events within a session."""
        events = []
        
        # Always start with game_start
        events.append({
            'type': 'game_start',
            'timestamp': start_time.isoformat()
        })
        
        current_time = start_time
        session_duration = (end_time - start_time).total_seconds() / 60
        
        # Generate events based on session length and pattern
        if pattern == 'addictive':
            # More "one more run" behavior
            deaths_per_hour = 12
            restarts_per_death = 0.9
        else:
            deaths_per_hour = 5
            restarts_per_death = 0.5
        
        num_deaths = int(session_duration / 60 * deaths_per_hour)
        
        for i in range(num_deaths):
            # Progress time
            time_increment = random.randint(3, 10)
            current_time += timedelta(minutes=time_increment)
            
            if current_time >= end_time:
                break
            
            # Death event
            events.append({
                'type': 'death',
                'timestamp': current_time.isoformat()
            })
            
            # Possibly restart quickly (one more run)
            if random.random() < restarts_per_death:
                restart_delay = random.randint(10, 120)  # seconds
                current_time += timedelta(seconds=restart_delay)
                
                if current_time < end_time:
                    events.append({
                        'type': 'restart',
                        'timestamp': current_time.isoformat()
                    })
        
        # End with game_end
        events.append({
            'type': 'game_end',
            'timestamp': end_time.isoformat()
        })
        
        return events
    
    @staticmethod
    def generate_addiction_test_cases() -> List[Dict[str, Any]]:
        """Generate specific test cases for addiction indicators."""
        test_cases = []
        
        # Night owl player
        night_sessions = []
        for day in range(7):
            date = datetime.utcnow() - timedelta(days=day)
            session = {
                'user_id': 'night_owl_player',
                'session_start': date.replace(hour=23).isoformat(),
                'session_end': (date + timedelta(hours=4)).isoformat(),
                'events': [
                    {'type': 'game_start', 'timestamp': date.replace(hour=23).isoformat()},
                    {'type': 'game_end', 'timestamp': (date + timedelta(hours=4)).isoformat()}
                ]
            }
            night_sessions.append(session)
        
        test_cases.append({
            'name': 'Night Owl Player',
            'description': 'Plays primarily during night hours',
            'sessions': night_sessions,
            'expected_indicators': {
                'night_time_play_ratio': 0.8,
                'risk_level': 'high'
            }
        })
        
        # One more run player
        one_more_sessions = []
        date = datetime.utcnow()
        for hour in [14, 15, 16, 17]:
            session_start = date.replace(hour=hour, minute=0)
            events = [{'type': 'game_start', 'timestamp': session_start.isoformat()}]
            
            # Many quick restarts
            current_time = session_start
            for _ in range(10):
                current_time += timedelta(minutes=5)
                events.append({'type': 'death', 'timestamp': current_time.isoformat()})
                current_time += timedelta(seconds=30)
                events.append({'type': 'restart', 'timestamp': current_time.isoformat()})
            
            session_end = current_time + timedelta(minutes=5)
            events.append({'type': 'game_end', 'timestamp': session_end.isoformat()})
            
            one_more_sessions.append({
                'user_id': 'one_more_player',
                'session_start': session_start.isoformat(),
                'session_end': session_end.isoformat(),
                'events': events
            })
        
        test_cases.append({
            'name': 'One More Run Player',
            'description': 'Exhibits frequent restart behavior',
            'sessions': one_more_sessions,
            'expected_indicators': {
                'one_more_run_ratio': 0.8,
                'risk_level': 'concerning'
            }
        })
        
        # Healthy player
        healthy_sessions = []
        for day in range(7):
            date = datetime.utcnow() - timedelta(days=day)
            if day % 2 == 0:  # Play every other day
                session = {
                    'user_id': 'healthy_player',
                    'session_start': date.replace(hour=15).isoformat(),
                    'session_end': date.replace(hour=16, minute=30).isoformat(),
                    'events': [
                        {'type': 'game_start', 'timestamp': date.replace(hour=15).isoformat()},
                        {'type': 'level_complete', 'timestamp': date.replace(hour=15, minute=30).isoformat()},
                        {'type': 'game_end', 'timestamp': date.replace(hour=16, minute=30).isoformat()}
                    ]
                }
                healthy_sessions.append(session)
        
        test_cases.append({
            'name': 'Healthy Player',
            'description': 'Moderate play patterns',
            'sessions': healthy_sessions,
            'expected_indicators': {
                'risk_level': 'low',
                'avg_session_duration': 1.5
            }
        })
        
        return test_cases


def generate_all_test_data(base_dir: Path = Path('tests/test_data')):
    """Generate all test data files."""
    base_dir.mkdir(exist_ok=True, parents=True)
    
    # Generate audio test data
    print("Generating audio test data...")
    audio_dir = base_dir / 'audio'
    AudioTestDataGenerator.generate_test_audio_files(audio_dir)
    
    # Generate localization test data
    print("Generating localization test data...")
    loc_dir = base_dir / 'localization'
    LocalizationTestDataGenerator.generate_localization_files(loc_dir)
    
    # Generate engagement test data
    print("Generating engagement test data...")
    engagement_dir = base_dir / 'engagement'
    engagement_dir.mkdir(exist_ok=True)
    
    # Regular session data
    sessions = EngagementTestDataGenerator.generate_session_data()
    with open(engagement_dir / 'session_data.json', 'w') as f:
        json.dump(sessions, f, indent=2)
    
    # Addiction test cases
    addiction_cases = EngagementTestDataGenerator.generate_addiction_test_cases()
    with open(engagement_dir / 'addiction_test_cases.json', 'w') as f:
        json.dump(addiction_cases, f, indent=2)
    
    print(f"All test data generated in {base_dir}")


if __name__ == '__main__':
    generate_all_test_data()
