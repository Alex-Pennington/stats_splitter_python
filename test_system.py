#!/usr/bin/env python3
"""
Test runner for the Firewood Splitter Statistics System

This script helps test the complete system by running both the simulator
and the main application with proper timing and coordination.
"""

import asyncio
import subprocess
import sys
import time
import logging
import signal
import os
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SystemTester:
    """Coordinates testing of the complete firewood splitter statistics system"""
    
    def __init__(self):
        self.main_process = None
        self.simulator_process = None
        self.processes = []
        
    def start_main_application(self):
        """Start the main statistics application"""
        logger.info("Starting main statistics application...")
        try:
            self.main_process = subprocess.Popen(
                [sys.executable, "main.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            self.processes.append(self.main_process)
            logger.info("Main application started successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to start main application: {e}")
            return False
    
    def start_simulator(self, duration_minutes=None, speed=10.0):
        """Start the firewood splitter simulator"""
        logger.info(f"Starting simulator (speed: {speed}x, duration: {duration_minutes} min)...")
        try:
            cmd = [sys.executable, "simulator.py", "--speed", str(speed)]
            if duration_minutes:
                cmd.extend(["--duration", str(duration_minutes)])
            
            self.simulator_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            self.processes.append(self.simulator_process)
            logger.info("Simulator started successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to start simulator: {e}")
            return False
    
    def monitor_processes(self):
        """Monitor running processes and log their output"""
        logger.info("Monitoring processes... Press Ctrl+C to stop")
        
        try:
            while True:
                # Check if processes are still running
                if self.main_process and self.main_process.poll() is not None:
                    logger.error("Main application has stopped unexpectedly")
                    break
                
                if self.simulator_process and self.simulator_process.poll() is not None:
                    logger.info("Simulator has completed")
                    # Let main app continue running
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, stopping processes...")
        
        self.cleanup_processes()
    
    def cleanup_processes(self):
        """Clean up all running processes"""
        logger.info("Cleaning up processes...")
        
        for process in self.processes:
            if process and process.poll() is None:
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning("Process didn't terminate gracefully, killing...")
                    process.kill()
                except Exception as e:
                    logger.error(f"Error cleaning up process: {e}")
        
        self.processes.clear()
        logger.info("All processes cleaned up")
    
    def run_quick_test(self):
        """Run a quick 2-minute test with 10x speed"""
        logger.info("🧪 Running Quick Test (2 minutes at 10x speed)")
        logger.info("This simulates about 20 minutes of real production")
        
        # Start main application
        if not self.start_main_application():
            return False
        
        # Wait for main app to initialize
        logger.info("Waiting 5 seconds for main app to initialize...")
        time.sleep(5)
        
        # Start simulator for 2 minutes at 10x speed
        if not self.start_simulator(duration_minutes=2, speed=10.0):
            self.cleanup_processes()
            return False
        
        # Monitor processes
        self.monitor_processes()
        return True
    
    def run_full_test(self):
        """Run a full test with realistic timing"""
        logger.info("🏭 Running Full Test (real-time simulation)")
        logger.info("This will run at normal speed - each cycle takes ~30 seconds")
        
        # Start main application
        if not self.start_main_application():
            return False
        
        # Wait for main app to initialize
        logger.info("Waiting 5 seconds for main app to initialize...")
        time.sleep(5)
        
        # Start simulator at normal speed (no duration limit)
        if not self.start_simulator(speed=1.0):
            self.cleanup_processes()
            return False
        
        # Monitor processes
        self.monitor_processes()
        return True

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test the Firewood Splitter Statistics System")
    parser.add_argument("--quick", action="store_true", 
                       help="Run quick test (2 min at 10x speed)")
    parser.add_argument("--full", action="store_true", 
                       help="Run full test (real-time)")
    parser.add_argument("--check-deps", action="store_true",
                       help="Check if dependencies are installed")
    
    args = parser.parse_args()
    
    # Check dependencies first
    if args.check_deps or (not args.quick and not args.full):
        logger.info("Checking dependencies...")
        
        # Check if required files exist
        required_files = [
            "main.py", "simulator.py", "production_stats.py", 
            "mqtt_client.py", "web_server.py", "config.py",
            "requirements.txt", ".env"
        ]
        
        missing_files = []
        for file in required_files:
            if not Path(file).exists():
                missing_files.append(file)
        
        if missing_files:
            logger.error(f"Missing required files: {', '.join(missing_files)}")
            return 1
        
        logger.info("✅ All required files present")
        
        # Check Python modules
        try:
            import paho.mqtt.client
            import flask
            import asyncio_mqtt
            logger.info("✅ All required Python modules available")
        except ImportError as e:
            logger.error(f"❌ Missing Python module: {e}")
            logger.info("Please run: pip install -r requirements.txt")
            return 1
        
        if not args.quick and not args.full:
            logger.info("✅ System check complete. Use --quick or --full to run tests.")
            return 0
    
    tester = SystemTester()
    
    # Set up signal handlers
    def signal_handler(signum, frame):
        logger.info("Received signal, cleaning up...")
        tester.cleanup_processes()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    if args.quick:
        success = tester.run_quick_test()
    elif args.full:
        success = tester.run_full_test()
    else:
        logger.error("Please specify --quick or --full test mode")
        return 1
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())