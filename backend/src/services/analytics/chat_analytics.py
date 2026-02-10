"""
Chat Analytics Helper

Aggregates real data from chat session JSON files.
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime, timedelta
from collections import defaultdict

from src.core import get_logger

logger = get_logger(__name__)

# Data directory for chat sessions
CHAT_SESSIONS_DIR = Path(__file__).parent.parent.parent.parent / "data" / "chat_sessions"


def get_total_sessions() -> int:
    """Count total number of chat sessions."""
    try:
        if not CHAT_SESSIONS_DIR.exists():
            return 0
        return len(list(CHAT_SESSIONS_DIR.glob("*.json")))
    except Exception as e:
        logger.error(f"Error counting sessions: {e}")
        return 0


def get_total_messages() -> int:
    """Count total messages across all sessions."""
    try:
        if not CHAT_SESSIONS_DIR.exists():
            return 0
        
        total = 0
        for session_file in CHAT_SESSIONS_DIR.glob("*.json"):
            try:
                with open(session_file, 'r') as f:
                    data = json.load(f)
                    total += len(data.get('messages', []))
            except Exception as e:
                logger.warning(f"Error reading {session_file}: {e}")
                continue
        
        return total
    except Exception as e:
        logger.error(f"Error counting messages: {e}")
        return 0


def get_avg_messages_per_session() -> float:
    """Calculate average messages per session."""
    total_sessions = get_total_sessions()
    if total_sessions == 0:
        return 0.0
    
    total_messages = get_total_messages()
    return round(total_messages / total_sessions, 2)


def get_sessions_by_agent() -> Dict[str, int]:
    """Get message count grouped by agent."""
    try:
        if not CHAT_SESSIONS_DIR.exists():
            return {}
        
        agent_counts = defaultdict(int)
        
        for session_file in CHAT_SESSIONS_DIR.glob("*.json"):
            try:
                with open(session_file, 'r') as f:
                    data = json.load(f)
                    messages = data.get('messages', [])
                    
                    for msg in messages:
                        if msg.get('sender') == 'agent':
                            agent_id = msg.get('agent_id', 'unknown')
                            agent_counts[agent_id] += 1
            except Exception as e:
                logger.warning(f"Error reading {session_file}: {e}")
                continue
        
        return dict(agent_counts)
    except Exception as e:
        logger.error(f"Error aggregating by agent: {e}")
        return {}


def get_recent_activity(days: int = 7) -> List[Dict[str, Any]]:
    """Get recent chat activity grouped by day."""
    try:
        if not CHAT_SESSIONS_DIR.exists():
            return []
        
        cutoff_date = datetime.now() - timedelta(days=days)
        daily_counts = defaultdict(lambda: {'sessions': 0, 'messages': 0})
        
        for session_file in CHAT_SESSIONS_DIR.glob("*.json"):
            try:
                with open(session_file, 'r') as f:
                    data = json.load(f)
                    
                    # Check session date
                    created_at_str = data.get('created_at')
                    if not created_at_str:
                        continue
                    
                    created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                    
                    if created_at >= cutoff_date:
                        day_key = created_at.strftime('%Y-%m-%d')
                        daily_counts[day_key]['sessions'] += 1
                        daily_counts[day_key]['messages'] += len(data.get('messages', []))
            except Exception as e:
                logger.warning(f"Error processing {session_file}: {e}")
                continue
        
        # Convert to list
        result = [
            {'date': date, **counts}
            for date, counts in sorted(daily_counts.items())
        ]
        
        return result
    except Exception as e:
        logger.error(f"Error getting recent activity: {e}")
        return []



def calculate_message_growth_rate() -> float:
    """Calculate percentage growth in messages (recent vs baseline)."""
    try:
        if not CHAT_SESSIONS_DIR.exists():
            return 0.0
        
        # Get recent activity
        recent = get_recent_activity(days=1)  # Today
        baseline = get_recent_activity(days=7)  # Last week
        
        if not baseline or not recent:
            return 0.0
        
        # Calculate average daily messages for baseline
        total_baseline_msgs = sum(d['messages'] for d in baseline)
        avg_baseline = total_baseline_msgs / max(len(baseline), 1)
        
        # Get today's messages
        today_msgs = recent[-1]['messages'] if recent else 0
        
        if avg_baseline == 0:
            return 0.0
        
        growth_rate = ((today_msgs - avg_baseline) / avg_baseline) * 100
        return round(growth_rate, 1)
    except Exception as e:
        logger.error(f"Error calculating message growth: {e}")
        return 0.0


def calculate_session_growth_rate() -> float:
    """Calculate percentage growth in sessions (recent vs baseline)."""
    try:
        if not CHAT_SESSIONS_DIR.exists():
            return 0.0
        
        recent = get_recent_activity(days=1)
        baseline = get_recent_activity(days=7)
        
        if not baseline or not recent:
            return 0.0
        
        # Calculate average daily sessions
        total_baseline_sessions = sum(d['sessions'] for d in baseline)
        avg_baseline = total_baseline_sessions / max(len(baseline), 1)
        
        today_sessions = recent[-1]['sessions'] if recent else 0
        
        if avg_baseline == 0:
            return 0.0
        
        growth_rate = ((today_sessions - avg_baseline) / avg_baseline) * 100
        return round(growth_rate, 1)
    except Exception as e:
        logger.error(f"Error calculating session growth: {e}")
        return 0.0


def calculate_avg_latency() -> float:
    """Calculate average latency from message timestamps in milliseconds."""
    try:
        if not CHAT_SESSIONS_DIR.exists():
            return 0.0
        
        latencies = []
        
        for session_file in CHAT_SESSIONS_DIR.glob("*.json"):
            try:
                with open(session_file, 'r') as f:
                    data = json.load(f)
                    messages = data.get('messages', [])
                    
                    # Calculate time between user message and agent response
                    for i in range(len(messages) - 1):
                        curr_msg = messages[i]
                        next_msg = messages[i + 1]
                        
                        # If user sends message and agent responds
                        if (curr_msg.get('sender') == 'user' and 
                            next_msg.get('sender') == 'agent'):
                            
                            try:
                                curr_time = datetime.fromisoformat(curr_msg['timestamp'].replace('Z', '+00:00'))
                                next_time = datetime.fromisoformat(next_msg['timestamp'].replace('Z', '+00:00'))
                                
                                latency_ms = (next_time - curr_time).total_seconds() * 1000
                                if 0 < latency_ms < 60000:  # Filter outliers (< 1 minute)
                                    latencies.append(latency_ms)
                            except (KeyError, ValueError):
                                continue
            except Exception as e:
                logger.warning(f"Error reading {session_file}: {e}")
                continue
        
        if not latencies:
            return 0.0
        
        return round(sum(latencies) / len(latencies), 0)
    except Exception as e:
        logger.error(f"Error calculating latency: {e}")
        return 0.0


def get_chat_analytics_summary() -> Dict[str, Any]:
    """Get comprehensive chat analytics summary with trends."""
    return {
        'total_sessions': get_total_sessions(),
        'total_messages': get_total_messages(),
        'avg_messages_per_session': get_avg_messages_per_session(),
        'messages_by_agent': get_sessions_by_agent(),
        'recent_activity': get_recent_activity(days=7),
        'trends': {
            'message_growth_rate': calculate_message_growth_rate(),
            'session_growth_rate': calculate_session_growth_rate(),
        },
        'performance': {
            'avg_latency_ms': calculate_avg_latency(),
        },
    }
