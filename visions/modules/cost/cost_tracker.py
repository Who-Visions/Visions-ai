#!/usr/bin/env python3
"""
💰 Visions AI Cost Tracker

Track API costs, credit usage, and budget estimates with rich visual output.

Usage:
    python cost_tracker.py                    # Show dashboard
    python cost_tracker.py --credits          # Show credit status
    python cost_tracker.py --estimate 500     # Estimate cost for N queries
    python cost_tracker.py --log MODEL IN OUT # Log token usage

Author: Gemini - Web & Cloud Specialist
"""

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from visions.core.config import Config

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.progress import Progress, BarColumn, TextColumn
    from rich.text import Text
    from rich import box
except ImportError:
    print("Installing rich...")
    import subprocess
    subprocess.run(["pip", "install", "rich"], check=True)
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.progress import Progress, BarColumn, TextColumn
    from rich.text import Text
    from rich import box

console = Console()

# ============================================================================
# PRICING DATA (from ai.google.dev/pricing - Dec 2025)
# ============================================================================

PRICING = {
    # ===================== GEMINI 3 =====================
    # Gemini 3 Pro Preview (Global endpoint only)
    Config.MODEL_PRO: {
        "input": 2.00,       # $2.00/1M (<=200k), $4.00 (>200k)
        "output": 12.00,     # $12.00/1M (<=200k), $18.00 (>200k)
        "location": "global",
        "context_cache": 0.20,
        "cache_storage": 4.50,  # per 1M tokens per hour
    },
    
    # Gemini 3 Pro Image Preview (Global endpoint only)
    Config.MODEL_IMAGE_PRO: {
        "input": 2.00,       # text/image input
        "output_text": 12.00,
        "output_image": 120.00,  # $120/1M tokens for images
        "per_image_1k_2k": 0.134,  # 1024-2048px = 1120 tokens
        "per_image_4k": 0.24,      # up to 4096px = 2000 tokens
        "location": "global",
    },
    
    # Gemini 3 Flash Preview
    Config.MODEL_FLASH: {
        "input_text": 0.50,
        "input_audio": 1.00,
        "output": 3.00,
        "location": "us-central1",
        "context_cache": 0.05,
        "cache_storage": 1.00,
    },
    
    # ===================== GEMINI 2.5 =====================
    # Gemini 2.5 Pro
    Config.MODEL_2_5_PRO: {
        "input": 1.25,       # $1.25/1M (<=200k), $2.50 (>200k)
        "output": 10.00,     # $10.00/1M (<=200k), $15.00 (>200k)
        "location": "us-central1",
        "context_cache": 0.125,
        "cache_storage": 4.50,
    },
    
    # Gemini 2.5 Flash
    Config.MODEL_2_5_FLASH: {
        "input_text": 0.30,
        "input_audio": 1.00,
        "output": 2.50,
        "location": "us-central1",
        "context_cache": 0.03,
        "cache_storage": 1.00,
    },
    
    # Gemini 2.5 Flash Lite
    Config.MODEL_2_5_FLASH_LITE: {
        "input": 0.10,
        "output": 0.40,
        "location": "us-central1",
        "context_cache": 0.01,
        "cache_storage": 1.00,
    },
    
    # Gemini 2.5 Flash Image
    Config.MODEL_IMAGE_FAST: {
        "input": 0.30,
        "per_image": 0.039,  # 1290 tokens = $0.039
        "location": "us-central1",
    },
    
    # ===================== GEMINI 2.0 =====================
    "gemini-2.0-flash": {  # Legacy
        "input_text": 0.10,
        "input_audio": 0.70,
        "output": 0.40,
        "per_image": 0.039,
        "location": "us-central1",
    },
    
    "gemini-2.0-flash-lite": { # Legacy
        "input": 0.075,
        "output": 0.30,
        "location": "us-central1",
    },
    
    # ===================== IMAGEN 4 =====================
    "imagen-4-fast": {"per_image": 0.02},
    "imagen-4-standard": {"per_image": 0.04},
    "imagen-4-ultra": {"per_image": 0.06},
    "imagen-3": {"per_image": 0.03},
    
    # ===================== VEO VIDEO =====================
    Config.MODEL_VEO: {"per_second": 0.40},
    Config.MODEL_VEO_FAST: {"per_second": 0.15},
    "veo-3-standard": {"per_second": 0.40},
    "veo-3-fast": {"per_second": 0.15},
    "veo-2": {"per_second": 0.35},
    
    # ===================== EMBEDDINGS =====================
    Config.EMBEDDING_MODEL: {"input": 0.15},
    "text-embedding-004": {"input": 0.000025},  # legacy
    
    # ===================== TOOLS =====================
    "grounding-search": {
        "per_request": 0.035,  # $35/1000 after free tier
        "free_tier": 1500,
    },
    "grounding-maps": {
        "per_request": 0.025,  # $25/1000 after free tier
        "free_tier": 1500,
    },
    
    # ===================== INFRASTRUCTURE =====================
    "reasoning-engine-cpu": {
        "per_hour": 0.0994,
        "free_tier_hours": 50,
    },
    "reasoning-engine-ram": {
        "per_gib_hour": 0.0105,
        "free_tier_gib_hours": 93,
    },
}

