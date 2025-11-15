# services/ue-version-monitor/main.py
"""
UE5 Version Monitoring Service
Monitors Epic Games GitHub for new UE5 releases and triggers update pipeline
"""

import os
import sys
import time
import requests
import json
from datetime import datetime
from typing import Optional, Dict
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

class UEVersionMonitor:
    def __init__(self, config_path: Optional[str] = None):
        self.github_api = "https://api.github.com/repos/EpicGames/UnrealEngine"
        self.config_path = config_path or "/opt/services/ue-version-monitor/config.json"
        self.load_config()
        
    def load_config(self):
        """Load configuration from file"""
        default_config = {
            "current_version": "5.6.1",
            "check_interval": 3600,  # 1 hour
            "notify_webhook": None,
            "auto_update": False
        }
        
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                self.config = {**default_config, **json.load(f)}
        else:
            self.config = default_config
            self.save_config()
    
    def save_config(self):
        """Save configuration to file"""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def check_for_updates(self) -> Optional[Dict]:
        """Check GitHub for new UE5 releases"""
        try:
            tags_url = f"{self.github_api}/tags"
            headers = {
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "UE5-Version-Monitor/1.0"
            }
            
            response = requests.get(tags_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            tags = response.json()
            # Filter UE5 tags (5.x.x-release format)
            ue5_tags = [
                t for t in tags 
                if t['name'].startswith('5.') and '-release' in t['name']
            ]
            
            if not ue5_tags:
                return None
            
            # Get latest version
            latest_tag = ue5_tags[0]['name']
            latest_version = latest_tag.replace('-release', '')
            
            if self.is_newer_version(latest_version, self.config['current_version']):
                return {
                    'new_version': latest_version,
                    'tag': latest_tag,
                    'current_version': self.config['current_version'],
                    'release_date': ue5_tags[0].get('commit', {}).get('date'),
                    'url': f"https://github.com/EpicGames/UnrealEngine/releases/tag/{latest_tag}"
                }
        except Exception as e:
            print(f"Error checking for updates: {e}")
        
        return None
    
    def is_newer_version(self, new: str, current: str) -> bool:
        """Compare version strings (e.g., '5.7.0' > '5.6.1')"""
        new_parts = [int(x) for x in new.split('.')]
        current_parts = [int(x) for x in current.split('.')]
        
        for i in range(max(len(new_parts), len(current_parts))):
            new_val = new_parts[i] if i < len(new_parts) else 0
            current_val = current_parts[i] if i < len(current_parts) else 0
            
            if new_val > current_val:
                return True
            elif new_val < current_val:
                return False
        return False
    
    def notify_update_available(self, update_info: Dict):
        """Notify about available update"""
        print(f"New UE5 version available: {update_info['new_version']}")
        print(f"Current version: {update_info['current_version']}")
        print(f"Release URL: {update_info['url']}")
        
        # Send webhook notification if configured
        if self.config.get('notify_webhook'):
            try:
                requests.post(
                    self.config['notify_webhook'],
                    json=update_info,
                    timeout=5
                )
            except Exception as e:
                print(f"Failed to send webhook notification: {e}")
        
        # Trigger auto-update if enabled
        if self.config.get('auto_update'):
            self.trigger_update(update_info['new_version'])
    
    def trigger_update(self, new_version: str):
        """Trigger automated update process"""
        update_script = "/opt/scripts/linux/update-ue-version.sh"
        if os.path.exists(update_script):
            import subprocess
            try:
                result = subprocess.run(
                    ['bash', update_script, new_version],
                    capture_output=True,
                    text=True,
                    timeout=3600  # 1 hour timeout
                )
                if result.returncode == 0:
                    self.config['current_version'] = new_version
                    self.save_config()
                    print(f"✅ Successfully updated to {new_version}")
                else:
                    print(f"❌ Update failed: {result.stderr}")
            except subprocess.TimeoutExpired:
                print("❌ Update timed out")
        else:
            print(f"Update script not found: {update_script}")
    
    def run_monitor_loop(self):
        """Run continuous monitoring loop"""
        print(f"Starting UE5 version monitor (checking every {self.config['check_interval']}s)")
        print(f"Current version: {self.config['current_version']}")
        
        while True:
            try:
                update_info = self.check_for_updates()
                if update_info:
                    self.notify_update_available(update_info)
                else:
                    print(f"[{datetime.now()}] No updates available")
                
                time.sleep(self.config['check_interval'])
            except KeyboardInterrupt:
                print("\nStopping monitor...")
                break
            except Exception as e:
                print(f"Error in monitor loop: {e}")
                time.sleep(60)  # Wait 1 minute before retrying

if __name__ == "__main__":
    monitor = UEVersionMonitor()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        # Single check mode
        update_info = monitor.check_for_updates()
        if update_info:
            monitor.notify_update_available(update_info)
            sys.exit(0)
        else:
            print("No updates available")
            sys.exit(0)
    else:
        # Continuous monitoring mode
        monitor.run_monitor_loop()








