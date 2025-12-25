#!/usr/bin/env python3
"""
📊 Visions AI Smart Expense Tracker

Inspired by FreeCodeCamp's expense tracker tutorial, adapted for GCP cost tracking.
Uses Gemini for auto-categorization and matplotlib for visualizations.

Features:
- Auto-categorize expenses using LLM
- Pie charts for expense breakdown
- Bar charts for category comparison
- Smart summaries with insights
- Export to CSV/JSON

Author: Gemini - Web & Cloud Specialist
"""

import json
import math
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, asdict
import csv

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    plt = None

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich import box
except ImportError:
    Console = None
    Table = None

# ============================================================================
# CONFIGURATION
# ============================================================================

DATA_DIR = Path(__file__).parent / "knowledge_base"
EXPENSE_LOG_FILE = DATA_DIR / "expense_log.json"
CHARTS_DIR = Path(__file__).parent / "charts"

# Expense categories (inspired by FreeCodeCamp article)
EXPENSE_CATEGORIES = {
    "text_generation": "💬 Text Generation",
    "image_generation": "🎨 Image Generation", 
    "video_generation": "🎬 Video Generation",
    "embedding": "🔗 Embedding",
    "grounding": "🌐 Grounding (Search/Maps)",
    "reasoning": "🧠 Reasoning Engine",
    "other": "📦 Other",
}

# Model to category mapping
MODEL_CATEGORIES = {
    "gemini-3-pro": "text_generation",
    "gemini-3-pro-image": "image_generation",
    "gemini-2.5-pro": "text_generation",
    "gemini-2.5-flash": "text_generation",
    "gemini-2.5-flash-lite": "text_generation",
    "gemini-2.5-flash-image": "image_generation",
    "imagen-4-fast": "image_generation",
    "imagen-4-standard": "image_generation",
    "imagen-4-ultra": "image_generation",
    "imagen-3": "image_generation",
    "veo-3.1-standard": "video_generation",
    "veo-3.1-fast": "video_generation",
    "veo-3-standard": "video_generation",
    "veo-3-fast": "video_generation",
    "veo-2": "video_generation",
    "text-embedding": "embedding",
    "google-search": "grounding",
    "google-maps": "grounding",
}

# ============================================================================
# EXPENSE ENTRY
# ============================================================================

@dataclass
class ExpenseEntry:
    """Single expense entry."""
    timestamp: str
    model: str
    category: str
    amount: float
    note: str
    tokens_in: int = 0
    tokens_out: int = 0
    
    def to_dict(self):
        return asdict(self)


