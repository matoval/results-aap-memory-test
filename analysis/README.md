# AAP 2.4 vs 2.5 Memory Usage Comparison Report

## Test Summary
Test completed: 2025-06-30T17:32:33Z

## Key Findings

### Overall System Memory
- AAP 2.4 Average Memory: 1929.2 MB
- AAP 2.5 Average Memory: 866.6 MB
- Memory Difference: -1062.6 MB (-55.1%)

### Receptor Memory Analysis
- AAP 2.4 Receptor Average: 33.3 MB
- AAP 2.5 Receptor Average: 3.0 MB
- Receptor Memory Difference: -30.3 MB (-91.0%)

### Top Memory Consuming Processes
**AAP 2.4 Top Processes:**
- /var/lib/awx/venv/awx/bin/p: 127.2 MB avg
- /usr/local/bin/node_exporte: 25.8 MB avg
- /usr/lib/systemd/systemd-jo: 16.7 MB avg

**AAP 2.5 Top Processes:**
- /usr/local/bin/node_exporte: 27.3 MB avg
- /usr/bin/python3.11: 24.0 MB avg
- /usr/lib/systemd/systemd-jo: 16.0 MB avg
- /usr/lib/systemd/systemd-ud: 12.1 MB avg
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
