"""
Configuration Module for WiFi People Detection System

Centralized configuration for all system components.
"""

from typing import Dict, List, Tuple
import os
from pathlib import Path


# === Project Paths ===

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"
LOGS_DIR = PROJECT_ROOT / "logs"
CONFIG_DIR = PROJECT_ROOT / "config"

# Ensure directories exist
for dir_path in [DATA_DIR, MODELS_DIR, LOGS_DIR, CONFIG_DIR]:
    dir_path.mkdir(exist_ok=True)


# === Detection Configuration ===

DETECTION_CONFIG = {
    'num_detectors': 4,
    'detector_ids': ['detector_0', 'detector_1', 'detector_2', 'detector_3'],
    'sampling_rate': 1,  # Hz
    'window_size': 20,   # Number of samples for feature extraction
    'detection_threshold': 0.5,  # Confidence threshold for presence
}


# === CSI Configuration ===

CSI_CONFIG = {
    # Hardware settings
    'sampling_rate': 10,  # Hz (CSI collection rate)
    'subcarriers': 30,  # Number of subcarriers for 20MHz WiFi channel
    'tx_antennas': 1,  # ESP32-S3 typically has 1 TX antenna
    'rx_antennas': 2,  # ESP32-S3 typically has 2 RX antennas
    'fft_size': 64,  # FFT size for CSI processing

    # Calibration settings
    'calibration_duration': 300,  # seconds (5 min default)
    'calibration_samples': 3000,  # Number of samples for calibration

    # Detector configuration
    'detectors': ['csi_1', 'csi_2', 'csi_3', 'csi_4'],
    'detector_hosts': {
        'csi_1': '192.168.1.101',
        'csi_2': '192.168.1.102',
        'csi_3': '192.168.1.103',
        'csi_4': '192.168.1.104',
    },
    'detector_port': 8080,  # WebSocket port for ESP32-S3

    # Communication settings
    'websocket_timeout': 10,  # seconds
    'connection_retry_interval': 5,  # seconds
    'max_connection_attempts': 3,

    # Data buffer settings
    'buffer_size': 100,  # Number of CSI samples to keep in buffer
    'buffer_persistence': False,  # Whether to persist buffer to disk

    # Feature extraction
    'extract_features': True,
    'feature_categories': [
        'amplitude_stats',
        'phase_stats',
        'frequency_domain',
        'temporal',
        'cross_subcarrier',
    ],

    # Sanitization settings
    'enable_lpc': True,  # Linear Phase Compensation
    'enable_cfo_correction': True,  # Carrier Frequency Offset
    'enable_sfo_correction': True,  # Sampling Frequency Offset

    # WebSocket endpoint
    'ws_endpoint': '/ws/csi/{detector_id}',
    'ws_csi_stream': '/ws/csi',  # Aggregated CSI stream
}


# === Machine Learning Configuration ===

ML_CONFIG = {
    # Model paths
    'presence_model_path': MODELS_DIR / 'presence_model.pkl',
    'counting_model_path': MODELS_DIR / 'counting_model.pkl',
    'scaler_path': MODELS_DIR / 'feature_scaler.pkl',

    # Training settings
    'train_test_split': 0.8,
    'random_state': 42,
    'cross_validation_folds': 5,

    # Model hyperparameters
    'presence_model': {
        'type': 'logistic_regression',
        'max_iter': 1000,
        'class_weight': 'balanced',
    },
    'counting_model': {
        'type': 'random_forest',
        'n_estimators': 100,
        'max_depth': 20,
        'min_samples_split': 5,
        'class_weight': 'balanced',
    },

    # Feature settings
    'feature_selection': {
        'enabled': True,
        'max_features': 100,
        'method': 'feature_importance',
    },
}


# === Signal Processing Configuration ===

SIGNAL_PROCESSING_CONFIG = {
    # Filtering
    'enable_filtering': True,
    'filter_type': 'butterworth',
    'cutoff_freq': 0.5,  # Normalized frequency (0-1)
    'filter_order': 4,

    # Windowing
    'window_type': 'hamming',
    'window_size': 20,

    # Feature extraction
    'extract_fft_features': True,
    'extract_time_features': True,
    'extract_statistical_features': True,

    # Outlier detection
    'outlier_method': 'iqr',  # 'iqr', 'zscore', 'isolation_forest'
    'outlier_threshold': 3.0,
}


# === Simulation Configuration ===

SIMULATION_CONFIG = {
    'enabled': True,
    'num_detectors': 4,
    'baseline_rssi': {
        'detector_0': -40,
        'detector_1': -45,
        'detector_2': -50,
        'detector_3': -55,
    },
    'people_attenuation': -4.0,  # dB per person
    'movement_noise': 3.5,  # Additional std when moving
    'static_noise': 1.5,  # Base noise std
    'multipath_factor': 1.5,  # Multipath interference factor
}


# === API Configuration ===

API_CONFIG = {
    'host': '0.0.0.0',
    'port': 8000,
    'reload': True,
    'log_level': 'info',

    # CORS
    'cors_origins': ['*'],
    'cors_methods': ['*'],
    'cors_headers': ['*'],

    # Rate limiting
    'enable_rate_limit': False,
    'rate_limit_requests': 100,
    'rate_limit_period': 60,  # seconds

    # WebSocket
    'websocket_ping_interval': 20,
    'websocket_ping_timeout': 20,
}


# === Spatial Mapping Configuration ===

