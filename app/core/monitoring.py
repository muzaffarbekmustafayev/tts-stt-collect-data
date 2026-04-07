from functools import wraps
from time import time
from typing import Callable
from app.core.logging import get_logger

logger = get_logger("monitoring")

def monitor_performance(func_name: str = None):
    """Decorator to monitor function execution time"""
    def decorator(func: Callable):
        name = func_name or func.__name__
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time()
            try:
                result = await func(*args, **kwargs)
                execution_time = time() - start_time
                
                if execution_time > 1.0:  # Log if takes more than 1 second
                    logger.warning(
                        f"Slow operation: {name} took {execution_time:.2f}s"
                    )
                else:
                    logger.debug(f"{name} executed in {execution_time:.3f}s")
                
                return result
            except Exception as e:
                execution_time = time() - start_time
                logger.error(
                    f"Error in {name} after {execution_time:.2f}s: {str(e)}"
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time()
            try:
                result = func(*args, **kwargs)
                execution_time = time() - start_time
                
                if execution_time > 1.0:
                    logger.warning(
                        f"Slow operation: {name} took {execution_time:.2f}s"
                    )
                else:
                    logger.debug(f"{name} executed in {execution_time:.3f}s")
                
                return result
            except Exception as e:
                execution_time = time() - start_time
                logger.error(
                    f"Error in {name} after {execution_time:.2f}s: {str(e)}"
                )
                raise
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class PerformanceStats:
    """Simple performance statistics tracker"""
    
    def __init__(self):
        self._stats = {}
    
    def record(self, operation: str, duration: float):
        """Record operation duration"""
        if operation not in self._stats:
            self._stats[operation] = {
                'count': 0,
                'total_time': 0.0,
                'min_time': float('inf'),
                'max_time': 0.0
            }
        
        stats = self._stats[operation]
        stats['count'] += 1
        stats['total_time'] += duration
        stats['min_time'] = min(stats['min_time'], duration)
        stats['max_time'] = max(stats['max_time'], duration)
    
    def get_stats(self, operation: str = None):
        """Get statistics for operation(s)"""
        if operation:
            if operation not in self._stats:
                return None
            
            stats = self._stats[operation]
            return {
                'operation': operation,
                'count': stats['count'],
                'avg_time': stats['total_time'] / stats['count'],
                'min_time': stats['min_time'],
                'max_time': stats['max_time'],
                'total_time': stats['total_time']
            }
        
        # Return all stats
        return {
            op: {
                'count': s['count'],
                'avg_time': s['total_time'] / s['count'],
                'min_time': s['min_time'],
                'max_time': s['max_time'],
                'total_time': s['total_time']
            }
            for op, s in self._stats.items()
        }
    
    def reset(self):
        """Reset all statistics"""
        self._stats.clear()

# Global performance stats instance
perf_stats = PerformanceStats()
