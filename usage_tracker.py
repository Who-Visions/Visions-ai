#!/usr/bin/env python3
"""
📊 Visions AI Daily Usage Tracker

Tracks daily image/video generations and alerts user at key thresholds.

Author: Gemini - Web & Cloud Specialist
"""

import json
from datetime import datetime, date
from pathlib import Path
from typing import Optional, Dict, Tuple
from dataclasses import dataclass, field

try:
    from rich.console import Console
    from rich.panel import Panel
except ImportError:
    Console = None
    Panel = None

# ============================================================================
# DAILY LIMITS (Rate limits from Google AI Studio - Tier 1)
# ============================================================================

DAILY_LIMITS = {
    # Gemini 3 Pro Image - by resolution
    "gemini-3-pro-image": {
        "rpd": 250,
        "cost": 0.134,  # Default (1K-2K)
        "name": "Gemini 3 Pro Image",
        "emoji": "🧠"
    },
    "gemini-3-pro-image-1k": {
        "rpd": 250,
        "cost": 0.134,  # 1024x1024 = 1120 tokens
        "name": "G3 Pro Image 1K",
        "emoji": "🧠"
    },
    "gemini-3-pro-image-2k": {
        "rpd": 250,
        "cost": 0.134,  # 2048x2048 = 1120 tokens
        "name": "G3 Pro Image 2K", 
        "emoji": "🧠"
    },
    "gemini-3-pro-image-4k": {
        "rpd": 250,
        "cost": 0.24,   # 4096x4096 = 2000 tokens
        "name": "G3 Pro Image 4K",
        "emoji": "🧠✨"
    },
    
    # Gemini 2.5 Flash Image
    "gemini-2.5-flash-image": {
        "rpd": 2000,
        "cost": 0.039,
        "name": "Gemini 2.5 Flash Image",
        "emoji": "⚡"
    },
    
    # Imagen 4
    "imagen-4-fast": {
        "rpd": 70,
        "cost": 0.02,
        "name": "Imagen 4 Fast",
        "emoji": "🖼️"
    },
    "imagen-4-standard": {
        "rpd": 70,
        "cost": 0.04,
        "name": "Imagen 4 Standard",
        "emoji": "📷"
    },
    "imagen-4-ultra": {
        "rpd": 30,
        "cost": 0.06,
        "name": "Imagen 4 Ultra",
        "emoji": "💎"
    },
    
    # Imagen 3
    "imagen-3": {
        "rpd": 100,  # Estimate, adjust as needed
        "cost": 0.03,
        "name": "Imagen 3",
        "emoji": "🎨"
    },
    
    # Veo Video
    "veo-3.1-standard": {
        "rpd": 10,
        "cost": 3.20,  # 8 second video @ $0.40/s
        "name": "Veo 3.1 Standard",
        "emoji": "🎬"
    },
    "veo-3.1-fast": {
        "rpd": 10,
        "cost": 1.20,  # 8 second video @ $0.15/s
        "name": "Veo 3.1 Fast",
        "emoji": "⚡🎬"
    },
    "veo-3-standard": {
        "rpd": 10,
        "cost": 3.20,  # 8 second video @ $0.40/s
        "name": "Veo 3 Standard",
        "emoji": "🎥"
    },
    "veo-3-fast": {
        "rpd": 10,
        "cost": 1.20,  # 8 second video @ $0.15/s
        "name": "Veo 3 Fast",
        "emoji": "⚡🎥"
    },
    "veo-2": {
        "rpd": 10,
        "cost": 2.80,  # 8 second video @ $0.35/s
        "name": "Veo 2",
        "emoji": "📹"
    },
}

# Alert thresholds (percentage of limit used)
ALERT_THRESHOLDS = [0, 50, 75, 85, 90, 95, 99, 100]

# ============================================================================
# USAGE TRACKER
# ============================================================================

