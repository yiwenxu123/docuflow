#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DocuFlow - 增强版启动脚本
集成了所有新功能和改进
"""

import sys
import os
import argparse
import signal
import atexit
from pathlib import Path
from typing import Optional, List, Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    # 导入核心模块
    from converter.document_converter import DocumentConverter
    from utils.logger import get_logger, StructuredLogger
    from utils.config_manager import ConfigManager
    from utils.error_handler import ErrorRecoveryManager, enhanced_retry
    from utils.performance import PerformanceMonitor, CacheManager
    
    # 导入GUI模块（如果可用）
    try:
        from gui.main_window import MainWindow
        GUI_AVAILABLE = True
    except ImportError:
        GUI_AVAILABLE = False
        print("警告: GUI模块不可用，将以命令行模式运行")
    
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保所有依赖都已正确安装")
    sys.exit(1)


class DocuFlowApp:
    """DocuFlow应用主类"""
    
    def __init__(self):
        self.logger: Optional[StructuredLogger] = None
        self.config_manager: Optional[ConfigManager] = None
        self.converter: Optional[DocumentConverter] = None
        self.performance_monitor: Optional[PerformanceMonitor] = None
        self.cache_manager: Optional[CacheManager] = None
        self.error_manager: Optional[ErrorRecoveryManager] = None
        self.gui_app = None
        
        # 注册清理函数
        atexit.register(self.cleanup)
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def initialize(self, config_path: Optional[str] = None) -> bool:
        """初始化应用"""
        try:
            # 1. 初始化配置管理器
            self.config_manager = ConfigManager()
            
            if config_path and Path(config_path).exists():
                self.config_manager.load_from_file(config_path)
            else:
                # 尝试加载默认配置
                default_config_path = project_root / "config" / "app_config.yaml"
                if default_config_path.exists():
                    self.config_manager.load_from_file(str(default_config_path))
                else:
                    print("使用默认配置")
            
            config = self.config_manager.get_config()
            
            # 2. 初始化日志系统
            self.logger = get_logger("DocuFlowApp")
            self.logger.info("应用启动", extra={
                "version": config.version,
                "debug_mode": config.debug,
                "config_path": config_path or "default"
            })
            
            # 4. 初始化性能监控
            self.performance_monitor = PerformanceMonitor()
            
            # 5. 初始化缓存管理器
            if config.performance.cache_enabled:
                self.cache_manager = CacheManager(
                    max_size_mb=config.performance.cache_size_mb
                )
            
            # 6. 初始化错误管理器
            self.error_manager = ErrorRecoveryManager()
            
            # 7. 初始化文档转换器
            self.converter = DocumentConverter(config)
            
            self.logger.info("应用初始化完成")
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error("应用初始化失败", extra={"error": str(e)})
            else:
                print(f"应用初始化失败: {e}")
            self.cleanup()
            return False
    
    def run_gui(self) -> int:
        """运行GUI模式"""
        if not GUI_AVAILABLE:
            self.logger.error("GUI不可用")
            return 1
        
        try:
            from PyQt5.QtWidgets import QApplication
            
            # 创建Qt应用
            app = QApplication(sys.argv)
            app.setApplicationName("DocuFlow")
            app.setApplicationVersion(self.config_manager.get_config().version)
            
            # 创建主窗口
            main_window = MainWindow(
                converter=self.converter,
                config_manager=self.config_manager,
                logger=self.logger
            )
            
            # 应用主题
            config = self.config_manager.get_config()
            if config.ui.theme != "auto":
                self._apply_theme(app, config.ui.theme)
            
            main_window.show()
            
            self.logger.info("GUI模式启动")
            return app.exec_()
            
        except Exception as e:
            self.logger.error("GUI启动失败", extra={"error": str(e)})
            return 1
    
    def run_cli(self, args: argparse.Namespace) -> int:
        """运行命令行模式"""
        try:
            self.logger.info("CLI模式启动", extra={"args": vars(args)})
            
            if args.command == "convert":
                return self._handle_convert_command(args)
            elif args.command == "batch":
                return self._handle_batch_command(args)
            elif args.command == "test":
                return self._handle_test_command(args)
            elif args.command == "config":
                return self._handle_config_command(args)
            elif args.command == "stats":
                return self._handle_stats_command(args)
            else:
                self.logger.error("未知命令", extra={"command": args.command})
                return 1
                
        except Exception as e:
            self.logger.error("CLI执行失败", extra={"error": str(e)})
            return 1
    
    @enhanced_retry(max_attempts=3, delay=1.0)
    def _handle_convert_command(self, args: argparse.Namespace) -> int:
        """处理单文件转换命令"""
        input_file = Path(args.input)
        if not input_file.exists():
            self.logger.error("输入文件不存在", extra={"file": str(input_file)})
            return 1
        
        output_dir = Path(args.output) if args.output else input_file.parent
        output_format = args.format or ".md"
        
        try:
            with self.performance_monitor.start_monitoring("single_conversion"):
                output_file = self.converter.convert_file(
                    str(input_file),
                    output_format,
                    str(output_dir)
                )
            
            self.logger.info("转换完成", extra={
                "input_file": str(input_file),
                "output_file": output_file,
                "format": output_format
            })
            
            print(f"转换完成: {output_file}")
            return 0
            
        except Exception as e:
            self.logger.error("转换失败", extra={
                "input_file": str(input_file),
                "error": str(e)
            })
            print(f"转换失败: {e}")
            return 1
    
    def _handle_batch_command(self, args: argparse.Namespace) -> int:
        """处理批量转换命令"""
        input_dir = Path(args.input)
        if not input_dir.exists():
            self.logger.error("输入目录不存在", extra={"dir": str(input_dir)})
            return 1
        
        # 查找所有支持的文件
        config = self.config_manager.get_config()
        supported_formats = config.conversion.supported_input_formats
        
        input_files = []
        for format_ext in supported_formats:
            input_files.extend(input_dir.glob(f"**/*{format_ext}"))
        
        if not input_files:
            self.logger.warning("未找到支持的文件", extra={"dir": str(input_dir)})
            print("未找到支持的文件")
            return 0
        
        output_dir = Path(args.output) if args.output else input_dir / "converted"
        output_format = args.format or ".md"
        
        try:
            def progress_callback(current: int, total: int, file_path: str, status: str):
                print(f"进度: {current}/{total} - {Path(file_path).name} - {status}")
            
            with self.performance_monitor.start_monitoring("batch_conversion"):
                output_files = self.converter.batch_convert(
                    [str(f) for f in input_files],
                    output_format,
                    str(output_dir),
                    progress_callback=progress_callback
                )
            
            self.logger.info("批量转换完成", extra={
                "input_count": len(input_files),
                "output_count": len(output_files),
                "format": output_format
            })
            
            print(f"批量转换完成: {len(output_files)}/{len(input_files)} 个文件")
            return 0
            
        except Exception as e:
            self.logger.error("批量转换失败", extra={"error": str(e)})
            print(f"批量转换失败: {e}")
            return 1
    
    def _handle_test_command(self, args: argparse.Namespace) -> int:
        """处理测试命令"""
        try:
            import unittest
            from tests.test_document_converter import (
                TestDocumentConverterBasic,
                TestDocumentConverterFormats,
                TestDocumentConverterEdgeCases
            )
            
            # 创建测试套件
            suite = unittest.TestSuite()
            
            if args.type == "basic" or args.type == "all":
                suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestDocumentConverterBasic))
            
            if args.type == "formats" or args.type == "all":
                suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestDocumentConverterFormats))
            
            if args.type == "edge" or args.type == "all":
                suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestDocumentConverterEdgeCases))
            
            # 运行测试
            runner = unittest.TextTestRunner(verbosity=2)
            result = runner.run(suite)
            
            # 记录测试结果
            self.logger.info("测试完成", extra={
                "tests_run": result.testsRun,
                "failures": len(result.failures),
                "errors": len(result.errors),
                "success_rate": (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
            })
            
            return 0 if result.wasSuccessful() else 1
            
        except Exception as e:
            self.logger.error("测试执行失败", extra={"error": str(e)})
            print(f"测试执行失败: {e}")
            return 1
    
    def _handle_config_command(self, args: argparse.Namespace) -> int:
        """处理配置命令"""
        try:
            if args.config_action == "show":
                config = self.config_manager.get_config()
                print("当前配置:")
                print(f"  应用版本: {config.version}")
                print(f"  调试模式: {config.debug}")
                print(f"  日志级别: {config.logging.level}")
                print(f"  最大文件大小: {config.conversion.max_file_size // (1024*1024)}MB")
                print(f"  支持的输入格式: {', '.join(config.conversion.supported_input_formats)}")
                print(f"  支持的输出格式: {', '.join(config.conversion.supported_output_formats)}")
            
            elif args.config_action == "export":
                output_file = args.output or "config_export.yaml"
                self.config_manager.export_config(output_file)
                print(f"配置已导出到: {output_file}")
            
            elif args.config_action == "validate":
                is_valid, errors = self.config_manager.validate_config()
                if is_valid:
                    print("配置验证通过")
                else:
                    print("配置验证失败:")
                    for error in errors:
                        print(f"  - {error}")
                    return 1
            
            return 0
            
        except Exception as e:
            self.logger.error("配置操作失败", extra={"error": str(e)})
            print(f"配置操作失败: {e}")
            return 1
    
    def _handle_stats_command(self, args: argparse.Namespace) -> int:
        """处理统计命令"""
        try:
            # 转换器统计
            converter_stats = self.converter.get_stats()
            print("转换器统计:")
            for key, value in converter_stats.items():
                print(f"  {key}: {value}")
            
            # 性能统计
            if self.performance_monitor:
                perf_stats = self.performance_monitor.get_stats()
                print("\n性能统计:")
                for operation, metrics in perf_stats.items():
                    print(f"  {operation}:")
                    print(f"    调用次数: {metrics.call_count}")
                    print(f"    总耗时: {metrics.total_time:.2f}s")
                    print(f"    平均耗时: {metrics.avg_time:.2f}s")
                    print(f"    最大内存: {metrics.max_memory_mb:.2f}MB")
            
            # 缓存统计
            if self.cache_manager:
                cache_stats = self.cache_manager.get_stats()
                print("\n缓存统计:")
                print(f"  缓存命中率: {cache_stats.get('hit_rate', 0):.1f}%")
                print(f"  缓存大小: {cache_stats.get('size', 0)}")
                print(f"  内存使用: {cache_stats.get('memory_usage_mb', 0):.2f}MB")
            
            return 0
            
        except Exception as e:
            self.logger.error("统计获取失败", extra={"error": str(e)})
            print(f"统计获取失败: {e}")
            return 1
    
    def _apply_theme(self, app, theme: str):
        """应用主题"""
        if theme == "dark":
            app.setStyleSheet("""
                QMainWindow {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QWidget {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QPushButton {
                    background-color: #404040;
                    border: 1px solid #555555;
                    padding: 5px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #505050;
                }
            """)
    
    def _signal_handler(self, signum, frame):
        """信号处理器"""
        if self.logger:
            self.logger.info("接收到退出信号", extra={"signal": signum})
        self.cleanup()
        sys.exit(0)
    
    def cleanup(self):
        """清理资源"""
        try:
            if self.logger:
                self.logger.info("应用清理开始")
            
            if self.converter:
                self.converter.cleanup_temp_files()
            
            if self.performance_monitor:
                # 性能监控器不需要显式停止，使用上下文管理器自动管理
                pass
            
            if self.cache_manager:
                self.cache_manager.clear_cache()
            
            if self.logger:
                self.logger.info("应用清理完成")
                
        except Exception as e:
            print(f"清理过程中出错: {e}")


def create_argument_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description="DocuFlow - 智能文档转换工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  %(prog)s gui                                    # 启动GUI模式
  %(prog)s convert input.txt -f .md              # 转换单个文件
  %(prog)s batch ./docs -o ./output -f .html     # 批量转换
  %(prog)s test --type all                       # 运行所有测试
  %(prog)s config show                           # 显示当前配置
  %(prog)s stats                                 # 显示统计信息
        """
    )
    
    parser.add_argument(
        "--config", "-c",
        help="配置文件路径"
    )
    
    parser.add_argument(
        "--debug", "-d",
        action="store_true",
        help="启用调试模式"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="详细输出"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # GUI命令
    gui_parser = subparsers.add_parser("gui", help="启动图形界面")
    
    # 转换命令
    convert_parser = subparsers.add_parser("convert", help="转换单个文件")
    convert_parser.add_argument("input", help="输入文件路径")
    convert_parser.add_argument("-f", "--format", help="输出格式 (如: .md, .html, .pdf)")
    convert_parser.add_argument("-o", "--output", help="输出目录")
    
    # 批量转换命令
    batch_parser = subparsers.add_parser("batch", help="批量转换文件")
    batch_parser.add_argument("input", help="输入目录路径")
    batch_parser.add_argument("-f", "--format", help="输出格式 (如: .md, .html, .pdf)")
    batch_parser.add_argument("-o", "--output", help="输出目录")
    
    # 测试命令
    test_parser = subparsers.add_parser("test", help="运行测试")
    test_parser.add_argument(
        "--type", 
        choices=["basic", "formats", "edge", "all"],
        default="all",
        help="测试类型"
    )
    
    # 配置命令
    config_parser = subparsers.add_parser("config", help="配置管理")
    config_parser.add_argument(
        "config_action",
        choices=["show", "export", "validate"],
        help="配置操作"
    )
    config_parser.add_argument("-o", "--output", help="导出文件路径")
    
    # 统计命令
    stats_parser = subparsers.add_parser("stats", help="显示统计信息")
    
    return parser


def main() -> int:
    """主函数"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # 如果没有指定命令，默认启动GUI
    if not args.command:
        args.command = "gui"
    
    # 创建应用实例
    app = DocuFlowApp()
    
    # 初始化应用
    if not app.initialize(args.config):
        return 1
    
    # 根据命令运行相应模式
    if args.command == "gui":
        return app.run_gui()
    else:
        return app.run_cli(args)


if __name__ == "__main__":
    sys.exit(main())