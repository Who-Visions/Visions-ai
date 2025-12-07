#!/usr/bin/env python3
"""
🧠 Visions AI Cost Intelligence

Comprehensive cost optimization with:
- Smart model routing (Flash Lite → Flash → Pro)
- Context caching for token savings
- Batch API support (50% cost reduction)
- Image resolution auto-selection
- Usage prediction & forecasting
- Real-time cost tracking
- Export reports (CSV/JSON)

Uses math module for precise financial calculations.

Author: Gemini - Web & Cloud Specialist
"""

import json
import hashlib
import math
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass, field, asdict
import csv

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich import box
except ImportError:
    Console = None
    Table = None
    Panel = None
    box = None

# ============================================================================
# CONFIGURATION
# ============================================================================

DATA_DIR = Path(__file__).parent / "knowledge_base"
CACHE_FILE = DATA_DIR / "context_cache.json"
QUERY_LOG_FILE = DATA_DIR / "query_log.json"
PREDICTIONS_FILE = DATA_DIR / "predictions.json"

# Credit configuration
CREDITS = {
    "glitched": {"amount": 600.0, "duration_days": 90},
    "genai": {"amount": 1000.0, "duration_days": 365},
}

# Precise daily burn calculations using math
GLITCHED_DAILY = CREDITS["glitched"]["amount"] / CREDITS["glitched"]["duration_days"]  # $6.67
GENAI_DAILY = CREDITS["genai"]["amount"] / CREDITS["genai"]["duration_days"]  # $2.74
DAILY_BUDGET = math.fsum([GLITCHED_DAILY, GENAI_DAILY])  # $9.41 (precise)
TOTAL_CREDITS = math.fsum([CREDITS["glitched"]["amount"], CREDITS["genai"]["amount"]])  # $1600

# Model tiers for smart routing
MODEL_TIERS = {
    "triage": {
        "model": "gemini-2.5-flash-lite",
        "cost_per_1k_input": 0.0001,
        "cost_per_1k_output": 0.0004,
        "use_for": ["greeting", "simple_question", "routing"]
    },
    "standard": {
        "model": "gemini-2.5-flash",
        "cost_per_1k_input": 0.0003,
        "cost_per_1k_output": 0.0025,
        "use_for": ["general", "code", "analysis"]
    },
    "advanced": {
        "model": "gemini-2.5-pro", 
        "cost_per_1k_input": 0.00125,
        "cost_per_1k_output": 0.01,
        "use_for": ["complex_reasoning", "research", "synthesis"]
    },
    "flagship": {
        "model": "gemini-3-pro-preview",
        "cost_per_1k_input": 0.002,
        "cost_per_1k_output": 0.012,
        "use_for": ["expert", "multimodal", "final_output"]
    }
}

# Image resolution tiers
IMAGE_TIERS = {
    "draft": {
        "resolution": "1k",
        "cost": 0.039,  # Flash Image
        "model": "gemini-2.5-flash-image"
    },
    "standard": {
        "resolution": "2k",
        "cost": 0.134,  # G3 Pro 2K
        "model": "gemini-3-pro-image-preview"
    },
    "premium": {
        "resolution": "4k",
        "cost": 0.24,   # G3 Pro 4K
        "model": "gemini-3-pro-image-preview"
    }
}

# ============================================================================
# CONTEXT CACHE
# ============================================================================