@dataclass
class DailyUsage:
    date: str
    counts: Dict[str, int] = field(default_factory=dict)
    costs: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self):
        return {
            "date": self.date,
            "counts": self.counts,
            "costs": self.costs
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            date=data["date"],
            counts=data.get("counts", {}),
            costs=data.get("costs", {})
        )


class DailyUsageTracker:
    """Tracks daily usage and alerts at thresholds."""
    
    USAGE_FILE = Path(__file__).parent / "knowledge_base" / "daily_usage.json"
    
    def __init__(self):
        self.console = Console() if Console else None
        self._load_usage()
    
    def _load_usage(self):
        """Load usage data from file."""
        if self.USAGE_FILE.exists():
            try:
                with open(self.USAGE_FILE) as f:
                    data = json.load(f)
                    self.usage = DailyUsage.from_dict(data)
            except:
                self.usage = DailyUsage(date=str(date.today()))
        else:
            self.usage = DailyUsage(date=str(date.today()))
        
        # Reset if new day
        if self.usage.date != str(date.today()):
            self.usage = DailyUsage(date=str(date.today()))
            self._save_usage()
    
    def _save_usage(self):
        """Save usage data to file."""
        self.USAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(self.USAGE_FILE, 'w') as f:
            json.dump(self.usage.to_dict(), f, indent=2)
    
    def get_usage(self, model: str) -> Tuple[int, int, float]:
        """Get current usage for a model.
        
        Returns: (used, limit, percent_used)
        """
        limit_info = DAILY_LIMITS.get(model, {"rpd": 100})
        limit = limit_info["rpd"]
        used = self.usage.counts.get(model, 0)
        percent = (used / limit * 100) if limit > 0 else 0
        return used, limit, percent
    
    def get_remaining(self, model: str) -> int:
        """Get remaining generations for a model."""
        used, limit, _ = self.get_usage(model)
        return max(0, limit - used)
    
    def _get_next_threshold(self, percent: float) -> Optional[int]:
        """Get the next threshold to alert at."""
        for threshold in ALERT_THRESHOLDS:
            if percent < threshold:
                return threshold
        return None
    
    def _get_alert_message(self, model: str, used: int, limit: int, percent: float) -> Optional[str]:
        """Generate alert message if at a threshold."""
        limit_info = DAILY_LIMITS.get(model, {})
        emoji = limit_info.get("emoji", "📊")
        name = limit_info.get("name", model)
        remaining = limit - used
        
        # First generation
        if used == 1:
            return f"{emoji} **First {name} of the day!** {remaining}/{limit} remaining"
        
        # Check thresholds
        for threshold in ALERT_THRESHOLDS:
            # Check if we just crossed this threshold
            prev_percent = ((used - 1) / limit * 100) if used > 1 else 0
            if prev_percent < threshold <= percent:
                if threshold == 100:
                    return f"🚫 **{name} LIMIT REACHED!** 0/{limit} remaining - wait until midnight PT"
                elif threshold >= 95:
                    return f"🔴 **{name} at {threshold}%!** Only {remaining}/{limit} left!"
                elif threshold >= 85:
                    return f"🟠 **{name} at {threshold}%** - {remaining}/{limit} remaining"
                elif threshold >= 75:
                    return f"🟡 **{name} at {threshold}%** - {remaining}/{limit} remaining"
                else:
                    return f"📊 **{name} at {threshold}%** - {remaining}/{limit} remaining"
        
        return None
    
    def record_generation(self, model: str, count: int = 1) -> Optional[str]:
        """Record a generation and return alert message if at threshold.
        
        Args:
            model: Model identifier (e.g., "gemini-3-pro-image")
            count: Number of generations (default 1)
            
        Returns:
            Alert message if at a threshold, None otherwise
        """
        # Initialize if needed
        if model not in self.usage.counts:
            self.usage.counts[model] = 0
            self.usage.costs[model] = 0.0
        
        # Get limit info
        limit_info = DAILY_LIMITS.get(model, {"rpd": 100, "cost": 0.1})
        cost_per = limit_info.get("cost", 0.1)
        
        # Update counts
        self.usage.counts[model] += count
        self.usage.costs[model] += cost_per * count
        
        # Save
        self._save_usage()
        
        # Get usage stats
        used, limit, percent = self.get_usage(model)
        
        # Generate alert if at threshold
        return self._get_alert_message(model, used, limit, percent)
    
    def check_can_generate(self, model: str) -> Tuple[bool, str]:
        """Check if we can generate and return reason if not.
        
        Returns:
            (can_generate, message)
        """
        used, limit, percent = self.get_usage(model)
        remaining = limit - used
        
        if remaining <= 0:
            return False, f"🚫 Daily limit reached for {model}. Resets at midnight PT."
        
        return True, f"✅ {remaining}/{limit} remaining today"
    
    def get_status_line(self, model: str) -> str:
        """Get a compact status line for display."""
        used, limit, percent = self.get_usage(model)
        remaining = limit - used
        limit_info = DAILY_LIMITS.get(model, {})
        emoji = limit_info.get("emoji", "📊")
        
        if percent >= 100:
            return f"{emoji} {used}/{limit} (LIMIT REACHED)"
        elif percent >= 90:
            return f"{emoji} {used}/{limit} (🔴 {percent:.0f}%)"
        elif percent >= 75:
            return f"{emoji} {used}/{limit} (🟠 {percent:.0f}%)"
        elif percent >= 50:
            return f"{emoji} {used}/{limit} (🟡 {percent:.0f}%)"
        else:
            return f"{emoji} {used}/{limit} ({percent:.0f}%)"
    
    def print_daily_summary(self):
        """Print a summary of today's usage."""
        if not self.console:
            return
        
        self.console.print()
        self.console.print(Panel.fit(
            "[bold cyan]📊 Today's Generation Usage[/bold cyan]",
            border_style="cyan"
        ))
        
        total_cost = 0.0
        for model, count in self.usage.counts.items():
            if count > 0:
                _, limit, percent = self.get_usage(model)
                cost = self.usage.costs.get(model, 0)
                total_cost += cost
                status = self.get_status_line(model)
                self.console.print(f"  {status} = ${cost:.2f}")
        
        if total_cost > 0:
            self.console.print(f"\n  [bold]Total spent today:[/bold] ${total_cost:.2f}")
        else:
            self.console.print("  [dim]No generations today[/dim]")


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_tracker = None

