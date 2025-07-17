# Baseline Results Summary

**Generated:** 2025-07-17T13:09:31.166230
**Model:** gemini-2.5-flash
**Total Queries:** 20
**Successful:** 20
**Failed:** 0
**Success Rate:** 100.0%

## Performance Metrics

- **Total Execution Time:** 900397.12ms
- **Average Query Time:** 45019.86ms
- **Queries Under 1s:** 0/20
- **Queries Under 5s:** 3/20

## Slowest Queries

- Show me subscription changes in the last 3 months (365836.78ms)
- Show me subscription items with their products (312023.70ms)
- Show me credit notes issued this year (41192.79ms)
- What's the average resolution time for support tickets? (24376.80ms)
- Create a pie chart of customers by segment (20137.88ms)

## Usage

Use this baseline for future comparisons:

```bash
# Compare against this baseline
python generate_baseline.py --baseline baseline_results.summary.json

# Run evaluation
pytest eval/test_eval.py
```
