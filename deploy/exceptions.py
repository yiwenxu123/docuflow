# -*- coding: utf-8 -*-
"""
DocuFlow 异常处理模块
定义统一的异常类型和错误处理机制
"""

import logging
from typing import Optional, Any

class DocuFlowException(Exception):
    """DocuFlow自定义异常基类"""
    
    def __init__(self, message: str, error_code: str = None, details: Any = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details
        
        # 记录异常日志
        logging.error(f"[{self.error_code}] {self.message}", extra={'details': self.details})
    
    def __str__(self) -> str:
        return f"[{self.error_code}] {self.message}"
    
    def to_dict(self) -> dict:
        """转换为字典格式，便于序列化"""
        return {
            'error_code': self.error_code,
            'message': self.message,
            'details': self.details,
            'exception_type': self.__class__.__name__
        }

class ConversionError(DocuFlowException):
    """文档转换错误"""
    pass

class FileAccessError(DocuFlowException):
    """文件访问错误"""
    pass

class UnsupportedFormatError(DocuFlowException):
    """不支持的文件格式错误"""
    pass

class FileSizeError(DocuFlowException):
    """文件大小超限错误"""
    pass

class ConfigurationError(DocuFlowException):
    """配置错误"""
    pass

class ValidationError(DocuFlowException):
    """验证错误"""
    pass

class NetworkError(DocuFlowException):
    """网络错误"""
    pass

class PermissionError(DocuFlowException):
    """权限错误"""
    pass

class TimeoutError(DocuFlowException):
    """超时错误"""
    pass

class ErrorHandler:
    """错误处理器"""
    
    @staticmethod
    def handle_file_error(file_path: str, operation: str, original_error: Exception) -> DocuFlowException:
        """处理文件相关错误"""
        if isinstance(original_error, FileNotFoundError):
            return FileAccessError(
                f"文件不存在: {file_path}",
                error_code="FILE_NOT_FOUND",
                details={'file_path': file_path, 'operation': operation}
            )
        elif isinstance(original_error, PermissionError):
            return PermissionError(
                f"没有权限访问文件: {file_path}",
                error_code="PERMISSION_DENIED",
                details={'file_path': file_path, 'operation': operation}
            )
        elif isinstance(original_error, OSError):
            return FileAccessError(
                f"文件系统错误: {str(original_error)}",
                error_code="FILE_SYSTEM_ERROR",
                details={'file_path': file_path, 'operation': operation, 'os_error': str(original_error)}
            )
        else:
            return FileAccessError(
                f"文件操作失败: {str(original_error)}",
                error_code="FILE_OPERATION_ERROR",
                details={'file_path': file_path, 'operation': operation, 'original_error': str(original_error)}
            )
    
    @staticmethod
    def handle_conversion_error(file_path: str, output_format: str, original_error: Exception) -> ConversionError:
        """处理转换相关错误"""
        return ConversionError(
            f"转换失败: {file_path} -> {output_format}",
            error_code="CONVERSION_FAILED",
            details={
                'file_path': file_path,
                'output_format': output_format,
                'original_error': str(original_error),
                'error_type': type(original_error).__name__
            }
        )
    
    @staticmethod
    def handle_validation_error(field: str, value: Any, reason: str) -> ValidationError:
        """处理验证错误"""
        return ValidationError(
            f"验证失败: {field} = {value}, 原因: {reason}",
            error_code="VALIDATION_FAILED",
            details={'field': field, 'value': value, 'reason': reason}
        )
    
    @staticmethod
    def handle_config_error(config_key: str, config_value: Any, reason: str) -> ConfigurationError:
        """处理配置错误"""
        return ConfigurationError(
            f"配置错误: {config_key} = {config_value}, 原因: {reason}",
            error_code="CONFIG_ERROR",
            details={'config_key': config_key, 'config_value': config_value, 'reason': reason}
        )

def safe_execute(func, *args, **kwargs):
    """安全执行函数，自动处理异常"""
    try:
        return func(*args, **kwargs), None
    except DocuFlowException as e:
        return None, e
    except Exception as e:
        # 将未知异常包装为DocuFlowException
        wrapped_error = DocuFlowException(
            f"未知错误: {str(e)}",
            error_code="UNKNOWN_ERROR",
            details={'original_error': str(e), 'error_type': type(e).__name__}
        )
        return None, wrapped_error

def log_exception(func):
    """异常日志装饰器"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.exception(f"函数 {func.__name__} 执行失败")
            raise
    return wrapper

def retry_on_error(max_retries: int = 3, delay: float = 1.0, exceptions: tuple = (Exception,)):
    """重试装饰器"""
    import time
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logging.warning(f"函数 {func.__name__} 第 {attempt + 1} 次尝试失败，{delay}秒后重试: {str(e)}")
                        time.sleep(delay)
                    else:
                        logging.error(f"函数 {func.__name__} 在 {max_retries} 次重试后仍然失败")
            
            raise last_exception
        return wrapper
    return decorator