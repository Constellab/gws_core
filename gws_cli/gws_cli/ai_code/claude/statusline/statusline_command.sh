#!/bin/bash
# Claude Code status line - shows token usage and context window
python3 -c "
import sys, json
data = json.load(sys.stdin)
cw = data.get('context_window', {})
total_in = cw.get('total_input_tokens', 0) or 0
total_out = cw.get('total_output_tokens', 0) or 0
total = total_in + total_out
used_pct = cw.get('used_percentage', 0) or 0
window_size = cw.get('context_window_size', 200000) or 200000
cost = (data.get('cost') or {}).get('total_cost_usd', 0) or 0

total_fmt = f'{total/1000:.1f}k' if total >= 1000 else str(total)
window_fmt = f'{window_size//1000}k'

print(f'Tokens: {total_fmt} (in:{total_in} out:{total_out}) | Context: {used_pct}% of {window_fmt} | Cost: \${cost:.4f}', end='')
"
