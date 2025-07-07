#!/usr/bin/env python3
"""
AAP Memory Usage Analysis Script

This script analyzes memory monitoring logs and generates
comparison reports between AAP 2.4 and 2.5.
"""

import os
import re
import json
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import argparse

def parse_receptor_version_logs(results_dir):
    """Parse receptor version information from log files"""
    version_info = {'aap24': {}, 'aap25': {}}
    
    for aap_version in ['aap24', 'aap25']:
        version_files = [f for f in os.listdir(results_dir) if f.startswith(f'receptor_version_{aap_version}_')]
        
        for version_file in version_files:
            hostname = version_file.replace(f'receptor_version_{aap_version}_', '').replace('.log', '')
            
            try:
                with open(os.path.join(results_dir, version_file), 'r') as f:
                    content = f.read()
                
                # Extract version information
                version_data = {
                    'version': 'Unknown',
                    'package': 'Unknown',
                    'service_status': 'Unknown',
                    'processes_found': False
                }
                
                # Parse version
                for line in content.split('\n'):
                    if 'receptor --version' in line or 'receptor version' in line:
                        next_line_idx = content.split('\n').index(line) + 1
                        if next_line_idx < len(content.split('\n')):
                            potential_version = content.split('\n')[next_line_idx].strip()
                            if potential_version and not potential_version.startswith('---'):
                                version_data['version'] = potential_version
                    elif 'receptor-' in line and '.rpm' not in line:
                        # Look for package info
                        version_data['package'] = line.strip()
                    elif 'Active:' in line:
                        if 'active (running)' in line:
                            version_data['service_status'] = 'Running'
                        elif 'inactive' in line:
                            version_data['service_status'] = 'Stopped'
                    elif 'receptor' in line and '/usr' in line:
                        version_data['processes_found'] = True
                
                version_info[aap_version][hostname] = version_data
                
            except Exception as e:
                print(f"Error parsing {version_file}: {e}")
                version_info[aap_version][hostname] = {
                    'version': 'Parse Error',
                    'package': 'Parse Error',
                    'service_status': 'Parse Error',
                    'processes_found': False
                }
    
    return version_info