class ContextCache:
    """Cache for reducing repeated token costs."""
    
    def __init__(self, max_entries: int = 1000, ttl_hours: int = 24):
        self.max_entries = max_entries
        self.ttl_hours = ttl_hours
        self.cache: Dict[str, Dict] = {}
        self._load()
    
    def _load(self):
        """Load cache from disk."""
        if CACHE_FILE.exists():
            try:
                with open(CACHE_FILE) as f:
                    data = json.load(f)
                    # Filter expired entries
                    now = datetime.now().timestamp()
                    self.cache = {
                        k: v for k, v in data.items()
                        if v.get("expires", 0) > now
                    }
            except:
                self.cache = {}
    
    def _save(self):
        """Save cache to disk."""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(CACHE_FILE, 'w') as f:
            json.dump(self.cache, f)
    
    def _hash_key(self, content: str) -> str:
        """Generate cache key from content."""
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def get(self, content: str) -> Optional[Dict]:
        """Get cached response for content."""
        key = self._hash_key(content)
        entry = self.cache.get(key)
        if entry and entry.get("expires", 0) > datetime.now().timestamp():
            entry["hits"] = entry.get("hits", 0) + 1
            return entry
        return None
    
    def set(self, content: str, response: str, tokens_saved: int = 0):
        """Cache a response."""
        key = self._hash_key(content)
        self.cache[key] = {
            "response": response,
            "tokens_saved": tokens_saved,
            "created": datetime.now().isoformat(),
            "expires": (datetime.now() + timedelta(hours=self.ttl_hours)).timestamp(),
            "hits": 0
        }
        
        # Prune if needed
        if len(self.cache) > self.max_entries:
            # Remove oldest entries
            sorted_entries = sorted(
                self.cache.items(),
                key=lambda x: x[1].get("expires", 0)
            )
            self.cache = dict(sorted_entries[-self.max_entries:])
        
        self._save()
    
    def get_stats(self) -> Dict:
        """Get cache statistics."""
        total_hits = sum(e.get("hits", 0) for e in self.cache.values())
        total_tokens_saved = sum(e.get("tokens_saved", 0) * e.get("hits", 0) for e in self.cache.values())
        return {
            "entries": len(self.cache),
            "total_hits": total_hits,
            "tokens_saved": total_tokens_saved,
            "estimated_savings": total_tokens_saved * 0.000002  # $2/1M tokens avg
        }


# ============================================================================
# QUERY LOGGER
# ============================================================================

@dataclass
class QueryEntry:
    """Single query log entry."""
    timestamp: str
    query_type: str  # "text", "image", "video", "batch"
    model: str
    tier: str  # "triage", "standard", "advanced", "flagship"
    input_tokens: int
    output_tokens: int
    cost: float
    cached: bool = False
    batch: bool = False
    
    def to_dict(self):
        return asdict(self)


