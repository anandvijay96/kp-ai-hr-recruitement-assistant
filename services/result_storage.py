import json
import os
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class ResultStorage:
    """Handles persistence of resume analysis results"""

    def __init__(self, storage_dir: str = "results"):
        self.storage_dir = storage_dir
        self.results_file = os.path.join(storage_dir, "analysis_results.json")
        self._ensure_storage_exists()

    def _ensure_storage_exists(self):
        """Ensure storage directory and file exist"""
        try:
            os.makedirs(self.storage_dir, exist_ok=True)
            if not os.path.exists(self.results_file):
                self._write_results([])
        except Exception as e:
            logger.error(f"Error creating storage: {str(e)}")

    def _read_results(self) -> List[Dict[str, Any]]:
        """Read all results from storage"""
        try:
            if os.path.exists(self.results_file):
                with open(self.results_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            logger.error(f"Error reading results: {str(e)}")
            return []

    def _write_results(self, results: List[Dict[str, Any]]):
        """Write results to storage"""
        try:
            with open(self.results_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error writing results: {str(e)}")
            raise

    def save_result(self, analysis: Dict[str, Any]) -> bool:
        """
        Save a single analysis result
        
        Args:
            analysis: Analysis result dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            results = self._read_results()
            
            # Add timestamp if not present
            if 'upload_date' not in analysis:
                analysis['upload_date'] = datetime.utcnow().isoformat()
            
            # Add to results
            results.append(analysis)
            
            # Keep only last 100 results to prevent file from growing too large
            if len(results) > 100:
                results = results[-100:]
            
            self._write_results(results)
            logger.info(f"Saved result for {analysis.get('filename', 'unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving result: {str(e)}")
            return False

    def get_all_results(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get all stored results
        
        Args:
            limit: Maximum number of results to return (most recent first)
            
        Returns:
            List of analysis results
        """
        try:
            results = self._read_results()
            
            # Sort by upload date (most recent first)
            results.sort(key=lambda x: x.get('upload_date', ''), reverse=True)
            
            if limit:
                results = results[:limit]
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting results: {str(e)}")
            return []

    def get_result_by_id(self, result_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific result by ID
        
        Args:
            result_id: The ID of the result to retrieve
            
        Returns:
            Analysis result or None if not found
        """
        try:
            results = self._read_results()
            for result in results:
                if result.get('id') == result_id:
                    return result
            return None
            
        except Exception as e:
            logger.error(f"Error getting result by ID: {str(e)}")
            return None

    def delete_result(self, result_id: str) -> bool:
        """
        Delete a specific result
        
        Args:
            result_id: The ID of the result to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            results = self._read_results()
            original_length = len(results)
            
            results = [r for r in results if r.get('id') != result_id]
            
            if len(results) < original_length:
                self._write_results(results)
                logger.info(f"Deleted result {result_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting result: {str(e)}")
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about stored results
        
        Returns:
            Dictionary with statistics
        """
        try:
            results = self._read_results()
            
            if not results:
                return {
                    'total_resumes': 0,
                    'average_authenticity': 0,
                    'average_jd_match': 0,
                    'high_quality_count': 0,
                    'low_quality_count': 0
                }
            
            # Calculate statistics
            authenticity_scores = [
                r.get('authenticity_score', {}).get('overall_score', 0)
                for r in results
            ]
            
            jd_matches = [
                r.get('matching_score', {}).get('overall_match', 0)
                for r in results
                if r.get('matching_score')
            ]
            
            high_quality = sum(1 for score in authenticity_scores if score >= 80)
            low_quality = sum(1 for score in authenticity_scores if score < 60)
            
            return {
                'total_resumes': len(results),
                'average_authenticity': round(sum(authenticity_scores) / len(authenticity_scores), 1),
                'average_jd_match': round(sum(jd_matches) / len(jd_matches), 1) if jd_matches else 0,
                'high_quality_count': high_quality,
                'low_quality_count': low_quality,
                'recent_uploads': len([r for r in results if self._is_recent(r.get('upload_date'))])
            }
            
        except Exception as e:
            logger.error(f"Error calculating statistics: {str(e)}")
            return {}

    def _is_recent(self, date_str: Optional[str], days: int = 7) -> bool:
        """Check if a date is within the last N days"""
        if not date_str:
            return False
        
        try:
            upload_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            days_ago = (datetime.utcnow() - upload_date).days
            return days_ago <= days
        except:
            return False

    def export_to_csv(self, output_path: str) -> bool:
        """
        Export results to CSV file
        
        Args:
            output_path: Path to output CSV file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            import csv
            
            results = self._read_results()
            if not results:
                return False
            
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'id', 'filename', 'upload_date', 'file_size',
                    'authenticity_score', 'font_consistency', 'grammar_score',
                    'formatting_score', 'jd_match', 'skills_match',
                    'experience_match', 'education_match'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for result in results:
                    auth_score = result.get('authenticity_score', {})
                    match_score = result.get('matching_score', {})
                    
                    row = {
                        'id': result.get('id', ''),
                        'filename': result.get('filename', ''),
                        'upload_date': result.get('upload_date', ''),
                        'file_size': result.get('file_size', 0),
                        'authenticity_score': auth_score.get('overall_score', 0),
                        'font_consistency': auth_score.get('font_consistency', 0),
                        'grammar_score': auth_score.get('grammar_score', 0),
                        'formatting_score': auth_score.get('formatting_score', 0),
                        'jd_match': match_score.get('overall_match', 0) if match_score else 0,
                        'skills_match': match_score.get('skills_match', 0) if match_score else 0,
                        'experience_match': match_score.get('experience_match', 0) if match_score else 0,
                        'education_match': match_score.get('education_match', 0) if match_score else 0,
                    }
                    
                    writer.writerow(row)
            
            logger.info(f"Exported {len(results)} results to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {str(e)}")
            return False