def parse_memory_logs(log_file):
    """Parse memory monitoring log files with receptor support"""
    memory_data = []
    
    with open(log_file, 'r') as f:
        content = f.read()
    
    # Parse receptor memory summary from entire file first
    global_receptor_memory = None
    all_lines = content.split('\n')
    for i, line in enumerate(all_lines):
        if 'RECEPTOR MEMORY SUMMARY' in line:
            # Look for receptor memory information in next few lines
            for j in range(i+1, min(i+10, len(all_lines))):
                if 'Total Receptor RSS Memory:' in all_lines[j]:
                    # Extract KB and MB values
                    match = re.search(r'(\d+) KB \((\d+) MB\)', all_lines[j])
                    if match:
                        global_receptor_memory = {
                            'rss_kb': int(match.group(1)),
                            'rss_mb': int(match.group(2))
                        }
                elif 'Number of Receptor Processes:' in all_lines[j]:
                    if global_receptor_memory:
                        match = re.search(r'(\d+)', all_lines[j])
                        if match:
                            global_receptor_memory['process_count'] = int(match.group(1))
            break
        
    # Extract timestamp and memory info patterns
    entries = re.split(r'=+', content)
    
    for entry in entries:
        lines = entry.strip().split('\n')
        
        timestamp_line = None
        memory_line = None
        top_processes = []
        aap_processes = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            if re.match(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', line):
                timestamp_line = line
            elif line.strip().startswith('Mem:'):
                memory_line = line
            elif 'Top 10 Processes by RSS Memory:' in line:
                # Parse top processes section
                i += 1
                if i < len(lines) and 'PID' in lines[i]:  # Skip header
                    i += 1
                while i < len(lines) and lines[i].strip() and not lines[i].startswith('AAP-related'):
                    process_line = lines[i].strip()
                    if process_line:
                        parts = process_line.split(None, 3)
                        if len(parts) >= 4:
                            try:
                                pid = int(parts[0])
                                ppid = int(parts[1])
                                rss = int(parts[3])
                                cmd = parts[2] if len(parts) > 2 else 'unknown'
                                top_processes.append({
                                    'pid': pid,
                                    'ppid': ppid,
                                    'cmd': cmd,
                                    'rss_kb': rss
                                })
                            except ValueError:
                                pass
                    i += 1
                continue
            elif 'AAP-related Processes and Children:' in line:
                # Parse AAP processes section
                i += 1
                while i < len(lines) and not lines[i].startswith('Process Tree'):
                    aap_line = lines[i].strip()
                    if 'Process:' in aap_line:
                        # Extract process info from "Process: name (PID: pid)"
                        match = re.search(r'Process: (.+) \(PID: (\d+)\)', aap_line)
                        if match:
                            process_name = match.group(1)
                            pid = int(match.group(2))
                            aap_processes.append({
                                'name': process_name,
                                'pid': pid,
                                'children': []
                            })
                    elif aap_line and 'Children of PID' in aap_line:
                        # Parse children in next lines until empty line
                        i += 1
                        while i < len(lines) and lines[i].strip():
                            child_line = lines[i].strip()
                            parts = child_line.split(None, 3)
                            if len(parts) >= 4:
                                try:
                                    child_pid = int(parts[0])
                                    child_ppid = int(parts[1])
                                    child_rss = int(parts[3])
                                    child_cmd = parts[2]
                                    if aap_processes:
                                        aap_processes[-1]['children'].append({
                                            'pid': child_pid,
                                            'ppid': child_ppid,
                                            'cmd': child_cmd,
                                            'rss_kb': child_rss
                                        })
                                except ValueError:
                                    pass
                            i += 1
                        continue
                    i += 1
                continue
            i += 1
        
        if timestamp_line and memory_line:
            # Parse memory info (free -m output)
            mem_parts = memory_line.split()
            if len(mem_parts) >= 4:
                total_mem = int(mem_parts[1])
                used_mem = int(mem_parts[2])
                
                memory_entry = {
                    'timestamp': datetime.strptime(timestamp_line, '%Y-%m-%d %H:%M:%S'),
                    'total_mb': total_mem,
                    'used_mb': used_mem,
                    'percent': (used_mem / total_mem) * 100,
                    'top_processes': top_processes,
                    'aap_processes': aap_processes
                }
                if global_receptor_memory:
                    memory_entry['receptor'] = global_receptor_memory
                memory_data.append(memory_entry)
    
    return memory_data

def analyze_process_data(data):
    """Analyze process data from memory logs"""
    process_analysis = {
        'top_memory_consumers': {},
        'aap_service_memory': {},
        'process_growth_trends': []
    }
    
    # Aggregate top processes across all timestamps
    all_processes = {}
    for entry in data:
        for proc in entry.get('top_processes', []):
            cmd = proc['cmd'][:50]  # Truncate command for readability
            if cmd not in all_processes:
                all_processes[cmd] = {'total_rss': 0, 'count': 0, 'avg_rss': 0}
            all_processes[cmd]['total_rss'] += proc['rss_kb']
            all_processes[cmd]['count'] += 1
    
    # Calculate averages and sort
    for cmd, stats in all_processes.items():
        stats['avg_rss'] = stats['total_rss'] / stats['count']
    
    process_analysis['top_memory_consumers'] = dict(
        sorted(all_processes.items(), key=lambda x: x[1]['avg_rss'], reverse=True)[:10]
    )
    
    # Analyze AAP service memory usage
    aap_services = {}
    for entry in data:
        for proc in entry.get('aap_processes', []):
            service_name = proc['name']
            if service_name not in aap_services:
                aap_services[service_name] = {'memory_samples': [], 'child_count': 0}
            
            # Calculate total memory for this service (parent + children)
            total_memory = 0
            child_count = len(proc.get('children', []))
            for child in proc.get('children', []):
                total_memory += child['rss_kb']
            
            aap_services[service_name]['memory_samples'].append(total_memory)
            aap_services[service_name]['child_count'] = max(
                aap_services[service_name]['child_count'], child_count
            )
    
    # Calculate statistics for AAP services
    for service, data in aap_services.items():
        if data['memory_samples']:
            data['avg_memory_kb'] = sum(data['memory_samples']) / len(data['memory_samples'])
            data['peak_memory_kb'] = max(data['memory_samples'])
            data['min_memory_kb'] = min(data['memory_samples'])
    
    process_analysis['aap_service_memory'] = aap_services
    
    return process_analysis

def generate_comparison_charts(aap24_data, aap25_data, output_dir):
    """Generate comparison charts"""
    
    # Create larger figure for more charts
    plt.figure(figsize=(20, 15))
    
    # Plot AAP 2.4 data
    if aap24_data:
        timestamps_24 = [d['timestamp'] for d in aap24_data]
        memory_24 = [d['used_mb'] for d in aap24_data]
        plt.subplot(3, 3, 1)
        plt.plot(timestamps_24, memory_24, label='AAP 2.4', color='blue')
        plt.title('AAP 2.4 Memory Usage Over Time')
        plt.xlabel('Time')
        plt.ylabel('Memory (MB)')
        plt.xticks(rotation=45)
        plt.grid(True)
    
    # Plot AAP 2.5 data
    if aap25_data:
        timestamps_25 = [d['timestamp'] for d in aap25_data]
        memory_25 = [d['used_mb'] for d in aap25_data]
        plt.subplot(3, 3, 2)
        plt.plot(timestamps_25, memory_25, label='AAP 2.5', color='red')
        plt.title('AAP 2.5 Memory Usage Over Time')
        plt.xlabel('Time')
        plt.ylabel('Memory (MB)')
        plt.xticks(rotation=45)
        plt.grid(True)
    
    # Comparison bar chart
    if aap24_data and aap25_data:
        avg_24 = sum(d['used_mb'] for d in aap24_data) / len(aap24_data)
        avg_25 = sum(d['used_mb'] for d in aap25_data) / len(aap25_data)
        max_24 = max(d['used_mb'] for d in aap24_data)
        max_25 = max(d['used_mb'] for d in aap25_data)
        
        plt.subplot(3, 3, 3)
        categories = ['Average Memory', 'Peak Memory']
        aap24_values = [avg_24, max_24]
        aap25_values = [avg_25, max_25]
        
        x = range(len(categories))
        width = 0.35
        
        plt.bar([i - width/2 for i in x], aap24_values, width, label='AAP 2.4', color='blue')
        plt.bar([i + width/2 for i in x], aap25_values, width, label='AAP 2.5', color='red')
        
        plt.xlabel('Metric')
        plt.ylabel('Memory (MB)')
        plt.title('AAP Memory Usage Comparison')
        plt.xticks(x, categories)
        plt.legend()
        plt.grid(True)
    
    # Process analysis charts
    if aap24_data:
        proc_analysis_24 = analyze_process_data(aap24_data)
        
        # Top processes chart for AAP 2.4
        plt.subplot(3, 3, 4)
        top_procs = list(proc_analysis_24['top_memory_consumers'].items())[:10]
        if top_procs:
            processes = [proc_name[:20] + '...' if len(proc_name) > 20 else proc_name for proc_name, _ in top_procs]
            memory_values = [data['avg_rss'] / 1024 for _, data in top_procs]  # Convert to MB
            
            plt.barh(processes, memory_values, color='lightblue')
            plt.title('AAP 2.4 Top Memory Processes')
            plt.xlabel('Average Memory (MB)')
            plt.grid(True)
    
    if aap25_data:
        proc_analysis_25 = analyze_process_data(aap25_data)
        
        # Top processes chart for AAP 2.5
        plt.subplot(3, 3, 5)
        top_procs = list(proc_analysis_25['top_memory_consumers'].items())[:10]
        if top_procs:
            processes = [proc_name[:20] + '...' if len(proc_name) > 20 else proc_name for proc_name, _ in top_procs]
            memory_values = [data['avg_rss'] / 1024 for _, data in top_procs]  # Convert to MB
            
            plt.barh(processes, memory_values, color='lightcoral')
            plt.title('AAP 2.5 Top Memory Processes')
            plt.xlabel('Average Memory (MB)')
            plt.grid(True)
    
    # AAP Service Memory Comparison
    if aap24_data and aap25_data:
        proc_analysis_24 = analyze_process_data(aap24_data)
        proc_analysis_25 = analyze_process_data(aap25_data)
        
        plt.subplot(3, 3, 6)
        services_24 = proc_analysis_24['aap_service_memory']
        services_25 = proc_analysis_25['aap_service_memory']
        
        # Get common services
        common_services = set(services_24.keys()) & set(services_25.keys())
        if common_services:
            service_names = list(common_services)[:5]  # Top 5 services
            aap24_mem = [services_24[s]['avg_memory_kb'] / 1024 for s in service_names]
            aap25_mem = [services_25[s]['avg_memory_kb'] / 1024 for s in service_names]
            
            x = range(len(service_names))
            width = 0.35
            
            plt.bar([i - width/2 for i in x], aap24_mem, width, label='AAP 2.4', color='blue')
            plt.bar([i + width/2 for i in x], aap25_mem, width, label='AAP 2.5', color='red')
            
            plt.xlabel('AAP Services')
            plt.ylabel('Average Memory (MB)')
            plt.title('AAP Service Memory Comparison')
            plt.xticks(x, [s[:10] + '...' if len(s) > 10 else s for s in service_names], rotation=45)
            plt.legend()
            plt.grid(True)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'memory_comparison_charts.png'), dpi=300, bbox_inches='tight')
    plt.close()

