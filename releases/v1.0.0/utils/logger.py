#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DocuFlow - 结构化日志系统
提供统一的日志记录和监控功能
"""

import logging
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional, Union
from pathlib import Path
from functools import wraps


class StructuredLogger:
    """结构化日志记录器"""
    
    def __init__(self, name: str, log_file: Optional[str] = None, level: int = logging.INFO):
        """初始化结构化日志记录器
        
        Args:
            name: 日志记录器名称
            log_file: 日志文件路径，如果为None则只输出到控制台
            level: 日志级别
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # 避免重复添加处理器
        if not self.logger.handlers:
            self._setup_handlers(log_file)
    
    def _setup_handlers(self, log_file: Optional[str]) -> None:
        """设置日志处理器"""
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # 文件处理器
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def _log_structured(self, level: int, event: str, **kwargs) -> None:
        """记录结构化日志
        
        Args:
            level: 日志级别
            event: 事件名称
            **kwargs: 额外的结构化数据
        """
        log_data = {
            'event': event,
            'timestamp': datetime.utcnow().isoformat(),
            **kwargs
        }
        
        # 格式化为JSON字符串
        message = json.dumps(log_data, ensure_ascii=False, separators=(',', ':'))
        self.logger.log(level, message)
    
    def info(self, event: str, **kwargs) -> None:
        """记录信息级别的结构化日志"""
        self._log_structured(logging.INFO, event, **kwargs)
    
    def warning(self, event: str, **kwargs) -> None:
        """记录警告级别的结构化日志"""
        self._log_structured(logging.WARNING, event, **kwargs)
    
    def error(self, event: str, **kwargs) -> None:
        """记录错误级别的结构化日志"""
        self._log_structured(logging.ERROR, event, **kwargs)
    
    def debug(self, event: str, **kwargs) -> None:
        """记录调试级别的结构化日志"""
        self._log_structured(logging.DEBUG, event, **kwargs)
    
    def log_conversion_start(self, file_path: str, target_format: str, **kwargs) -> None:
        """记录转换开始事件"""
        self.info(
            'conversion_started',
            file_path=file_path,
            target_format=target_format,
            **kwargs
        )
    
    def log_conversion_complete(self, file_path: str, output_path: str, 
                              duration: float, success: bool, **kwargs) -> None:
        """记录转换完成事件"""
        self.info(
            'conversion_completed',
            file_path=file_path,
            output_path=output_path,
            duration_seconds=round(duration, 3),
            success=success,
            **kwargs
        )
    
    def log_conversion_error(self, file_path: str, error_type: str, 
                           error_message: str, **kwargs) -> None:
        """记录转换错误事件"""
        self.error(
            'conversion_error',
            file_path=file_path,
            error_type=error_type,
            error_message=error_message,
            **kwargs
        )
    
    def log_batch_operation(self, operation: str, total_files: int, 
                          successful: int, failed: int, duration: float, **kwargs) -> None:
        """记录批量操作事件"""
        self.info(
            'batch_operation_completed',
            operation=operation,
            total_files=total_files,
            successful_files=successful,
            failed_files=failed,
            success_rate=round((successful / max(total_files, 1)) * 100, 2),
            duration_seconds=round(duration, 3),
            **kwargs
        )
    
    def log_file_validation(self, file_path: str, valid: bool, 
                          reason: Optional[str] = None, **kwargs) -> None:
        """记录文件验证事件"""
        log_data = {
            'file_path': file_path,
            'valid': valid
        }
        
        if reason:
            log_data['reason'] = reason
        
        log_data.update(kwargs)
        
        if valid:
            self.debug('file_validation_passed', **log_data)
        else:
            self.warning('file_validation_failed', **log_data)
    
    def log_performance_metric(self, metric_name: str, value: Union[int, float], 
                             unit: str = '', **kwargs) -> None:
        """记录性能指标"""
        self.info(
            'performance_metric',
            metric_name=metric_name,
            value=value,
            unit=unit,
            **kwargs
        )
    
    def log_system_info(self, **kwargs) -> None:
        """记录系统信息"""
        import platform
        import sys
        
        system_info = {
            'python_version': sys.version,
            'platform': platform.platform(),
            'architecture': platform.architecture(),
            'processor': platform.processor(),
        }
        system_info.update(kwargs)
        
        self.info('system_info', **system_info)


class PerformanceMonitor:
    """性能监控装饰器和工具"""
    
    def __init__(self, logger: StructuredLogger):
        self.logger = logger
    
    def monitor_performance(self, operation_name: str = None):
        """性能监控装饰器
        
        Args:
            operation_name: 操作名称，如果为None则使用函数名
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                op_name = operation_name or func.__name__
                start_time = time.time()
                
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    
                    self.logger.log_performance_metric(
                        f'{op_name}_duration',
                        duration,
                        'seconds',
                        operation=op_name,
                        success=True
                    )
                    
                    return result
                    
                except Exception as e:
                    duration = time.time() - start_time
                    
                    self.logger.log_performance_metric(
                        f'{op_name}_duration',
                        duration,
                        'seconds',
                        operation=op_name,
                        success=False,
                        error=str(e)
                    )
                    
                    raise
            
            return wrapper
        return decorator
    
    def time_operation(self, operation_name: str):
        """上下文管理器形式的性能监控
        
        Args:
            operation_name: 操作名称
        """
        return TimedOperation(self.logger, operation_name)


class TimedOperation:
    """计时操作上下文管理器"""
    
    def __init__(self, logger: StructuredLogger, operation_name: str):
        self.logger = logger
        self.operation_name = operation_name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        self.logger.debug(
            'operation_started',
            operation=self.operation_name
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        success = exc_type is None
        
        log_data = {
            'operation': self.operation_name,
            'duration_seconds': round(duration, 3),
            'success': success
        }
        
        if not success:
            log_data.update({
                'error_type': exc_type.__name__ if exc_type else None,
                'error_message': str(exc_val) if exc_val else None
            })
        
        self.logger.info('operation_completed', **log_data)
        
        return False  # 不抑制异常


# 全局日志实例
_global_logger = None


def get_logger(name: str = 'docuflow', log_file: Optional[str] = None) -> StructuredLogger:
    """获取全局日志实例
    
    Args:
        name: 日志记录器名称
        log_file: 日志文件路径
        
    Returns:
        StructuredLogger: 结构化日志记录器实例
    """
    global _global_logger
    
    if _global_logger is None:
        _global_logger = StructuredLogger(name, log_file)
    
    return _global_logger


def setup_logging(log_file: Optional[str] = None, level: int = logging.INFO) -> StructuredLogger:
    """设置全局日志配置
    
    Args:
        log_file: 日志文件路径
        level: 日志级别
        
    Returns:
        StructuredLogger: 配置好的日志记录器
    """
    global _global_logger
    _global_logger = StructuredLogger('docuflow', log_file, level)
    return _global_logger


# 便捷函数
def log_info(event: str, **kwargs) -> None:
    """记录信息日志的便捷函数"""
    get_logger().info(event, **kwargs)


def log_error(event: str, **kwargs) -> None:
    """记录错误日志的便捷函数"""
    get_logger().error(event, **kwargs)


def log_warning(event: str, **kwargs) -> None:
    """记录警告日志的便捷函数"""
    get_logger().warning(event, **kwargs)


def monitor_performance(operation_name: str = None):
    """性能监控装饰器的便捷函数"""
    logger = get_logger()
    monitor = PerformanceMonitor(logger)
    return monitor.monitor_performance(operation_name)