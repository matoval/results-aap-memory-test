#!/usr/bin/env python3
"""
AAP Memory Usage HTML Report Generator

This script generates an HTML report comparing AAP 2.4 and 2.5 memory usage.
"""

import os
import json
import argparse
from datetime import datetime
import base64
import sys
import glob

def load_analysis_data(analysis_dir):
    """Load analysis data from JSON file"""
    summary_file = os.path.join(analysis_dir, 'memory_analysis_summary.json')
    if not os.path.exists(summary_file):
        print(f"Warning: Analysis summary file not found at {summary_file}")
        return None
    
    try:
        with open(summary_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading analysis data: {e}")
        return None

def encode_image_to_base64(image_path):
    """Encode image to base64 for embedding in HTML"""
    if not os.path.exists(image_path):
        return None
    
    try:
        with open(image_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    except Exception as e:
        print(f"Error encoding image {image_path}: {e}")
        return None

def generate_html_report(analysis_data, analysis_dir):
    """Generate HTML report"""
    
    # Get chart image
    chart_path = os.path.join(analysis_dir, 'memory_comparison_charts.png')
    chart_base64 = encode_image_to_base64(chart_path)
    
    # Generate timestamp
    report_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AAP Memory Usage Comparison Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #ee0000;
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 3px solid #ee0000;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #333;
            border-left: 4px solid #ee0000;
            padding-left: 15px;
            margin-top: 30px;
        }}
        .alert {{
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
        }}
        .alert-info {{
            background-color: #d1ecf1;
            border: 1px solid #b7d4ea;
            color: #0c5460;
        }}
        .alert-warning {{
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #ee0000;
            text-align: center;
            color: #6c757d;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Red Hat Ansible Automation Platform<br>Memory Usage Comparison Report</h1>
        
        <div class="alert alert-info">
            <strong>Report Generated:</strong> {report_time}<br>
            <strong>Analysis Directory:</strong> {analysis_dir}
        </div>
"""

    if analysis_data:
        html_content += """
        <h2>Memory Usage Analysis Results</h2>
        <p>Memory analysis data was found and processed successfully.</p>
        
        <h3>Overall System Memory Comparison</h3>
        <div style="display: flex; gap: 20px; margin: 20px 0;">
            <div style="flex: 1; background: #e3f2fd; padding: 15px; border-radius: 8px;">
                <h4 style="margin-top: 0; color: #1976d2;">AAP 2.4</h4>
        """
        
        aap24 = analysis_data.get('aap24', {})
        aap25 = analysis_data.get('aap25', {})
        comparison = analysis_data.get('comparison', {})
        
        if aap24:
            html_content += f"""
                <ul style="list-style: none; padding: 0;">
                    <li><strong>Average Memory:</strong> {aap24.get('avg_memory_mb', 0):.1f} MB</li>
                    <li><strong>Peak Memory:</strong> {aap24.get('peak_memory_mb', 0):.1f} MB</li>
                    <li><strong>Min Memory:</strong> {aap24.get('min_memory_mb', 0):.1f} MB</li>
                    <li><strong>Samples:</strong> {aap24.get('samples', 0)}</li>
                </ul>
            """
        
        html_content += """
            </div>
            <div style="flex: 1; background: #ffebee; padding: 15px; border-radius: 8px;">
                <h4 style="margin-top: 0; color: #d32f2f;">AAP 2.5</h4>
        """
        
        if aap25:
            html_content += f"""
                <ul style="list-style: none; padding: 0;">
                    <li><strong>Average Memory:</strong> {aap25.get('avg_memory_mb', 0):.1f} MB</li>
                    <li><strong>Peak Memory:</strong> {aap25.get('peak_memory_mb', 0):.1f} MB</li>
                    <li><strong>Min Memory:</strong> {aap25.get('min_memory_mb', 0):.1f} MB</li>
                    <li><strong>Samples:</strong> {aap25.get('samples', 0)}</li>
                </ul>
            """
        
        html_content += """
            </div>
        </div>
        """
        
        # Add comparison summary
        if comparison:
            diff_mb = comparison.get('avg_memory_diff_mb', 0)
            diff_percent = comparison.get('avg_memory_diff_percent', 0)
            uses_more = comparison.get('aap25_uses_more', False)
            
            color = '#d32f2f' if uses_more else '#4caf50'
            symbol = '' if uses_more else ''
            direction = 'more' if uses_more else 'less'
            
            html_content += f"""
            <div class="alert alert-info">
                <h4 style="margin-top: 0;">{symbol} Memory Difference Analysis</h4>
                <p><strong>AAP 2.5 uses {abs(diff_mb):.1f} MB {direction} memory than AAP 2.4</strong></p>
                <p style="color: {color}; font-size: 1.2em; font-weight: bold;">
                    Difference: {diff_percent:+.1f}%
                </p>
            </div>
            """
        
        # Add top processes comparison
        html_content += """
        <h3>Top Memory Consuming Processes</h3>
        <div style="display: flex; gap: 20px; margin: 20px 0;">
            <div style="flex: 1;">
                <h4>AAP 2.4 Top Processes</h4>
                <table style="width: 100%; border-collapse: collapse; border: 1px solid #ddd;">
                    <thead>
                        <tr style="background-color: #f5f5f5;">
                            <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Process</th>
                            <th style="border: 1px solid #ddd; padding: 8px; text-align: right;">Avg Memory (MB)</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        if aap24.get('top_processes'):
            for i, (process, data) in enumerate(aap24['top_processes'][:5]):
                avg_mb = data.get('avg_rss', 0) / 1024
                process_short = process[:40] + '...' if len(process) > 40 else process
                html_content += f"""
                        <tr>
                            <td style="border: 1px solid #ddd; padding: 8px; font-family: monospace; font-size: 0.9em;">{process_short}</td>
                            <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{avg_mb:.1f}</td>
                        </tr>
                """
        
        html_content += """
                    </tbody>
                </table>
            </div>
            <div style="flex: 1;">
                <h4>AAP 2.5 Top Processes</h4>
                <table style="width: 100%; border-collapse: collapse; border: 1px solid #ddd;">
                    <thead>
                        <tr style="background-color: #f5f5f5;">
                            <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Process</th>
                            <th style="border: 1px solid #ddd; padding: 8px; text-align: right;">Avg Memory (MB)</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        if aap25.get('top_processes'):
            for i, (process, data) in enumerate(aap25['top_processes'][:5]):
                avg_mb = data.get('avg_rss', 0) / 1024
                process_short = process[:40] + '...' if len(process) > 40 else process
                html_content += f"""
                        <tr>
                            <td style="border: 1px solid #ddd; padding: 8px; font-family: monospace; font-size: 0.9em;">{process_short}</td>
                            <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{avg_mb:.1f}</td>
                        </tr>
                """
        
        html_content += """
                    </tbody>
                </table>
            </div>
        </div>
        """
        
        # Add receptor memory comparison if available
        if aap24.get('receptor_memory') and aap25.get('receptor_memory'):
            html_content += """
            <h3>Receptor Memory Analysis</h3>
            <div style="display: flex; gap: 20px; margin: 20px 0;">
                <div style="flex: 1; background: #e8f5e8; padding: 15px; border-radius: 8px;">
                    <h4 style="margin-top: 0;">AAP 2.4 Receptor</h4>
            """
            
            receptor24 = aap24['receptor_memory']
            html_content += f"""
                    <ul style="list-style: none; padding: 0;">
                        <li><strong>Average:</strong> {receptor24.get('avg_memory_mb', 0):.1f} MB</li>
                        <li><strong>Peak:</strong> {receptor24.get('peak_memory_mb', 0):.1f} MB</li>
                        <li><strong>Samples:</strong> {receptor24.get('samples', 0)}</li>
                    </ul>
                </div>
                <div style="flex: 1; background: #ffe8e8; padding: 15px; border-radius: 8px;">
                    <h4 style="margin-top: 0;">AAP 2.5 Receptor</h4>
            """
            
            receptor25 = aap25['receptor_memory']
            html_content += f"""
                    <ul style="list-style: none; padding: 0;">
                        <li><strong>Average:</strong> {receptor25.get('avg_memory_mb', 0):.1f} MB</li>
                        <li><strong>Peak:</strong> {receptor25.get('peak_memory_mb', 0):.1f} MB</li>
                        <li><strong>Samples:</strong> {receptor25.get('samples', 0)}</li>
                    </ul>
                </div>
            </div>
            """
            
            # Add receptor comparison if available
            if comparison.get('receptor'):
                receptor_comparison = comparison['receptor']
                receptor_diff = receptor_comparison.get('avg_memory_diff_mb', 0)
                receptor_percent = receptor_comparison.get('avg_memory_diff_percent', 0)
                
                html_content += f"""
                <div class="alert alert-info">
                    <strong>Receptor Memory Difference:</strong> {receptor_diff:+.1f} MB ({receptor_percent:+.1f}%)
                </div>
                """
        
        # Add charts if available
        if chart_base64:
            html_content += f"""
            <h3>Memory Usage Charts</h3>
            <div style="text-align: center; margin: 20px 0;">
                <img src="data:image/png;base64,{chart_base64}" 
                     alt="Memory Comparison Charts" 
                     style="max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 8px;">
            </div>
            """
        
        html_content += """
        <h3>Generated Files</h3>
        <ul>
            <li><strong>memory_comparison_charts.png</strong> - Visual comparison charts</li>
            <li><strong>memory_analysis_summary.json</strong> - Detailed numerical analysis</li>
            <li><strong>README.md</strong> - Markdown summary report</li>
        </ul>
        """
    else:
        html_content += """
        <div class="alert alert-warning">
            <strong>Warning:</strong> No memory analysis data available. This may be due to:
            <ul>
                <li>Memory monitoring logs are empty or contain only startup messages</li>
                <li>Memory monitoring service may not be collecting data properly</li>
                <li>Tests may not have run long enough to generate substantial data</li>
            </ul>
            <p><strong>Recommendation:</strong> Check the memory monitoring service configuration and ensure tests run for sufficient duration.</p>
        </div>
        
        <h2>Available Log Files</h2>
        <p>The following log files were found but contain no memory data:</p>
        <ul>
        """
        
        # List available log files
        log_files = glob.glob(os.path.join(os.path.dirname(analysis_dir), "memory_monitor_*.log"))
        for log_file in sorted(log_files):
            filename = os.path.basename(log_file)
            html_content += f"            <li>{filename}</li>\n"
        
        html_content += """
        </ul>
        """
    
    html_content += f"""
        <div class="footer">
            <p>Generated by AAP Memory Testing Automation Framework</p>
            <p>Report Path: {os.path.join(analysis_dir, 'comparison_report.html')}</p>
        </div>
    </div>
</body>
</html>
    """
    
    return html_content

def main():
    parser = argparse.ArgumentParser(description='Generate HTML report for AAP memory analysis')
    parser.add_argument('--analysis-dir', 
                        default=os.getcwd(),
                        help='Analysis directory containing results')
    args = parser.parse_args()
    
    analysis_dir = os.path.abspath(args.analysis_dir)
    
    print(f"Generating HTML report from: {analysis_dir}")
    
    # Load analysis data
    analysis_data = load_analysis_data(analysis_dir)
    
    # Generate HTML report
    html_content = generate_html_report(analysis_data, analysis_dir)
    
    # Save report
    report_path = os.path.join(analysis_dir, 'comparison_report.html')
    try:
        with open(report_path, 'w') as f:
            f.write(html_content)
        
        print(f"HTML report generated successfully: {report_path}")
        return 0
        
    except Exception as e:
        print(f"Error writing HTML report: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())