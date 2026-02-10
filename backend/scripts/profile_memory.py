#!/usr/bin/env python3
"""
Memory Profiler Script for DCIS Backend

Profiles memory usage during a sustained test run to detect leaks.

Usage:
    python scripts/profile_memory.py --duration 1800  # 30 min test
    python scripts/profile_memory.py --interval 10     # Sample every 10s

Requires:
    pip install memory-profiler psutil matplotlib
"""

import argparse
import time
import psutil
import os
from memory_profiler import profile
from datetime import datetime
import matplotlib.pyplot as plt


class MemoryProfiler:
    """Monitor memory usage over time"""
    
    def __init__(self, interval=5):
        self.interval = interval
        self.memory_samples = []
        self.timestamps = []
        self.process = psutil.Process(os.getpid())
    
    def sample_memory(self):
        """Take a memory sample"""
        mem_info = self.process.memory_info()
        rss_mb = mem_info.rss / 1024 / 1024  # Convert to MB
        
        self.memory_samples.append(rss_mb)
        self.timestamps.append(datetime.now())
        
        return rss_mb
    
    def run_test(self, duration_seconds):
        """Run memory profiling test"""
        print(f"Starting memory profiling for {duration_seconds} seconds...")
        print(f"Sampling every {self.interval} seconds")
        print(f"PID: {self.process.pid}")
        
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        iteration = 0
        while time.time() < end_time:
            rss_mb = self.sample_memory()
            elapsed = time.time() - start_time
            
            iteration += 1
            if iteration % 10 == 0:
                print(f"[{elapsed:.0f}s] Memory: {rss_mb:.2f} MB")
            
            time.sleep(self.interval)
        
        print(f"\nCompleted {len(self.memory_samples)} samples")
        self.analyze_results()
    
    def analyze_results(self):
        """Analyze memory usage patterns"""
        if not self.memory_samples:
            print("No samples collected")
            return
        
        min_mem = min(self.memory_samples)
        max_mem = max(self.memory_samples)
        avg_mem = sum(self.memory_samples) / len(self.memory_samples)
        final_mem = self.memory_samples[-1]
        initial_mem = self.memory_samples[0]
        growth = final_mem - initial_mem
        
        print("\n" + "="*50)
        print("MEMORY ANALYSIS")
        print("="*50)
        print(f"Initial Memory:  {initial_mem:.2f} MB")
        print(f"Final Memory:    {final_mem:.2f} MB")
        print(f"Min Memory:      {min_mem:.2f} MB")
        print(f"Max Memory:      {max_mem:.2f} MB")
        print(f"Average Memory:  {avg_mem:.2f} MB")
        print(f"Growth:          {growth:.2f} MB ({(growth/initial_mem*100):.1f}%)")
        
        # Detect potential leak
        if growth > initial_mem * 0.2:  # >20% growth
            print(f"\n⚠️  WARNING: Potential memory leak detected!")
            print(f"   Memory grew by {growth:.2f} MB ({(growth/initial_mem*100):.1f}%)")
        else:
            print(f"\n✅ Memory usage appears stable")
        
        # Save plot
        self.save_plot()
    
    def save_plot(self):
        """Save memory usage plot"""
        plt.figure(figsize=(12, 6))
        
        # Convert timestamps to seconds elapsed
        start = self.timestamps[0]
        elapsed_times = [(t - start).total_seconds() for t in self.timestamps]
        
        plt.plot(elapsed_times, self.memory_samples, 'b-', linewidth=2)
        plt.xlabel('Time (seconds)')
        plt.ylabel('Memory (MB)')
        plt.title('DCIS Backend - Memory Usage Over Time')
        plt.grid(True, alpha=0.3)
        
        filename = f"memory_profile_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        print(f"\n📊 Memory plot saved to: {filename}")


@profile
def simulate_workload():
    """Simulate typical DCIS workload"""
    # Import backend modules
    try:
        from backend.src.services.orchestrator.meta_orchestrator import MetaOrchestrator
        
        orchestrator = MetaOrchestrator()
        
        # Simulate queries
        queries = [
            "Explain machine learning",
            "Write Python code to sort a list",
            "What is quantum computing?",
        ]
        
        for query in queries * 10:
            # Simulate processing
            result = orchestrator.process_query(query)
            time.sleep(0.1)
    
    except Exception as e:
        print(f"Workload simulation error: {e}")
        # Continue profiling even if imports fail


def main():
    parser = argparse.ArgumentParser(description='Memory profiler for DCIS backend')
    parser.add_argument('--duration', type=int, default=300,
                       help='Test duration in seconds (default: 300 = 5 min)')
    parser.add_argument('--interval', type=int, default=5,
                       help='Sampling interval in seconds (default: 5)')
    parser.add_argument('--workload', action='store_true',
                       help='Run simulated workload during profiling')
    
    args = parser.parse_args()
    
    profiler = MemoryProfiler(interval=args.interval)
    
    if args.workload:
        print("Running with simulated workload...")
        # Run workload in background while profiling
        import threading
        workload_thread = threading.Thread(target=simulate_workload)
        workload_thread.daemon = True
        workload_thread.start()
    
    profiler.run_test(args.duration)


if __name__ == "__main__":
    main()
