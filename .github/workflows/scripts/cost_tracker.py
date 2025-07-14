import json
import os
import sys
from typing import Dict, Optional, Tuple


class CostTracker:
    """Track AI usage costs for Claude and OpenAI models."""
    
    # Pricing per 1 million tokens
    PRICING = {
        'claude-sonnet-4-20250514': {
            'input': 3.00,   # $3/MTok
            'output': 15.00  # $15/MTok
        },
        'gpt-4.1-nano-2025-04-14': {
            'input': 0.10,   # $1.10/MTok  
            'output': 0.40   # $4.40/MTok
        }
    }
    
    def __init__(self):
        self.cost_file = '/tmp/ai_costs.json'
        self.costs = self._load_costs()
    
    def _load_costs(self) -> Dict:
        """Load existing cost data or initialize empty structure."""
        if os.path.exists(self.cost_file):
            try:
                with open(self.cost_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load existing costs: {e}", file=sys.stderr)
        
        return {
            'total_cost': 0.0,
            'calls': []
        }
    
    def _save_costs(self):
        """Save cost data to file."""
        try:
            with open(self.cost_file, 'w') as f:
                json.dump(self.costs, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save costs: {e}", file=sys.stderr)
    
    def extract_token_usage(self, response_data: Dict, model: str) -> Tuple[int, int]:
        """Extract input and output tokens from API response."""
        input_tokens = 0
        output_tokens = 0
        
        try:
            if model.startswith('claude'):
                # Claude response format
                usage = response_data.get('usage', {})
                input_tokens = usage.get('input_tokens', 0)
                output_tokens = usage.get('output_tokens', 0)
            else:
                # OpenAI response format
                usage = response_data.get('usage', {})
                input_tokens = usage.get('prompt_tokens', 0)
                output_tokens = usage.get('completion_tokens', 0)
        except Exception as e:
            print(f"Warning: Could not extract token usage: {e}", file=sys.stderr)
        
        return input_tokens, output_tokens
    
    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for given model and token usage."""
        if model not in self.PRICING:
            print(f"Warning: Unknown model {model}, cost calculation may be inaccurate", file=sys.stderr)
            return 0.0
        
        pricing = self.PRICING[model]
        
        # Convert tokens to millions and calculate cost
        input_cost = (input_tokens / 1_000_000) * pricing['input']
        output_cost = (output_tokens / 1_000_000) * pricing['output']
        
        return input_cost + output_cost
    
    def track_api_call(self, model: str, response_data: Dict, call_type: str = "review", 
                      context: Optional[str] = None):
        """Track an API call and calculate its cost."""
        input_tokens, output_tokens = self.extract_token_usage(response_data, model)
        cost = self.calculate_cost(model, input_tokens, output_tokens)
        
        call_data = {
            'model': model,
            'call_type': call_type,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'cost': cost,
            'context': context
        }
        
        self.costs['calls'].append(call_data)
        self.costs['total_cost'] += cost
        
        # Log the cost information
        print(f"AI Cost Tracking - {call_type.upper()}:", file=sys.stderr)
        print(f"  Model: {model}", file=sys.stderr)
        print(f"  Input tokens: {input_tokens:,}", file=sys.stderr)
        print(f"  Output tokens: {output_tokens:,}", file=sys.stderr)
        print(f"  Cost: ${cost:.6f}", file=sys.stderr)
        if context:
            print(f"  Context: {context}", file=sys.stderr)
        
        self._save_costs()
        return cost
    
    def get_summary(self) -> Dict:
        """Get cost summary for display."""
        total_input_tokens = sum(call['input_tokens'] for call in self.costs['calls'])
        total_output_tokens = sum(call['output_tokens'] for call in self.costs['calls'])
        
        # Group by model
        by_model = {}
        for call in self.costs['calls']:
            model = call['model']
            if model not in by_model:
                by_model[model] = {
                    'calls': 0,
                    'input_tokens': 0,
                    'output_tokens': 0,
                    'cost': 0.0
                }
            by_model[model]['calls'] += 1
            by_model[model]['input_tokens'] += call['input_tokens']
            by_model[model]['output_tokens'] += call['output_tokens']
            by_model[model]['cost'] += call['cost']
        
        # Group by call type
        by_type = {}
        for call in self.costs['calls']:
            call_type = call['call_type']
            if call_type not in by_type:
                by_type[call_type] = {
                    'calls': 0,
                    'input_tokens': 0,
                    'output_tokens': 0,
                    'cost': 0.0
                }
            by_type[call_type]['calls'] += 1
            by_type[call_type]['input_tokens'] += call['input_tokens']
            by_type[call_type]['output_tokens'] += call['output_tokens']
            by_type[call_type]['cost'] += call['cost']
        
        return {
            'total_cost': self.costs['total_cost'],
            'total_calls': len(self.costs['calls']),
            'total_input_tokens': total_input_tokens,
            'total_output_tokens': total_output_tokens,
            'by_model': by_model,
            'by_type': by_type,
            'individual_calls': self.costs['calls'],
            'timestamp': self._get_timestamp()
        }
    
    def print_detailed_summary(self):
        """Print a detailed cost summary to stderr."""
        summary = self.get_summary()
        
        # Header with box drawing
        print("\n┌" + "─" * 78 + "┐", file=sys.stderr)
        print("│" + " " * 27 + "AI USAGE COST SUMMARY" + " " * 30 + "│", file=sys.stderr)
        print("└" + "─" * 78 + "┘", file=sys.stderr)
        
        # Overall summary box
        print("\nOVERALL STATISTICS", file=sys.stderr)
        print("┌─────────────────────┬─────────────────────────────────────────────────────┐", file=sys.stderr)
        print(f"│ Total Cost          │ ${summary['total_cost']:>53.6f} │", file=sys.stderr)
        print(f"│ Total API Calls     │ {summary['total_calls']:>53,} │", file=sys.stderr)
        print(f"│ Total Input Tokens  │ {summary['total_input_tokens']:>53,} │", file=sys.stderr)
        print(f"│ Total Output Tokens │ {summary['total_output_tokens']:>53,} │", file=sys.stderr)
        print("└─────────────────────┴─────────────────────────────────────────────────────┘", file=sys.stderr)
        
        # Cost by model table
        if summary['by_model']:
            print("\nCOST BY MODEL", file=sys.stderr)
            print("┌─────────────────────────┬───────┬─────────────┬──────────────┬─────────────┐", file=sys.stderr)
            print("│ Model                   │ Calls │ Input Tokens│ Output Tokens│    Cost ($) │", file=sys.stderr)
            print("├─────────────────────────┼───────┼─────────────┼──────────────┼─────────────┤", file=sys.stderr)
            
            for model, data in summary['by_model'].items():
                model_name = model[:23] if len(model) > 23 else model
                print(f"│ {model_name:<23} │ {data['calls']:>5} │ {data['input_tokens']:>11,} │ {data['output_tokens']:>12,} │ {data['cost']:>11.6f} │", file=sys.stderr)
            
            print("└─────────────────────────┴───────┴─────────────┴──────────────┴─────────────┘", file=sys.stderr)
        
        # Cost by operation table
        if summary['by_type']:
            print("\nCOST BY OPERATION", file=sys.stderr)
            print("┌─────────────────────────┬───────┬─────────────┬──────────────┬─────────────┐", file=sys.stderr)
            print("│ Operation               │ Calls │ Input Tokens│ Output Tokens│    Cost ($) │", file=sys.stderr)
            print("├─────────────────────────┼───────┼─────────────┼──────────────┼─────────────┤", file=sys.stderr)
            
            for op_type, data in summary['by_type'].items():
                op_name = op_type[:23] if len(op_type) > 23 else op_type
                print(f"│ {op_name:<23} │ {data['calls']:>5} │ {data['input_tokens']:>11,} │ {data['output_tokens']:>12,} │ {data['cost']:>11.6f} │", file=sys.stderr)
            
            print("└─────────────────────────┴───────┴─────────────┴──────────────┴─────────────┘", file=sys.stderr)
        
        # Individual calls table
        if summary['individual_calls']:
            print("\nINDIVIDUAL CALLS", file=sys.stderr)
            print("┌────┬──────────────┬─────────────────────────┬─────────────┬──────────────┬─────────────┐", file=sys.stderr)
            print("│ #  │ Operation    │ Model                   │ Input Tokens│ Output Tokens│    Cost ($) │", file=sys.stderr)
            print("├────┼──────────────┼─────────────────────────┼─────────────┼──────────────┼─────────────┤", file=sys.stderr)
            
            for i, call in enumerate(summary['individual_calls'], 1):
                op_name = call['call_type'][:12] if len(call['call_type']) > 12 else call['call_type']
                model_name = call['model'][:23] if len(call['model']) > 23 else call['model']
                print(f"│ {i:>2} │ {op_name:<12} │ {model_name:<23} │ {call['input_tokens']:>11,} │ {call['output_tokens']:>12,} │ {call['cost']:>11.6f} │", file=sys.stderr)
                
                # Add context row if present
                if call.get('context'):
                    context_text = call['context'][:59] + "..." if len(call['context']) > 59 else call['context']
                    print(f"│    │ Context: {context_text:<59} │", file=sys.stderr)
            
            print("└────┴──────────────┴─────────────────────────┴─────────────┴──────────────┴─────────────┘", file=sys.stderr)
        
        print(f"\nReport generated on {summary.get('timestamp', 'unknown time')}", file=sys.stderr)
    
    def _get_timestamp(self):
        """Get current timestamp in a readable format."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    

def initialize_cost_tracking():
    """Initialize cost tracking for the workflow."""
    # Clear any existing cost data for this run
    cost_file = '/tmp/ai_costs.json'
    if os.path.exists(cost_file):
        os.remove(cost_file)
    
    tracker = CostTracker()
    print("AI cost tracking initialized", file=sys.stderr)
    return tracker


def finalize_cost_tracking():
    """Print final cost summary and save to GitHub Actions output."""
    tracker = CostTracker()
    tracker.print_detailed_summary()
    
    summary = tracker.get_summary()
    
    # Save summary to GitHub Actions output if available
    if 'GITHUB_OUTPUT' in os.environ:
        with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
            fh.write(f"total_ai_cost={summary['total_cost']:.6f}\n")
            fh.write(f"total_ai_calls={summary['total_calls']}\n")
            fh.write(f"total_input_tokens={summary['total_input_tokens']}\n")
            fh.write(f"total_output_tokens={summary['total_output_tokens']}\n")
    
    # Also save a human-readable summary to a file for artifacts
    try:
        with open('/tmp/ai_cost_summary.txt', 'w') as f:
            f.write("AI USAGE COST SUMMARY\n")
            f.write("="*60 + "\n\n")
            f.write(f"Total Cost: ${summary['total_cost']:.6f}\n")
            f.write(f"Total API Calls: {summary['total_calls']}\n")
            f.write(f"Total Input Tokens: {summary['total_input_tokens']:,}\n")
            f.write(f"Total Output Tokens: {summary['total_output_tokens']:,}\n\n")
            
            f.write("COST BY MODEL:\n")
            f.write("-" * 40 + "\n")
            for model, data in summary['by_model'].items():
                f.write(f"{model}:\n")
                f.write(f"  Calls: {data['calls']}\n")
                f.write(f"  Input tokens: {data['input_tokens']:,}\n")
                f.write(f"  Output tokens: {data['output_tokens']:,}\n")
                f.write(f"  Cost: ${data['cost']:.6f}\n\n")
            
            f.write("COST BY OPERATION:\n")
            f.write("-" * 40 + "\n")
            for op_type, data in summary['by_type'].items():
                f.write(f"{op_type}:\n")
                f.write(f"  Calls: {data['calls']}\n")
                f.write(f"  Input tokens: {data['input_tokens']:,}\n")
                f.write(f"  Output tokens: {data['output_tokens']:,}\n")
                f.write(f"  Cost: ${data['cost']:.6f}\n\n")
            
            if summary['individual_calls']:
                f.write("INDIVIDUAL CALLS:\n")
                f.write("-" * 40 + "\n")
                for i, call in enumerate(summary['individual_calls'], 1):
                    f.write(f"{i}. {call['call_type']} - {call['model']}\n")
                    f.write(f"   Input: {call['input_tokens']:,} tokens, Output: {call['output_tokens']:,} tokens\n")
                    f.write(f"   Cost: ${call['cost']:.6f}\n")
                    if call.get('context'):
                        f.write(f"   Context: {call['context']}\n")
                    f.write("\n")
    except Exception as e:
        print(f"Warning: Could not save human-readable summary: {e}", file=sys.stderr)
    
    return summary


if __name__ == "__main__":
    # If called directly, print current cost summary
    tracker = CostTracker()
    tracker.print_detailed_summary()