class QueryLogger:
    """Log all queries with cost tracking."""
    
    def __init__(self):
        self.entries: List[Dict] = []
        self._load()
    
    def _load(self):
        """Load query log from disk."""
        if QUERY_LOG_FILE.exists():
            try:
                with open(QUERY_LOG_FILE) as f:
                    self.entries = json.load(f)
            except:
                self.entries = []
    
    def _save(self):
        """Save query log to disk."""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(QUERY_LOG_FILE, 'w') as f:
            json.dump(self.entries, f, indent=2)
    
    def log(self, entry: QueryEntry):
        """Log a query."""
        self.entries.append(entry.to_dict())
        self._save()
    
    def get_today(self) -> List[Dict]:
        """Get today's entries."""
        today = str(date.today())
        return [e for e in self.entries if e["timestamp"].startswith(today)]
    
    def get_cost_breakdown(self, days: int = 7) -> Dict:
        """Get cost breakdown by model/tier."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        recent = [e for e in self.entries if e["timestamp"] >= cutoff]
        
        breakdown = {
            "by_tier": {},
            "by_model": {},
            "by_type": {},
            "total_cost": 0,
            "total_queries": len(recent),
            "cache_savings": 0
        }
        
        for entry in recent:
            tier = entry.get("tier", "unknown")
            model = entry.get("model", "unknown")
            qtype = entry.get("query_type", "unknown")
            cost = entry.get("cost", 0)
            
            breakdown["by_tier"][tier] = breakdown["by_tier"].get(tier, 0) + cost
            breakdown["by_model"][model] = breakdown["by_model"].get(model, 0) + cost
            breakdown["by_type"][qtype] = breakdown["by_type"].get(qtype, 0) + cost
            breakdown["total_cost"] += cost
            
            if entry.get("cached"):
                breakdown["cache_savings"] += cost * 0.9  # 90% saved if cached
        
        return breakdown
    
    def export_csv(self, filepath: str, days: int = 30):
        """Export to CSV."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        recent = [e for e in self.entries if e["timestamp"] >= cutoff]
        
        with open(filepath, 'w', newline='') as f:
            if recent:
                writer = csv.DictWriter(f, fieldnames=recent[0].keys())
                writer.writeheader()
                writer.writerows(recent)
    
    def export_json(self, filepath: str, days: int = 30):
        """Export to JSON."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        recent = [e for e in self.entries if e["timestamp"] >= cutoff]
        
        with open(filepath, 'w') as f:
            json.dump(recent, f, indent=2)


# ============================================================================
# SMART ROUTER
# ============================================================================

class SmartRouter:
    """Intelligent model routing for cost optimization."""
    
    # Keywords for query classification
    TRIAGE_KEYWORDS = ["hi", "hello", "hey", "thanks", "bye", "ok", "yes", "no"]
    ADVANCED_KEYWORDS = ["analyze", "research", "compare", "explain why", "deep dive", "comprehensive"]
    FLAGSHIP_KEYWORDS = ["expert", "professional", "best quality", "final", "publish", "perfect"]
    
    @classmethod
    def classify_query(cls, query: str) -> str:
        """Classify query to determine appropriate tier."""
        query_lower = query.lower().strip()
        
        # Very short = triage
        if len(query_lower) < 20:
            return "triage"
        
        # Check for flagship keywords
        if any(kw in query_lower for kw in cls.FLAGSHIP_KEYWORDS):
            return "flagship"
        
        # Check for advanced keywords
        if any(kw in query_lower for kw in cls.ADVANCED_KEYWORDS):
            return "advanced"
        
        # Check for triage keywords (greetings)
        words = query_lower.split()
        if len(words) <= 3 and any(w in cls.TRIAGE_KEYWORDS for w in words):
            return "triage"
        
        # Default to standard
        return "standard"
    
    @classmethod
    def get_model(cls, tier: str) -> str:
        """Get model for tier."""
        return MODEL_TIERS.get(tier, MODEL_TIERS["standard"])["model"]
    
    @classmethod
    def estimate_cost(cls, tier: str, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost for a query using precise math."""
        tier_info = MODEL_TIERS.get(tier, MODEL_TIERS["standard"])
        input_cost = (input_tokens / 1000) * tier_info["cost_per_1k_input"]
        output_cost = (output_tokens / 1000) * tier_info["cost_per_1k_output"]
        # Use math.fsum for precise floating-point addition
        return math.fsum([input_cost, output_cost])


# ============================================================================
# IMAGE RESOLUTION SELECTOR
# ============================================================================

class ImageResolutionSelector:
    """Auto-select optimal image resolution based on use case."""
    
    # Keywords for resolution selection
    DRAFT_KEYWORDS = ["draft", "quick", "preview", "test", "sketch", "rough", "concept"]
    PREMIUM_KEYWORDS = ["4k", "high resolution", "print", "professional", "detailed", "final", "publish"]
    
    @classmethod
    def select_resolution(cls, prompt: str, explicit_resolution: Optional[str] = None) -> str:
        """Select optimal resolution for prompt."""
        if explicit_resolution:
            return explicit_resolution
        
        prompt_lower = prompt.lower()
        
        # Check for premium keywords
        if any(kw in prompt_lower for kw in cls.PREMIUM_KEYWORDS):
            return "premium"
        
        # Check for draft keywords
        if any(kw in prompt_lower for kw in cls.DRAFT_KEYWORDS):
            return "draft"
        
        # Default to standard
        return "standard"
    
    @classmethod
    def get_model_and_cost(cls, tier: str) -> Tuple[str, float]:
        """Get model and cost for resolution tier."""
        tier_info = IMAGE_TIERS.get(tier, IMAGE_TIERS["standard"])
        return tier_info["model"], tier_info["cost"]


