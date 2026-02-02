"""
FastAPI Backend for WiFi People Detection System
RESTful API and WebSocket server for real-time detection.
"""
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import asyncio
import logging
from datetime import datetime
import os
from pathlib import Path
import numpy as np

from src.wifi_simulator import WiFiRSSISimulator
from src.signal_processing import SignalProcessor
from src.ml_models import PeopleDetectorML
from src.spatial_mapper import (
    RoomLayoutMapper,
    WallVisualizer,
    generate_svg_floorplan,
    RoomLayout,
    create_sample_wall_grid
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="WiFi People Detection API",
    version="1.0.0",
    description="WiFi RSSI-based people detection system"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
wifi_sim: Optional[WiFiRSSISimulator] = None
signal_processor: Optional[SignalProcessor] = None
ml_models: Optional[PeopleDetectorML] = None
room_mapper: Optional[RoomLayoutMapper] = None
wall_visualizer: Optional[WallVisualizer] = None
latest_detections: Dict[str, any] = {}
latest_layout: Optional[RoomLayout] = None
websocket_clients: List[WebSocket] = []


# === Request/Response Models ===

class DetectionRequest(BaseModel):
    """Request for detection prediction."""
    features: Dict[str, float] = Field(..., description="Feature dictionary from signal processor")


class CalibrationRequest(BaseModel):
    """Request to start calibration."""
    duration_minutes: int = Field(5, description="Calibration duration in minutes")
    room_id: str = Field("default", description="Room identifier")


class DetectionResponse(BaseModel):
    """Detection result response."""
    presence: bool = Field(..., description="Whether people are present")
    presence_confidence: float = Field(..., description="Confidence in presence detection")
    count: int = Field(..., description="Predicted number of people")
    count_confidence: float = Field(..., description="Confidence in count prediction")
    timestamp: datetime = Field(default_factory=datetime.now)


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: datetime
    models_loaded: bool
    simulation_running: bool


# === Startup/Shutdown Events ===

@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    global wifi_sim, signal_processor, ml_models

    logger.info("Starting WiFi People Detection API")

    # Initialize components
    wifi_sim = WiFiRSSISimulator(num_detectors=4)
    signal_processor = SignalProcessor()
    ml_models = PeopleDetectorML()
    room_mapper = RoomLayoutMapper(room_size=(10.0, 10.0))
    wall_visualizer = WallVisualizer()

    # Try to load pre-trained models
    ml_models.load_models()

    # If no models exist, train simple models for demo
    if ml_models.presence_model is None or ml_models.counting_model is None:
        logger.info("No pre-trained models found. Training with synthetic data...")

        # Generate simple synthetic training data
        from sklearn.ensemble import RandomForestClassifier
        import numpy as np

        # Create simple synthetic features
        np.random.seed(42)
        n_samples = 300
        n_features = 80  # Typical number of features from 4 detectors

        # Generate presence detection data
        X_presence = np.random.randn(n_samples, n_features)
        y_presence = np.array([0] * (n_samples // 2) + [1] * (n_samples // 2))

        # Generate counting data
        X_counting = np.random.randn(n_samples * 6, n_features)
        y_counting = np.array([i for i in range(6) for _ in range(n_samples)])

        # Train presence model
        if ml_models.presence_model is None:
            from sklearn.linear_model import LogisticRegression
            from sklearn.preprocessing import StandardScaler
            from sklearn.pipeline import Pipeline

            ml_models.presence_model = Pipeline([
                ('scaler', StandardScaler()),
                ('classifier', LogisticRegression(max_iter=1000, random_state=42))
            ])
            ml_models.presence_model.fit(X_presence, y_presence)
            logger.info("Trained presence detection model")

        # Train counting model
        if ml_models.counting_model is None:
            ml_models.counting_model = RandomForestClassifier(
                n_estimators=50,
                max_depth=10,
                random_state=42
            )
            ml_models.counting_model.fit(X_counting, y_counting)
            logger.info("Trained people counting model")

    # Start background simulation
    asyncio.create_task(simulate_continuous_detection())

    logger.info("Startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down WiFi People Detection API")


# === API Endpoints ===

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint."""
    return {
        "message": "WiFi People Detection API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        models_loaded=ml_models.presence_model is not None and ml_models.counting_model is not None,
        simulation_running=True
    )


@app.post("/api/v1/detection/predict", response_model=DetectionResponse)
async def predict_detection(request: DetectionRequest):
    """
    Make prediction from features.

    Args:
        request: Detection request with features

    Returns:
        Detection response with predictions
    """
    try:
        # Predict presence
        presence, presence_conf = ml_models.predict_presence(request.features)

        # Predict count
        count, count_conf = ml_models.predict_count(request.features)

        return DetectionResponse(
            presence=presence,
            presence_confidence=presence_conf,
            count=count if presence else 0,
            count_confidence=count_conf,
            timestamp=datetime.now()
        )
    except ValueError as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/detection/latest")
async def get_latest_detection():
    """Get latest detection results."""
    if not latest_detections:
        return {"message": "No detections available yet"}
    return latest_detections


@app.post("/api/v1/calibration/start")
async def start_calibration(request: CalibrationRequest):
    """Start calibration process."""
    logger.info(
        f"Calibration started: duration={request.duration_minutes}min, "
        f"room_id={request.room_id}"
    )

    return {
        "message": "Calibration started",
        "duration_minutes": request.duration_minutes,
        "room_id": request.room_id,
        "started_at": datetime.now()
    }


@app.get("/api/v1/simulation/scenarios")
async def get_simulation_scenarios():
    """Get available simulation scenarios."""
    return {
        "scenarios": [
            {"id": 0, "name": "Empty room", "people": 0, "moving": False},
            {"id": 1, "name": "One person stationary", "people": 1, "moving": False},
            {"id": 2, "name": "One person moving", "people": 1, "moving": True},
            {"id": 3, "name": "Two people", "people": 2, "moving": True},
            {"id": 4, "name": "Three people", "people": 3, "moving": False},
            {"id": 5, "name": "Four people", "people": 4, "moving": True},
            {"id": 6, "name": "Five people", "people": 5, "moving": True},
        ]
    }


@app.post("/api/v1/simulation/set")
async def set_simulation_scenario(
    people: int = 0,
    moving: bool = False
):
    """Set simulation scenario."""
    if wifi_sim is None:
        raise HTTPException(status_code=500, detail="Simulator not initialized")

    wifi_sim.set_scenario(people, moving)

    return {
        "message": "Scenario updated",
        "people": people,
        "moving": moving,
        "timestamp": datetime.now()
    }


# === WebSocket Endpoint ===

@app.websocket("/ws/detection")
async def detection_websocket(websocket: WebSocket):
    """
    WebSocket for real-time detection updates.

    Clients connect to receive live detection updates.
    """
    await websocket.accept()
    websocket_clients.append(websocket)
    logger.info("WebSocket client connected")

    try:
        # Send initial state
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to WiFi detection stream",
            "timestamp": datetime.now().isoformat()
        })

        # Keep connection alive and send updates
        while True:
            await asyncio.sleep(10)

            if latest_detections:
                await websocket.send_json({
                    "type": "detection",
                    "data": latest_detections
                })

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
        websocket_clients.remove(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket in websocket_clients:
            websocket_clients.remove(websocket)


# === Background Simulation Task ===

async def simulate_continuous_detection():
    """
    Background task: Continuously simulate WiFi and detect people.

    Runs different scenarios automatically to demonstrate the system.
    """
    logger.info("Starting continuous detection simulation")

    scenarios = [
        (0, False, "Empty room"),
        (1, True, "One person walking"),
        (2, True, "Two people talking"),
        (3, False, "Three people sitting"),
        (0, False, "Empty room"),
        (1, True, "One person working"),
        (4, True, "Four people in meeting"),
        (0, False, "Empty room"),
        (2, False, "Two people working"),
        (5, True, "Five people in group"),
    ]

    scenario_idx = 0

    while True:
        num_people, moving, description = scenarios[scenario_idx]
        wifi_sim.set_scenario(num_people, moving)
        logger.info(f"Scenario: {description}")

        # Collect RSSI for 20 seconds
        rssi_data = {f"detector_{i}": [] for i in range(4)}

        start_time = datetime.now()
        while (datetime.now() - start_time).total_seconds() < 20:
            for det_id in range(4):
                rssi = wifi_sim.simulate_rssi(
                    f"detector_{det_id}",
                    num_people,
                    moving
                )
                rssi_data[f"detector_{det_id}"].append(rssi)

            await asyncio.sleep(1)

        # Extract features from each detector
        all_features = {}
        for detector_id, rssi_values in rssi_data.items():
            features = signal_processor.extract_features(rssi_values)
            all_features.update({f"{detector_id}_{k}": v for k, v in features.items()})

        # Predict
        presence, presence_conf = ml_models.predict_presence(all_features)
        count, count_conf = ml_models.predict_count(all_features)

        # Update latest detection
        latest_detections.update({
            "timestamp": datetime.now().isoformat(),
            "presence": presence,
            "presence_confidence": round(presence_conf, 3),
            "count": count if presence else 0,
            "count_confidence": round(count_conf, 3),
            "scenario": description,
            "actual_people": num_people,
            "rssi_mean": round(np.mean([np.mean(v) for v in rssi_data.values()]), 2)
        })

        logger.info(
            f"Detection: presence={presence}, count={count}, "
            f"confidence={count_conf:.2f}, actual={num_people}"
        )

        # Broadcast to WebSocket clients
        if websocket_clients:
            for client in websocket_clients:
                try:
                    await client.send_json({
                        "type": "detection",
                        "data": latest_detections
                    })
                except Exception as e:
                    logger.error(f"Failed to send WebSocket message: {e}")

        # Move to next scenario
        scenario_idx = (scenario_idx + 1) % len(scenarios)

        await asyncio.sleep(5)  # Brief pause between scenarios


# === Room Layout Endpoints ===

@app.get("/api/v1/room-layout")
async def get_room_layout():
    """
    Return current detected room layout.

    Returns:
        Room layout with walls, dimensions, corners, etc.
    """
    global latest_layout

    if latest_layout is None:
        # Generate sample layout if none exists
        logger.info("No layout detected yet, generating sample...")
        sample_grid = create_sample_wall_grid(room_type="rectangular")

        detector_positions = [
            (2.0, 2.0),
            (8.0, 2.0),
            (2.0, 8.0),
            (8.0, 8.0)
        ]

        latest_layout = room_mapper.walls_to_layout(sample_grid, detector_positions)
        latest_layout = room_mapper.optimize_layout(latest_layout)

    return latest_layout.to_dict()


@app.get("/api/v1/room-layout/floorplan")
async def get_floorplan():
    """
    Return SVG floorplan for dashboard.

    Returns:
        SVG string of floorplan
    """
    global latest_layout

    if latest_layout is None:
        # Get or create layout
        await get_room_layout()

    svg_string = generate_svg_floorplan(latest_layout)

    return {
        "svg": svg_string,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/v1/room-layout/calibrate")
async def calibrate_room_layout():
    """
    Trigger room layout detection and mapping.

    Simulates wall detection and creates a new room layout.
    In production, this would trigger actual WiFi-based wall detection.

    Returns:
        Calibration status and detected layout
    """
    global latest_layout

    logger.info("Starting room layout calibration...")

    # Simulate wall detection
    # In production, this would collect WiFi RSSI data and detect walls
    sample_grid = create_sample_wall_grid(room_type="rectangular")

    detector_positions = [
        (2.0, 2.0),
        (8.0, 2.0),
        (2.0, 8.0),
        (8.0, 8.0)
    ]

    # Convert to layout
    latest_layout = room_mapper.walls_to_layout(sample_grid, detector_positions)

    # Optimize layout
    latest_layout = room_mapper.optimize_layout(latest_layout)

    # Generate visualizations
    output_dir = Path("docs/floorplan_examples")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Floorplan image
    wall_visualizer.generate_floorplan_image(
        latest_layout,
        str(output_dir / "latest_floorplan.png")
    )

    # 3D view
    wall_visualizer.generate_3d_room_view(
        latest_layout,
        str(output_dir / "latest_3d_view.png")
    )

    # Heatmap
    wall_visualizer.generate_heatmap(
        sample_grid,
        str(output_dir / "latest_heatmap.png")
    )

    # Save layout data
    latest_layout.save(str(output_dir / "latest_layout.json"))

    logger.info(f"Calibration complete: {len(latest_layout.walls)} walls detected")

    return {
        "status": "success",
        "message": "Room layout calibration complete",
        "walls_detected": len(latest_layout.walls),
        "area_m2": latest_layout.area,
        "corners": len(latest_layout.corners),
        "timestamp": datetime.now().isoformat(),
        "layout": latest_layout.to_dict()
    }


@app.get("/api/v1/room-layout/heatmap")
async def get_wall_heatmap():
    """
    Return wall detection probability heatmap.

    Returns:
        Heatmap visualization data
    """
    global latest_layout

    # Generate sample grid if no layout
    if latest_layout is None:
        await get_room_layout()

    # Create sample probability grid
    sample_grid = create_sample_wall_grid(room_type="rectangular")

    # Generate heatmap
    output_path = "docs/floorplan_examples/api_heatmap.png"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    wall_visualizer.generate_heatmap(
        sample_grid,
        output_path,
        "Wall Detection Probability Heatmap"
    )

    return {
        "status": "success",
        "heatmap_path": output_path,
        "timestamp": datetime.now().isoformat(),
        "grid_shape": sample_grid.shape,
        "description": "Wall detection probability heatmap (blue=low, red=high)"
    }


@app.get("/api/v1/room-layout/images")
async def get_layout_images():
    """
    Get list of available layout visualization images.

    Returns:
        List of image paths and metadata
    """
    output_dir = Path("docs/floorplan_examples")

    if not output_dir.exists():
        return {
            "images": [],
            "message": "No layout images available"
        }

    image_files = []
    for ext in ['*.png', '*.jpg', '*.svg']:
        for img_path in output_dir.glob(ext):
            image_files.append({
                "name": img_path.name,
                "path": str(img_path),
                "size": img_path.stat().st_size,
                "modified": datetime.fromtimestamp(img_path.stat().st_mtime).isoformat()
            })

    return {
        "images": sorted(image_files, key=lambda x: x['modified'], reverse=True),
        "count": len(image_files)
    }


# === Main Entry Point ===

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