# ============================================================================
# CREDIT DATA
# ============================================================================

@dataclass
class Credit:
    name: str
    original: float
    remaining: float
    start_date: datetime
    expiry: datetime
    duration_days: int  # Total duration in days
    status: str  # "active", "expired_but_working", "expired"
    
    @property
    def used(self) -> float:
        return self.original - self.remaining
    
    @property
    def percent_remaining(self) -> float:
        return (self.remaining / self.original) * 100 if self.original > 0 else 0
    
    @property
    def days_until_expiry(self) -> int:
        return (self.expiry - datetime.now()).days
    
    @property
    def days_elapsed(self) -> int:
        return (datetime.now() - self.start_date).days
    
    @property
    def days_remaining(self) -> int:
        return max(0, self.days_until_expiry)
    
    @property
    def is_active(self) -> bool:
        return self.status in ["active", "expired_but_working"]
    
    @property
    def daily_burn_limit(self) -> float:
        """Maximum daily spend to use credits evenly over duration."""
        return self.original / self.duration_days
    
    @property
    def ideal_remaining(self) -> float:
        """What we should have remaining if burning evenly."""
        if self.days_remaining <= 0:
            return 0
        return self.daily_burn_limit * self.days_remaining
    
    @property
    def burn_status(self) -> str:
        """Are we on track, over, or under budget?"""
        if self.remaining > self.ideal_remaining + 1:
            return "under"  # Spending less than ideal
        elif self.remaining < self.ideal_remaining - 1:
            return "over"   # Spending more than ideal
        return "on_track"


# Credit start date: 2025-12-03 (when billing started)
START_DATE = datetime(2025, 12, 3)

CREDITS = [
    Credit(
        name="Free Trial (Glitched)",
        original=300.00,
        remaining=286.22,
        start_date=START_DATE,
        expiry=START_DATE + timedelta(days=90),  # 90 days for $300
        duration_days=90,
        status="expired_but_working"
    ),
    Credit(
        name="Free Trial Upgrade",
        original=299.29,
        remaining=298.36,
        start_date=datetime(2025, 12, 6),  # Started when original "expired"
        expiry=datetime(2025, 12, 6) + timedelta(days=90),  # 90 days for $300
        duration_days=90,
        status="active"
    ),
    Credit(
        name="GenAI App Builder",
        original=1000.00,
        remaining=1000.00,
        start_date=datetime(2025, 12, 4),
        expiry=datetime(2025, 12, 4) + timedelta(days=365),  # 365 days for $1000
        duration_days=365,
        status="active"
    ),
]

# ============================================================================
# DAILY BURN LIMITS
# ============================================================================

