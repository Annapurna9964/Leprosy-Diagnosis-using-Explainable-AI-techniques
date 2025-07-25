#!/usr/bin/env python3
"""
Setup script for the Leprosy Detection AI Application.
This script will check dependencies, setup directories, and prepare the environment.
"""

import os
import sys
import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_python_version():
    """Check if Python version is compatible"""
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        logger.error("Python 3.8 or higher is required.")
        return False
    logger.info(f"Python version {python_version.major}.{python_version.minor} detected.")
    return True

def check_dependencies():
    """Check if required Python packages are installed"""
    required_packages = [
        'flask', 'flask-login', 'flask-sqlalchemy', 'flask-wtf',
        'matplotlib', 'numpy', 'opencv-python', 'pandas', 'scikit-learn',
        'pillow', 'werkzeug', 'gunicorn'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            logger.info(f"Package {package} found.")
        except ImportError:
            missing_packages.append(package)
            logger.warning(f"Package {package} not found.")
    
    if missing_packages:
        logger.error(f"Missing packages: {', '.join(missing_packages)}")
        install = input("Do you want to install missing packages? (y/n): ")
        if install.lower() == 'y':
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
                logger.info("Packages installed successfully.")
                return True
            except subprocess.CalledProcessError:
                logger.error("Failed to install packages.")
                return False
        else:
            logger.warning("Continuing without installing missing packages.")
            return False
    
    return True

def check_kaggle_credentials():
    """Check if Kaggle credentials are available"""
    kaggle_username = os.environ.get('KAGGLE_USERNAME')
    kaggle_key = os.environ.get('KAGGLE_KEY')
    
    if not kaggle_username or not kaggle_key:
        kaggle_json = os.path.expanduser("~/.kaggle/kaggle.json")
        if os.path.exists(kaggle_json):
            logger.info("Kaggle credentials found in ~/.kaggle/kaggle.json")
            return True
        
        logger.warning("Kaggle credentials not found in environment variables or kaggle.json.")
        setup_creds = input("Do you want to set up Kaggle credentials now? (y/n): ")
        
        if setup_creds.lower() == 'y':
            username = input("Enter your Kaggle username: ")
            key = input("Enter your Kaggle API key: ")
            
            # Set environment variables for current session
            os.environ['KAGGLE_USERNAME'] = username
            os.environ['KAGGLE_KEY'] = key
            
            # Ask if user wants to persist credentials
            persist = input("Do you want to persist these credentials for future sessions? (y/n): ")
            if persist.lower() == 'y':
                kaggle_dir = os.path.expanduser("~/.kaggle")
                os.makedirs(kaggle_dir, exist_ok=True)
                
                import json
                with open(os.path.join(kaggle_dir, "kaggle.json"), "w") as f:
                    json.dump({"username": username, "key": key}, f)
                
                os.chmod(os.path.join(kaggle_dir, "kaggle.json"), 0o600)
                logger.info("Kaggle credentials saved to ~/.kaggle/kaggle.json")
            
            return True
        else:
            logger.warning("Continuing without Kaggle credentials.")
            return False
    
    logger.info("Kaggle credentials found in environment variables.")
    return True

def setup_directories():
    """Ensure all required directories exist"""
    directories = [
        'model',
        'dataset',
        'dataset/leprosy_dataset',
        'dataset/leprosy_dataset/positive',
        'dataset/leprosy_dataset/negative',
        'dataset/leprosy_dataset/irrelevant',
        'test_samples',
        'test_samples/positive',
        'test_samples/negative',
        'test_results',
        'static/uploads',
        'instance'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Directory {directory} ensured.")
    
    return True

def run_data_preparation():
    """Run the data preparation scripts"""
    if not os.path.exists('model/leprosy_classifier.pkl'):
        # Check if datasets are already downloaded
        positive_dir = 'dataset/leprosy_dataset/positive'
        negative_dir = 'dataset/leprosy_dataset/negative'
        
        if (not os.path.exists(positive_dir) or len(os.listdir(positive_dir)) < 10 or
            not os.path.exists(negative_dir) or len(os.listdir(negative_dir)) < 10):
            
            logger.info("Datasets not found or incomplete. Preparing to download...")
            credentials_ready = check_kaggle_credentials()
            
            if credentials_ready:
                logger.info("Running prepare_kaggle_data.py...")
                try:
                    subprocess.check_call([sys.executable, "prepare_kaggle_data.py"])
                    logger.info("Dataset preparation completed successfully.")
                except subprocess.CalledProcessError:
                    logger.error("Failed to prepare datasets.")
                    return False
            else:
                logger.error("Cannot prepare datasets without Kaggle credentials.")
                return False
        else:
            logger.info("Datasets already downloaded.")
        
        # Prepare test samples
        test_pos_dir = 'test_samples/positive'
        test_neg_dir = 'test_samples/negative'
        
        if (not os.path.exists(test_pos_dir) or len(os.listdir(test_pos_dir)) < 5 or
            not os.path.exists(test_neg_dir) or len(os.listdir(test_neg_dir)) < 5):
            
            logger.info("Test samples not found or incomplete. Preparing...")
            try:
                subprocess.check_call([sys.executable, "prepare_test_samples.py"])
                logger.info("Test samples prepared successfully.")
            except subprocess.CalledProcessError:
                logger.error("Failed to prepare test samples.")
                return False
        else:
            logger.info("Test samples already prepared.")
        
        # Train the model
        logger.info("Training the model...")
        try:
            subprocess.check_call([sys.executable, "retrain_model.py"])
            logger.info("Model training completed successfully.")
        except subprocess.CalledProcessError:
            logger.error("Failed to train the model.")
            return False
    else:
        logger.info("Model already exists. Skipping data preparation and training.")
    
    return True

def main():
    """Main setup function"""
    logger.info("Starting setup for Leprosy Detection AI Application...")
    
    # Check prerequisites
    if not check_python_version():
        logger.error("Setup failed: Incompatible Python version.")
        return False
    
    if not check_dependencies():
        logger.warning("Setup may not work correctly without required packages.")
    
    # Setup directories
    if not setup_directories():
        logger.error("Setup failed: Could not create required directories.")
        return False
    
    # Run data preparation
    if not run_data_preparation():
        logger.warning("Data preparation incomplete. The application may not work properly.")
    
    logger.info("Setup completed successfully!")
    logger.info("To run the application, use: python main.py")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)