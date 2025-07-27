#!/usr/bin/env python3

import logging
import os
from datetime import datetime

def setup_subscription_logger():
    """
    Sets up a dedicated logger for subscription/deployment operations.
    Logs to both file and console for comprehensive monitoring.
    
    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logger
    logger = logging.getLogger('subscription_logger')
    logger.setLevel(logging.INFO)
    
    # Prevent duplicate handlers if logger already exists
    if logger.handlers:
        return logger
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler for subscribed_app.log
    log_dir = '/home/kdresdell/Documents/DEV/minipass_env/MinipassWebSite'
    log_file = os.path.join(log_dir, 'subscribed_app.log')
    
    file_handler = logging.FileHandler(log_file, mode='a')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(detailed_formatter)
    
    # Console handler for immediate feedback
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(detailed_formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def log_subprocess_call(logger, command, description="Subprocess call"):
    """
    Logs a subprocess command before execution.
    
    Args:
        logger: Logger instance
        command: Command list or string to be executed
        description: Human-readable description of the command
    """
    cmd_str = ' '.join(command) if isinstance(command, list) else str(command)
    logger.info(f"🔧 {description}")
    logger.info(f"💻 Command: {cmd_str}")

def log_subprocess_result(logger, result, success_msg="Command completed", error_msg="Command failed"):
    """
    Logs the result of a subprocess execution.
    
    Args:
        logger: Logger instance
        result: subprocess.CompletedProcess result
        success_msg: Message to log on success
        error_msg: Message to log on failure
    """
    if result.returncode == 0:
        logger.info(f"✅ {success_msg}")
        if result.stdout and result.stdout.strip():
            logger.info(f"📤 Output: {result.stdout.strip()}")
    else:
        logger.error(f"❌ {error_msg} (exit code: {result.returncode})")
        if result.stderr and result.stderr.strip():
            logger.error(f"🚫 Error: {result.stderr.strip()}")
        if result.stdout and result.stdout.strip():
            logger.error(f"📤 Output: {result.stdout.strip()}")

def log_operation_start(logger, operation_name, **kwargs):
    """
    Logs the start of a major operation with parameters.
    
    Args:
        logger: Logger instance
        operation_name: Name of the operation starting
        **kwargs: Key-value pairs of operation parameters
    """
    logger.info(f"🚀 Starting operation: {operation_name}")
    for key, value in kwargs.items():
        logger.info(f"   📋 {key}: {value}")

def log_operation_end(logger, operation_name, success=True, error_msg=None):
    """
    Logs the completion of a major operation.
    
    Args:
        logger: Logger instance
        operation_name: Name of the operation ending
        success: Whether the operation succeeded
        error_msg: Error message if operation failed
    """
    if success:
        logger.info(f"🎉 Operation completed successfully: {operation_name}")
    else:
        logger.error(f"💥 Operation failed: {operation_name}")
        if error_msg:
            logger.error(f"🔍 Error details: {error_msg}")

def log_file_operation(logger, operation, file_path, additional_info=None):
    """
    Logs file system operations.
    
    Args:
        logger: Logger instance
        operation: Description of file operation (e.g., "Creating directory", "Writing file")
        file_path: Path being operated on
        additional_info: Optional additional information
    """
    logger.info(f"📁 {operation}: {file_path}")
    if additional_info:
        logger.info(f"   ℹ️  {additional_info}")

def log_validation_check(logger, check_name, passed, details=None):
    """
    Logs validation check results.
    
    Args:
        logger: Logger instance
        check_name: Name of the validation check
        passed: Whether the check passed
        details: Additional details about the check
    """
    status = "✅ PASSED" if passed else "❌ FAILED"
    logger.info(f"🔍 Validation - {check_name}: {status}")
    if details:
        logger.info(f"   🔎 Details: {details}")