# Glitched = 2x $300 credits / 90 days = $6.67/day
# GenAI = $1000 credits / 365 days = $2.74/day
# Combined max daily burn: $6.67 + $2.74 = $9.41/day

BURN_LIMITS = {
    "glitched_daily": 600.00 / 90,     # $6.67/day (2x $300 trial credits)
    "genai_daily": 1000.00 / 365,      # $2.74/day
    "combined_daily": (600.00 / 90) + (1000.00 / 365),  # $9.41/day total
}

# ============================================================================
# RATE LIMITS (from Google AI Studio - Tier 1 Paid)
# ============================================================================
# These are hard caps regardless of budget!

RATE_LIMITS = {
    # Gemini 3
    "gemini-3-pro": {"rpm": 25, "tpm": 1_000_000, "rpd": 250},
    "gemini-3-pro-image": {"rpm": 20, "tpm": 100_000, "rpd": 250},
    
    # Gemini 2.5
    "gemini-2.5-pro": {"rpm": 15, "tpm": 1_000_000, "rpd": 300},
    "gemini-2.5-flash": {"rpm": 1000, "tpm": 1_000_000, "rpd": 10_000},
    "gemini-2.5-flash-lite": {"rpm": 4000, "tpm": 4_000_000, "rpd": "unlimited"},
    "gemini-2.5-flash-image": {"rpm": 500, "tpm": 500_000, "rpd": 2000},
    
    # Gemini 2.0
    "gemini-2.0-flash": {"rpm": 2000, "tpm": 4_000_000, "rpd": "unlimited"},
    "gemini-2.0-flash-lite": {"rpm": 4000, "tpm": 4_000_000, "rpd": "unlimited"},
    
    # Imagen 4
    "imagen-4-fast": {"rpm": 10, "rpd": 70},
    "imagen-4-standard": {"rpm": 10, "rpd": 70},
    "imagen-4-ultra": {"rpm": 5, "rpd": 30},
    
    # Veo 3
    "veo-3-standard": {"rpm": 2, "rpd": 10},
    "veo-3-fast": {"rpm": 2, "rpd": 10},
}

# ============================================================================
# IMAGE GENERATION COSTS (Official ai.google.dev pricing - Dec 2025)
# ============================================================================

# Gemini 3 Pro Image Preview - per-image pricing (from tokens)
# Image output priced at $120/1M tokens
# - 1K-2K images (1024-2048px): 1120 tokens = $0.134/image
# - 4K images (up to 4096px): 2000 tokens = $0.24/image
G3_IMAGE_COSTS = {
    "1k": {
        "resolution": "1024x1024",
        "output_tokens": 1120,
        "cost": 0.134,  # Official: $0.134/image
    },
    "2k": {
        "resolution": "2048x2048", 
        "output_tokens": 1120,  # Same as 1K
        "cost": 0.134,  # Official: $0.134/image
    },
    "4k": {
        "resolution": "4096x4096",
        "output_tokens": 2000,
        "cost": 0.24,   # Official: $0.24/image
    },
}

# Veo Video Generation - per-second pricing
VEO_COSTS = {
    "veo-3.1-standard": 0.40,  # $0.40/second with audio
    "veo-3.1-fast": 0.15,      # $0.15/second with audio
    "veo-3-standard": 0.40,
    "veo-3-fast": 0.15,
}

def get_daily_image_capacity():
    """Calculate how many images can be generated per day within budget."""
    daily_budget = BURN_LIMITS["combined_daily"]
    
    capacity = {
        "g3_pro": {},
        "veo": {},
    }
    
    # G3 Pro Image at different resolutions
    for res, data in G3_IMAGE_COSTS.items():
        capacity["g3_pro"][res] = {
            "cost_per_image": data["cost"],
            "images_per_day": int(daily_budget / data["cost"]),
            "resolution": data["resolution"],
        }
    
    # Veo video (8 second videos)
    for model, cost_per_sec in VEO_COSTS.items():
        video_cost = cost_per_sec * 8  # 8 second video
        capacity["veo"][model] = {
            "cost_per_video": video_cost,
            "videos_per_day": int(daily_budget / video_cost),
        }
    
    return capacity


