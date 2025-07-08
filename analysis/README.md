# AAP 2.4 vs 2.5 Memory Usage Comparison Report

## Test Summary
Test completed: 2025-07-07T15:49:31Z

## Key Findings

### Overall System Memory
- AAP 2.4 Average Memory: 1150.5 MB
- AAP 2.5 Average Memory: 1458.2 MB
- Memory Difference: 307.7 MB (26.7%)

### Receptor Memory Analysis
- AAP 2.4 Receptor Average: 33.5 MB
- AAP 2.5 Receptor Average: 24.6 MB
- Receptor Memory Difference: -8.9 MB (-26.5%)

### Top Memory Consuming Processes
**AAP 2.4 Top Processes:**
- /var/lib/awx/venv/awx/bin/u: 127.3 MB avg
- /var/lib/awx/venv/awx/bin/p: 125.6 MB avg
- /usr/libexec/packagekitd: 38.9 MB avg
- /usr/lib/systemd/systemd-ud: 13.6 MB avg
- /usr/lib/systemd/systemd-lo: 13.3 MB avg

**AAP 2.5 Top Processes:**
- /var/lib/awx/venv/awx/bin/u: 164.0 MB avg
- /var/lib/awx/venv/awx/bin/p: 161.4 MB avg
- Analysis results available in /home/msandova/repos/results-aap-memory-test/analysis
- Memory monitoring data collected from all nodes
- Comparison charts generated

## Files Generated
- `memory_comparison_charts.png` - Visual comparison charts
- `memory_analysis_summary.json` - Detailed numerical analysis
- `memory_comparison_report.html` - Interactive HTML report with side-by-side comparisons
- `memory_usage_data.csv` - Raw data for further analysis
- Individual node logs in respective subdirectories

## Next Steps
1. Open memory_comparison_report.html in a web browser for detailed analysis
2. Review the generated charts and summary
3. Analyze peak memory usage differences
4. Check for memory leaks or unusual patterns
5. Document findings for capacity planning

## Grafana Dashboard
Real-time monitoring available at: http://192.168.1.207:3000

## Raw Data Location
All raw monitoring data: /home/msandova/repos/results-aap-memory-test
