"""
Wispr Flow Integration for Visions
Reads dictation history from Wispr Flow's SQLite database
"""

import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional

FLOW_DB_PATH = "C:/Users/super/AppData/Roaming/Wispr Flow/flow.sqlite"


class WisprFlowReader:
    """Read dictation history from Wispr Flow."""
    
    def __init__(self, db_path: str = FLOW_DB_PATH):
        self.db_path = db_path
    
    def _connect(self):
        return sqlite3.connect(self.db_path)
    
    def get_recent_dictations(self, limit: int = 20) -> List[Dict]:
        """Get recent dictations."""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timestamp, app, formattedText, editedText
            FROM History 
            WHERE formattedText IS NOT NULL AND formattedText != ''
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        results = []
        for row in cursor.fetchall():
            ts, app, formatted, edited = row
            results.append({
                "timestamp": ts,
                "app": app,
                "text": edited or formatted,  # Use edited if available
                "formatted_text": formatted
            })
        
        conn.close()
        return results
    
    def get_dictations_today(self) -> List[Dict]:
        """Get all dictations from today."""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_ts = int(today.timestamp() * 1000)
        
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timestamp, app, formattedText, editedText
            FROM History 
            WHERE timestamp >= ? AND formattedText IS NOT NULL
            ORDER BY timestamp DESC
        """, (today_ts,))
        
        results = []
        for row in cursor.fetchall():
            ts, app, formatted, edited = row
            results.append({
                "timestamp": ts,
                "app": app,
                "text": edited or formatted
            })
        
        conn.close()
        return results
    
    def search_dictations(self, query: str, limit: int = 20) -> List[Dict]:
        """Search dictations by text content."""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timestamp, app, formattedText, editedText
            FROM History 
            WHERE (formattedText LIKE ? OR editedText LIKE ?)
            ORDER BY timestamp DESC
            LIMIT ?
        """, (f"%{query}%", f"%{query}%", limit))
        
        results = []
        for row in cursor.fetchall():
            ts, app, formatted, edited = row
            results.append({
                "timestamp": ts,
                "app": app,
                "text": edited or formatted
            })
        
        conn.close()
        return results
    
    def get_stats(self) -> Dict:
        """Get dictation statistics."""
        conn = self._connect()
        cursor = conn.cursor()
        
        # Total count
        cursor.execute("SELECT COUNT(*) FROM History WHERE formattedText IS NOT NULL")
        total = cursor.fetchone()[0]
        
        # Total words (approximate)
        cursor.execute("SELECT formattedText FROM History WHERE formattedText IS NOT NULL")
        word_count = sum(len(str(row[0]).split()) for row in cursor.fetchall())
        
        # Apps used
        cursor.execute("""
            SELECT app, COUNT(*) as count 
            FROM History 
            WHERE app IS NOT NULL 
            GROUP BY app 
            ORDER BY count DESC
            LIMIT 10
        """)
        apps = {row[0]: row[1] for row in cursor.fetchall()}
        
        conn.close()
        
        return {
            "total_dictations": total,
            "total_words": word_count,
            "top_apps": apps
        }


# Voice tool function for Visions
def get_flow_context(action: str = "recent", query: str = None, limit: int = 10) -> str:
    """Get context from Wispr Flow dictation history."""
    reader = WisprFlowReader()
    
    if action == "recent":
        dictations = reader.get_recent_dictations(limit)
        if not dictations:
            return "No recent dictations found."
        
        lines = []
        for d in dictations:
            app = d['app'] or 'Unknown'
            text = d['text'][:100] + "..." if len(str(d['text'])) > 100 else d['text']
            lines.append(f"[{app}] {text}")
        return "Recent dictations:\n" + "\n".join(lines)
    
    elif action == "today":
        dictations = reader.get_dictations_today()
        if not dictations:
            return "No dictations today."
        return f"Today you dictated {len(dictations)} messages across various apps."
    
    elif action == "search" and query:
        dictations = reader.search_dictations(query, limit)
        if not dictations:
            return f"No dictations found matching '{query}'."
        
        lines = []
        for d in dictations:
            text = d['text'][:100] + "..." if len(str(d['text'])) > 100 else d['text']
            lines.append(f"- {text}")
        return f"Found {len(dictations)} dictations matching '{query}':\n" + "\n".join(lines)
    
    elif action == "stats":
        stats = reader.get_stats()
        apps_str = ", ".join(f"{k}: {v}" for k, v in list(stats['top_apps'].items())[:5])
        return f"Flow Stats: {stats['total_dictations']} dictations, ~{stats['total_words']} words. Top apps: {apps_str}"
    
    else:
        return "Unknown action. Use: recent, today, search, or stats."


# Function declaration for Gemini Live API
FLOW_FUNCTION_DECLARATION = {
    "name": "get_flow_context",
    "description": "Access Wispr Flow dictation history. Get recent dictations, search past conversations, or view stats. Use when user asks about what they've said, recent conversations, or voice history.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["recent", "today", "search", "stats"],
                "description": "Action: recent (last dictations), today (today's dictations), search (find by text), stats (usage statistics)"
            },
            "query": {
                "type": "string",
                "description": "Search query for 'search' action"
            },
            "limit": {
                "type": "integer",
                "description": "Number of results to return (default 10)"
            }
        },
        "required": ["action"]
    }
}


if __name__ == "__main__":
    # Test
    print(get_flow_context("recent", limit=5))
    print("\n" + get_flow_context("stats"))
