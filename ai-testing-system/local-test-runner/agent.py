#!/usr/bin/env python3
"""
Local Test Runner Agent
Monitors GameObserver output, bundles captures, uploads to AWS
Part of AI-Driven Game Testing System (Tier 2)
"""

import os
import sys
import time
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import boto3
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('test-runner-agent.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class CaptureBundle:
    """Bundle of screenshot + telemetry JSON"""
    screenshot_path: str
    telemetry_path: str
    event_type: str
    timestamp: str
    capture_id: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


class GameObserverWatcher(FileSystemEventHandler):
    """Watches GameObserver output directory for new captures"""
    
    def __init__(self, agent: 'LocalTestRunnerAgent'):
        self.agent = agent
        self.pending_pairs = {}  # Track incomplete pairs
        
    def on_created(self, event):
        """Handle new file creation"""
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        
        if file_path.suffix == '.png':
            self._handle_screenshot(file_path)
        elif file_path.suffix == '.json':
            self._handle_telemetry(file_path)
    
    def _handle_screenshot(self, screenshot_path: Path):
        """Handle new screenshot file"""
        base_name = screenshot_path.stem
        telemetry_path = screenshot_path.with_suffix('.json')
        
        if telemetry_path.exists():
            # Both files exist - create bundle
            self._create_bundle(screenshot_path, telemetry_path)
        else:
            # Wait for telemetry file
            self.pending_pairs[base_name] = {
                'screenshot': screenshot_path,
                'created_at': time.time()
            }
    
    def _handle_telemetry(self, telemetry_path: Path):
        """Handle new telemetry file"""
        base_name = telemetry_path.stem
        screenshot_path = telemetry_path.with_suffix('.png')
        
        if screenshot_path.exists():
            # Both files exist - create bundle
            self._create_bundle(screenshot_path, telemetry_path)
        elif base_name in self.pending_pairs:
            # Screenshot was waiting for this telemetry
            screenshot_path = self.pending_pairs[base_name]['screenshot']
            self._create_bundle(screenshot_path, telemetry_path)
            del self.pending_pairs[base_name]
    
    def _create_bundle(self, screenshot_path: Path, telemetry_path: Path):
        """Create capture bundle and queue for upload"""
        try:
            # Read telemetry to get event type
            with open(telemetry_path, 'r') as f:
                telemetry = json.load(f)
            
            bundle = CaptureBundle(
                screenshot_path=str(screenshot_path),
                telemetry_path=str(telemetry_path),
                event_type=telemetry.get('event_type', 'Unknown'),
                timestamp=telemetry.get('timestamp', datetime.utcnow().isoformat()),
                capture_id=screenshot_path.stem
            )
            
            logger.info(f"New capture bundle: {bundle.event_type} - {bundle.capture_id}")
            self.agent.queue_bundle(bundle)
            
        except Exception as e:
            logger.error(f"Error creating bundle: {e}")


class LocalTestRunnerAgent:
    """
    Local Test Runner Agent
    
    Responsibilities:
    1. Monitor GameObserver output directory
    2. Bundle screenshot + telemetry pairs
    3. Upload bundles to AWS S3
    4. Notify AWS Orchestrator
    5. Handle job queue from AWS
    """
    
    def __init__(self, config_path: str = "config.json"):
        self.config = self._load_config(config_path)
        self.s3_client = boto3.client('s3')
        self.sqs_client = boto3.client('sqs')
        self.upload_queue = []
        self.observer = None
        
        logger.info("Local Test Runner Agent initialized")
        logger.info(f"Watching: {self.config['watch_directory']}")
        logger.info(f"S3 Bucket: {self.config['s3_bucket']}")
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file"""
        default_config = {
            "watch_directory": "../../../unreal/GameObserver/Captures",
            "s3_bucket": "body-broker-qa-captures",
            "sqs_queue_url": "",
            "orchestrator_url": "http://localhost:8000",
            "upload_batch_size": 10,
            "upload_interval_seconds": 30,
            "aws_region": "us-east-1"
        }
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        return default_config
    
    def queue_bundle(self, bundle: CaptureBundle):
        """Add bundle to upload queue"""
        self.upload_queue.append(bundle)
        
        # Upload if batch size reached
        if len(self.upload_queue) >= self.config['upload_batch_size']:
            self.upload_bundles()
    
    def upload_bundles(self):
        """Upload queued bundles to S3"""
        if not self.upload_queue:
            return
        
        logger.info(f"Uploading {len(self.upload_queue)} bundles to S3...")
        
        uploaded = []
        failed = []
        
        for bundle in self.upload_queue:
            try:
                # Upload screenshot
                screenshot_key = f"captures/{bundle.timestamp}/{bundle.capture_id}.png"
                with open(bundle.screenshot_path, 'rb') as f:
                    self.s3_client.put_object(
                        Bucket=self.config['s3_bucket'],
                        Key=screenshot_key,
                        Body=f,
                        ContentType='image/png'
                    )
                
                # Upload telemetry
                telemetry_key = f"captures/{bundle.timestamp}/{bundle.capture_id}.json"
                with open(bundle.telemetry_path, 'rb') as f:
                    self.s3_client.put_object(
                        Bucket=self.config['s3_bucket'],
                        Key=telemetry_key,
                        Body=f,
                        ContentType='application/json'
                    )
                
                # Notify orchestrator
                self._notify_orchestrator(bundle, screenshot_key, telemetry_key)
                
                uploaded.append(bundle)
                logger.info(f"Uploaded: {bundle.capture_id}")
                
            except Exception as e:
                logger.error(f"Upload failed for {bundle.capture_id}: {e}")
                failed.append(bundle)
        
        # Clear uploaded bundles
        self.upload_queue = failed
        
        logger.info(f"Upload complete: {len(uploaded)} succeeded, {len(failed)} failed")
    
    def _notify_orchestrator(self, bundle: CaptureBundle, screenshot_key: str, telemetry_key: str):
        """Notify AWS Orchestrator of new capture"""
        try:
            payload = {
                "capture_id": bundle.capture_id,
                "event_type": bundle.event_type,
                "timestamp": bundle.timestamp,
                "screenshot_key": screenshot_key,
                "telemetry_key": telemetry_key,
                "s3_bucket": self.config['s3_bucket']
            }
            
            response = requests.post(
                f"{self.config['orchestrator_url']}/captures/new",
                json=payload,
                timeout=5
            )
            
            if response.status_code == 200:
                logger.debug(f"Orchestrator notified: {bundle.capture_id}")
            else:
                logger.warning(f"Orchestrator notification failed: {response.status_code}")
                
        except Exception as e:
            logger.warning(f"Could not notify orchestrator: {e}")
    
    def start_watching(self):
        """Start watching GameObserver output directory"""
        watch_path = Path(self.config['watch_directory'])
        
        if not watch_path.exists():
            logger.warning(f"Watch directory does not exist: {watch_path}")
            logger.info("Creating directory...")
            watch_path.mkdir(parents=True, exist_ok=True)
        
        event_handler = GameObserverWatcher(self)
        self.observer = Observer()
        self.observer.schedule(event_handler, str(watch_path), recursive=False)
        self.observer.start()
        
        logger.info(f"Started watching: {watch_path}")
    
    def poll_job_queue(self):
        """Poll SQS job queue for test execution requests"""
        if not self.config.get('sqs_queue_url'):
            return
        
        try:
            response = self.sqs_client.receive_message(
                QueueUrl=self.config['sqs_queue_url'],
                MaxNumberOfMessages=1,
                WaitTimeSeconds=5
            )
            
            messages = response.get('Messages', [])
            
            for message in messages:
                self._handle_job(message)
                
                # Delete message from queue
                self.sqs_client.delete_message(
                    QueueUrl=self.config['sqs_queue_url'],
                    ReceiptHandle=message['ReceiptHandle']
                )
                
        except Exception as e:
            logger.error(f"Error polling job queue: {e}")
    
    def _handle_job(self, message: Dict):
        """Handle test execution job from orchestrator"""
        try:
            body = json.loads(message['Body'])
            job_type = body.get('job_type')
            
            logger.info(f"Received job: {job_type}")
            
            if job_type == 'run_tests':
                self._run_ue5_tests(body)
            elif job_type == 'capture_baseline':
                self._capture_baseline(body)
            else:
                logger.warning(f"Unknown job type: {job_type}")
                
        except Exception as e:
            logger.error(f"Error handling job: {e}")
    
    def _run_ue5_tests(self, job_data: Dict):
        """Execute UE5 automation tests"""
        logger.info("Executing UE5 tests...")
        
        # TODO: Implement UE5 test execution
        # This will call run-ue5-tests.ps1 script
        pass
    
    def _capture_baseline(self, job_data: Dict):
        """Trigger baseline capture in game"""
        logger.info("Baseline capture requested")
        
        # TODO: Send command to game via HTTP API
        pass
    
    def run(self):
        """Main agent loop"""
        self.start_watching()
        
        logger.info("Local Test Runner Agent running")
        logger.info("Press Ctrl+C to stop")
        
        try:
            while True:
                # Periodic upload of queued bundles
                time.sleep(self.config['upload_interval_seconds'])
                
                if self.upload_queue:
                    self.upload_bundles()
                
                # Poll for jobs from orchestrator
                self.poll_job_queue()
                
        except KeyboardInterrupt:
            logger.info("Stopping agent...")
            
            # Upload remaining bundles
            if self.upload_queue:
                logger.info("Uploading remaining bundles...")
                self.upload_bundles()
            
            if self.observer:
                self.observer.stop()
                self.observer.join()
            
            logger.info("Agent stopped")


def main():
    """Entry point"""
    agent = LocalTestRunnerAgent()
    agent.run()


if __name__ == "__main__":
    main()