def get_tracker() -> DailyUsageTracker:
    """Get the singleton tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = DailyUsageTracker()
    return _tracker


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def record_image_generation(model: str = "gemini-3-pro-image") -> Optional[str]:
    """Record an image generation and return alert if at threshold."""
    return get_tracker().record_generation(model)


def record_video_generation(model: str = "veo-3.1-standard") -> Optional[str]:
    """Record a video generation and return alert if at threshold."""
    return get_tracker().record_generation(model)


def can_generate(model: str) -> Tuple[bool, str]:
    """Check if we can generate with this model."""
    return get_tracker().check_can_generate(model)


def get_remaining(model: str) -> int:
    """Get remaining generations for a model."""
    return get_tracker().get_remaining(model)


def get_status(model: str) -> str:
    """Get status line for a model."""
    return get_tracker().get_status_line(model)


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="📊 Daily Usage Tracker")
    parser.add_argument("--status", "-s", action="store_true", help="Show today's status")
    parser.add_argument("--simulate", "-m", type=str, help="Simulate N generations for a model (format: model:count)")
    args = parser.parse_args()
    
    tracker = get_tracker()
    
    if args.simulate:
        parts = args.simulate.split(":")
        model = parts[0]
        count = int(parts[1]) if len(parts) > 1 else 1
        
        console = Console() if Console else None
        for i in range(count):
            alert = tracker.record_generation(model)
            if alert and console:
                console.print(alert)
    
    tracker.print_daily_summary()
