"""
Performance benchmarking for Windows-Use Agent
"""
import time
import statistics
from typing import List, Dict
from pathlib import Path
import json
from datetime import datetime

class PerformanceBenchmark:
    def __init__(self, agent):
        self.agent = agent
        self.results = []
    
    def run_benchmarks(self):
        """Run performance benchmarks"""
        print("\n" + "="*100)
        print("PERFORMANCE BENCHMARKING")
        print("="*100 + "\n")
        
        benchmarks = [
            ("Simple Query Response Time", lambda: self.agent.invoke("Hello"), 5),
            ("Tool Execution Speed - Launch", lambda: self.agent.invoke("Open notepad"), 3),
            ("Tool Execution Speed - Type", lambda: self.agent.invoke("Type 'test' in notepad"), 3),
            ("Multi-Step Task Performance", lambda: self.agent.invoke("Open calculator, type 5+5, then close it"), 3),
            ("Reasoning Speed", lambda: self.agent.invoke("What applications can you help me open?"), 3),
        ]
        
        for name, test_func, iterations in benchmarks:
            print(f"\nBenchmarking: {name}")
            print("-" * 80)
            
            times = []
            for i in range(iterations):
                start = time.time()
                try:
                    test_func()
                    elapsed = time.time() - start
                    times.append(elapsed)
                    print(f"  Iteration {i+1}: {elapsed:.2f}s")
                except Exception as e:
                    print(f"  Iteration {i+1}: ERROR - {e}")
            
            if times:
                avg_time = statistics.mean(times)
                min_time = min(times)
                max_time = max(times)
                
                self.results.append({
                    'name': name,
                    'iterations': iterations,
                    'avg_time': avg_time,
                    'min_time': min_time,
                    'max_time': max_time,
                    'all_times': times
                })
                
                print(f"  Average: {avg_time:.2f}s | Min: {min_time:.2f}s | Max: {max_time:.2f}s")
        
        self.save_results()
        self.print_summary()
    
    def save_results(self):
        """Save benchmark results"""
        output_dir = Path("tests/automated/results")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"benchmark_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': timestamp,
                'benchmarks': self.results
            }, f, indent=2)
        
        print(f"\nBenchmark results saved to: {output_file}")
    
    def print_summary(self):
        """Print benchmark summary"""
        print("\n" + "="*100)
        print("BENCHMARK SUMMARY")
        print("="*100 + "\n")
        
        for result in self.results:
            print(f"{result['name']:<50} {result['avg_time']:>8.2f}s (avg)")
        
        print("\n" + "="*100 + "\n")