def main():
    parser = argparse.ArgumentParser(description='Analyze AAP memory usage')
    parser.add_argument('--analysis-dir', default='/tmp/aap-memory-test-results/analysis', 
                        help='Analysis output directory')
    args = parser.parse_args()
    
    analysis_dir = args.analysis_dir
    logs_dir = os.path.join(analysis_dir, 'logs')
    
    # Parse receptor version information
    print("Parsing receptor version information...")
    version_info = parse_receptor_version_logs(analysis_dir)
    
    # Find log files in logs directory and main analysis directory
    aap24_logs = []
    aap25_logs = []
    
    # Check both logs subdirectory, main analysis directory, and parent directory
    search_dirs = [logs_dir, analysis_dir, os.path.dirname(analysis_dir)]
    
    for search_dir in search_dirs:
        if os.path.exists(search_dir):
            for root, dirs, files in os.walk(search_dir):
                for file in files:
                    if 'memory_monitor' in file and file.endswith('.log'):
                        file_path = os.path.join(root, file)
                        if 'aap24' in file:
                            aap24_logs.append(file_path)
                        elif 'aap25' in file:
                            aap25_logs.append(file_path)
    
    # Parse data
    aap24_data = []
    aap25_data = []
    
    for log_file in aap24_logs:
        try:
            data = parse_memory_logs(log_file)
            aap24_data.extend(data)
        except Exception as e:
            print(f"Error parsing {log_file}: {e}")
    
    for log_file in aap25_logs:
        try:
            data = parse_memory_logs(log_file)
            aap25_data.extend(data)
        except Exception as e:
            print(f"Error parsing {log_file}: {e}")
    
    # Generate reports
    if aap24_data or aap25_data:
        generate_comparison_charts(aap24_data, aap25_data, analysis_dir)
        
        # Generate process analysis
        aap24_process_analysis = analyze_process_data(aap24_data) if aap24_data else {}
        aap25_process_analysis = analyze_process_data(aap25_data) if aap25_data else {}
        
        # Generate receptor memory analysis
        def analyze_receptor_data(data):
            receptor_entries = [d for d in data if 'receptor' in d and d['receptor']]
            if not receptor_entries:
                return None
            
            return {
                'samples': len(receptor_entries),
                'avg_memory_mb': sum(d['receptor']['rss_mb'] for d in receptor_entries) / len(receptor_entries),
                'peak_memory_mb': max(d['receptor']['rss_mb'] for d in receptor_entries),
                'min_memory_mb': min(d['receptor']['rss_mb'] for d in receptor_entries)
            }
        
        aap24_receptor_analysis = analyze_receptor_data(aap24_data) if aap24_data else None
        aap25_receptor_analysis = analyze_receptor_data(aap25_data) if aap25_data else None
        
        # Generate summary report
        summary = {
            'aap24': {
                'samples': len(aap24_data),
                'avg_memory_mb': sum(d['used_mb'] for d in aap24_data) / len(aap24_data) if aap24_data else 0,
                'peak_memory_mb': max(d['used_mb'] for d in aap24_data) if aap24_data else 0,
                'min_memory_mb': min(d['used_mb'] for d in aap24_data) if aap24_data else 0,
                'process_analysis': aap24_process_analysis,
                'receptor_memory': aap24_receptor_analysis
            },
            'aap25': {
                'samples': len(aap25_data),
                'avg_memory_mb': sum(d['used_mb'] for d in aap25_data) / len(aap25_data) if aap25_data else 0,
                'peak_memory_mb': max(d['used_mb'] for d in aap25_data) if aap25_data else 0,
                'min_memory_mb': min(d['used_mb'] for d in aap25_data) if aap25_data else 0,
                'process_analysis': aap25_process_analysis,
                'receptor_memory': aap25_receptor_analysis
            },
            'versions': version_info
        }
        
        # Calculate differences
        if aap24_data and aap25_data:
            avg_diff = summary['aap25']['avg_memory_mb'] - summary['aap24']['avg_memory_mb']
            peak_diff = summary['aap25']['peak_memory_mb'] - summary['aap24']['peak_memory_mb']
            avg_diff_percent = (avg_diff / summary['aap24']['avg_memory_mb']) * 100
            
            summary['comparison'] = {
                'avg_memory_diff_mb': avg_diff,
                'peak_memory_diff_mb': peak_diff,
                'avg_memory_diff_percent': avg_diff_percent,
                'aap25_uses_more': avg_diff > 0
            }
            
            # Add receptor memory comparison
            if aap24_receptor_analysis and aap25_receptor_analysis:
                receptor_avg_diff = aap25_receptor_analysis['avg_memory_mb'] - aap24_receptor_analysis['avg_memory_mb']
                receptor_avg_diff_percent = (receptor_avg_diff / aap24_receptor_analysis['avg_memory_mb']) * 100
                
                summary['comparison']['receptor'] = {
                    'avg_memory_diff_mb': receptor_avg_diff,
                    'avg_memory_diff_percent': receptor_avg_diff_percent
                }
        
        # Save summary
        with open(os.path.join(analysis_dir, 'memory_analysis_summary.json'), 'w') as f:
            json.dump(summary, f, indent=2)
        
        print("Analysis complete!")
        print(f"Results saved to: {analysis_dir}")
        print(f"Summary: {json.dumps(summary, indent=2)}")
    else:
        print("No memory data found for analysis")

if __name__ == "__main__":
    main()
