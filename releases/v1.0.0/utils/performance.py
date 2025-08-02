#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DocuFlow - 性能监控和缓存模块
提供性能监控、缓存管理和资源优化功能
"""

import time
import psutil
import hashlib
import pickle
import threading
from pathlib import Path
from typing import Any, Dict, Optional, Callable, Union, List, Tuple
from dataclasses import dataclass, field
from functools import wraps, lru_cache
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from utils.logger import get_logger


@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    operation_name: str
    start_time: float
    end_time: float
    duration: float
    memory_usage_mb: float
    cpu_percent: float
    file_size_mb: Optional[float] = None
    throughput_mbps: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.file_size_mb and self.duration > 0:
            self.throughput_mbps = self.file_size_mb / self.duration


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, max_history: int = 1000):
        self.logger = get_logger('performance_monitor')
        self.metrics_history: deque = deque(maxlen=max_history)
        self.operation_stats: Dict[str, List[float]] = defaultdict(list)
        self.lock = threading.Lock()
        self._process = psutil.Process()
    
    def start_monitoring(self, operation_name: str) -> 'PerformanceContext':
        """开始监控操作
        
        Args:
            operation_name: 操作名称
            
        Returns:
            PerformanceContext: 性能监控上下文
        """
        return PerformanceContext(self, operation_name)
    
    def record_metrics(self, metrics: PerformanceMetrics) -> None:
        """记录性能指标
        
        Args:
            metrics: 性能指标
        """
        with self.lock:
            self.metrics_history.append(metrics)
            self.operation_stats[metrics.operation_name].append(metrics.duration)
        
        # 记录到结构化日志
        self.logger.log_performance_metric(
            f'{metrics.operation_name}_performance',
            metrics.duration,
            'seconds',
            memory_usage_mb=metrics.memory_usage_mb,
            cpu_percent=metrics.cpu_percent,
            file_size_mb=metrics.file_size_mb,
            throughput_mbps=metrics.throughput_mbps,
            success=metrics.success
        )
    
    def get_operation_statistics(self, operation_name: str) -> Dict[str, float]:
        """获取操作统计信息
        
        Args:
            operation_name: 操作名称
            
        Returns:
            dict: 统计信息
        """
        with self.lock:
            durations = self.operation_stats.get(operation_name, [])
        
        if not durations:
            return {}
        
        return {
            'count': len(durations),
            'total_time': sum(durations),
            'average_time': sum(durations) / len(durations),
            'min_time': min(durations),
            'max_time': max(durations),
            'median_time': sorted(durations)[len(durations) // 2]
        }
    
    def get_system_metrics(self) -> Dict[str, float]:
        """获取系统性能指标
        
        Returns:
            dict: 系统指标
        """
        try:
            memory_info = self._process.memory_info()
            cpu_percent = self._process.cpu_percent()
            
            # 系统整体指标
            system_memory = psutil.virtual_memory()
            system_cpu = psutil.cpu_percent(interval=0.1)
            disk_usage = psutil.disk_usage('/')
            
            return {
                'process_memory_mb': memory_info.rss / 1024 / 1024,
                'process_cpu_percent': cpu_percent,
                'system_memory_percent': system_memory.percent,
                'system_cpu_percent': system_cpu,
                'disk_usage_percent': disk_usage.percent,
                'available_memory_mb': system_memory.available / 1024 / 1024
            }
        except Exception as e:
            self.logger.error('system_metrics_error', error=str(e))
            return {}
    
    def get_performance_report(self) -> Dict[str, Any]:
        """生成性能报告
        
        Returns:
            dict: 性能报告
        """
        with self.lock:
            total_operations = len(self.metrics_history)
            successful_operations = sum(1 for m in self.metrics_history if m.success)
            
            if total_operations == 0:
                return {'message': 'No performance data available'}
            
            # 按操作类型分组统计
            operation_summary = {}
            for op_name in self.operation_stats:
                operation_summary[op_name] = self.get_operation_statistics(op_name)
            
            # 最近的性能趋势
            recent_metrics = list(self.metrics_history)[-100:]  # 最近100个操作
            avg_duration = sum(m.duration for m in recent_metrics) / len(recent_metrics)
            avg_memory = sum(m.memory_usage_mb for m in recent_metrics) / len(recent_metrics)
            
            return {
                'summary': {
                    'total_operations': total_operations,
                    'successful_operations': successful_operations,
                    'success_rate': successful_operations / total_operations * 100,
                    'average_duration': avg_duration,
                    'average_memory_usage_mb': avg_memory
                },
                'operation_statistics': operation_summary,
                'system_metrics': self.get_system_metrics(),
                'recent_performance': {
                    'sample_size': len(recent_metrics),
                    'average_duration': avg_duration,
                    'average_memory_usage': avg_memory
                }
            }
    
    def clear_history(self) -> None:
        """清空性能历史记录"""
        with self.lock:
            self.metrics_history.clear()
            self.operation_stats.clear()
        
        self.logger.info('performance_history_cleared')


class PerformanceContext:
    """性能监控上下文管理器"""
    
    def __init__(self, monitor: PerformanceMonitor, operation_name: str, 
                 file_path: Optional[str] = None):
        self.monitor = monitor
        self.operation_name = operation_name
        self.file_path = file_path
        self.start_time = 0.0
        self.start_memory = 0.0
        self.start_cpu = 0.0
    
    def __enter__(self) -> 'PerformanceContext':
        self.start_time = time.time()
        
        try:
            memory_info = self.monitor._process.memory_info()
            self.start_memory = memory_info.rss / 1024 / 1024  # MB
            self.start_cpu = self.monitor._process.cpu_percent()
        except Exception:
            self.start_memory = 0.0
            self.start_cpu = 0.0
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = time.time()
        duration = end_time - self.start_time
        
        try:
            memory_info = self.monitor._process.memory_info()
            end_memory = memory_info.rss / 1024 / 1024  # MB
            memory_usage = max(end_memory - self.start_memory, 0)
            cpu_percent = self.monitor._process.cpu_percent()
        except Exception:
            memory_usage = 0.0
            cpu_percent = 0.0
        
        # 计算文件大小（如果提供了文件路径）
        file_size_mb = None
        if self.file_path and Path(self.file_path).exists():
            file_size_mb = Path(self.file_path).stat().st_size / 1024 / 1024
        
        # 创建性能指标
        metrics = PerformanceMetrics(
            operation_name=self.operation_name,
            start_time=self.start_time,
            end_time=end_time,
            duration=duration,
            memory_usage_mb=memory_usage,
            cpu_percent=cpu_percent,
            file_size_mb=file_size_mb,
            success=exc_type is None,
            error_message=str(exc_val) if exc_val else None
        )
        
        self.monitor.record_metrics(metrics)
        
        return False  # 不抑制异常


class CacheManager:
    """缓存管理器"""
    
    def __init__(self, cache_dir: Optional[str] = None, max_size_mb: int = 100):
        self.logger = get_logger('cache_manager')
        self.cache_dir = Path(cache_dir) if cache_dir else Path.cwd() / '.cache'
        self.max_size_mb = max_size_mb
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 内存缓存
        self._memory_cache: Dict[str, Any] = {}
        self._cache_access_times: Dict[str, float] = {}
        self._cache_lock = threading.Lock()
        
        self.logger.info(
            'cache_manager_initialized',
            cache_dir=str(self.cache_dir),
            max_size_mb=max_size_mb
        )
    
    def _generate_cache_key(self, *args, **kwargs) -> str:
        """生成缓存键
        
        Args:
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            str: 缓存键
        """
        # 创建包含所有参数的字符串
        key_data = f"{args}_{sorted(kwargs.items())}"
        
        # 生成哈希
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get_from_memory_cache(self, key: str) -> Optional[Any]:
        """从内存缓存获取数据
        
        Args:
            key: 缓存键
            
        Returns:
            缓存的数据或None
        """
        with self._cache_lock:
            if key in self._memory_cache:
                self._cache_access_times[key] = time.time()
                return self._memory_cache[key]
        
        return None
    
    def set_memory_cache(self, key: str, value: Any) -> None:
        """设置内存缓存
        
        Args:
            key: 缓存键
            value: 缓存值
        """
        with self._cache_lock:
            self._memory_cache[key] = value
            self._cache_access_times[key] = time.time()
            
            # 检查缓存大小，必要时清理
            self._cleanup_memory_cache()
    
    def _cleanup_memory_cache(self) -> None:
        """清理内存缓存"""
        # 如果缓存项过多，删除最久未访问的项
        max_items = 1000  # 最大缓存项数
        
        if len(self._memory_cache) > max_items:
            # 按访问时间排序，删除最久未访问的项
            sorted_items = sorted(
                self._cache_access_times.items(),
                key=lambda x: x[1]
            )
            
            items_to_remove = len(self._memory_cache) - max_items + 100
            for key, _ in sorted_items[:items_to_remove]:
                self._memory_cache.pop(key, None)
                self._cache_access_times.pop(key, None)
    
    def get_from_disk_cache(self, key: str) -> Optional[Any]:
        """从磁盘缓存获取数据
        
        Args:
            key: 缓存键
            
        Returns:
            缓存的数据或None
        """
        cache_file = self.cache_dir / f"{key}.cache"
        
        try:
            if cache_file.exists():
                with open(cache_file, 'rb') as f:
                    data = pickle.load(f)
                
                # 更新访问时间
                cache_file.touch()
                
                self.logger.debug('disk_cache_hit', key=key)
                return data
        except Exception as e:
            self.logger.warning('disk_cache_read_error', key=key, error=str(e))
            # 删除损坏的缓存文件
            try:
                cache_file.unlink()
            except Exception:
                pass
        
        return None
    
    def set_disk_cache(self, key: str, value: Any) -> bool:
        """设置磁盘缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            
        Returns:
            bool: 是否成功设置
        """
        cache_file = self.cache_dir / f"{key}.cache"
        
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(value, f)
            
            self.logger.debug('disk_cache_set', key=key)
            
            # 检查磁盘缓存大小
            self._cleanup_disk_cache()
            
            return True
            
        except Exception as e:
            self.logger.error('disk_cache_write_error', key=key, error=str(e))
            return False
    
    def _cleanup_disk_cache(self) -> None:
        """清理磁盘缓存"""
        try:
            # 计算缓存目录大小
            total_size = sum(
                f.stat().st_size for f in self.cache_dir.glob('*.cache')
                if f.is_file()
            )
            
            max_size_bytes = self.max_size_mb * 1024 * 1024
            
            if total_size > max_size_bytes:
                # 按访问时间排序，删除最久未访问的文件
                cache_files = [
                    (f, f.stat().st_atime) for f in self.cache_dir.glob('*.cache')
                    if f.is_file()
                ]
                
                cache_files.sort(key=lambda x: x[1])  # 按访问时间排序
                
                # 删除文件直到大小在限制内
                for cache_file, _ in cache_files:
                    try:
                        file_size = cache_file.stat().st_size
                        cache_file.unlink()
                        total_size -= file_size
                        
                        if total_size <= max_size_bytes * 0.8:  # 保留20%的空间
                            break
                    except Exception as e:
                        self.logger.warning(
                            'cache_cleanup_error',
                            file=str(cache_file),
                            error=str(e)
                        )
                
                self.logger.info(
                    'disk_cache_cleaned',
                    final_size_mb=total_size / 1024 / 1024
                )
        
        except Exception as e:
            self.logger.error('cache_cleanup_failed', error=str(e))
    
    def clear_cache(self, memory_only: bool = False) -> None:
        """清空缓存
        
        Args:
            memory_only: 是否只清空内存缓存
        """
        with self._cache_lock:
            self._memory_cache.clear()
            self._cache_access_times.clear()
        
        if not memory_only:
            try:
                for cache_file in self.cache_dir.glob('*.cache'):
                    cache_file.unlink()
                
                self.logger.info('cache_cleared')
            except Exception as e:
                self.logger.error('cache_clear_error', error=str(e))
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            dict: 缓存统计信息
        """
        with self._cache_lock:
            memory_items = len(self._memory_cache)
        
        try:
            disk_files = list(self.cache_dir.glob('*.cache'))
            disk_items = len(disk_files)
            disk_size_mb = sum(f.stat().st_size for f in disk_files) / 1024 / 1024
        except Exception:
            disk_items = 0
            disk_size_mb = 0.0
        
        return {
            'memory_cache': {
                'items': memory_items,
                'max_items': 1000
            },
            'disk_cache': {
                'items': disk_items,
                'size_mb': round(disk_size_mb, 2),
                'max_size_mb': self.max_size_mb,
                'usage_percent': round((disk_size_mb / self.max_size_mb) * 100, 2)
            }
        }


