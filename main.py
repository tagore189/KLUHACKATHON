import os
import uuid
import shutil
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from utils.preprocessing import allowed_file, preprocess_image, ensure_upload_dir, get_image_metadata
from utils.detection import detect_damage, init_client
from utils.severity import assess_severity
from utils.cost_estimator import estimate_costs, load_cost_data
from utils.report_generator import generate_report

# Load environment variables
load_dotenv()

app = FastAPI(
    title="VisionClaim API",
    description="Automotive Damage Estimation using Google Gemini 1.5 Flash",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure upload directory exists and mount it as static
upload_dir = ensure_upload_dir()
app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")

@app.get("/")
async def root():
    return {
        "message": "Welcome to your Custom Local VisionClaim API",
        "status": "online",
        "engine": "Local OpenCV Analysis",
        "endpoints": {
            "root": "GET /",
            "analyze": "POST /analyze",
            "test": "POST /test",
            "docs": "/docs"
        }
    }

@app.post("/test")
async def test_post(data: dict):
    """Simple POST endpoint that echoes back the received data."""
    return {
        "message": "POST request received successfully!",
        "received_data": data
    }

@app.post("/analyze")
async def analyze_image(file: UploadFile = File(...), currency: str = "INR"):
    """
    Upload an image of a damaged vehicle and get a structured AI analysis.
    
    - **file**: The image file (png, jpg, jpeg, webp, bmp)
    - **currency**: Target currency for cost estimation (default: INR)
    """
    if not allowed_file(file.filename):
        raise HTTPException(
            status_code=400, 
            detail="Invalid file type. Allowed: png, jpg, jpeg, webp, bmp"
        )

    try:
        # Create unique filename
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(upload_dir, filename)

        # Save uploaded file
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Preprocess
        preprocess_image(filepath)

        # Get image metadata
        metadata = get_image_metadata(filepath)

        # Detect damage using Gemini
        detection_result = detect_damage(filepath)

        if not detection_result.get('vehicle_detected', False):
            raise HTTPException(
                status_code=400, 
                detail="No vehicle detected in the image. Please upload a clear photo of a damaged vehicle."
            )

        # Assess severity
        severity_assessment = assess_severity(detection_result.get('damages', []))

        # Estimate costs
        cost_estimate = estimate_costs(
            detection_result.get('damages', []),
            severity_assessment,
            target_currency=currency
        )

        # Generate report
        report = generate_report(
            detection_result,
            severity_assessment,
            cost_estimate,
            image_filename=filename
        )

        # Add metadata and full image URL
        report['image_url'] = f'/uploads/{filename}'
        report['image_metadata'] = metadata
        
        return report

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
