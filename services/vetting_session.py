"""
Vetting Session Service
Temporary storage for resume vetting results before approval/upload to database
"""

import json
import os
import hashlib
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class VettingSession:
    """Manage temporary storage for resume vetting sessions"""
    
    def __init__(self, session_dir: str = "temp/vetting_sessions"):
        self.session_dir = session_dir
        os.makedirs(session_dir, exist_ok=True)
        
    def _get_session_file(self, session_id: str) -> str:
        """Get path to session storage file"""
        return os.path.join(self.session_dir, f"{session_id}.json")
    
    def _get_file_hash(self, file_content: bytes) -> str:
        """Generate hash for file content"""
        return hashlib.sha256(file_content).hexdigest()
    
    def create_session(self, session_id: str) -> Dict:
        """Create a new vetting session"""
        session_data = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "scanned_resumes": {},
            "approved": [],
            "rejected": []
        }
        
        session_file = self._get_session_file(session_id)
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
        
        logger.info(f"Created vetting session: {session_id}")
        return session_data
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Retrieve session data"""
        session_file = self._get_session_file(session_id)
        
        if not os.path.exists(session_file):
            return None
        
        try:
            with open(session_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading session {session_id}: {e}")
            return None
    
    def store_scan_result(self, session_id: str, file_hash: str, file_name: str, scan_result: Dict) -> bool:
        """Store a resume scan result in the session"""
        session_data = self.get_session(session_id)
        
        if not session_data:
            session_data = self.create_session(session_id)
        
        # Store scan result
        session_data["scanned_resumes"][file_hash] = {
            "file_name": file_name,
            "file_hash": file_hash,
            "scan_result": scan_result,
            "scanned_at": datetime.now().isoformat(),
            "status": "pending"  # pending, approved, rejected
        }
        
        # Save session
        session_file = self._get_session_file(session_id)
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
        
        logger.info(f"Stored scan result for {file_name} in session {session_id}")
        return True
    
    def mark_approved(self, session_id: str, file_hash: str) -> bool:
        """Mark a resume as approved"""
        session_data = self.get_session(session_id)
        
        if not session_data or file_hash not in session_data["scanned_resumes"]:
            return False
        
        # Update status
        session_data["scanned_resumes"][file_hash]["status"] = "approved"
        
        # Add to approved list if not already there
        if file_hash not in session_data["approved"]:
            session_data["approved"].append(file_hash)
        
        # Remove from rejected list if present
        if file_hash in session_data["rejected"]:
            session_data["rejected"].remove(file_hash)
        
        # Save session
        session_file = self._get_session_file(session_id)
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
        
        logger.info(f"Approved {file_hash} in session {session_id}")
        return True
    
    def mark_rejected(self, session_id: str, file_hash: str) -> bool:
        """Mark a resume as rejected"""
        session_data = self.get_session(session_id)
        
        if not session_data or file_hash not in session_data["scanned_resumes"]:
            return False
        
        # Update status
        session_data["scanned_resumes"][file_hash]["status"] = "rejected"
        
        # Add to rejected list if not already there
        if file_hash not in session_data["rejected"]:
            session_data["rejected"].append(file_hash)
        
        # Remove from approved list if present
        if file_hash in session_data["approved"]:
            session_data["approved"].remove(file_hash)
        
        # Save session
        session_file = self._get_session_file(session_id)
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
        
        logger.info(f"Rejected {file_hash} in session {session_id}")
        return True
    
    def get_scanned_resumes(self, session_id: str) -> List[Dict]:
        """Get all scanned resumes in the session"""
        session_data = self.get_session(session_id)
        
        if not session_data:
            return []
        
        return list(session_data["scanned_resumes"].values())
    
    def get_approved_resumes(self, session_id: str) -> List[Dict]:
        """Get approved resumes from the session"""
        session_data = self.get_session(session_id)
        
        if not session_data:
            return []
        
        approved = []
        for file_hash in session_data["approved"]:
            if file_hash in session_data["scanned_resumes"]:
                approved.append(session_data["scanned_resumes"][file_hash])
        
        return approved
    
    def bulk_approve_by_score(self, session_id: str, min_score: float) -> int:
        """Bulk approve resumes with score >= min_score"""
        session_data = self.get_session(session_id)
        
        if not session_data:
            return 0
        
        approved_count = 0
        
        for file_hash, resume_data in session_data["scanned_resumes"].items():
            scan_result = resume_data.get("scan_result", {})
            authenticity_score = scan_result.get("authenticity_score", {})
            overall_score = authenticity_score.get("overall_score", 0)
            
            if overall_score >= min_score and resume_data["status"] == "pending":
                self.mark_approved(session_id, file_hash)
                approved_count += 1
        
        logger.info(f"Bulk approved {approved_count} resumes with score >= {min_score}")
        return approved_count
    
    def clear_session(self, session_id: str) -> bool:
        """Clear/delete a vetting session"""
        session_file = self._get_session_file(session_id)
        
        if os.path.exists(session_file):
            try:
                os.remove(session_file)
                logger.info(f"Cleared vetting session: {session_id}")
                return True
            except Exception as e:
                logger.error(f"Error clearing session {session_id}: {e}")
                return False
        
        return False
    
    def cleanup_old_sessions(self, hours: int = 24) -> int:
        """Clean up sessions older than specified hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        cleaned_count = 0
        
        for filename in os.listdir(self.session_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self.session_dir, filename)
                
                try:
                    with open(filepath, 'r') as f:
                        session_data = json.load(f)
                    
                    created_at = datetime.fromisoformat(session_data.get("created_at", ""))
                    
                    if created_at < cutoff_time:
                        os.remove(filepath)
                        cleaned_count += 1
                        logger.info(f"Cleaned up old session: {filename}")
                        
                except Exception as e:
                    logger.error(f"Error processing session file {filename}: {e}")
        
        logger.info(f"Cleaned up {cleaned_count} old vetting sessions")
        return cleaned_count
