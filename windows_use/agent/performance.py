"""
Performance monitoring utilities for Windows-Use agent
"""
import time
import functools
from typing import Dict, Any, Callable
from collections import defaultdict

class PerformanceMonitor:
    """Monitor and track performance metrics"""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.start_times = {}
        self.enabled = True
    
    def start_timer(self, operation: str):
        """Start timing an operation"""
        if self.enabled:
            self.start_times[operation] = time.time()
    
    def end_timer(self, operation: str):
        """End timing an operation and record the duration"""
        if self.enabled and operation in self.start_times:
            duration = time.time() - self.start_times[operation]
            self.metrics[operation].append(duration)
            del self.start_times[operation]
            return duration
        return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        stats = {}
        for operation, durations in self.metrics.items():
            if durations:
                stats[operation] = {
                    'count': len(durations),
                    'total_time': sum(durations),
                    'avg_time': sum(durations) / len(durations),
                    'min_time': min(durations),
                    'max_time': max(durations)
                }
        return stats
    
    def print_stats(self):
        """Print performance statistics"""
        stats = self.get_stats()
        if not stats:
            print("No performance data collected yet")
            return
        
        print("\nPerformance Statistics:")
        print("-" * 50)
        for operation, data in stats.items():
            print(f"{operation}:")
            print(f"   Count: {data['count']}")
            print(f"   Avg Time: {data['avg_time']:.3f}s")
            print(f"   Min Time: {data['min_time']:.3f}s")
            print(f"   Max Time: {data['max_time']:.3f}s")
            print(f"   Total Time: {data['total_time']:.3f}s")
            print()
    
    def clear_stats(self):
        """Clear all performance statistics"""
        self.metrics.clear()
        self.start_times.clear()
    
    def enable(self):
        """Enable performance monitoring"""
        self.enabled = True
    
    def disable(self):
        """Disable performance monitoring"""
        self.enabled = False

def timed(operation_name: str = None):
    """Decorator to time function execution"""
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get the performance monitor from the first argument if it's an Agent instance
            monitor = None
            if args and hasattr(args[0], 'performance_monitor'):
                monitor = args[0].performance_monitor
            
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            if monitor:
                monitor.start_timer(op_name)
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                if monitor:
                    duration = monitor.end_timer(op_name)
                    if duration > 1.0:  # Log slow operations
                        print(f"Slow operation: {op_name} took {duration:.3f}s")
        
        return wrapper
    return decorator

# Global performance monitor instance
global_monitor = PerformanceMonitor()