def show_image_capacity():
    """Display daily image generation capacity."""
    console.print()
    console.print(Panel.fit(
        "[bold cyan]🎨 DAILY IMAGE & VIDEO GENERATION CAPACITY[/bold cyan]",
        border_style="cyan"
    ))
    console.print()
    
    capacity = get_daily_image_capacity()
    daily_budget = BURN_LIMITS["combined_daily"]
    
    console.print(f"[dim]Daily Budget: ${daily_budget:.2f} | Rate limits may cap actual usage[/dim]\n")
    
    # Gemini 3 Pro Image (Flagship)
    g3_limit = RATE_LIMITS.get("gemini-3-pro-image", {}).get("rpd", "?")
    table = Table(title=f"🧠 Gemini 3 Pro Image Preview [Rate Limit: {g3_limit} RPD]", box=box.ROUNDED)
    table.add_column("Resolution", style="cyan")
    table.add_column("Dimensions", justify="center")
    table.add_column("Cost/Image", justify="right", style="yellow")
    table.add_column("Budget Max", justify="right", style="dim")
    table.add_column("Actual Max", justify="right", style="green bold")
    
    for res in ["1k", "2k", "4k"]:
        data = capacity["g3_pro"][res]
        budget_max = data['images_per_day']
        actual_max = min(budget_max, g3_limit) if isinstance(g3_limit, int) else budget_max
        table.add_row(
            res.upper(),
            data["resolution"],
            f"${data['cost_per_image']:.3f}",
            f"{budget_max:,}",
            f"{actual_max:,}"
        )
    
    console.print(table)
    console.print(table)
    console.print()
    
    # Veo Video
    table = Table(title="🎬 Veo Video Generation (8s videos) [Rate Limit: 10 RPD!]", box=box.ROUNDED)
    table.add_column("Model", style="cyan")
    table.add_column("Cost/Video", justify="right", style="yellow")
    table.add_column("Budget Max", justify="right", style="dim")
    table.add_column("Rate Limit", justify="right", style="red bold")
    table.add_column("Actual Max", justify="right", style="green bold")
    
    veo_info = {
        "veo-3.1-standard": ("Veo 3.1 Standard", 10),
        "veo-3.1-fast": ("Veo 3.1 Fast", 10),
        "veo-3-standard": ("Veo 3 Standard", 10),
        "veo-3-fast": ("Veo 3 Fast", 10),
    }
    for model in ["veo-3.1-standard", "veo-3.1-fast", "veo-3-standard", "veo-3-fast"]:
        name, rate_limit = veo_info[model]
        data = capacity["veo"][model]
        actual_max = min(data['videos_per_day'], rate_limit)
        table.add_row(
            name,
            f"${data['cost_per_video']:.2f}",
            f"{data['videos_per_day']:,}",
            f"{rate_limit}",
            f"{actual_max}"
        )
    
    console.print(table)


# ============================================================================
# USAGE TRACKING
# ============================================================================

USAGE_LOG_PATH = Path(__file__).parent / "knowledge_base" / "usage_log.json"


@dataclass 
class UsageEntry:
    timestamp: str
    model: str
    input_tokens: int
    output_tokens: int
    cost: float
    
    def to_dict(self):
        return {
            "timestamp": self.timestamp,
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cost": self.cost
        }


def load_usage_log() -> list:
    if USAGE_LOG_PATH.exists():
        with open(USAGE_LOG_PATH) as f:
            return json.load(f)
    return []


def save_usage_log(entries: list):
    USAGE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(USAGE_LOG_PATH, 'w') as f:
        json.dump(entries, f, indent=2)


