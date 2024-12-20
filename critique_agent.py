import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta

class CritiqueAgent:
    """Evaluate agent performance against defined critique rules"""
    
    @staticmethod
    def evaluate_progress(progress_history: List[Dict], rules: List[str]) -> Dict[str, Any]:
        """
        Evaluate agent progress against defined rules
        
        Args:
            progress_history (List[Dict]): History of agent progress entries
            rules (List[str]): List of critique rules to apply
        
        Returns:
            Dict containing critique results
        """
        results = {
            'passed': [],
            'failed': [],
            'warnings': []
        }
        
        # Check if progress history is empty
        if not progress_history:
            results['failed'].append("No progress history available")
            return results
        
        # Parse and evaluate each rule
        for rule in rules:
            try:
                if 'progress updates' in rule.lower():
                    result = CritiqueAgent._check_progress_frequency(progress_history, rule)
                    if result['status'] == 'failed':
                        results['failed'].append(result['message'])
                    elif result['status'] == 'warning':
                        results['warnings'].append(result['message'])
                    else:
                        results['passed'].append(result['message'])
                
                # Add more rule types here as needed
                
            except Exception as e:
                logging.error(f"Error evaluating rule '{rule}': {e}")
                results['failed'].append(f"Error processing rule: {rule}")
        
        return results
    
    @staticmethod
    def _check_progress_frequency(progress_history: List[Dict], rule: str) -> Dict[str, str]:
        """
        Check frequency of progress updates
        
        Example rules:
        - "Check progress updates > 1 per 5min"
        - "Check progress updates < 3 per hour"
        """
        # Parse rule for frequency and time window
        import re
        
        match = re.search(r'(\d+)\s*(?:updates?)\s*([<>])\s*(\d+)\s*(?:per)\s*(\w+)', rule.lower())
        if not match:
            return {'status': 'failed', 'message': f"Invalid rule format: {rule}"}
        
        expected_count, comparison, threshold, time_unit = match.groups()
        expected_count, threshold = int(expected_count), int(threshold)
        
        # Convert time unit to timedelta
        time_deltas = {
            'min': timedelta(minutes=1),
            'minute': timedelta(minutes=1),
            'minutes': timedelta(minutes=1),
            'hour': timedelta(hours=1),
            'hours': timedelta(hours=1)
        }
        
        if time_unit not in time_deltas:
            return {'status': 'failed', 'message': f"Unsupported time unit: {time_unit}"}
        
        time_window = time_deltas[time_unit] * threshold
        
        # Sort progress history by timestamp
        sorted_history = sorted(progress_history, key=lambda x: datetime.fromisoformat(x['timestamp']))
        
        # Count updates within time windows
        update_counts = []
        for i in range(len(sorted_history)):
            window_start = datetime.fromisoformat(sorted_history[i]['timestamp'])
            window_end = window_start + time_window
            
            # Count updates within this window
            window_updates = [
                entry for entry in sorted_history[i+1:] 
                if window_start <= datetime.fromisoformat(entry['timestamp']) <= window_end
            ]
            update_counts.append(len(window_updates))
        
        # Evaluate against rule
        if comparison == '>':
            passed = any(count > expected_count for count in update_counts)
            status = 'passed' if passed else 'failed'
        else:  # '<'
            passed = all(count < expected_count for count in update_counts)
            status = 'passed' if passed else 'warning'
        
        message = (
            f"Progress update rule '{rule}' " + 
            ("passed" if passed else "failed") + 
            f": Found {max(update_counts)} updates in a {threshold} {time_unit} window"
        )
        
        return {
            'status': status,
            'message': message
        }
