#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DocuFlow - 配置管理模块
提供统一的配置加载、验证和管理功能
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass, field
from utils.logger import get_logger


@dataclass
class ConversionConfig:
    """转换相关配置"""
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    max_batch_size: int = 50
    timeout_seconds: int = 300
    temp_dir: Optional[str] = None
    pandoc_path: Optional[str] = None
    enable_ocr: bool = False
    ocr_language: str = 'chi_sim+eng'
    quality_settings: Dict[str, Any] = field(default_factory=lambda: {
        'pdf_dpi': 300,
        'image_quality': 85,
        'compression_level': 6
    })
    # 新增字段以支持配置文件
    supported_input_formats: List[str] = field(default_factory=lambda: [
        '.pdf', '.docx', '.doc', '.txt', '.md', '.html', '.htm', '.rtf', '.odt'
    ])
    supported_output_formats: List[str] = field(default_factory=lambda: [
        '.md', '.html', '.pdf', '.txt', '.docx'
    ])
    default_output_format: str = '.md'
    max_file_size_mb: Optional[int] = None
    temp_directory: Optional[str] = None
    output_directory: Optional[str] = None
    preserve_structure: bool = True
    command_timeout: int = 30
    pandoc_extra_args: List[str] = field(default_factory=list)  # 命令超时时间（秒）
    
    def __post_init__(self):
        # 兼容性处理
        if self.max_file_size_mb is not None:
            self.max_file_size = self.max_file_size_mb * 1024 * 1024
        if self.temp_directory is not None:
            self.temp_dir = self.temp_directory


@dataclass
class LoggingConfig:
    """日志相关配置"""
    level: str = 'INFO'
    file_path: Optional[str] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    enable_structured_logging: bool = True
    log_performance: bool = True
    # 新增字段以支持配置文件
    console_output: bool = True
    file_output: bool = True
    max_file_size_mb: Optional[int] = None
    structured_logging: Optional[bool] = None
    rotation: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        # 兼容性处理
        if self.max_file_size_mb is not None:
            self.max_file_size = self.max_file_size_mb * 1024 * 1024
        if self.structured_logging is not None:
            self.enable_structured_logging = self.structured_logging


@dataclass
class SecurityConfig:
    """安全相关配置"""
    allowed_extensions: List[str] = field(default_factory=lambda: [
        '.pdf', '.docx', '.doc', '.txt', '.md', '.html', '.htm', '.rtf', '.odt'
    ])
    blocked_extensions: List[str] = field(default_factory=lambda: [
        '.exe', '.bat', '.cmd', '.sh', '.ps1', '.scr', '.com', '.pif'
    ])
    max_path_length: int = 260
    scan_for_malware: bool = False
    quarantine_suspicious_files: bool = False


@dataclass
class PerformanceConfig:
    """性能相关配置"""
    max_workers: int = 4
    chunk_size: int = 8192
    memory_limit_mb: int = 512
    cache_enabled: bool = True
    cache_size_mb: int = 100
    enable_compression: bool = True
    parallel_processing: bool = True
    # 新增字段以支持配置文件
    cache_ttl: int = 3600  # 缓存生存时间（秒）
    monitoring: Optional[Dict[str, Any]] = None
    optimization: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        # 兼容性处理
        if self.monitoring is None:
            self.monitoring = {}
        if self.optimization is None:
            self.optimization = {}


@dataclass
class UIConfig:
    """用户界面相关配置"""
    theme: str = 'light'
    language: str = 'zh_CN'
    window_size: tuple = (1200, 800)
    auto_save_settings: bool = True
    show_progress_details: bool = True
    enable_notifications: bool = True