def cached_operation(cache_manager: Optional[CacheManager] = None,
                    use_memory_cache: bool = True,
                    use_disk_cache: bool = False,
                    cache_key_func: Optional[Callable] = None):
    """缓存操作装饰器
    
    Args:
        cache_manager: 缓存管理器
        use_memory_cache: 是否使用内存缓存
        use_disk_cache: 是否使用磁盘缓存
        cache_key_func: 自定义缓存键生成函数
        
    Returns:
        装饰器函数
    """
    if cache_manager is None:
        cache_manager = CacheManager()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            if cache_key_func:
                cache_key = cache_key_func(*args, **kwargs)
            else:
                cache_key = cache_manager._generate_cache_key(
                    func.__name__, *args, **kwargs
                )
            
            # 尝试从缓存获取结果
            result = None
            
            if use_memory_cache:
                result = cache_manager.get_from_memory_cache(cache_key)
                if result is not None:
                    return result
            
            if use_disk_cache:
                result = cache_manager.get_from_disk_cache(cache_key)
                if result is not None:
                    # 同时设置内存缓存
                    if use_memory_cache:
                        cache_manager.set_memory_cache(cache_key, result)
                    return result
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 缓存结果
            if use_memory_cache:
                cache_manager.set_memory_cache(cache_key, result)
            
            if use_disk_cache:
                cache_manager.set_disk_cache(cache_key, result)
            
            return result
        
        return wrapper
    
    return decorator


