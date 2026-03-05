#!/usr/bin/env python3
"""
Date: 2026.01.26
Author: Ishani Jayasekara
Purpose: Generate global PPI network in .gml format from STRING file

Performance Tracking Module
===========================
Reusable performance tracking for bioinformatics pipelines
Tracks execution time, CPU usage, and memory consumption

Usage:
    from performance_tracker import PerformanceTracker, track_performance
    
    # Method 1: Class-based tracking
    tracker = PerformanceTracker()
    tracker.start_step("My Step")
    # ... do work ...
    tracker.end_step("My Step")
    tracker.print_summary()
    
    # Method 2: Decorator
    @track_performance
    def my_function():
        # ... do work ...
        pass
    
    # Method 3: Context manager
    with track_step("My Step"):
        # ... do work ...
        pass
"""

import time
import psutil
import os
from datetime import datetime
from functools import wraps
from contextlib import contextmanager
import json


class PerformanceTracker:
    """
    Track execution time, CPU usage, and memory for pipeline steps
    """
    
    def __init__(self, pipeline_name="Pipeline"):
        """
        Initialize performance tracker
        
        Args:
            pipeline_name: Name of the pipeline for reporting
        """
        self.pipeline_name = pipeline_name
        self.process = psutil.Process(os.getpid())
        self.metrics = {}
        self.step_order = []
        self.pipeline_start_time = time.time()
        self.pipeline_start_cpu = self.process.cpu_percent(interval=0.1)
        self.pipeline_start_mem = self.process.memory_info().rss / 1024 / 1024
        
    def start_step(self, step_name):
        """
        Start tracking a pipeline step
        
        Args:
            step_name: Name of the step to track
        """
        if step_name not in self.step_order:
            self.step_order.append(step_name)
            
        self.metrics[step_name] = {
            'start_time': time.time(),
            'start_cpu': self.process.cpu_percent(interval=0.1),
            'start_mem': self.process.memory_info().rss / 1024 / 1024,
            'status': 'running'
        }
        
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] ▶ Starting: {step_name}")
        
    def end_step(self, step_name, status="completed"):
        """
        End tracking a pipeline step
        
        Args:
            step_name: Name of the step
            status: Status of completion (completed/failed)
        """
        if step_name not in self.metrics:
            print(f"Warning: Step '{step_name}' was not started")
            return
        
        m = self.metrics[step_name]
        m['end_time'] = time.time()
        m['end_cpu'] = self.process.cpu_percent(interval=0.1)
        m['end_mem'] = self.process.memory_info().rss / 1024 / 1024
        m['elapsed'] = m['end_time'] - m['start_time']
        m['mem_delta'] = m['end_mem'] - m['start_mem']
        m['status'] = status
        
        timestamp = datetime.now().strftime('%H:%M:%S')
        status_icon = "✓" if status == "completed" else "✗"
        
        print(f"[{timestamp}] {status_icon} {step_name}")
        print(f"  Time: {self._format_time(m['elapsed'])}")
        print(f"  CPU: {m['end_cpu']:.1f}%")
        print(f"  Memory: {m['end_mem']:.1f} MB (Δ {m['mem_delta']:+.1f} MB)")
        
    def _format_time(self, seconds):
        """Format time in human-readable format"""
        if seconds < 60:
            return f"{seconds:.2f}s"
        elif seconds < 3600:
            return f"{seconds/60:.2f}m ({seconds:.1f}s)"
        else:
            return f"{seconds/3600:.2f}h ({seconds/60:.1f}m)"
    
    def print_summary(self):
        """Print overall performance summary"""
        total_time = time.time() - self.pipeline_start_time
        total_cpu = self.process.cpu_percent(interval=0.1)
        total_mem = self.process.memory_info().rss / 1024 / 1024
        mem_delta = total_mem - self.pipeline_start_mem
        
        print(f"\n{'='*80}")
        print(f"PERFORMANCE SUMMARY: {self.pipeline_name}")
        print(f"{'='*80}")
        print(f"{'Step':<35} {'Time':<15} {'CPU %':<10} {'Mem Δ (MB)':<12} {'Status':<10}")
        print(f"{'-'*80}")
        
        for step in self.step_order:
            if step in self.metrics:
                m = self.metrics[step]
                if 'elapsed' in m:
                    time_str = self._format_time(m['elapsed'])
                    status_icon = "✓" if m['status'] == "completed" else "✗"
                    print(f"{step:<35} {time_str:<15} {m['end_cpu']:>6.1f}    "
                          f"{m['mem_delta']:>10.1f}    {status_icon} {m['status']}")
        
        print(f"{'-'*80}")
        print(f"{'TOTAL PIPELINE TIME':<35} {self._format_time(total_time):<15}")
        print(f"{'FINAL CPU USAGE':<35} {total_cpu:.1f}%")
        print(f"{'TOTAL MEMORY CHANGE':<35} {mem_delta:+.1f} MB (Final: {total_mem:.1f} MB)")
        print(f"{'='*80}\n")
        
    def get_metrics(self):
        """
        Get metrics dictionary
        
        Returns:
            Dictionary containing all metrics
        """
        return {
            'pipeline_name': self.pipeline_name,
            'total_time': time.time() - self.pipeline_start_time,
            'timestamp': datetime.now().isoformat(),
            'steps': self.metrics
        }
    
    def save_metrics(self, output_file):
        """
        Save metrics to JSON file
        
        Args:
            output_file: Path to output JSON file
        """
        metrics = self.get_metrics()
        with open(output_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        print(f"✓ Metrics saved to: {output_file}")


@contextmanager
def track_step(step_name, tracker=None):
    """
    Context manager for tracking a single step
    
    Args:
        step_name: Name of the step
        tracker: Optional PerformanceTracker instance
        
    Usage:
        with track_step("Load data"):
            data = load_data()
    """
    if tracker is None:
        tracker = PerformanceTracker()
    
    tracker.start_step(step_name)
    
    try:
        yield tracker
        tracker.end_step(step_name, status="completed")
    except Exception as e:
        tracker.end_step(step_name, status="failed")
        raise


def track_performance(func):
    """
    Decorator to track performance of a function
    
    Usage:
        @track_performance
        def my_function():
            # do work
            pass
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        process = psutil.Process(os.getpid())
        
        start_time = time.time()
        start_cpu = process.cpu_percent(interval=0.1)
        start_memory = process.memory_info().rss / 1024 / 1024
        
        print(f"\n{'='*70}")
        print(f"▶ Running: {func.__name__}")
        print(f"{'='*70}")
        
        try:
            result = func(*args, **kwargs)
            status = "✓ COMPLETED"
        except Exception as e:
            status = f"✗ FAILED: {str(e)}"
            raise
        finally:
            end_time = time.time()
            end_cpu = process.cpu_percent(interval=0.1)
            end_memory = process.memory_info().rss / 1024 / 1024
            
            elapsed = end_time - start_time
            
            print(f"\n{'='*70}")
            print(f"{status}: {func.__name__}")
            print(f"{'='*70}")
            print(f"  ⏱  Time: {elapsed:.2f}s ({elapsed/60:.2f}m)")
            print(f"  💻 CPU: {end_cpu:.1f}%")
            print(f"  🧠 Memory: {end_memory:.1f} MB (Δ {end_memory-start_memory:+.1f} MB)")
            print(f"{'='*70}\n")
        
        return result
    
    return wrapper


def get_system_info():
    """
    Get system information for logging
    
    Returns:
        Dictionary with system information
    """
    import platform
    
    return {
        'platform': platform.system(),
        'platform_version': platform.version(),
        'architecture': platform.machine(),
        'processor': platform.processor(),
        'python_version': platform.python_version(),
        'cpu_count': psutil.cpu_count(),
        'cpu_count_logical': psutil.cpu_count(logical=True),
        'total_memory_gb': psutil.virtual_memory().total / (1024**3),
        'available_memory_gb': psutil.virtual_memory().available / (1024**3)
    }


def print_system_info():
    """Print system information"""
    info = get_system_info()
    
    print(f"\n{'='*70}")
    print(f"SYSTEM INFORMATION")
    print(f"{'='*70}")
    print(f"Platform: {info['platform']} {info['architecture']}")
    print(f"Processor: {info['processor']}")
    print(f"Python: {info['python_version']}")
    print(f"CPU Cores: {info['cpu_count']} physical, {info['cpu_count_logical']} logical")
    print(f"Total Memory: {info['total_memory_gb']:.1f} GB")
    print(f"Available Memory: {info['available_memory_gb']:.1f} GB")
    print(f"{'='*70}\n")


if __name__ == '__main__':
    # Demo usage
    print("Performance Tracker Demo")
    print_system_info()
    
    # Demo 1: Class-based tracking
    tracker = PerformanceTracker("Demo Pipeline")
    
    tracker.start_step("Step 1: Data loading")
    time.sleep(1)
    tracker.end_step("Step 1: Data loading")
    
    tracker.start_step("Step 2: Processing")
    time.sleep(2)
    tracker.end_step("Step 2: Processing")
    
    tracker.print_summary()
    
    # Demo 2: Context manager
    print("\nDemo: Context Manager")
    with track_step("Quick operation"):
        time.sleep(0.5)
    
    # Demo 3: Decorator
    @track_performance
    def example_function():
        time.sleep(1)
        return "Done"
    
    print("\nDemo: Decorator")
    example_function()