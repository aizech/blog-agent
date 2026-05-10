#!/usr/bin/env python3
"""
Research helper script for technical blog writing.
Provides utilities for organizing and validating research sources.
"""

import json
import sys
from datetime import datetime
from typing import List, Dict, Any

class ResearchHelper:
    def __init__(self):
        self.sources = []
    
    def add_source(self, url: str, title: str, relevance: str, key_points: List[str]):
        """Add a research source with metadata."""
        source = {
            "url": url,
            "title": title,
            "relevance": relevance,  # "high", "medium", "low"
            "key_points": key_points,
            "added_date": datetime.now().isoformat()
        }
        self.sources.append(source)
    
    def get_high_relevance_sources(self) -> List[Dict[str, Any]]:
        """Get only high-relevance sources."""
        return [s for s in self.sources if s["relevance"] == "high"]
    
    def export_research_summary(self) -> str:
        """Export a formatted summary of research findings."""
        if not self.sources:
            return "No sources researched yet."
        
        summary = "# Research Summary\n\n"
        
        # High relevance sources first
        high_sources = self.get_high_relevance_sources()
        if high_sources:
            summary += "## Key Sources\n\n"
            for source in high_sources:
                summary += f"**{source['title']}** ({source['url']})\n"
                for point in source['key_points']:
                    summary += f"- {point}\n"
                summary += "\n"
        
        # All sources
        summary += "## All Sources\n\n"
        for source in self.sources:
            relevance_indicator = "🔥" if source["relevance"] == "high" else "📚" if source["relevance"] == "medium" else "📄"
            summary += f"{relevance_indicator} [{source['title']}]({source['url']}) - {source['relevance']} relevance\n"
        
        return summary
    
    def save_to_file(self, filename: str):
        """Save research data to JSON file."""
        with open(filename, 'w') as f:
            json.dump(self.sources, f, indent=2)
    
    def load_from_file(self, filename: str):
        """Load research data from JSON file."""
        try:
            with open(filename, 'r') as f:
                self.sources = json.load(f)
        except FileNotFoundError:
            print(f"No research file found at {filename}")

def main():
    """Command line interface for research helper."""
    if len(sys.argv) < 2:
        print("Usage: python research_helper.py <command>")
        print("Commands: summary, export")
        return
    
    helper = ResearchHelper()
    helper.load_from_file("research_data.json")
    
    command = sys.argv[1]
    
    if command == "summary":
        print(helper.export_research_summary())
    elif command == "export":
        helper.save_to_file("research_data.json")
        print("Research data saved to research_data.json")
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