SPATIAL_CONFIG = {
    'room_size': (10.0, 10.0),  # meters (width, length)
    'detector_positions': [
        (0.0, 0.0),    # detector_0: bottom-left
        (10.0, 0.0),   # detector_1: bottom-right
        (0.0, 10.0),   # detector_2: top-left
        (10.0, 10.0),  # detector_3: top-right
    ],
    'grid_resolution': 0.5,  # meters
    'wall_threshold': 0.7,  # Confidence threshold for wall detection
    'visualization_size': (800, 800),  # pixels
}


# === Logging Configuration ===

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'INFO',
            'formatter': 'standard',
            'filename': str(LOGS_DIR / 'detectpeople.log'),
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
        },
    },
    'loggers': {
        '': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}


# === ESP32-S3 Hardware Configuration ===

ESP32_CONFIG = {
    # WiFi settings
    'wifi_channel': 6,  # 2.4GHz channel
    'wifi_bandwidth': 20,  # MHz (20 or 40)
    'tx_power': 78,  # 0.25dBm units (max 78 = 19.5dBm)

    # CSI collection
    'csi_enabled': True,
    'csi_sampling_rate': 10,  # Hz
    'csi_buffer_size': 128,

    # WebSocket server
    'websocket_port': 8080,
    'websocket_max_clients': 4,

    # Data format
    'csi_format': 'complex',  # 'complex', 'real_imag', 'magnitude_phase'
    'rssi_enabled': True,

    # Power management
    'sleep_enabled': False,
    'sleep_duration': 0,  # seconds
}


# === Testing Configuration ===

TESTING_CONFIG = {
    'test_data_size': 100,
    'random_seed': 42,
    'enable_coverage': True,
    'coverage_threshold': 80,

    # Performance testing
    'performance_test_duration': 60,  # seconds
    'performance_test_throughput': 100,  # requests/second
}


# === Feature Flags ===

FEATURE_FLAGS = {
    'csi_enabled': True,  # Enable CSI data collection
    'spatial_mapping_enabled': True,  # Enable spatial mapping
    'wall_detection_enabled': True,  # Enable wall detection
    'real_time_detection': True,  # Enable real-time detection
    'persist_models': True,  # Save trained models to disk
    'enable_mlops': False,  # Enable ML ops (monitoring, tracking)
}


# === Environment Configuration ===

def load_env_config():
    """Load configuration from environment variables."""
    config = {}

    # API settings
    config['api_host'] = os.getenv('API_HOST', API_CONFIG['host'])
    config['api_port'] = int(os.getenv('API_PORT', API_CONFIG['port']))
    config['api_reload'] = os.getenv('API_RELOAD', 'true').lower() == 'true'

    # CSI settings
    config['csi_enabled'] = os.getenv('CSI_ENABLED', 'true').lower() == 'true'
    config['csi_sampling_rate'] = int(os.getenv('CSI_SAMPLING_RATE', str(CSI_CONFIG['sampling_rate'])))

    # Detector hosts
    for i in range(1, 5):
        host_key = f'CSI_{i}_HOST'
        if host_key in os.environ:
            CSI_CONFIG['detector_hosts'][f'csi_{i}'] = os.environ[host_key]

    # Feature flags
    for flag, default_value in FEATURE_FLAGS.items():
        env_key = f'FEATURE_{flag.upper()}'
        config[flag] = os.getenv(env_key, str(default_value)).lower() == 'true'

    return config


# === Configuration Validation ===

def validate_config() -> List[str]:
    """
    Validate configuration settings.

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Validate CSI config
    if CSI_CONFIG['sampling_rate'] <= 0:
        errors.append("CSI sampling rate must be positive")

    if CSI_CONFIG['subcarriers'] not in [30, 64, 128]:
        errors.append("CSI subcarriers must be 30, 64, or 128")

    # Validate detector configuration
    if len(CSI_CONFIG['detectors']) != len(CSI_CONFIG['detector_hosts']):
        errors.append("Number of detector IDs must match number of detector hosts")

    # Validate ML config
    if ML_CONFIG['train_test_split'] <= 0 or ML_CONFIG['train_test_split'] >= 1:
        errors.append("Train/test split must be between 0 and 1")

    # Validate paths
    if not MODELS_DIR.exists():
        errors.append(f"Models directory does not exist: {MODELS_DIR}")

    return errors


# === Configuration Display ===

def print_config():
    """Print current configuration."""
    print("\n" + "="*60)
    print("WiFi People Detection System Configuration")
    print("="*60)

    print("\n=== Detection ===")
    for key, value in DETECTION_CONFIG.items():
        print(f"  {key}: {value}")

    print("\n=== CSI ===")
    for key, value in CSI_CONFIG.items():
        if key != 'detector_hosts':
            print(f"  {key}: {value}")
    print("  detector_hosts:")
    for det_id, host in CSI_CONFIG['detector_hosts'].items():
        print(f"    {det_id}: {host}")

    print("\n=== Machine Learning ===")
    for key, value in ML_CONFIG.items():
        print(f"  {key}: {value}")

    print("\n=== Signal Processing ===")
    for key, value in SIGNAL_PROCESSING_CONFIG.items():
        print(f"  {key}: {value}")

    print("\n=== API ===")
    for key, value in API_CONFIG.items():
        print(f"  {key}: {value}")

    print("\n=== Feature Flags ===")
    for flag, enabled in FEATURE_FLAGS.items():
        status = "ENABLED" if enabled else "DISABLED"
        print(f"  {flag}: {status}")

    print("\n" + "="*60 + "\n")

    # Validate config
    errors = validate_config()
    if errors:
        print("Configuration Validation Errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("Configuration is valid!")


if __name__ == '__main__':
    print_config()
