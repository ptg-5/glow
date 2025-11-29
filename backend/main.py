from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import uvicorn

from .database import init_db, get_db, DetectionEvent, SensorLog

app = FastAPI(title="Hailo AI Backend")

# --- Pydantic Models ---
class DetectionCreate(BaseModel):
    label: str
    confidence: float
    bbox_xmin: float
    bbox_ymin: float
    bbox_width: float
    bbox_height: float

class DetectionResponse(DetectionCreate):
    id: int
    timestamp: datetime
    class Config:
        orm_mode = True

class SensorDataCreate(BaseModel):
    temperature: float
    humidity: float
    cpu_usage: float

class SensorDataResponse(SensorDataCreate):
    id: int
    timestamp: datetime
    class Config:
        orm_mode = True

# --- Events ---
@app.on_event("startup")
def on_startup():
    init_db()

# --- Endpoints ---

@app.get("/")
def read_root():
    return {"status": "running", "service": "Hailo AI Backend"}

# Detection Endpoints
@app.post("/detections/", response_model=DetectionResponse)
def create_detection(detection: DetectionCreate, db: Session = Depends(get_db)):
    db_detection = DetectionEvent(**detection.dict())
    db.add(db_detection)
    db.commit()
    db.refresh(db_detection)
    return db_detection

@app.get("/detections/", response_model=List[DetectionResponse])
def read_detections(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    detections = db.query(DetectionEvent).order_by(DetectionEvent.timestamp.desc()).offset(skip).limit(limit).all()
    return detections

# Sensor Endpoints
@app.post("/sensors/", response_model=SensorDataResponse)
def create_sensor_log(data: SensorDataCreate, db: Session = Depends(get_db)):
    db_log = SensorLog(**data.dict())
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

@app.get("/sensors/latest", response_model=SensorDataResponse)
def read_latest_sensor(db: Session = Depends(get_db)):
    latest = db.query(SensorLog).order_by(SensorLog.timestamp.desc()).first()
    if latest is None:
        raise HTTPException(status_code=404, detail="No sensor data found")
    return latest

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