def performance_monitored(monitor: Optional[PerformanceMonitor] = None,
                         operation_name: Optional[str] = None):
    """性能监控装饰器
    
    Args:
        monitor: 性能监控器
        operation_name: 操作名称
        
    Returns:
        装饰器函数
    """
    if monitor is None:
        monitor = PerformanceMonitor()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation_name or func.__name__
            
            with monitor.start_monitoring(op_name):
                return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


# 全局实例
_global_performance_monitor = None
_global_cache_manager = None


def get_performance_monitor() -> PerformanceMonitor:
    """获取全局性能监控器
    
    Returns:
        PerformanceMonitor: 性能监控器实例
    """
    global _global_performance_monitor
    
    if _global_performance_monitor is None:
        _global_performance_monitor = PerformanceMonitor()
    
    return _global_performance_monitor


def get_cache_manager() -> CacheManager:
    """获取全局缓存管理器
    
    Returns:
        CacheManager: 缓存管理器实例
    """
    global _global_cache_manager
    
    if _global_cache_manager is None:
        _global_cache_manager = CacheManager()
    
    return _global_cache_manager


# 便捷装饰器
def monitor_performance(operation_name: Optional[str] = None):
    """性能监控便捷装饰器"""
    return performance_monitored(get_performance_monitor(), operation_name)


def cache_result(use_disk: bool = False):
    """结果缓存便捷装饰器"""
    return cached_operation(
        get_cache_manager(),
        use_memory_cache=True,
        use_disk_cache=use_disk
    )