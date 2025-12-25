#!/usr/bin/env python3
"""
💰 Visions AI Official Pricing Reference

Complete pricing data from ai.google.dev (December 2025)
All prices are for Paid Tier in USD per 1M tokens unless noted.

Author: Gemini - Web & Cloud Specialist
"""

import math
from datetime import datetime, date
from typing import Dict, Optional

# ============================================================================
# OFFICIAL PRICING (ai.google.dev - December 2025)
# ============================================================================

PRICING = {
    # ========================================================================
    # GEMINI 3 PRO PREVIEW
    # ========================================================================
    "gemini-3-pro-preview": {
        "standard": {
            "input_short": 2.00,      # prompts <= 200k tokens
            "input_long": 4.00,       # prompts > 200k tokens
            "output_short": 12.00,    # prompts <= 200k
            "output_long": 18.00,     # prompts > 200k
            "context_cache_short": 0.20,
            "context_cache_long": 0.40,
            "cache_storage_hourly": 4.50,
        },
        "batch": {
            "input_short": 1.00,      # 50% discount
            "input_long": 2.00,
            "output_short": 6.00,
            "output_long": 9.00,
        },
        "grounding_search": {
            "free_per_month": 5000,
            "price_per_1k": 14.00,    # Starts Jan 5, 2026
        },
    },
    
    # ========================================================================
    # GEMINI 3 PRO IMAGE PREVIEW
    # ========================================================================
    "gemini-3-pro-image-preview": {
        "standard": {
            "text_input": 2.00,
            "image_input_per_image": 0.0011,  # 560 tokens
            "text_output": 12.00,
            "image_output_1k_2k": 0.134,      # 1024x1024 to 2048x2048
            "image_output_4k": 0.24,          # Up to 4096x4096
        },
        "batch": {
            "text_input": 1.00,
            "image_input_per_image": 0.0006,
            "text_output": 6.00,
            "image_output_1k_2k": 0.067,      # 50% discount
            "image_output_4k": 0.12,
        },
    },

    # ========================================================================
    # GEMINI 3 FLASH PREVIEW
    # ========================================================================
    "gemini-3-flash-preview": {
        "standard": {
            "input_text_image_video": 0.50,
            "input_audio": 1.00,
            "output": 3.00,
            "context_cache_text_image_video": 0.05,
            "context_cache_audio": 0.10,
            "cache_storage_hourly": 1.00,
        },
        "batch": {
            "input_text_image_video": 0.25,
            "input_audio": 0.50,
            "output": 1.50,
        },
        "grounding_search": {
            "free_per_month": 5000,
            "price_per_1k": 14.00,    # Starts Jan 5, 2026
        },
    },
    
    # ========================================================================
    # VEO 3.1
    # ========================================================================
    "veo-3.1-generate-preview": {
        "standard": 0.40,  # per second, with audio
        "fast": 0.15,      # per second, with audio
    },
    "veo-3.1": { # Alias
        "standard": 0.40,  # per second, with audio
        "fast": 0.15,      # per second, with audio
    },
    
    # ========================================================================
    # VEO 3
    # ========================================================================
    "veo-3.0-generate-001": {
        "standard": 0.40,  # per second, with audio
    },
    "veo-3.0-fast-generate-001": {
        "fast": 0.15,      # per second, with audio
    },

    # ========================================================================
    # EMBEDDINGS
    # ========================================================================
    "gemini-embedding-001": {
        "standard": {
            "input": 0.15,
        },
        "batch": {
            "input": 0.075,
        },
    },
}

# ============================================================================
# TOOLS PRICING
# ============================================================================

TOOLS_PRICING = {
    "google_search": {
        "free_rpd": 1500,  # Shared between Flash and Flash-Lite
        "price_per_1k": 35.00,
        "gemini_3_free_per_month": 5000,
        "gemini_3_price_per_1k": 14.00,  # Starts Jan 5, 2026
    },
    "google_maps": {
        "free_rpd": 1500,  # Flash/Flash-Lite
        "pro_free_rpd": 10000,  # Pro models
        "price_per_1k": 25.00,
    },
    "code_execution": "free",
    "url_context": "charged_as_input_tokens",
    "file_search": {
        "embedding_cost": 0.15,  # per 1M tokens
        "retrieval": "charged_as_input_tokens",
    },
}

# ============================================================================
# QUICK COST CALCULATORS
# ============================================================================