def log_usage(model: str, input_tokens: int, output_tokens: int) -> float:
    """Log token usage and return the cost."""
    cost = calculate_cost(model, input_tokens, output_tokens)
    
    entry = UsageEntry(
        timestamp=datetime.now().isoformat(),
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost=cost
    )
    
    entries = load_usage_log()
    entries.append(entry.to_dict())
    save_usage_log(entries)
    
    return cost


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate cost for token usage."""
    if model not in PRICING:
        console.print(f"[yellow]Warning: Unknown model {model}[/yellow]")
        return 0.0
    
    pricing = PRICING[model]
    
    if "per_image" in pricing:
        return pricing["per_image"]
    if "per_video" in pricing:
        return pricing["per_video"]
    
    input_cost = (input_tokens / 1_000_000) * pricing.get("input", 0)
    output_cost = (output_tokens / 1_000_000) * pricing.get("output", 0)
    
    return input_cost + output_cost


def get_usage_stats() -> dict:
    """Get usage statistics from log."""
    entries = load_usage_log()
    
    today = datetime.now().date()
    this_month = today.replace(day=1)
    
    stats = {
        "total_cost": 0.0,
        "today_cost": 0.0,
        "month_cost": 0.0,
        "total_queries": 0,
        "by_model": {}
    }
    
    for entry in entries:
        cost = entry.get("cost", 0)
        model = entry.get("model", "unknown")
        timestamp = datetime.fromisoformat(entry["timestamp"]).date()
        
        stats["total_cost"] += cost
        stats["total_queries"] += 1
        
        if timestamp == today:
            stats["today_cost"] += cost
        
        if timestamp >= this_month:
            stats["month_cost"] += cost
        
        if model not in stats["by_model"]:
            stats["by_model"][model] = {"cost": 0, "count": 0}
        stats["by_model"][model]["cost"] += cost
        stats["by_model"][model]["count"] += 1
    
    return stats


# ============================================================================
# DISPLAY FUNCTIONS
# ============================================================================

def show_credits():
    """Display credit status with rich formatting."""
    console.print()
    console.print(Panel.fit(
        "[bold cyan]💰 VISIONS AI CREDIT STATUS[/bold cyan]",
        border_style="cyan"
    ))
    console.print()
    
    # Credits table
    table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta")
    table.add_column("Credit", style="cyan")
    table.add_column("Original", justify="right")
    table.add_column("Remaining", justify="right", style="green")
    table.add_column("Used", justify="right", style="red")
    table.add_column("Expiry", justify="center")
    table.add_column("Status", justify="center")
    
    total_remaining = 0
    total_original = 0
    
    for credit in CREDITS:
        # Status emoji
        if credit.status == "expired_but_working":
            status = "🎰 [yellow]Glitched![/yellow]"
        elif credit.status == "active":
            status = "✅ [green]Active[/green]"
        else:
            status = "❌ [red]Expired[/red]"
        
        # Days until expiry
        days = credit.days_until_expiry
        if days < 0:
            expiry_str = f"[red]{credit.expiry.strftime('%Y-%m-%d')} (EXPIRED)[/red]"
        elif days < 30:
            expiry_str = f"[yellow]{credit.expiry.strftime('%Y-%m-%d')} ({days}d)[/yellow]"
        else:
            expiry_str = f"[green]{credit.expiry.strftime('%Y-%m-%d')}[/green]"
        
        if credit.is_active:
            total_remaining += credit.remaining
            total_original += credit.original
        
        table.add_row(
            credit.name,
            f"${credit.original:,.2f}",
            f"${credit.remaining:,.2f}",
            f"${credit.used:,.2f}",
            expiry_str,
            status
        )
    
    console.print(table)
    console.print()
    
    # Summary panel
    total_used = total_original - total_remaining
    percent_remaining = (total_remaining / total_original * 100) if total_original > 0 else 0
    
    # Calculate days elapsed since start
    days_elapsed = (datetime.now() - START_DATE).days
    
    summary = f"""
[bold]Total Original:[/bold]  ${total_original:,.2f}
[bold]Total Used:[/bold]      ${total_used:,.2f}
[bold]───────────────────────[/bold]
[bold green]AVAILABLE:[/bold green]       [bold green]${total_remaining:,.2f}[/bold green] ({percent_remaining:.1f}%)

