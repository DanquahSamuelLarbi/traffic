# SmartLight MVP Benchmark Report

This report benchmarks the performance of the **SmartLight Adaptive Traffic Light Optimization System** against a standard **Static Fixed-Time** controller configuration.

## Key Performance Indicators (KPIs)

| Metric | Static Fixed-Time | SmartLight Adaptive | Performance Change |
| :--- | :---: | :---: | :---: |
| **Completed Vehicles** | 402 | 463 | +15.2% |
| **Avg Travel Time** | 87.45s | 56.73s | -35.1% (Speedup) |
| **Avg Waiting Time (Delay)** | 42.56s | 12.32s | -71.1% (Delay Reduction) |
| **Total Waiting Time** | 17109.00s | 5703.00s | -66.7% |

## Performance Analysis

* **Average Waiting Time Reduction:** The SmartLight system achieved a **71.1% reduction** in average vehicle waiting time. This exceeds the project's target threshold of $\ge 20\%$.
* **Travel Efficiency:** Average transit duration was shortened by **35.1%**, enabling vehicles to clear the intersection significantly faster.
* **Throughput Increase:** Because the green phases dynamically adapt to actual vehicle density (particularly during the highly unbalanced peak traffic flow from 300s to 700s), the junction was able to process **+15.2% more vehicles** within the 1000-second testing window.

---
*Report generated automatically on completion of the SmartLight simulation benchmark suite.*
