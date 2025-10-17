"""
User Feedback API
Allows HR team members to submit feedback and bug reports
"""
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from typing import List, Optional
from datetime import datetime
import os
import uuid
import logging
import json

router = APIRouter(prefix="/feedback", tags=["feedback"])
logger = logging.getLogger(__name__)

# Feedback storage directory
FEEDBACK_DIR = "feedback_submissions"
os.makedirs(FEEDBACK_DIR, exist_ok=True)


@router.post("")
async def submit_feedback(
    type: str = Form(...),
    priority: str = Form("medium"),
    title: str = Form(...),
    description: str = Form(...),
    page: str = Form(...),
    userAgent: str = Form(""),
    screenResolution: str = Form(""),
    screenshots: List[UploadFile] = File(default=[])
):
    """
    Submit user feedback with optional screenshots
    
    Args:
        type: Type of feedback (bug, feature, general)
        priority: Priority level (low, medium, high, critical)
        title: Brief title
        description: Detailed description
        page: Current page URL
        userAgent: Browser user agent
        screenResolution: Screen resolution
        screenshots: Optional screenshot files
    """
    try:
        # Generate unique feedback ID
        feedback_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        feedback_folder = os.path.join(FEEDBACK_DIR, f"{timestamp}_{feedback_id}")
        os.makedirs(feedback_folder, exist_ok=True)
        
        # Save screenshots
        screenshot_paths = []
        for idx, screenshot in enumerate(screenshots):
            if screenshot.filename:
                # Generate safe filename
                ext = os.path.splitext(screenshot.filename)[1]
                screenshot_filename = f"screenshot_{idx + 1}{ext}"
                screenshot_path = os.path.join(feedback_folder, screenshot_filename)
                
                # Save file
                with open(screenshot_path, "wb") as f:
                    content = await screenshot.read()
                    f.write(content)
                
                screenshot_paths.append(screenshot_filename)
        
        # Create feedback data
        feedback_data = {
            "id": feedback_id,
            "timestamp": datetime.now().isoformat(),
            "type": type,
            "priority": priority,
            "title": title,
            "description": description,
            "page": page,
            "userAgent": userAgent,
            "screenResolution": screenResolution,
            "screenshots": screenshot_paths,
            "status": "new"
        }
        
        # Save feedback as JSON
        feedback_file = os.path.join(feedback_folder, "feedback.json")
        with open(feedback_file, "w") as f:
            json.dump(feedback_data, f, indent=2)
        
        # Log feedback submission
        logger.info(f"Feedback submitted: {feedback_id} - {type} - {title}")
        
        # TODO: Send email notification to dev team
        # TODO: Create Jira/GitHub issue automatically
        
        return {
            "success": True,
            "message": "Feedback submitted successfully",
            "feedback_id": feedback_id
        }
        
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to submit feedback")


@router.get("/list")
async def list_feedback():
    """
    List all feedback submissions (for admin review)
    """
    try:
        feedbacks = []
        
        if os.path.exists(FEEDBACK_DIR):
            for folder in os.listdir(FEEDBACK_DIR):
                feedback_path = os.path.join(FEEDBACK_DIR, folder, "feedback.json")
                if os.path.exists(feedback_path):
                    with open(feedback_path, "r") as f:
                        feedback = json.load(f)
                        # Add folder name to feedback data for easy screenshot access
                        feedback['folder_name'] = folder
                        feedbacks.append(feedback)
        
        # Sort by timestamp (newest first)
        feedbacks.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return {
            "success": True,
            "feedbacks": feedbacks,
            "total": len(feedbacks)
        }
        
    except Exception as e:
        logger.error(f"Error listing feedback: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list feedback")
