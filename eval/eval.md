# Neo4j Agent Evaluation Guide

Quick guide for evaluating and comparing Neo4j agent performance across different models.

## Quick Start

```bash
# 1. Setup environment
./install.sh
source .venv/bin/activate

# 2. Generate baseline for current model
cd eval
python generate_baseline.py

# 3. Compare different models
export MODEL_NAME=gemini-2.5-pro
python generate_baseline.py --output gemini_pro_baseline.json
```

## Evaluation Tools

### 1. Generate Baseline
Creates performance baseline for the current model:

```bash
python generate_baseline.py
```

Output files:
- `baseline_results.json` - Complete test results
- `baseline_results.summary.md` - Human-readable summary

### 2. Compare Models

Test different Gemini models:
```bash
# Gemini Flash (default)
export MODEL_NAME=gemini-2.5-flash
python generate_baseline.py --output flash_baseline.json

# Gemini Pro
export MODEL_NAME=gemini-2.5-pro
python generate_baseline.py --output pro_baseline.json

# Gemini 1.5 Pro
export MODEL_NAME=gemini-1.5-pro
python generate_baseline.py --output 1.5pro_baseline.json
```

### 3. Run ADK Evaluation

For detailed evaluation with Google ADK:
```bash
adk eval neo4j_database_agent data/baseline_queries.test.json --config_file_path data/test_config.json
```

## Test Coverage

20 comprehensive test cases covering:
- Basic queries (customer counts, subscriptions)
- Data filtering (active records, date ranges)
- Aggregations (MRR, revenue trends)
- Visualizations (charts and graphs)
- Graph analysis (paths, centrality)
- Complex queries (multi-condition filters)

## Key Metrics

Compare models on:
- **Success Rate**: % of queries completed successfully
- **Speed**: Average query execution time
- **Tool Usage**: Efficiency of tool calls
- **Accuracy**: Quality of generated Cypher queries

## Example Results

```
=== MODEL COMPARISON ===
Flash avg time: 45019.86ms
Pro avg time: 25110.13ms
Performance improvement: 44.2%

Flash success rate: 20/20 (100%)
Pro success rate: 20/20 (100%)
```

## Files

- `data/baseline_queries.test.json` - Test queries
- `data/test_config.json` - Evaluation criteria  
- `generate_baseline.py` - Baseline generator
- `test_eval.py` - Pytest runner

## Tips

1. Always test with the same Neo4j data for consistent comparisons
2. Run multiple times to account for variance
3. Check both speed and accuracy - faster isn't always better
4. Review actual vs expected Cypher queries for optimization opportunities