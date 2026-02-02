"""
CSI API Integration Module

This file contains the CSI-specific endpoints to be integrated into the main API.
"""
from fastapi import HTTPException, WebSocket
from typing import Dict, Optional
import asyncio
import logging
from datetime import datetime
import numpy as np

from src.csi_collector import CSICollector, CSICollectorManager, CSIData, CSI_CONFIG

logger = logging.getLogger(__name__)

# === Request/Response Models ===

from pydantic import BaseModel, Field


class CSIDataResponse(BaseModel):
    """CSI data response."""
    timestamp: datetime
    detector_id: str
    amplitude_mean: float
    amplitude_std: float
    phase_std: float
    rssi: float
    num_subcarriers: int


class CSICalibrationResponse(BaseModel):
    """CSI calibration response."""
    message: str
    detector_id: str
    calibration_started: datetime
    estimated_completion: datetime


# === CSI Endpoints to be added to api.py ===

async def get_latest_csi(
    latest_csi_data: Dict[str, CSIData]
) -> Dict[str, CSIDataResponse]:
    """
    Get latest CSI measurements from all detectors.

    Returns:
        Dictionary mapping detector_id to CSI data summary
    """
    if not latest_csi_data:
        return {"message": "No CSI data available yet"}

    response = {}
    for detector_id, csi_data in latest_csi_data.items():
        response[detector_id] = CSIDataResponse(
            timestamp=csi_data.timestamp,
            detector_id=csi_data.detector_id,
            amplitude_mean=float(np.mean(csi_data.amplitude)),
            amplitude_std=float(np.std(csi_data.amplitude)),
            phase_std=float(np.std(csi_data.phase)),
            rssi=csi_data.rssi,
            num_subcarriers=len(csi_data.subcarriers)
        )

    return response


async def get_csi_by_detector(
    detector_id: str,
    latest_csi_data: Dict[str, CSIData]
) -> CSIDataResponse:
    """
    Get latest CSI data for specific detector.

    Args:
        detector_id: CSI detector identifier

    Returns:
        CSI data for specified detector
    """
    if detector_id not in latest_csi_data:
        raise HTTPException(
            status_code=404,
            detail=f"CSI data for {detector_id} not available"
        )

    csi_data = latest_csi_data[detector_id]

    return CSIDataResponse(
        timestamp=csi_data.timestamp,
        detector_id=csi_data.detector_id,
        amplitude_mean=float(np.mean(csi_data.amplitude)),
        amplitude_std=float(np.std(csi_data.amplitude)),
        phase_std=float(np.std(csi_data.phase)),
        rssi=csi_data.rssi,
        num_subcarriers=len(csi_data.subcarriers)
    )


async def calibrate_csi(
    csi_manager: CSICollectorManager,
    detector_id: Optional[str] = None,
    duration_minutes: int = 5
) -> CSICalibrationResponse:
    """
    Trigger CSI calibration routine.

    Collects baseline CSI data for noise floor estimation and offset correction.

    Args:
        csi_manager: CSI collector manager instance
        detector_id: Specific detector to calibrate (None = all detectors)
        duration_minutes: Calibration duration in minutes

    Returns:
        Calibration status response
    """
    if csi_manager is None:
        raise HTTPException(
            status_code=500,
            detail="CSI manager not initialized"
        )

    duration_seconds = duration_minutes * 60
    start_time = datetime.now()
    completion_time = datetime.fromtimestamp(
        start_time.timestamp() + duration_seconds
    )

    if detector_id:
        # Calibrate specific detector
        collector = csi_manager.get_collector(detector_id)
        if not collector:
            raise HTTPException(
                status_code=404,
                detail=f"Detector {detector_id} not found"
            )

        # Start calibration in background
        asyncio.create_task(collector.calibrate(duration_seconds))

        return CSICalibrationResponse(
            message=f"Calibration started for {detector_id}",
            detector_id=detector_id,
            calibration_started=start_time,
            estimated_completion=completion_time
        )
    else:
        # Calibrate all detectors
        for collector in csi_manager.collectors.values():
            asyncio.create_task(collector.calibrate(duration_seconds))

        return CSICalibrationResponse(
            message="Calibration started for all detectors",
            detector_id="all",
            calibration_started=start_time,
            estimated_completion=completion_time
        )


async def get_csi_features(
    detector_id: str,
    latest_csi_data: Dict[str, CSIData],
    csi_manager: CSICollectorManager
):
    """
    Extract features from latest CSI data for specific detector.

    Args:
        detector_id: CSI detector identifier
        latest_csi_data: Dictionary of latest CSI data
        csi_manager: CSI collector manager instance

    Returns:
        Dictionary of extracted features (500-1000 features)
    """
    if detector_id not in latest_csi_data:
        raise HTTPException(
            status_code=404,
            detail=f"No CSI data for {detector_id}"
        )

    csi_data = latest_csi_data[detector_id]

    # Get collector to extract features
    collector = csi_manager.get_collector(detector_id)
    if not collector:
        raise HTTPException(
            status_code=404,
            detail=f"Collector {detector_id} not found"
        )

    # Extract features
    features = collector.extract_features(csi_data)

    return {
        "detector_id": detector_id,
        "timestamp": csi_data.timestamp.isoformat(),
        "num_features": len(features),
        "features": features
    }


def get_csi_config() -> Dict:
    """Get CSI configuration."""
    return CSI_CONFIG