[dim]🎰 Includes "expired" credit still being honored[/dim]
"""
    
    console.print(Panel(summary, title="💵 Summary", border_style="green"))
    console.print()
    
    # Daily burn limits panel
    glitched_limit = BURN_LIMITS["glitched_daily"]
    genai_limit = BURN_LIMITS["genai_daily"]
    combined_limit = BURN_LIMITS["combined_daily"]
    
    # Calculate end dates
    glitched_end = START_DATE + timedelta(days=90)
    genai_end = datetime(2025, 12, 4) + timedelta(days=365)
    
    burn_info = f"""
[bold cyan]📅 TIMELINE[/bold cyan]
   Start Date:       [green]{START_DATE.strftime('%Y-%m-%d')}[/green]
   Days Elapsed:     [yellow]{days_elapsed}[/yellow]
   
[bold cyan]🔥 DAILY BURN LIMITS[/bold cyan]
   Glitched ($600/90d):   [bold yellow]${glitched_limit:.2f}/day[/bold yellow]  → ends [red]{glitched_end.strftime('%Y-%m-%d')}[/red]
   GenAI ($1000/365d):    [bold yellow]${genai_limit:.2f}/day[/bold yellow]  → ends [green]{genai_end.strftime('%Y-%m-%d')}[/green]
   ────────────────────────────────────────
   [bold]Combined Max:[/bold]         [bold green]${combined_limit:.2f}/day[/bold green]

[dim]Stay under ${combined_limit:.2f}/day to use all credits evenly[/dim]
"""
    
    console.print(Panel(burn_info, title="🔥 Burn Rate Limits", border_style="yellow"))


def show_pricing():
    """Display pricing reference."""
    console.print()
    console.print(Panel.fit(
        "[bold cyan]💵 PRICING REFERENCE[/bold cyan]",
        border_style="cyan"
    ))
    console.print()
    
    # Text models
    table = Table(title="Text Models (per 1M tokens)", box=box.ROUNDED)
    table.add_column("Model", style="cyan")
    table.add_column("Input", justify="right", style="yellow")
    table.add_column("Output", justify="right", style="red")
    table.add_column("Location")
    
    text_models = ["gemini-3-pro-preview", "gemini-3-flash-preview"]
    for model in text_models:
        p = PRICING[model]
        input_price = p.get('input', p.get('input_text', 0))
        table.add_row(
            model,
            f"${input_price:.2f}",
            f"${p['output']:.2f}",
            p['location']
        )
    
    console.print(table)
    console.print()
    
    # Image models
    table = Table(title="Image Models", box=box.ROUNDED)
    table.add_column("Model", style="cyan")
    table.add_column("Input", justify="right", style="yellow")
    table.add_column("Output", justify="right", style="red")
    table.add_column("Est. Per Image", justify="right", style="magenta")
    
    table.add_row("gemini-3-pro-image-preview", "$2.00/1M", "$120.00/1M", "~$0.12")
    table.add_row("gemini-3-flash-preview", "$0.50/1M", "$3.00/1M", "-")
    
    console.print(table)


def show_usage():
    """Display usage statistics."""
    stats = get_usage_stats()
    
    console.print()
    console.print(Panel.fit(
        "[bold cyan]📊 USAGE STATISTICS[/bold cyan]",
        border_style="cyan"
    ))
    console.print()
    
    # Overview
    summary = f"""
