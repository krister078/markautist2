#!/usr/bin/env python3
"""
Simple script to display current AI cost tracking information.
This can be called at any point in the workflow to show costs so far.
"""

import sys
import os

# Add the scripts directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cost_tracker import CostTracker

def main():
    """Display current cost information."""
    try:
        tracker = CostTracker()
        summary = tracker.get_summary()
        
        if summary['total_calls'] == 0:
            print("No AI calls tracked yet", file=sys.stderr)
            return
        
        tracker.print_detailed_summary()
        
    except Exception as e:
        print(f"Error displaying costs: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
