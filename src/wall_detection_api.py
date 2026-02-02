"""
Wall Detection API Module

Adds wall detection endpoints to the main FastAPI application.
"""

from fastapi import HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, Optional, List
from datetime import datetime
import asyncio
import logging
import uuid

logger = logging.getLogger(__name__)


# === Request/Response Models ===

class WallDetectionRequest(BaseModel):
    """Request for wall detection."""
    duration_seconds: int = Field(30, description="CSI data collection duration in seconds", ge=10, le=300)
    classify_materials: bool = Field(True, description="Whether to classify wall materials")


class WallCalibrationRequest(BaseModel):
    """Request to start wall detection calibration."""
    duration_seconds: int = Field(300, description="Calibration duration in seconds", ge=60, le=1800)


class WallStatusResponse(BaseModel):
    """Wall detection system status response."""
    initialized: bool
    calibrating: bool
    current_layout: Optional[Dict]
    last_detection: Optional[str]
    metrics: Dict


class CalibrationStatusResponse(BaseModel):
    """Calibration job status response."""
    job_id: str
    status: str  # pending, running, completed, failed
    progress: float  # 0-100
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error: Optional[str]


# === Calibration Job Management ===

class CalibrationJobManager:
    """Manages calibration jobs"""

    def __init__(self):
        self.jobs: Dict[str, Dict] = {}
        self.active_job: Optional[str] = None

    def create_job(self, duration_seconds: int) -> str:
        """Create a new calibration job"""
        job_id = str(uuid.uuid4())

        self.jobs[job_id] = {
            'status': 'pending',
            'progress': 0.0,
            'started_at': None,
            'completed_at': None,
            'error': None,
            'duration_seconds': duration_seconds
        }

        return job_id

    def start_job(self, job_id: str):
        """Start a calibration job"""
        if job_id not in self.jobs:
            raise ValueError(f"Job {job_id} not found")

        if self.active_job:
            raise RuntimeError(f"Calibration already running: {self.active_job}")

        self.jobs[job_id]['status'] = 'running'
        self.jobs[job_id]['started_at'] = datetime.now()
        self.active_job = job_id

    def update_progress(self, job_id: str, progress: float):
        """Update job progress"""
        if job_id in self.jobs:
            self.jobs[job_id]['progress'] = progress

    def complete_job(self, job_id: str, error: Optional[str] = None):
        """Mark job as complete"""
        if job_id in self.jobs:
            self.jobs[job_id]['status'] = 'completed' if error is None else 'failed'
            self.jobs[job_id]['completed_at'] = datetime.now()
            self.jobs[job_id]['error'] = error
            self.active_job = None

    def get_job(self, job_id: str) -> Optional[Dict]:
        """Get job details"""
        return self.jobs.get(job_id)


# Global calibration job manager
calibration_manager = CalibrationJobManager()


# === API Endpoints ===