[bold]Today:[/bold]        ${stats['today_cost']:.4f}
[bold]This Month:[/bold]   ${stats['month_cost']:.4f}
[bold]All Time:[/bold]     ${stats['total_cost']:.4f}
[bold]Total Queries:[/bold] {stats['total_queries']}
"""
    console.print(Panel(summary, title="📈 Overview", border_style="blue"))
    
    if stats["by_model"]:
        table = Table(title="By Model", box=box.ROUNDED)
        table.add_column("Model", style="cyan")
        table.add_column("Queries", justify="right")
        table.add_column("Cost", justify="right", style="yellow")
        
        for model, data in sorted(stats["by_model"].items(), key=lambda x: x[1]["cost"], reverse=True):
            table.add_row(model, str(data["count"]), f"${data['cost']:.4f}")
        
        console.print(table)


def estimate_cost(num_queries: int, query_type: str = "mixed"):
    """Estimate cost for N queries."""
    console.print()
    console.print(Panel.fit(
        f"[bold cyan]📊 COST ESTIMATE: {num_queries:,} Queries[/bold cyan]",
        border_style="cyan"
    ))
    console.print()
    
    # Average costs by type
    costs_per_query = {
        "simple": 0.0001,      # Greeting (Flash Lite only)
        "quick": 0.002,        # Single model
        "grounded": 0.04,      # With search
        "cascade": 0.07,       # Full cascade
        "image_g3": 0.12,      # G3 Pro image
        "image_flash": 0.03,   # Flash image
        "mixed": 0.035,        # Average mix
    }
    
    cost_per = costs_per_query.get(query_type, costs_per_query["mixed"])
    total_cost = num_queries * cost_per
    
    # How long will credits last
    total_credits = sum(c.remaining for c in CREDITS if c.is_active)
    daily_queries = num_queries
    daily_cost = total_cost
    days_remaining = total_credits / daily_cost if daily_cost > 0 else float('inf')
    
    table = Table(box=box.ROUNDED)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right", style="yellow")
    
    table.add_row("Query Type", query_type)
    table.add_row("Cost per Query", f"${cost_per:.4f}")
    table.add_row("Total Queries", f"{num_queries:,}")
    table.add_row("Estimated Cost", f"${total_cost:.2f}")
    table.add_row("", "")
    table.add_row("Available Credits", f"${total_credits:,.2f}")
    table.add_row("Days at this rate", f"{days_remaining:.0f} days")
    
    console.print(table)
    console.print()
    
    # Monthly projection
    monthly_cost = daily_cost * 30
    console.print(f"[dim]Monthly projection ({num_queries:,}/day): ${monthly_cost:,.2f}[/dim]")


def show_dashboard():
    """Show full dashboard."""
    console.clear()
    console.print()
    console.print(Panel.fit(
        "[bold magenta]✨ VISIONS AI COST TRACKER ✨[/bold magenta]",
        border_style="magenta"
    ))
    
    show_credits()
    console.print()
    show_usage()


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="💰 Visions AI Cost Tracker")
    parser.add_argument("--credits", "-c", action="store_true", help="Show credit status")
    parser.add_argument("--pricing", "-p", action="store_true", help="Show pricing reference")
    parser.add_argument("--usage", "-u", action="store_true", help="Show usage statistics")
    parser.add_argument("--images", "-i", action="store_true", help="Show daily image generation capacity")
    parser.add_argument("--estimate", "-e", type=int, metavar="N", help="Estimate cost for N queries")
    parser.add_argument("--type", "-t", default="mixed", 
                       choices=["simple", "quick", "grounded", "cascade", "image_g3", "image_flash", "mixed"],
                       help="Query type for estimation")
    parser.add_argument("--log", "-l", nargs=3, metavar=("MODEL", "IN", "OUT"), 
                       help="Log usage: MODEL INPUT_TOKENS OUTPUT_TOKENS")
    
    args = parser.parse_args()
    
    if args.credits:
        show_credits()
    elif args.pricing:
        show_pricing()
    elif args.usage:
        show_usage()
    elif args.images:
        show_image_capacity()
    elif args.estimate:
        estimate_cost(args.estimate, args.type)
    elif args.log:
        model, input_tokens, output_tokens = args.log
        cost = log_usage(model, int(input_tokens), int(output_tokens))
        console.print(f"[green]✓ Logged: {model} ({input_tokens} in, {output_tokens} out) = ${cost:.6f}[/green]")
    else:
        show_dashboard()


if __name__ == "__main__":
    main()
