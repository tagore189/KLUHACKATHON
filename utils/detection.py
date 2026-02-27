"""Refined local damage detection module using OpenCV with spatial heuristics."""
import json
import os
import cv2
import numpy as np

def init_client(api_key=None):
    """No-op for local detection."""
    return None


def detect_damage(image_path):
    """
    Analyze vehicle damage locally using OpenCV image processing and spatial heuristics.
    Maps image coordinates to logical vehicle parts and analyzes contour shapes.
    """
    try:
        # Load image
        img = cv2.imread(image_path)
        if img is None:
            raise FileNotFoundError(f"Could not read image at {image_path}")

        height, width = img.shape[:2]

        # Basic image processing for damage detection
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Use adaptive thresholding and Canny to find structural variations
        edges = cv2.Canny(blurred, 30, 100)
        
        # Dilate edges to bridge small gaps in damage regions
        kernel = np.ones((3,3), np.uint8)
        dilated = cv2.dilate(edges, kernel, iterations=1)
        
        # Find contours
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter significant areas (minimizing noise)
        significant_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > 800]
        
        damages = []
        for cnt in significant_contours[:8]: # Analyze top 8 potential points
            x, y, w, h = cv2.boundingRect(cnt)
            area = cv2.contourArea(cnt)
            aspect_ratio = float(w)/h if h > 0 else 0
            
            # 1. Precise Part Identification via Spatial Mapping (Heuristics)
            # Normalizing coordinates (0.0 to 1.0)
            nx = (x + w/2) / width
            ny = (y + h/2) / height
            
            part = "body_panel"
            if ny > 0.75:
                part = "front_bumper" if nx < 0.5 else "rear_bumper"
            elif ny < 0.35:
                part = "hood" if nx < 0.7 else "roof"
            elif nx < 0.2 or nx > 0.8:
                part = "fender"
            elif ny > 0.4 and ny < 0.7:
                part = "door"
            
            # Specific check for headlights/taillights (corners)
            if (nx < 0.15 or nx > 0.85) and (ny > 0.6 and ny < 0.8):
                part = "headlight" if nx < 0.5 else "taillight"

            # 2. Damage Type Classification via Shape Analysis
            # Long, thin contours are likely scratches. Large, rounder ones are dents.
            if aspect_ratio > 4 or aspect_ratio < 0.25:
                damage_type = "scratch"
            elif area > 10000:
                damage_type = "dent"
            elif area > 5000:
                damage_type = "deformation"
            else:
                damage_type = "paint_damage"

            # 3. Severity Calculation
            severity = "minor"
            if area > 15000 or (damage_type == "dent" and area > 8000):
                severity = "moderate"
            if area > 35000:
                severity = "severe"

            damages.append({
                "part": part,
                "damage_type": damage_type,
                "severity": severity,
                "confidence": round(0.75 + (min(area, 20000) / 200000), 2),
                "description": f"Local analysis detected {damage_type} on the {part.replace('_', ' ')} (Size: {int(area)}px)."
            })

        # Final Logic & Summary
        vehicle_detected = len(significant_contours) > 0
        overall_severity = "minor"
        if len(damages) > 4:
            overall_severity = "moderate"
        if any(d["severity"] == "severe" for d in damages):
            overall_severity = "severe"

        result = {
            "vehicle_detected": vehicle_detected,
            "vehicle_type": "sedan", # Simulated detection
            "vehicle_color": "detected",
            "damages": damages,
            "overall_severity": overall_severity,
            "drivable": overall_severity != "severe",
            "summary": f"Custom Local API detected {len(damages)} precise damage points across the vehicle using spatial heuristics."
        }
        
        return result

    except Exception as e:
        print(f"Local detection error: {str(e)}")
        raise e