async def get_csi_status(csi_manager: Optional[CSICollectorManager]) -> Dict:
    """Get CSI collector status."""
    if csi_manager is None:
        return {
            "status": "not_initialized",
            "collectors": {}
        }

    status = {
        "status": "initialized",
        "collectors": {}
    }

    for detector_id, collector in csi_manager.collectors.items():
        status["collectors"][detector_id] = {
            "detector_id": detector_id,
            "host": collector.host,
            "port": collector.port,
            "connected": collector.is_connected,
            "calibrated": collector.is_calibrated,
            "buffer_size": len(collector.csi_buffer)
        }

    return status


# === Background CSI Collection Task ===

async def collect_csi_continuous(
    csi_manager: Optional[CSICollectorManager],
    latest_csi_data: Dict[str, CSIData],
    websocket_clients: list
):
    """
    Background task: Continuously collect CSI data from all detectors.

    Args:
        csi_manager: CSI collector manager instance
        latest_csi_data: Dictionary to store latest CSI data
        websocket_clients: List of connected WebSocket clients
    """
    if csi_manager is None:
        logger.warning("CSI manager not initialized, skipping CSI collection")
        return

    logger.info("Starting continuous CSI data collection")

    while True:
        try:
            # Collect CSI data from all detectors
            csi_data_dict = await csi_manager.collect_all()

            # Update latest CSI data
            for detector_id, csi_data in csi_data_dict.items():
                if csi_data is not None:
                    latest_csi_data[detector_id] = csi_data

            # Broadcast to WebSocket clients
            if latest_csi_data and websocket_clients:
                for client in websocket_clients:
                    try:
                        await client.send_json({
                            "type": "csi",
                            "data": {
                                det_id: data.to_dict()
                                for det_id, data in latest_csi_data.items()
                            }
                        })
                    except Exception as e:
                        logger.error(f"Failed to send CSI WebSocket message: {e}")

        except Exception as e:
            logger.error(f"Error in CSI collection: {e}")

        # Wait for next collection cycle (10 Hz = 100ms)
        await asyncio.sleep(0.1)


# === CSI WebSocket Handler ===

async def csi_websocket_handler(
    websocket: WebSocket,
    latest_csi_data: Dict[str, CSIData],
    websocket_clients: list
):
    """
    WebSocket endpoint for CSI-specific data streaming.

    Args:
        websocket: WebSocket connection
        latest_csi_data: Dictionary of latest CSI data
        websocket_clients: List of connected clients
    """
    await websocket.accept()
    websocket_clients.append(websocket)
    logger.info("CSI WebSocket client connected")

    try:
        # Send initial state
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to CSI data stream",
            "timestamp": datetime.now().isoformat()
        })

        # Keep connection alive and send updates
        while True:
            await asyncio.sleep(10)

            # Send CSI updates
            if latest_csi_data:
                await websocket.send_json({
                    "type": "csi",
                    "data": {
                        det_id: data.to_dict()
                        for det_id, data in latest_csi_data.items()
                    }
                })

    except Exception as e:
        logger.error(f"CSI WebSocket error: {e}")
    finally:
        if websocket in websocket_clients:
            websocket_clients.remove(websocket)


# === Integration Helper ===

def get_csi_integration_code():
    """
    Return code snippets to integrate CSI into main api.py file.

    Usage:
        1. Import CSI modules at top of api.py
        2. Add CSI global state variables
        3. Add CSI endpoints
        4. Initialize CSI manager in startup_event
        5. Start CSI background task
    """
    return {
        "imports": """
# CSI imports
from src.csi_collector import CSICollector, CSICollectorManager, CSIData, CSI_CONFIG
""",
        "global_state": """
# CSI collectors
csi_manager: Optional[CSICollectorManager] = None
latest_csi_data: Dict[str, CSIData] = {}
csi_calibration_status: Dict[str, bool] = {}
""",
        "startup_code": """
    # Initialize CSI collector manager (if detectors configured)
    detector_configs = [
        {'id': f'csi_{i}', 'host': f'192.168.1.{100+i}', 'port': 8080}
        for i in range(1, 5)
    ]
    csi_manager = CSICollectorManager(detector_configs)

    # Start CSI data collection (background task)
    asyncio.create_task(collect_csi_continuous(
        csi_manager, latest_csi_data, websocket_clients
    ))
""",
        "endpoints": """
# CSI endpoints
@app.get("/api/v1/csi/latest")
async def get_latest_csi_endpoint():
    return await get_latest_csi(latest_csi_data)

@app.get("/api/v1/csi/detector/{detector_id}")
async def get_csi_by_detector_endpoint(detector_id: str):
    return await get_csi_by_detector(detector_id, latest_csi_data)

@app.post("/api/v1/csi/calibrate")
async def calibrate_csi_endpoint(
    detector_id: Optional[str] = None,
    duration_minutes: int = 5
):
    return await calibrate_csi(csi_manager, detector_id, duration_minutes)

@app.get("/api/v1/csi/features/{detector_id}")
async def get_csi_features_endpoint(detector_id: str):
    return await get_csi_features(detector_id, latest_csi_data, csi_manager)

@app.get("/api/v1/csi/config")
async def get_csi_config_endpoint():
    return get_csi_config()

@app.get("/api/v1/csi/status")
async def get_csi_status_endpoint():
    return await get_csi_status(csi_manager)

@app.websocket("/ws/csi")
async def csi_websocket_endpoint(websocket: WebSocket):
    await csi_websocket_handler(websocket, latest_csi_data, websocket_clients)
"""
    }


if __name__ == '__main__':
    print("CSI API Integration Module")
    print("\nIntegration code snippets:")
    integration_code = get_csi_integration_code()
    for section, code in integration_code.items():
        print(f"\n=== {section.upper()} ===")
        print(code)