def estimate_text_cost(model: str, input_tokens: int, output_tokens: int, 
                       use_batch: bool = False, prompt_length: str = "short") -> float:
    """Estimate cost for a text query."""
    pricing = PRICING.get(model)
    if not pricing:
        return 0.0
    
    tier = "batch" if use_batch else "standard"
    tier_pricing = pricing.get(tier, pricing.get("standard", {}))
    
    # Determine input/output prices
    if prompt_length == "long":
        input_price = tier_pricing.get("input_long", tier_pricing.get("input_short", tier_pricing.get("input_text_image_video", 0)))
        output_price = tier_pricing.get("output_long", tier_pricing.get("output_short", tier_pricing.get("output", 0)))
    else:
        input_price = tier_pricing.get("input_short", tier_pricing.get("input_text_image_video", tier_pricing.get("input", 0)))
        output_price = tier_pricing.get("output_short", tier_pricing.get("output", 0))
    
    input_cost = (input_tokens / 1_000_000) * input_price
    output_cost = (output_tokens / 1_000_000) * output_price
    
    return math.fsum([input_cost, output_cost])


def estimate_image_cost(model: str, resolution: str = "2k", use_batch: bool = False) -> float:
    """Estimate cost for image generation."""
    if model in ["gemini-3-pro-image-preview", "gemini-3-pro-image"]:
        tier = "batch" if use_batch else "standard"
        if resolution == "4k":
            return PRICING["gemini-3-pro-image-preview"][tier]["image_output_4k"]
        else:
            return PRICING["gemini-3-pro-image-preview"][tier]["image_output_1k_2k"]
    
    return 0.0


def estimate_video_cost(model: str, duration_seconds: int = 8) -> float:
    """Estimate cost for video generation."""
    if "veo-3.1" in model:
        rate = PRICING["veo-3.1"]["fast"] if "fast" in model else PRICING["veo-3.1"]["standard"]
        return rate * duration_seconds
    
    return 0.0


def get_grounding_cost(tool: str, query_count: int, model: str = "gemini-3-flash-preview") -> float:
    """Calculate grounding cost after free tier."""
    if tool == "google_search":
        if "gemini-3" in model:
            free = TOOLS_PRICING["google_search"]["gemini_3_free_per_month"]
            rate = TOOLS_PRICING["google_search"]["gemini_3_price_per_1k"]
        else:
            free = TOOLS_PRICING["google_search"]["free_rpd"]
            rate = TOOLS_PRICING["google_search"]["price_per_1k"]
    elif tool == "google_maps":
        free = TOOLS_PRICING["google_maps"]["free_rpd"]
        rate = TOOLS_PRICING["google_maps"]["price_per_1k"]
    else:
        return 0.0
    
    billable = max(0, query_count - free)
    return (billable / 1000) * rate


# ============================================================================
# SUMMARY FUNCTIONS
# ============================================================================

def print_pricing_summary():
    """Print a summary of key pricing."""
    from rich.console import Console
    from rich.table import Table
    from rich import box
    
    console = Console()
    
    # Text models
    table = Table(title="💬 Text Model Pricing (per 1M tokens)", box=box.ROUNDED)
    table.add_column("Model", style="cyan")
    table.add_column("Input", justify="right")
    table.add_column("Output", justify="right")
    table.add_column("Batch In", justify="right", style="green")
    table.add_column("Batch Out", justify="right", style="green")
    
    table.add_row("Gemini 3 Pro", "$2.00", "$12.00", "$1.00", "$6.00")
    table.add_row("Gemini 3 Flash", "$0.50", "$3.00", "$0.25", "$1.50")
    
    console.print(table)
    
    # Image models
    table2 = Table(title="\n🎨 Image Generation Pricing (per image)", box=box.ROUNDED)
    table2.add_column("Model", style="cyan")
    table2.add_column("Standard", justify="right")
    table2.add_column("Batch", justify="right", style="green")
    
    table2.add_row("G3 Pro Image (1K/2K)", "$0.134", "$0.067")
    table2.add_row("G3 Pro Image (4K)", "$0.24", "$0.12")
    
    console.print(table2)
    
    # Video models
    table3 = Table(title="\n🎬 Video Generation Pricing (per second)", box=box.ROUNDED)
    table3.add_column("Model", style="cyan")
    table3.add_column("Rate", justify="right")
    table3.add_column("8s Video", justify="right")
    
    table3.add_row("Veo 3.1 Standard", "$0.40/s", "$3.20")
    table3.add_row("Veo 3.1 Fast", "$0.15/s", "$1.20")
    table3.add_row("Veo 3 Standard", "$0.40/s", "$3.20")
    table3.add_row("Veo 3 Fast", "$0.15/s", "$1.20")
    
    console.print(table3)
    
    # Tools
    table4 = Table(title="\n🔧 Tools Pricing", box=box.ROUNDED)
    table4.add_column("Tool", style="cyan")
    table4.add_column("Free Tier", justify="right")
    table4.add_column("Paid", justify="right")
    
    table4.add_row("Google Search", "5,000 / mo", "$14/1K queries")
    table4.add_row("Embeddings", "-", "$0.15/1M tokens")
    table4.add_row("Code Execution", "Free", "Free")
    
    console.print(table4)


if __name__ == "__main__":
    print_pricing_summary()