# ============================================================================
# USAGE PREDICTOR
# ============================================================================

class UsagePredictor:
    """Predict when limits/credits will be exhausted using precise math."""
    
    def __init__(self, query_logger: QueryLogger):
        self.logger = query_logger
    
    def get_daily_average(self, days: int = 7) -> float:
        """Get average daily cost using precise math.fsum."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        recent = [e for e in self.logger.entries if e["timestamp"] >= cutoff]
        
        if not recent:
            return 0.0
        
        # Use math.fsum for precise floating-point summation
        costs = [e.get("cost", 0) for e in recent]
        total_cost = math.fsum(costs)
        
        # Count unique days
        unique_days = len(set(e["timestamp"][:10] for e in recent))
        
        return total_cost / max(unique_days, 1)
    
    def predict_credit_exhaustion(self, remaining_credits: float) -> Dict:
        """Predict when credits will run out."""
        daily_avg = self.get_daily_average()
        
        if daily_avg <= 0:
            return {
                "days_remaining": math.inf,
                "exhaustion_date": "N/A",
                "status": "No usage data"
            }
        
        days_remaining = remaining_credits / daily_avg
        # Use math.floor for conservative estimate
        exhaustion_date = date.today() + timedelta(days=math.floor(days_remaining))
        
        # Determine status based on thresholds
        if days_remaining > 90:
            status = "✅ Healthy"
        elif days_remaining > 30:
            status = "🟡 Monitor"
        elif days_remaining > 7:
            status = "🟠 Warning"
        else:
            status = "🔴 Critical"
        
        return {
            "days_remaining": round(days_remaining, 1),
            "exhaustion_date": str(exhaustion_date),
            "daily_average": round(daily_avg, 4),
            "status": status
        }
    
    def predict_daily_limit_hit(self, model: str, current_count: int, limit: int) -> Dict:
        """Predict when daily limit will be hit."""
        # Get hourly rate from today's usage
        today = str(date.today())
        today_entries = [e for e in self.logger.entries 
                        if e["timestamp"].startswith(today) and e.get("model") == model]
        
        if not today_entries:
            return {
                "will_hit_limit": False,
                "estimated_time": "Unknown",
                "rate_per_hour": 0
            }
        
        # Calculate hourly rate
        first_entry = min(e["timestamp"] for e in today_entries)
        hours_elapsed = (datetime.now() - datetime.fromisoformat(first_entry)).total_seconds() / 3600
        
        if hours_elapsed < 0.1:
            hours_elapsed = 0.1
        
        rate_per_hour = len(today_entries) / hours_elapsed
        remaining = limit - current_count
        
        if rate_per_hour <= 0:
            return {
                "will_hit_limit": False,
                "estimated_time": "N/A",
                "rate_per_hour": 0
            }
        
        hours_until_limit = remaining / rate_per_hour
        estimated_time = datetime.now() + timedelta(hours=hours_until_limit)
        
        return {
            "will_hit_limit": True,
            "estimated_time": estimated_time.strftime("%H:%M"),
            "rate_per_hour": round(rate_per_hour, 1),
            "remaining": remaining
        }


# ============================================================================
# BATCH PROCESSOR
# ============================================================================

class BatchProcessor:
    """Queue requests for batch processing (50% cost savings)."""
    
    BATCH_FILE = DATA_DIR / "batch_queue.json"
    
    def __init__(self):
        self.queue: List[Dict] = []
        self._load()
    
    def _load(self):
        """Load batch queue from disk."""
        if self.BATCH_FILE.exists():
            try:
                with open(self.BATCH_FILE) as f:
                    self.queue = json.load(f)
            except:
                self.queue = []
    
    def _save(self):
        """Save batch queue to disk."""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(self.BATCH_FILE, 'w') as f:
            json.dump(self.queue, f, indent=2)
    
    def add_to_queue(self, request: Dict) -> str:
        """Add request to batch queue."""
        request_id = f"batch_{len(self.queue)}_{datetime.now().strftime('%H%M%S')}"
        self.queue.append({
            "id": request_id,
            "request": request,
            "added": datetime.now().isoformat(),
            "status": "queued"
        })
        self._save()
        return request_id
    
    def get_queue_stats(self) -> Dict:
        """Get queue statistics."""
        return {
            "queued": len([q for q in self.queue if q["status"] == "queued"]),
            "processing": len([q for q in self.queue if q["status"] == "processing"]),
            "completed": len([q for q in self.queue if q["status"] == "completed"]),
            "estimated_savings": len(self.queue) * 0.05  # ~$0.05 per query saved
        }


# ============================================================================
# COST INTELLIGENCE (MAIN CLASS)
# ============================================================================

class CostIntelligence:
    """Main cost intelligence orchestrator."""
    
    def __init__(self):
        self.cache = ContextCache()
        self.logger = QueryLogger()
        self.predictor = UsagePredictor(self.logger)
        self.batch = BatchProcessor()
        self.console = Console() if Console else None
    
    def route_query(self, query: str) -> Tuple[str, str]:
        """Route query to optimal model.
        
        Returns: (model_name, tier)
        """
        tier = SmartRouter.classify_query(query)
        model = SmartRouter.get_model(tier)
        return model, tier
    
    def check_cache(self, content: str) -> Optional[str]:
        """Check if content is cached."""
        cached = self.cache.get(content)
        if cached:
            return cached.get("response")
        return None
    
    def cache_response(self, content: str, response: str, tokens: int = 0):
        """Cache a response."""
        self.cache.set(content, response, tokens)
    
    def select_image_resolution(self, prompt: str, explicit: Optional[str] = None) -> Tuple[str, str, float]:
        """Select optimal image resolution.
        
        Returns: (tier, model, cost)
        """
        tier = ImageResolutionSelector.select_resolution(prompt, explicit)
        model, cost = ImageResolutionSelector.get_model_and_cost(tier)
        return tier, model, cost
    
    def log_query(self, query_type: str, model: str, tier: str, 
                  input_tokens: int, output_tokens: int, cached: bool = False, batch: bool = False):
        """Log a query with cost."""
        cost = SmartRouter.estimate_cost(tier, input_tokens, output_tokens)
        if batch:
            cost *= 0.5  # 50% batch discount
        if cached:
            cost *= 0.1  # 90% cache savings
        
        entry = QueryEntry(
            timestamp=datetime.now().isoformat(),
            query_type=query_type,
            model=model,
            tier=tier,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
            cached=cached,
            batch=batch
        )
        self.logger.log(entry)
        return cost
    
    def get_predictions(self, remaining_credits: float = 1584.58) -> Dict:
        """Get usage predictions."""
        return self.predictor.predict_credit_exhaustion(remaining_credits)
    
    def get_cost_breakdown(self, days: int = 7) -> Dict:
        """Get cost breakdown."""
        return self.logger.get_cost_breakdown(days)
    
    def export_report(self, format: str = "json", days: int = 30) -> str:
        """Export usage report."""
        filepath = DATA_DIR / f"report_{date.today()}.{format}"
        if format == "csv":
            self.logger.export_csv(str(filepath), days)
        else:
            self.logger.export_json(str(filepath), days)
        return str(filepath)
    
    def print_dashboard(self):
        """Print cost intelligence dashboard."""
        if not self.console:
            return
        
        self.console.print()
        self.console.print(Panel.fit(
            "[bold magenta]🧠 COST INTELLIGENCE DASHBOARD[/bold magenta]",
            border_style="magenta"
        ))
        
        # Cost breakdown
        breakdown = self.get_cost_breakdown(7)
        self.console.print(f"\n[bold]📊 Last 7 Days:[/bold]")
        self.console.print(f"   Total Cost: ${breakdown['total_cost']:.4f}")
        self.console.print(f"   Queries: {breakdown['total_queries']}")
        self.console.print(f"   Cache Savings: ${breakdown['cache_savings']:.4f}")
        
        # By tier
        if breakdown['by_tier']:
            self.console.print(f"\n[bold]📈 By Tier:[/bold]")
            for tier, cost in sorted(breakdown['by_tier'].items(), key=lambda x: x[1], reverse=True):
                self.console.print(f"   {tier}: ${cost:.4f}")
        
        # Predictions
        predictions = self.get_predictions()
        self.console.print(f"\n[bold]🔮 Credit Prediction:[/bold]")
        self.console.print(f"   {predictions['status']}")
        self.console.print(f"   Daily Average: ${predictions.get('daily_average', 0):.4f}")
        self.console.print(f"   Days Remaining: {predictions.get('days_remaining', '∞')}")
        self.console.print(f"   Exhaustion Date: {predictions.get('exhaustion_date', 'N/A')}")
        
        # Cache stats
        cache_stats = self.cache.get_stats()
        self.console.print(f"\n[bold]💾 Cache:[/bold]")
        self.console.print(f"   Entries: {cache_stats['entries']}")
        self.console.print(f"   Hits: {cache_stats['total_hits']}")
        self.console.print(f"   Tokens Saved: {cache_stats['tokens_saved']:,}")
        self.console.print(f"   Estimated Savings: ${cache_stats['estimated_savings']:.4f}")
        
        # Batch queue
        batch_stats = self.batch.get_queue_stats()
        if batch_stats['queued'] > 0:
            self.console.print(f"\n[bold]📦 Batch Queue:[/bold]")
            self.console.print(f"   Queued: {batch_stats['queued']}")
            self.console.print(f"   Est. Savings: ${batch_stats['estimated_savings']:.2f}")


# ============================================================================
# SINGLETON & CONVENIENCE
# ============================================================================

_instance = None

def get_intelligence() -> CostIntelligence:
    """Get singleton instance."""
    global _instance
    if _instance is None:
        _instance = CostIntelligence()
    return _instance


# Convenience functions
def route_query(query: str) -> Tuple[str, str]:
    """Route query to optimal model."""
    return get_intelligence().route_query(query)

def check_cache(content: str) -> Optional[str]:
    """Check cache for content."""
    return get_intelligence().check_cache(content)

def log_query(query_type: str, model: str, tier: str, input_tokens: int, output_tokens: int, **kwargs):
    """Log a query."""
    return get_intelligence().log_query(query_type, model, tier, input_tokens, output_tokens, **kwargs)

def select_image_resolution(prompt: str, explicit: Optional[str] = None) -> Tuple[str, str, float]:
    """Select image resolution."""
    return get_intelligence().select_image_resolution(prompt, explicit)


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="🧠 Cost Intelligence")
    parser.add_argument("--dashboard", "-d", action="store_true", help="Show dashboard")
    parser.add_argument("--export", "-e", choices=["csv", "json"], help="Export report")
    parser.add_argument("--days", type=int, default=30, help="Days to export")
    parser.add_argument("--route", "-r", type=str, help="Route a query (test)")
    args = parser.parse_args()
    
    intel = get_intelligence()
    
    if args.dashboard:
        intel.print_dashboard()
    elif args.export:
        filepath = intel.export_report(args.export, args.days)
        print(f"✅ Exported to: {filepath}")
    elif args.route:
        model, tier = intel.route_query(args.route)
        print(f"Query: {args.route}")
        print(f"Tier: {tier}")
        print(f"Model: {model}")
    else:
        intel.print_dashboard()