@dataclass
class AppConfig:
    """应用程序主配置"""
    version: str = '1.0.0'
    debug: bool = False
    conversion: ConversionConfig = field(default_factory=ConversionConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    
    @property
    def COMMAND_TIMEOUT(self) -> int:
        """获取命令超时时间"""
        return getattr(self.conversion, 'command_timeout', 30)
    
    @property
    def SUPPORTED_CONVERSIONS(self) -> Dict[str, List[str]]:
        """获取支持的转换格式映射"""
        return {
            '.md': ['.html', '.pdf', '.docx', '.txt'],
            '.html': ['.md', '.pdf', '.txt', '.docx'],
            '.txt': ['.md', '.html', '.pdf', '.docx'],
            '.docx': ['.md', '.html', '.pdf', '.txt'],
            '.pdf': ['.md', '.html', '.txt'],
            '.htm': ['.md', '.pdf', '.txt', '.docx'],
            '.xlsx': ['.html', '.docx', '.md', '.txt'],
            '.xls': ['.html', '.docx', '.md', '.txt']
        }
    
    def __post_init__(self):
        """配置初始化后的验证"""
        self._validate_config()
    
    def _validate_config(self) -> None:
        """验证配置的有效性"""
        # 验证文件大小限制
        if self.conversion.max_file_size <= 0:
            raise ValueError("max_file_size must be positive")
        
        # 验证批处理大小
        if self.conversion.max_batch_size <= 0:
            raise ValueError("max_batch_size must be positive")
        
        # 验证超时设置
        if self.conversion.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        
        # 验证工作线程数
        if self.performance.max_workers <= 0:
            raise ValueError("max_workers must be positive")
        
        # 验证内存限制
        if self.performance.memory_limit_mb <= 0:
            raise ValueError("memory_limit_mb must be positive")


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_dir: Optional[str] = None):
        """初始化配置管理器
        
        Args:
            config_dir: 配置文件目录，如果为None则使用默认目录
        """
        self.logger = get_logger('config_manager')
        self.config_dir = Path(config_dir) if config_dir else self._get_default_config_dir()
        self.config_file = self.config_dir / 'config.yaml'
        self.user_config_file = self.config_dir / 'user_config.yaml'
        
        # 确保配置目录存在
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载配置
        self._config = self._load_config()
        
        self.logger.info(
            'config_manager_initialized',
            config_dir=str(self.config_dir),
            config_file=str(self.config_file)
        )
    
    def _get_default_config_dir(self) -> Path:
        """获取默认配置目录"""
        if os.name == 'nt':  # Windows
            config_dir = Path(os.environ.get('APPDATA', '')) / 'DocuFlow'
        else:  # Unix-like
            config_dir = Path.home() / '.config' / 'docuflow'
        
        return config_dir
    
    def _load_config(self) -> AppConfig:
        """加载配置"""
        try:
            # 首先尝试加载用户配置
            if self.user_config_file.exists():
                config_data = self._load_yaml_file(self.user_config_file)
                self.logger.info('user_config_loaded', file=str(self.user_config_file))
            elif self.config_file.exists():
                config_data = self._load_yaml_file(self.config_file)
                self.logger.info('default_config_loaded', file=str(self.config_file))
            else:
                # 使用默认配置并保存
                config_data = {}
                self._save_default_config()
                self.logger.info('default_config_created')
            
            # 创建配置对象
            return self._create_config_from_dict(config_data)
            
        except Exception as e:
            self.logger.error(
                'config_load_failed',
                error=str(e),
                error_type=type(e).__name__
            )
            # 返回默认配置
            return AppConfig()
    
    def _load_yaml_file(self, file_path: Path) -> Dict[str, Any]:
        """加载YAML文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            self.logger.error(
                'yaml_parse_error',
                file=str(file_path),
                error=str(e)
            )
            return {}
    
    def _create_config_from_dict(self, config_data: Dict[str, Any]) -> AppConfig:
        """从字典创建配置对象"""
        try:
            # 递归合并配置
            merged_config = self._merge_with_defaults(config_data)
            
            # 创建配置对象
            return AppConfig(
                version=merged_config.get('version', '1.0.0'),
                debug=merged_config.get('debug', False),
                conversion=ConversionConfig(**merged_config.get('conversion', {})),
                logging=LoggingConfig(**merged_config.get('logging', {})),
                security=SecurityConfig(**merged_config.get('security', {})),
                performance=PerformanceConfig(**merged_config.get('performance', {})),
                ui=UIConfig(**merged_config.get('ui', {}))
            )
        except Exception as e:
            self.logger.error(
                'config_creation_failed',
                error=str(e),
                error_type=type(e).__name__
            )
            return AppConfig()
    
    def _merge_with_defaults(self, user_config: Dict[str, Any]) -> Dict[str, Any]:
        """将用户配置与默认配置合并"""
        default_config = self._get_default_config_dict()
        return self._deep_merge(default_config, user_config)
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """深度合并两个字典"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _get_default_config_dict(self) -> Dict[str, Any]:
        """获取默认配置字典"""
        default_config = AppConfig()
        return {
            'version': default_config.version,
            'debug': default_config.debug,
            'conversion': {
                'max_file_size': default_config.conversion.max_file_size,
                'max_batch_size': default_config.conversion.max_batch_size,
                'timeout_seconds': default_config.conversion.timeout_seconds,
                'temp_dir': default_config.conversion.temp_dir,
                'pandoc_path': default_config.conversion.pandoc_path,
                'enable_ocr': default_config.conversion.enable_ocr,
                'ocr_language': default_config.conversion.ocr_language,
                'quality_settings': default_config.conversion.quality_settings
            },
            'logging': {
                'level': default_config.logging.level,
                'file_path': default_config.logging.file_path,
                'max_file_size': default_config.logging.max_file_size,
                'backup_count': default_config.logging.backup_count,
                'format': default_config.logging.format,
                'enable_structured_logging': default_config.logging.enable_structured_logging,
                'log_performance': default_config.logging.log_performance
            },
            'security': {
                'allowed_extensions': default_config.security.allowed_extensions,
                'blocked_extensions': default_config.security.blocked_extensions,
                'max_path_length': default_config.security.max_path_length,
                'scan_for_malware': default_config.security.scan_for_malware,
                'quarantine_suspicious_files': default_config.security.quarantine_suspicious_files
            },
            'performance': {
                'max_workers': default_config.performance.max_workers,
                'chunk_size': default_config.performance.chunk_size,
                'memory_limit_mb': default_config.performance.memory_limit_mb,
                'cache_enabled': default_config.performance.cache_enabled,
                'cache_size_mb': default_config.performance.cache_size_mb,
                'enable_compression': default_config.performance.enable_compression,
                'parallel_processing': default_config.performance.parallel_processing
            },
            'ui': {
                'theme': default_config.ui.theme,
                'language': default_config.ui.language,
                'window_size': default_config.ui.window_size,
                'auto_save_settings': default_config.ui.auto_save_settings,
                'show_progress_details': default_config.ui.show_progress_details,
                'enable_notifications': default_config.ui.enable_notifications
            }
        }
    
    def _save_default_config(self) -> None:
        """保存默认配置到文件"""
        try:
            config_dict = self._get_default_config_dict()
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
            
            self.logger.info('default_config_saved', file=str(self.config_file))
        except Exception as e:
            self.logger.error(
                'config_save_failed',
                file=str(self.config_file),
                error=str(e)
            )
    
    def save_user_config(self, config: Optional[AppConfig] = None) -> bool:
        """保存用户配置
        
        Args:
            config: 要保存的配置，如果为None则保存当前配置
            
        Returns:
            bool: 是否保存成功
        """
        try:
            config_to_save = config or self._config
            config_dict = self._config_to_dict(config_to_save)
            
            with open(self.user_config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
            
            self.logger.info('user_config_saved', file=str(self.user_config_file))
            return True
            
        except Exception as e:
            self.logger.error(
                'user_config_save_failed',
                file=str(self.user_config_file),
                error=str(e)
            )
            return False
    
    def _config_to_dict(self, config: AppConfig) -> Dict[str, Any]:
        """将配置对象转换为字典"""
        return {
            'version': config.version,
            'debug': config.debug,
            'conversion': {
                'max_file_size': config.conversion.max_file_size,
                'max_batch_size': config.conversion.max_batch_size,
                'timeout_seconds': config.conversion.timeout_seconds,
                'temp_dir': config.conversion.temp_dir,
                'pandoc_path': config.conversion.pandoc_path,
                'enable_ocr': config.conversion.enable_ocr,
                'ocr_language': config.conversion.ocr_language,
                'quality_settings': config.conversion.quality_settings
            },
            'logging': {
                'level': config.logging.level,
                'file_path': config.logging.file_path,
                'max_file_size': config.logging.max_file_size,
                'backup_count': config.logging.backup_count,
                'format': config.logging.format,
                'enable_structured_logging': config.logging.enable_structured_logging,
                'log_performance': config.logging.log_performance
            },
            'security': {
                'allowed_extensions': config.security.allowed_extensions,
                'blocked_extensions': config.security.blocked_extensions,
                'max_path_length': config.security.max_path_length,
                'scan_for_malware': config.security.scan_for_malware,
                'quarantine_suspicious_files': config.security.quarantine_suspicious_files
            },
            'performance': {
                'max_workers': config.performance.max_workers,
                'chunk_size': config.performance.chunk_size,
                'memory_limit_mb': config.performance.memory_limit_mb,
                'cache_enabled': config.performance.cache_enabled,
                'cache_size_mb': config.performance.cache_size_mb,
                'enable_compression': config.performance.enable_compression,
                'parallel_processing': config.performance.parallel_processing
            },
            'ui': {
                'theme': config.ui.theme,
                'language': config.ui.language,
                'window_size': list(config.ui.window_size),
                'auto_save_settings': config.ui.auto_save_settings,
                'show_progress_details': config.ui.show_progress_details,
                'enable_notifications': config.ui.enable_notifications
            }
        }
    
    def get_config(self) -> AppConfig:
        """获取当前配置"""
        return self._config
    
    @property
    def COMMAND_TIMEOUT(self) -> int:
        """获取命令超时时间"""
        return self._config.COMMAND_TIMEOUT
    
    @property
    def SUPPORTED_CONVERSIONS(self) -> Dict[str, List[str]]:
        """获取支持的转换格式映射"""
        return self._config.SUPPORTED_CONVERSIONS
    
    def update_config(self, **kwargs) -> bool:
        """更新配置
        
        Args:
            **kwargs: 要更新的配置项
            
        Returns:
            bool: 是否更新成功
        """
        try:
            # 创建新的配置对象
            config_dict = self._config_to_dict(self._config)
            
            # 更新配置
            for key, value in kwargs.items():
                if '.' in key:
                    # 支持嵌套键，如 'conversion.max_file_size'
                    keys = key.split('.')
                    current = config_dict
                    for k in keys[:-1]:
                        if k not in current:
                            current[k] = {}
                        current = current[k]
                    current[keys[-1]] = value
                else:
                    config_dict[key] = value
            
            # 验证并创建新配置
            new_config = self._create_config_from_dict(config_dict)
            self._config = new_config
            
            self.logger.info('config_updated', updated_keys=list(kwargs.keys()))
            return True
            
        except Exception as e:
            self.logger.error(
                'config_update_failed',
                error=str(e),
                error_type=type(e).__name__
            )
            return False
    
    def reset_to_defaults(self) -> bool:
        """重置为默认配置
        
        Returns:
            bool: 是否重置成功
        """
        try:
            self._config = AppConfig()
            self.logger.info('config_reset_to_defaults')
            return True
        except Exception as e:
            self.logger.error(
                'config_reset_failed',
                error=str(e)
            )
            return False
    
    def validate_config(self) -> List[str]:
        """验证当前配置
        
        Returns:
            list: 验证错误列表，空列表表示验证通过
        """
        errors = []
        
        try:
            # 验证配置对象
            self._config._validate_config()
        except ValueError as e:
            errors.append(str(e))
        
        # 额外的验证逻辑
        if self._config.conversion.pandoc_path:
            pandoc_path = Path(self._config.conversion.pandoc_path)
            if not pandoc_path.exists():
                errors.append(f"Pandoc path does not exist: {pandoc_path}")
        
        if self._config.conversion.temp_dir:
            temp_dir = Path(self._config.conversion.temp_dir)
            if not temp_dir.exists():
                try:
                    temp_dir.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    errors.append(f"Cannot create temp directory: {e}")
        
        return errors
    
    def export_config(self, file_path: str, format: str = 'yaml') -> bool:
        """导出配置到文件
        
        Args:
            file_path: 导出文件路径
            format: 导出格式 ('yaml' 或 'json')
            
        Returns:
            bool: 是否导出成功
        """
        try:
            config_dict = self._config_to_dict(self._config)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                if format.lower() == 'json':
                    json.dump(config_dict, f, indent=2, ensure_ascii=False)
                else:
                    yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
            
            self.logger.info(
                'config_exported',
                file=file_path,
                format=format
            )
            return True
            
        except Exception as e:
            self.logger.error(
                'config_export_failed',
                file=file_path,
                format=format,
                error=str(e)
            )
            return False
    
    def import_config(self, file_path: str) -> bool:
        """从文件导入配置
        
        Args:
            file_path: 配置文件路径
            
        Returns:
            bool: 是否导入成功
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                self.logger.error('config_import_file_not_found', file=str(file_path))
                return False
            
            # 根据文件扩展名确定格式
            if file_path.suffix.lower() == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
            else:
                config_data = self._load_yaml_file(file_path)
            
            # 创建新配置
            new_config = self._create_config_from_dict(config_data)
            self._config = new_config
            
            self.logger.info('config_imported', file=str(file_path))
            return True
            
        except Exception as e:
            self.logger.error(
                'config_import_failed',
                file=str(file_path),
                error=str(e)
            )
            return False


# 全局配置管理器实例
_global_config_manager = None


def get_config_manager(config_dir: Optional[str] = None) -> ConfigManager:
    """获取全局配置管理器实例
    
    Args:
        config_dir: 配置目录
        
    Returns:
        ConfigManager: 配置管理器实例
    """
    global _global_config_manager
    
    if _global_config_manager is None:
        _global_config_manager = ConfigManager(config_dir)
    
    return _global_config_manager


def get_config() -> AppConfig:
    """获取当前应用配置
    
    Returns:
        AppConfig: 应用配置对象
    """
    return get_config_manager().get_config()


# 为ConfigManager类添加load_from_file方法（作为import_config的别名）
def _add_load_from_file_method():
    """为ConfigManager类添加load_from_file方法"""
    def load_from_file(self, file_path: str) -> bool:
        """从文件加载配置（import_config的别名）
        
        Args:
            file_path: 配置文件路径
            
        Returns:
            bool: 是否加载成功
        """
        return self.import_config(file_path)
    
    # 将方法添加到ConfigManager类
    ConfigManager.load_from_file = load_from_file

# 执行方法添加
_add_load_from_file_method()