class ExpenseTracker:
    """Smart expense tracker with auto-categorization and visualization."""
    
    def __init__(self):
        self.entries: List[Dict] = []
        self.console = Console() if Console else None
        self._load()
    
    def _load(self):
        """Load expenses from disk."""
        if EXPENSE_LOG_FILE.exists():
            try:
                with open(EXPENSE_LOG_FILE) as f:
                    self.entries = json.load(f)
            except:
                self.entries = []
    
    def _save(self):
        """Save expenses to disk."""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(EXPENSE_LOG_FILE, 'w') as f:
            json.dump(self.entries, f, indent=2)
    
    def auto_categorize(self, model: str, note: str = "") -> str:
        """Auto-categorize expense based on model/note (LLM-style)."""
        # First check model mapping
        if model in MODEL_CATEGORIES:
            return MODEL_CATEGORIES[model]
        
        # Fallback to note-based categorization
        note_lower = note.lower()
        if any(kw in note_lower for kw in ["image", "picture", "photo", "generate"]):
            return "image_generation"
        elif any(kw in note_lower for kw in ["video", "clip", "animation"]):
            return "video_generation"
        elif any(kw in note_lower for kw in ["search", "google", "maps"]):
            return "grounding"
        elif any(kw in note_lower for kw in ["embed", "vector"]):
            return "embedding"
        
        return "text_generation"  # Default
    
    def add_expense(self, model: str, amount: float, note: str = "",
                    tokens_in: int = 0, tokens_out: int = 0) -> ExpenseEntry:
        """Add a new expense with auto-categorization."""
        category = self.auto_categorize(model, note)
        
        entry = ExpenseEntry(
            timestamp=datetime.now().isoformat(),
            model=model,
            category=category,
            amount=amount,
            note=note or f"API call to {model}",
            tokens_in=tokens_in,
            tokens_out=tokens_out
        )
        
        self.entries.append(entry.to_dict())
        self._save()
        return entry
    
    def get_summary(self, days: int = 7) -> Dict:
        """Get expense summary by category."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        recent = [e for e in self.entries if e["timestamp"] >= cutoff]
        
        summary = {
            "total": 0.0,
            "by_category": {},
            "by_model": {},
            "count": len(recent),
            "period_days": days,
        }
        
        for entry in recent:
            amount = entry.get("amount", 0)
            category = entry.get("category", "other")
            model = entry.get("model", "unknown")
            
            summary["total"] = math.fsum([summary["total"], amount])
            summary["by_category"][category] = math.fsum([
                summary["by_category"].get(category, 0), amount
            ])
            summary["by_model"][model] = math.fsum([
                summary["by_model"].get(model, 0), amount
            ])
        
        return summary
    
    def get_daily_totals(self, days: int = 30) -> Dict[str, float]:
        """Get daily expense totals."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        recent = [e for e in self.entries if e["timestamp"] >= cutoff]
        
        daily = {}
        for entry in recent:
            day = entry["timestamp"][:10]
            daily[day] = math.fsum([daily.get(day, 0), entry.get("amount", 0)])
        
        return daily
    
    # ========================================================================
    # VISUALIZATIONS (matplotlib)
    # ========================================================================
    
    def plot_pie_chart(self, days: int = 7, save_path: Optional[str] = None) -> Optional[str]:
        """Create pie chart of expenses by category."""
        if not MATPLOTLIB_AVAILABLE:
            print("matplotlib not available for visualization")
            return None
        
        summary = self.get_summary(days)
        
        if not summary["by_category"]:
            print("No expenses to visualize")
            return None
        
        # Prepare data
        categories = []
        amounts = []
        for cat, amount in summary["by_category"].items():
            if amount > 0:
                label = EXPENSE_CATEGORIES.get(cat, cat)
                categories.append(label)
                amounts.append(amount)
        
        # Create chart
        fig, ax = plt.subplots(figsize=(8, 8))
        colors = plt.cm.Set3(range(len(categories)))
        
        wedges, texts, autotexts = ax.pie(
            amounts,
            labels=categories,
            autopct='%1.1f%%',
            startangle=90,
            shadow=True,
            colors=colors
        )
        
        ax.set_title(f"GCP Expense Breakdown (Last {days} Days)\nTotal: ${summary['total']:.2f}")
        
        # Save or show
        if save_path:
            CHARTS_DIR.mkdir(parents=True, exist_ok=True)
            filepath = CHARTS_DIR / save_path
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            plt.close()
            return str(filepath)
        else:
            plt.show()
            return None
    
    def plot_bar_chart(self, days: int = 7, save_path: Optional[str] = None) -> Optional[str]:
        """Create bar chart of expenses by category."""
        if not MATPLOTLIB_AVAILABLE:
            print("matplotlib not available for visualization")
            return None
        
        summary = self.get_summary(days)
        
        if not summary["by_category"]:
            print("No expenses to visualize")
            return None
        
        # Prepare data
        categories = []
        amounts = []
        for cat, amount in sorted(summary["by_category"].items(), key=lambda x: x[1], reverse=True):
            if amount > 0:
                label = EXPENSE_CATEGORIES.get(cat, cat)
                categories.append(label.split()[1] if " " in label else label)  # Remove emoji for bar
                amounts.append(amount)
        
        # Create chart
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(categories, amounts, color='#4285F4', edgecolor='black')
        
        # Add value labels on bars
        for bar, amount in zip(bars, amounts):
            height = bar.get_height()
            ax.annotate(f'${amount:.2f}',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3),
                       textcoords="offset points",
                       ha='center', va='bottom', fontsize=9)
        
        ax.set_xlabel('Category')
        ax.set_ylabel('Amount Spent ($)')
        ax.set_title(f'GCP Expenses by Category (Last {days} Days)')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        # Save or show
        if save_path:
            CHARTS_DIR.mkdir(parents=True, exist_ok=True)
            filepath = CHARTS_DIR / save_path
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            plt.close()
            return str(filepath)
        else:
            plt.show()
            return None
    
    def plot_daily_trend(self, days: int = 30, save_path: Optional[str] = None) -> Optional[str]:
        """Create line chart of daily expenses."""
        if not MATPLOTLIB_AVAILABLE:
            print("matplotlib not available for visualization")
            return None
        
        daily = self.get_daily_totals(days)
        
        if not daily:
            print("No expenses to visualize")
            return None
        
        # Sort by date
        dates = sorted(daily.keys())
        amounts = [daily[d] for d in dates]
        
        # Convert to datetime for plotting
        date_objs = [datetime.strptime(d, "%Y-%m-%d") for d in dates]
        
        # Create chart
        fig, ax = plt.subplots(figsize=(12, 5))
        ax.plot(date_objs, amounts, marker='o', linewidth=2, markersize=6, color='#EA4335')
        ax.fill_between(date_objs, amounts, alpha=0.3, color='#EA4335')
        
        # Add daily budget line
        daily_budget = 9.41
        ax.axhline(y=daily_budget, color='#34A853', linestyle='--', 
                   label=f'Daily Budget (${daily_budget:.2f})', linewidth=2)
        
        ax.set_xlabel('Date')
        ax.set_ylabel('Amount Spent ($)')
        ax.set_title(f'Daily GCP Expenses (Last {days} Days)')
        ax.legend()
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, days // 10)))
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        # Save or show
        if save_path:
            CHARTS_DIR.mkdir(parents=True, exist_ok=True)
            filepath = CHARTS_DIR / save_path
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            plt.close()
            return str(filepath)
        else:
            plt.show()
            return None
    
    def generate_all_charts(self, days: int = 7) -> List[str]:
        """Generate all visualization charts."""
        charts = []
        
        pie = self.plot_pie_chart(days, f"expense_pie_{date.today()}.png")
        if pie:
            charts.append(pie)
        
        bar = self.plot_bar_chart(days, f"expense_bar_{date.today()}.png")
        if bar:
            charts.append(bar)
        
        trend = self.plot_daily_trend(30, f"expense_trend_{date.today()}.png")
        if trend:
            charts.append(trend)
        
        return charts
    
    # ========================================================================
    # SMART INSIGHTS
    # ========================================================================
    
    def get_insights(self, days: int = 7) -> List[str]:
        """Generate smart insights about spending."""
        summary = self.get_summary(days)
        daily_budget = 9.41
        insights = []
        
        if summary["count"] == 0:
            return ["📊 No expense data for the selected period."]
        
        # Total spend insight
        avg_daily = summary["total"] / max(days, 1)
        if avg_daily > daily_budget:
            insights.append(f"🔴 Spending ${avg_daily:.2f}/day exceeds ${daily_budget:.2f} budget by ${avg_daily - daily_budget:.2f}")
        else:
            savings = daily_budget - avg_daily
            insights.append(f"✅ Spending ${avg_daily:.2f}/day - ${savings:.2f} under daily budget")
        
        # Top category
        if summary["by_category"]:
            top_cat = max(summary["by_category"].items(), key=lambda x: x[1])
            cat_name = EXPENSE_CATEGORIES.get(top_cat[0], top_cat[0])
            pct = (top_cat[1] / summary["total"] * 100) if summary["total"] > 0 else 0
            insights.append(f"💡 Top spending: {cat_name} ({pct:.1f}% = ${top_cat[1]:.2f})")
        
        # Top model
        if summary["by_model"]:
            top_model = max(summary["by_model"].items(), key=lambda x: x[1])
            insights.append(f"🔧 Most used: {top_model[0]} (${top_model[1]:.2f})")
        
        # Image generation check
        img_cost = summary["by_category"].get("image_generation", 0)
        if img_cost > summary["total"] * 0.5:
            insights.append(f"🎨 Image generation is >50% of spending. Consider using Flash Image ($0.039) for drafts.")
        
        # Video check
        vid_cost = summary["by_category"].get("video_generation", 0)
        if vid_cost > 0:
            insights.append(f"🎬 Video generation: ${vid_cost:.2f} - Remember only 10 videos/day allowed!")
        
        return insights
    
    # ========================================================================
    # DISPLAY
    # ========================================================================
    
    def print_summary(self, days: int = 7):
        """Print expense summary with rich formatting."""
        if not self.console:
            return
        
        summary = self.get_summary(days)
        insights = self.get_insights(days)
        
        self.console.print()
        self.console.print(Panel.fit(
            "[bold green]💰 SMART EXPENSE TRACKER[/bold green]",
            border_style="green"
        ))
        
        # Summary stats
        self.console.print(f"\n[bold]📊 Last {days} Days Summary:[/bold]")
        self.console.print(f"   Total Spent: [yellow]${summary['total']:.4f}[/yellow]")
        self.console.print(f"   Transactions: {summary['count']}")
        
        # By category table
        if summary["by_category"]:
            table = Table(title="By Category", box=box.ROUNDED)
            table.add_column("Category", style="cyan")
            table.add_column("Amount", justify="right", style="yellow")
            table.add_column("Share", justify="right")
            
            for cat, amount in sorted(summary["by_category"].items(), key=lambda x: x[1], reverse=True):
                pct = (amount / summary["total"] * 100) if summary["total"] > 0 else 0
                label = EXPENSE_CATEGORIES.get(cat, cat)
                table.add_row(label, f"${amount:.4f}", f"{pct:.1f}%")
            
            self.console.print(table)
        
        # Insights
        self.console.print(f"\n[bold]💡 Smart Insights:[/bold]")
        for insight in insights:
            self.console.print(f"   {insight}")
    
    def export_csv(self, filepath: str, days: int = 30):
        """Export expenses to CSV."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        recent = [e for e in self.entries if e["timestamp"] >= cutoff]
        
        with open(filepath, 'w', newline='') as f:
            if recent:
                writer = csv.DictWriter(f, fieldnames=recent[0].keys())
                writer.writeheader()
                writer.writerows(recent)


# ============================================================================
# SINGLETON & CLI
# ============================================================================

_tracker = None

def get_expense_tracker() -> ExpenseTracker:
    """Get singleton instance."""
    global _tracker
    if _tracker is None:
        _tracker = ExpenseTracker()
    return _tracker


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="💰 Smart Expense Tracker")
    parser.add_argument("--summary", "-s", type=int, nargs="?", const=7, help="Show summary (default: 7 days)")
    parser.add_argument("--charts", "-c", type=int, nargs="?", const=7, help="Generate charts (default: 7 days)")
    parser.add_argument("--export", "-e", type=str, help="Export to CSV file")
    parser.add_argument("--add", "-a", nargs=3, metavar=("MODEL", "AMOUNT", "NOTE"), help="Add expense")
    args = parser.parse_args()
    
    tracker = get_expense_tracker()
    
    if args.add:
        model, amount, note = args.add
        entry = tracker.add_expense(model, float(amount), note)
        print(f"✅ Added: {entry.model} = ${entry.amount:.4f} [{entry.category}]")
    
    if args.summary is not None:
        tracker.print_summary(args.summary)
    
    if args.charts is not None:
        print(f"📊 Generating charts for last {args.charts} days...")
        charts = tracker.generate_all_charts(args.charts)
        for chart in charts:
            print(f"   ✅ Saved: {chart}")
    
    if args.export:
        tracker.export_csv(args.export)
        print(f"✅ Exported to: {args.export}")
    
    if not any([args.summary, args.charts, args.export, args.add]):
        tracker.print_summary(7)
