#!/usr/bin/env python3
"""
Main Application Entry Point for Value-Added Prompt Framework

This module serves as the main entry point for the Value-Added Prompt Framework,
providing options to run the application in different modes.
"""

import os
import sys
import argparse
import asyncio
import subprocess
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def check_dependencies():
    """Check if all required dependencies are installed."""
    required_packages = [
        'streamlit',
        'openai',
        'pydantic',
        'tinydb'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nInstall them with:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True

def check_environment():
    """Check environment setup."""
    print("🔍 Checking environment...")
    
    # Check Python version
    python_version = sys.version_info
    if python_version < (3, 8):
        print(f"❌ Python 3.8+ required. Current version: {python_version.major}.{python_version.minor}")
        return False
    
    print(f"✅ Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Check dependencies
    if not check_dependencies():
        return False
    
    print("✅ All dependencies installed")
    
    # Check OpenAI API key (optional since UI can handle it)
    if not os.getenv("OPENAI_API_KEY"):
        print("ℹ️  OpenAI API key not found in environment variables")
        print("   You can enter it directly in the UI when you run the application")
    else:
        print("✅ OpenAI API key configured in environment")
    
    return True

def run_streamlit():
    """Run the Streamlit UI."""
    print("🚀 Starting Streamlit UI...")
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "streamlit_ui.py",
            "--server.port", "8501",
            "--server.headless", "true"
        ])
    except KeyboardInterrupt:
        print("\n👋 Streamlit application stopped")
    except Exception as e:
        print(f"❌ Error running Streamlit: {e}")

async def run_cli_demo():
    """Run a command-line demo of the framework."""
    print("🧠 Value-Added Prompt Framework - CLI Demo")
    print("=" * 50)
    
    try:
        from value_added_framework import ValueAddedFramework, FrameworkConfig
        
        # Initialize framework
        config = FrameworkConfig(session_duration_minutes=10)  # Short demo session
        framework = ValueAddedFramework(config)
        
        # Start session
        print("Starting therapy session...")
        chat_id = framework.start_session()
        print(f"✅ Session started (ID: {chat_id})")
        print()
        
        # Demo messages
        demo_messages = [
            "Hello, I'm feeling really anxious about work lately.",
            "I keep having trouble sleeping because my mind races at night.",
            "Sometimes I feel like I'm not good enough at my job.",
            "What can I do to manage these feelings better?"
        ]
        
        for i, message in enumerate(demo_messages, 1):
            print(f"👤 Patient: {message}")
            
            try:
                response = await framework.process_user_message(message)
                
                print(f"👨‍⚕️ Therapist: {response['patient_response']}")
                print(f"📝 Clinical Notes: {response['psychiatrist_thoughts']}")
                print(f"⏱️  Time Left: {response['time_left']}")
                print(f"📊 Tokens Used: {response['usage_stats']['total_tokens']}")
                print("-" * 50)
                
                # Brief pause
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"❌ Error processing message: {e}")
                break
        
        # End session
        print("\n🏁 Ending session...")
        summary = framework.end_session()
        print("📋 Session Summary:")
        print(f"   - Messages: {summary['message_count']['total']}")
        print(f"   - Duration: {summary['session_duration_minutes']} minutes")
        print(f"   - Patient: {summary['patient_name']}")
        
    except Exception as e:
        print(f"❌ Demo error: {e}")

def run_example():
    """Run the example from the framework module."""
    print("🧪 Running framework example...")
    try:
        from value_added_framework import example_usage
        asyncio.run(example_usage())
    except Exception as e:
        print(f"❌ Example error: {e}")

def install_requirements():
    """Install required packages."""
    requirements = [
        "streamlit>=1.28.0",
        "openai>=1.0.0",
        "pydantic>=2.0.0",
        "tinydb>=4.8.0"
    ]
    
    print("📦 Installing requirements...")
    for req in requirements:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", req])
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {req}: {e}")
            return False
    
    print("✅ All requirements installed successfully!")
    return True

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Value-Added Prompt Framework - Dynamic Context-Enhanced Prompt Engineering"
    )
    
    parser.add_argument(
        "mode",
        choices=["ui", "demo", "example", "install", "check"],
        help="Run mode: ui (Streamlit), demo (CLI), example (framework test), install (dependencies), check (environment)"
    )
    
    args = parser.parse_args()
    
    print("🧠 Value-Added Prompt Framework")
    print("Dynamic Context-Enhanced Prompt Engineering")
    print("=" * 60)
    
    if args.mode == "install":
        install_requirements()
        return
    
    if args.mode == "check":
        if check_environment():
            print("✅ Environment ready!")
        else:
            print("❌ Environment setup incomplete")
        return
    
    # Check environment for other modes (except UI which handles API key internally)
    if args.mode != "ui":
        if not check_environment():
            print("\n💡 Run 'python main.py install' to install dependencies")
            print("💡 Run 'python main.py check' to verify setup")
            return
    else:
        # For UI mode, just check dependencies, not API key
        if not check_dependencies():
            print("\n💡 Run 'python main.py install' to install dependencies")
            return
    
    if args.mode == "ui":
        run_streamlit()
    elif args.mode == "demo":
        asyncio.run(run_cli_demo())
    elif args.mode == "example":
        run_example()

if __name__ == "__main__":
    main()