async def register_wall_detection_routes(app, wall_system):
    """
    Register wall detection routes with FastAPI app

    Args:
        app: FastAPI application
        wall_system: WallDetectionSystem instance
    """

    @app.get("/api/v1/walls/status", response_model=WallStatusResponse)
    async def get_wall_detection_status():
        """Get wall detection system status"""
        try:
            status = wall_system.get_system_status()
            return WallStatusResponse(**status)
        except Exception as e:
            logger.error(f"Error getting wall status: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/v1/walls/detect")
    async def detect_walls(request: WallDetectionRequest):
        """
        Trigger wall detection

        Returns detected room layout including walls, materials, and dimensions.
        Takes approximately 30 seconds for data collection and processing.
        """
        try:
            # Detect room layout
            layout = await wall_system.detect_room_layout(
                duration_seconds=request.duration_seconds,
                classify_materials=request.classify_materials
            )

            # Generate visualizations
            visualizations = wall_system.generate_visualizations(layout)

            # Return layout details
            return {
                "status": "success",
                "layout": {
                    "dimensions": layout.dimensions,
                    "area": layout.area,
                    "perimeter": layout.perimeter,
                    "confidence": layout.confidence,
                    "wall_count": len(layout.walls),
                    "walls": [
                        {
                            "start": wall.start_point,
                            "end": wall.end_point,
                            "thickness": wall.thickness,
                            "material": wall.material,
                            "confidence": wall.confidence
                        }
                        for wall in layout.walls
                    ]
                },
                "visualizations": visualizations,
                "detected_at": layout.detected_at
            }

        except Exception as e:
            logger.error(f"Wall detection error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/v1/walls/calibrate")
    async def start_wall_calibration(
        request: WallCalibrationRequest,
        background_tasks: BackgroundTasks
    ):
        """
        Start wall detection calibration

        Calibration runs in background. Returns job ID for tracking.
        Calibration takes approximately 5 minutes with an empty room.
        """
        try:
            # Check if calibration already running
            if wall_system.is_calibrating:
                raise HTTPException(
                    status_code=409,
                    detail="Calibration already in progress"
                )

            # Create calibration job
            job_id = calibration_manager.create_job(request.duration_seconds)

            # Start calibration in background
            background_tasks.add_task(
                run_calibration,
                wall_system,
                job_id,
                request.duration_seconds
            )

            return {
                "message": "Calibration started",
                "job_id": job_id,
                "estimated_time_seconds": request.duration_seconds
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Calibration start error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/v1/walls/calibration/{job_id}", response_model=CalibrationStatusResponse)
    async def get_calibration_status(job_id: str):
        """Get calibration job status"""
        job = calibration_manager.get_job(job_id)

        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")

        return CalibrationStatusResponse(
            job_id=job_id,
            **job
        )

    @app.get("/api/v1/walls/layout")
    async def get_current_layout():
        """Get current detected room layout"""
        if wall_system.current_layout is None:
            raise HTTPException(
                status_code=404,
                detail="No layout detected yet. Run /api/v1/walls/detect first"
            )

        layout = wall_system.current_layout

        return {
            "dimensions": layout.dimensions,
            "area": layout.area,
            "perimeter": layout.perimeter,
            "confidence": layout.confidence,
            "wall_count": len(layout.walls),
            "walls": [
                {
                    "start": wall.start_point,
                    "end": wall.end_point,
                    "thickness": wall.thickness,
                    "material": wall.material,
                    "confidence": wall.confidence
                }
                for wall in layout.walls
            ],
            "detected_at": layout.detected_at
        }

    @app.get("/api/v1/walls/visualizations")
    async def get_visualizations():
        """Get paths to all generated visualizations"""
        try:
            if wall_system.current_layout is None:
                raise HTTPException(
                    status_code=404,
                    detail="No layout detected yet"
                )

            # Generate visualizations
            visualizations = wall_system.generate_visualizations()

            return {
                "visualizations": visualizations,
                "generated_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Visualization error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/v1/walls/export")
    async def export_layout():
        """Export current room layout to JSON"""
        try:
            if wall_system.current_layout is None:
                raise HTTPException(
                    status_code=404,
                    detail="No layout detected yet"
                )

            export_path = wall_system.export_layout()

            return {
                "message": "Layout exported successfully",
                "path": export_path
            }

        except Exception as e:
            logger.error(f"Export error: {e}")
            raise HTTPException(status_code=500, detail=str(e))


# === Background Task ===

async def run_calibration(
    wall_system,
    job_id: str,
    duration_seconds: int
):
    """
    Run calibration in background

    Args:
        wall_system: WallDetectionSystem instance
        job_id: Calibration job ID
        duration_seconds: Calibration duration
    """
    try:
        # Start job
        calibration_manager.start_job(job_id)

        # Progress callback
        async def progress_callback(progress: float):
            calibration_manager.update_progress(job_id, progress * 100)

        # Run calibration
        await wall_system.calibrate_system(
            duration_seconds=duration_seconds,
            progress_callback=progress_callback
        )

        # Mark complete
        calibration_manager.complete_job(job_id)
        logger.info(f"Calibration job {job_id} completed successfully")

    except Exception as e:
        logger.error(f"Calibration job {job_id} failed: {e}")
        calibration_manager.complete_job(job_id, error=str(e))


# === Integration Helper ===

async def initialize_wall_detection_api(app):
    """
    Initialize wall detection API

    Call this during FastAPI startup to register wall detection routes.

    Args:
        app: FastAPI application
    """
    try:
        # Import wall detection system
        from src.wall_detection_system import WallDetectionSystem

        # Create and initialize wall system
        wall_system = WallDetectionSystem()
        await wall_system.initialize()

        # Store in app state
        app.state.wall_system = wall_system

        # Register routes
        await register_wall_detection_routes(app, wall_system)

        logger.info("Wall detection API initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize wall detection API: {e}")
        # Don't fail startup, just log the error
