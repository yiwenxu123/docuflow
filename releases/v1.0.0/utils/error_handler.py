#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DocuFlow - 增强错误处理和重试机制
提供统一的错误处理、重试策略和错误恢复功能
"""

import time
import functools
import traceback
from typing import Type, Tuple, Callable, Any, Optional, Dict, List, Union
from dataclasses import dataclass
from enum import Enum
from utils.logger import get_logger


class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RetryStrategy(Enum):
    """重试策略"""
    FIXED_DELAY = "fixed_delay"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIBONACCI_BACKOFF = "fibonacci_backoff"


@dataclass
class ErrorContext:
    """错误上下文信息"""
    operation: str
    file_path: Optional[str] = None
    input_format: Optional[str] = None
    output_format: Optional[str] = None
    user_data: Optional[Dict[str, Any]] = None
    timestamp: float = 0.0
    
    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


@dataclass
class RetryConfig:
    """重试配置"""
    max_attempts: int = 3
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_multiplier: float = 2.0
    jitter: bool = True
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
    
    def calculate_delay(self, attempt: int) -> float:
        """计算重试延迟时间
        
        Args:
            attempt: 当前重试次数（从1开始）
            
        Returns:
            float: 延迟时间（秒）
        """
        if self.strategy == RetryStrategy.FIXED_DELAY:
            delay = self.base_delay
        elif self.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = self.base_delay * (self.backoff_multiplier ** (attempt - 1))
        elif self.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = self.base_delay * attempt
        elif self.strategy == RetryStrategy.FIBONACCI_BACKOFF:
            delay = self.base_delay * self._fibonacci(attempt)
        else:
            delay = self.base_delay
        
        # 应用最大延迟限制
        delay = min(delay, self.max_delay)
        
        # 添加抖动以避免雷群效应
        if self.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)
        
        return delay
    
    def _fibonacci(self, n: int) -> int:
        """计算斐波那契数列第n项"""
        if n <= 1:
            return 1
        a, b = 1, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b


class ErrorRecoveryManager:
    """错误恢复管理器"""
    
    def __init__(self):
        self.logger = get_logger('error_recovery')
        self.recovery_strategies: Dict[Type[Exception], Callable] = {}
        self.error_history: List[Dict[str, Any]] = []
        self.max_history_size = 1000
    
    def register_recovery_strategy(self, exception_type: Type[Exception], 
                                 recovery_func: Callable) -> None:
        """注册错误恢复策略
        
        Args:
            exception_type: 异常类型
            recovery_func: 恢复函数
        """
        self.recovery_strategies[exception_type] = recovery_func
        self.logger.info(
            'recovery_strategy_registered',
            exception_type=exception_type.__name__,
            recovery_function=recovery_func.__name__
        )
    
    def attempt_recovery(self, exception: Exception, context: ErrorContext) -> bool:
        """尝试错误恢复
        
        Args:
            exception: 发生的异常
            context: 错误上下文
            
        Returns:
            bool: 是否成功恢复
        """
        exception_type = type(exception)
        
        # 查找匹配的恢复策略
        recovery_func = None
        for exc_type, func in self.recovery_strategies.items():
            if issubclass(exception_type, exc_type):
                recovery_func = func
                break
        
        if recovery_func is None:
            self.logger.warning(
                'no_recovery_strategy_found',
                exception_type=exception_type.__name__,
                operation=context.operation
            )
            return False
        
        try:
            self.logger.info(
                'attempting_error_recovery',
                exception_type=exception_type.__name__,
                operation=context.operation,
                recovery_function=recovery_func.__name__
            )
            
            result = recovery_func(exception, context)
            
            if result:
                self.logger.info(
                    'error_recovery_successful',
                    exception_type=exception_type.__name__,
                    operation=context.operation
                )
            else:
                self.logger.warning(
                    'error_recovery_failed',
                    exception_type=exception_type.__name__,
                    operation=context.operation
                )
            
            return result
            
        except Exception as recovery_error:
            self.logger.error(
                'error_recovery_exception',
                exception_type=exception_type.__name__,
                operation=context.operation,
                recovery_error=str(recovery_error)
            )
            return False
    
    def record_error(self, exception: Exception, context: ErrorContext, 
                    severity: ErrorSeverity = ErrorSeverity.MEDIUM) -> None:
        """记录错误信息
        
        Args:
            exception: 异常对象
            context: 错误上下文
            severity: 错误严重程度
        """
        error_record = {
            'timestamp': context.timestamp,
            'operation': context.operation,
            'exception_type': type(exception).__name__,
            'exception_message': str(exception),
            'severity': severity.value,
            'file_path': context.file_path,
            'input_format': context.input_format,
            'output_format': context.output_format,
            'user_data': context.user_data,
            'traceback': traceback.format_exc()
        }
        
        self.error_history.append(error_record)
        
        # 限制历史记录大小
        if len(self.error_history) > self.max_history_size:
            self.error_history = self.error_history[-self.max_history_size:]
        
        # 记录到结构化日志
        self.logger.error(
            'error_recorded',
            **error_record
        )
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """获取错误统计信息
        
        Returns:
            dict: 错误统计信息
        """
        if not self.error_history:
            return {
                'total_errors': 0,
                'error_types': {},
                'severity_distribution': {},
                'recent_errors': []
            }
        
        # 统计错误类型
        error_types = {}
        severity_distribution = {}
        
        for error in self.error_history:
            exc_type = error['exception_type']
            severity = error['severity']
            
            error_types[exc_type] = error_types.get(exc_type, 0) + 1
            severity_distribution[severity] = severity_distribution.get(severity, 0) + 1
        
        # 获取最近的错误
        recent_errors = sorted(
            self.error_history,
            key=lambda x: x['timestamp'],
            reverse=True
        )[:10]
        
        return {
            'total_errors': len(self.error_history),
            'error_types': error_types,
            'severity_distribution': severity_distribution,
            'recent_errors': recent_errors
        }
    
    def clear_error_history(self) -> None:
        """清空错误历史记录"""
        self.error_history.clear()
        self.logger.info('error_history_cleared')


class EnhancedRetryDecorator:
    """增强的重试装饰器"""
    
    def __init__(self, config: RetryConfig, 
                 recovery_manager: Optional[ErrorRecoveryManager] = None):
        self.config = config
        self.recovery_manager = recovery_manager
        self.logger = get_logger('retry_decorator')
    
    def __call__(self, func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(1, self.config.max_attempts + 1):
                try:
                    # 记录重试开始
                    if attempt > 1:
                        self.logger.info(
                            'retry_attempt',
                            function=func.__name__,
                            attempt=attempt,
                            max_attempts=self.config.max_attempts
                        )
                    
                    result = func(*args, **kwargs)
                    
                    # 成功执行，记录日志
                    if attempt > 1:
                        self.logger.info(
                            'retry_successful',
                            function=func.__name__,
                            successful_attempt=attempt
                        )
                    
                    return result
                    
                except self.config.exceptions as e:
                    last_exception = e
                    
                    # 创建错误上下文
                    context = ErrorContext(
                        operation=func.__name__,
                        user_data={'args': str(args), 'kwargs': str(kwargs)}
                    )
                    
                    # 记录错误
                    if self.recovery_manager:
                        severity = self._determine_severity(e, attempt)
                        self.recovery_manager.record_error(e, context, severity)
                        
                        # 尝试错误恢复
                        if self.recovery_manager.attempt_recovery(e, context):
                            self.logger.info(
                                'error_recovered_retrying',
                                function=func.__name__,
                                attempt=attempt
                            )
                            continue
                    
                    # 如果是最后一次尝试，不再重试
                    if attempt == self.config.max_attempts:
                        self.logger.error(
                            'retry_exhausted',
                            function=func.__name__,
                            total_attempts=attempt,
                            final_error=str(e)
                        )
                        break
                    
                    # 计算延迟时间并等待
                    delay = self.config.calculate_delay(attempt)
                    self.logger.debug(
                        'retry_delay',
                        function=func.__name__,
                        attempt=attempt,
                        delay_seconds=delay
                    )
                    
                    time.sleep(delay)
                
                except Exception as e:
                    # 不在重试范围内的异常，直接抛出
                    self.logger.error(
                        'non_retryable_exception',
                        function=func.__name__,
                        exception_type=type(e).__name__,
                        exception_message=str(e)
                    )
                    raise
            
            # 所有重试都失败了，抛出最后一个异常
            if last_exception:
                raise last_exception
        
        return wrapper
    
    def _determine_severity(self, exception: Exception, attempt: int) -> ErrorSeverity:
        """确定错误严重程度
        
        Args:
            exception: 异常对象
            attempt: 当前尝试次数
            
        Returns:
            ErrorSeverity: 错误严重程度
        """
        # 根据异常类型和尝试次数确定严重程度
        if attempt == self.config.max_attempts:
            return ErrorSeverity.HIGH
        elif attempt > self.config.max_attempts // 2:
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW


def retry_with_recovery(config: Optional[RetryConfig] = None,
                       recovery_manager: Optional[ErrorRecoveryManager] = None):
    """重试装饰器工厂函数
    
    Args:
        config: 重试配置
        recovery_manager: 错误恢复管理器
        
    Returns:
        装饰器函数
    """
    if config is None:
        config = RetryConfig()
    
    return EnhancedRetryDecorator(config, recovery_manager)


def create_file_operation_recovery() -> ErrorRecoveryManager:
    """创建文件操作错误恢复管理器
    
    Returns:
        ErrorRecoveryManager: 配置好的错误恢复管理器
    """
    recovery_manager = ErrorRecoveryManager()
    
    # 文件不存在错误恢复
    def recover_file_not_found(exception: FileNotFoundError, context: ErrorContext) -> bool:
        """恢复文件不存在错误"""
        if context.file_path:
            # 尝试在常见位置查找文件
            import os
            from pathlib import Path
            
            file_path = Path(context.file_path)
            search_dirs = [
                file_path.parent,
                Path.cwd(),
                Path.home() / 'Documents',
                Path.home() / 'Downloads'
            ]
            
            for search_dir in search_dirs:
                potential_file = search_dir / file_path.name
                if potential_file.exists():
                    # 更新上下文中的文件路径
                    context.file_path = str(potential_file)
                    return True
        
        return False
    
    # 权限错误恢复
    def recover_permission_error(exception: PermissionError, context: ErrorContext) -> bool:
        """恢复权限错误"""
        if context.file_path:
            import os
            import stat
            
            try:
                # 尝试修改文件权限
                file_path = context.file_path
                current_permissions = os.stat(file_path).st_mode
                os.chmod(file_path, current_permissions | stat.S_IREAD | stat.S_IWRITE)
                return True
            except Exception:
                pass
        
        return False
    
    # 磁盘空间不足错误恢复
    def recover_disk_space_error(exception: OSError, context: ErrorContext) -> bool:
        """恢复磁盘空间不足错误"""
        if "No space left on device" in str(exception) or "disk full" in str(exception).lower():
            # 尝试清理临时文件
            import tempfile
            import shutil
            
            try:
                temp_dir = tempfile.gettempdir()
                # 清理临时文件（这里只是示例，实际应该更谨慎）
                for temp_file in Path(temp_dir).glob('docuflow_*'):
                    if temp_file.is_file():
                        temp_file.unlink()
                return True
            except Exception:
                pass
        
        return False
    
    # 注册恢复策略
    recovery_manager.register_recovery_strategy(FileNotFoundError, recover_file_not_found)
    recovery_manager.register_recovery_strategy(PermissionError, recover_permission_error)
    recovery_manager.register_recovery_strategy(OSError, recover_disk_space_error)
    
    return recovery_manager


def create_conversion_recovery() -> ErrorRecoveryManager:
    """创建转换操作错误恢复管理器
    
    Returns:
        ErrorRecoveryManager: 配置好的错误恢复管理器
    """
    recovery_manager = ErrorRecoveryManager()
    
    # 导入转换相关异常
    try:
        from exceptions import ConversionError, UnsupportedFormatError
    except ImportError:
        # 如果无法导入，定义基本异常类
        class ConversionError(Exception):
            pass
        
        class UnsupportedFormatError(Exception):
            pass
    
    # 转换错误恢复
    def recover_conversion_error(exception: ConversionError, context: ErrorContext) -> bool:
        """恢复转换错误"""
        # 尝试使用备用转换方法
        if context.input_format and context.output_format:
            # 这里可以实现备用转换逻辑
            # 例如：如果pandoc失败，尝试使用其他转换工具
            pass
        
        return False
    
    # 不支持格式错误恢复
    def recover_unsupported_format(exception: UnsupportedFormatError, context: ErrorContext) -> bool:
        """恢复不支持格式错误"""
        # 尝试格式转换或建议替代格式
        if context.input_format:
            # 建议相似的支持格式
            format_suggestions = {
                '.docx': ['.doc', '.rtf', '.txt'],
                '.xlsx': ['.xls', '.csv', '.txt'],
                '.pptx': ['.ppt', '.pdf']
            }
            
            suggestions = format_suggestions.get(context.input_format, [])
            if suggestions:
                # 记录建议
                recovery_manager.logger.info(
                    'format_suggestions_available',
                    original_format=context.input_format,
                    suggestions=suggestions
                )
        
        return False
    
    # 注册恢复策略
    recovery_manager.register_recovery_strategy(ConversionError, recover_conversion_error)
    recovery_manager.register_recovery_strategy(UnsupportedFormatError, recover_unsupported_format)
    
    return recovery_manager


# 全局错误恢复管理器实例
_global_file_recovery_manager = None
_global_conversion_recovery_manager = None


def get_file_recovery_manager() -> ErrorRecoveryManager:
    """获取文件操作错误恢复管理器
    
    Returns:
        ErrorRecoveryManager: 文件操作错误恢复管理器
    """
    global _global_file_recovery_manager
    
    if _global_file_recovery_manager is None:
        _global_file_recovery_manager = create_file_operation_recovery()
    
    return _global_file_recovery_manager


def get_conversion_recovery_manager() -> ErrorRecoveryManager:
    """获取转换操作错误恢复管理器
    
    Returns:
        ErrorRecoveryManager: 转换操作错误恢复管理器
    """
    global _global_conversion_recovery_manager
    
    if _global_conversion_recovery_manager is None:
        _global_conversion_recovery_manager = create_conversion_recovery()
    
    return _global_conversion_recovery_manager


# 便捷装饰器
def robust_file_operation(max_attempts: int = 3, base_delay: float = 1.0):
    """文件操作健壮性装饰器
    
    Args:
        max_attempts: 最大重试次数
        base_delay: 基础延迟时间
        
    Returns:
        装饰器函数
    """
    config = RetryConfig(
        max_attempts=max_attempts,
        base_delay=base_delay,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        exceptions=(FileNotFoundError, PermissionError, OSError)
    )
    
    return retry_with_recovery(config, get_file_recovery_manager())


def robust_conversion_operation(max_attempts: int = 2, base_delay: float = 2.0):
    """转换操作健壮性装饰器
    
    Args:
        max_attempts: 最大重试次数
        base_delay: 基础延迟时间
        
    Returns:
        装饰器函数
    """
    try:
        from exceptions import ConversionError, UnsupportedFormatError, FileSizeError
        exceptions = (ConversionError, UnsupportedFormatError, FileSizeError)
    except ImportError:
        exceptions = (Exception,)
    
    config = RetryConfig(
        max_attempts=max_attempts,
        base_delay=base_delay,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        exceptions=exceptions
    )
    
    return retry_with_recovery(config, get_conversion_recovery_manager())


# 便捷函数别名
def enhanced_retry(max_attempts: int = 3, delay: float = 1.0, 
                  strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF,
                  exceptions: Tuple[Type[Exception], ...] = (Exception,)):
    """增强重试装饰器（便捷函数）
    
    Args:
        max_attempts: 最大重试次数
        delay: 基础延迟时间
        strategy: 重试策略
        exceptions: 需要重试的异常类型
        
    Returns:
        装饰器函数
    """
    config = RetryConfig(
        max_attempts=max_attempts,
        base_delay=delay,
        strategy=strategy,
        exceptions=exceptions
    )
    
    return retry_with_recovery(config)