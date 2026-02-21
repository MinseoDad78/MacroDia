#!/usr/bin/env python3
"""
Python conversion of ManagementFile.jar
A file cleanup utility that automatically organizes old files into dated backup folders.

Original Java package: fury.*
"""

import os
import sys
import configparser
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Set


class FuryProperties:
    """
    Python equivalent of fury.util.FuryProperties
    Manages configuration properties for the file cleanup application.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.prop_file = Path.home() / "config.properties"
        self.config = configparser.ConfigParser()
        self._load_properties()
        self._initialized = True
    
    def _load_properties(self):
        """Load or create default configuration properties."""
        create_new = False
        
        if not self.prop_file.exists() or self.prop_file.stat().st_size == 0:
            create_new = True
            self.prop_file.touch()
            print(f"Created config file: {self.prop_file.absolute()}")
        
        if create_new:
            # Create default configuration content
            default_content = """# File Cleanup Manager Configuration
# Directory names to monitor (relative to home directory)
directory=Downloads,Documents,Desktop
# File extensions to exclude from cleanup
exceptFile=.lnk
"""
            with open(self.prop_file, 'w') as f:
                f.write(default_content)
        
        try:
            # Read using configparser with allow_no_value for simple key=value format
            self.config.read_string("[DEFAULT]\n" + self.prop_file.read_text())
        except Exception as e:
            print(f"Error reading config file: {e}")
            # Fallback to defaults
            self.config.read_string("[DEFAULT]\ndirectory=Downloads,Documents,Desktop\nexceptFile=.lnk\n")
    
    def get_property(self, key: str, default: str = None) -> str:
        """Get a property value."""
        return self.config.get('DEFAULT', key, fallback=default)
    
    def set_property(self, key: str, value: str):
        """Set a property value."""
        if not self.config.has_section('DEFAULT'):
            self.config.add_section('DEFAULT')
        self.config.set('DEFAULT', key, value)
        
        # Save in simple format (without [DEFAULT] section header)
        content_lines = []
        for option in self.config.options('DEFAULT'):
            content_lines.append(f"{option}={self.config.get('DEFAULT', option)}")
        
        with open(self.prop_file, 'w') as f:
            f.write("# File Cleanup Manager Configuration\n")
            f.write("# Directory names to monitor (relative to home directory)\n")
            f.write("# File extensions to exclude from cleanup\n")
            f.write('\n'.join(content_lines))
    
    @classmethod
    def get_instance(cls):
        """Get singleton instance."""
        return cls()


class FuryFilter:
    """
    Python equivalent of fury.util.FuryFilter
    File filter that excludes directories, hidden files, and specified extensions.
    """
    
    def __init__(self):
        properties = FuryProperties.get_instance()
        except_file_str = properties.get_property('exceptFile', '.lnk')
        self.file_extensions = [ext.strip() for ext in except_file_str.split(',')]
    
    def accept(self, file_path: Path) -> bool:
        """
        Check if a file should be accepted for processing.
        Returns True if file should be processed, False otherwise.
        """
        # Exclude directories
        if file_path.is_dir():
            return False
        
        # Exclude hidden files
        if file_path.name.startswith('.'):
            return False
        
        # Exclude files with specified extensions
        for ext in self.file_extensions:
            if file_path.name.endswith(ext):
                return False
        
        return True


class FileClearup:
    """
    Python equivalent of fury.core.FileClearup
    Main logic for organizing and backing up old files.
    """
    
    def __init__(self):
        self.directories: List[Path] = []
        self.current_date = datetime.now().strftime('%Y%m%d')
        self.sdf_display = '%Y-%m-%d %H:%M:%S'
        
        # Load directory configuration
        properties = FuryProperties.get_instance()
        directory_str = properties.get_property('directory', 'Downloads,Documents,Desktop')
        directory_names = [name.strip() for name in directory_str.split(',')]
        
        # Convert to Path objects under user home
        home_dir = Path.home()
        for dir_name in directory_names:
            directory = home_dir / dir_name
            self.directories.append(directory)
    
    def execute(self):
        """
        Main execution method that processes all configured directories.
        """
        for directory in self.directories:
            print(f"Processing: {directory.absolute()}")
            
            if not directory.exists():
                print(f"Directory does not exist: {directory}")
                continue
            
            # Get files using the filter
            fury_filter = FuryFilter()
            files = [f for f in directory.iterdir() if fury_filter.accept(f)]
            
            if not files:
                continue
            
            # Determine backup directory
            backup_dir = self._get_backup_directory(directory)
            
            # Ensure backup directory exists
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Process each file
            for file_path in files:
                self._process_file(file_path, backup_dir)
    
    def _get_backup_directory(self, directory: Path) -> Path:
        """
        Determine the backup directory path.
        For Desktop: creates BACKUP/{date} subdirectory
        For others: creates {date} subdirectory
        """
        if 'Desktop' in directory.name:
            return directory / 'BACKUP' / self.current_date
        else:
            return directory / self.current_date
    
    def _process_file(self, file_path: Path, backup_dir: Path):
        """
        Process a single file - move to backup if it's not from today.
        """
        try:
            # Get file's last modified date
            file_modified_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            file_date = file_modified_time.strftime('%Y%m%d')
            
            if file_date != self.current_date:
                # File is not from today, move it to backup
                backup_file_path = backup_dir / file_path.name
                
                # Handle filename conflicts
                counter = 1
                original_backup_path = backup_file_path
                while backup_file_path.exists():
                    stem = original_backup_path.stem
                    suffix = original_backup_path.suffix
                    backup_file_path = backup_dir / f"{stem}_{counter}{suffix}"
                    counter += 1
                
                # Move the file
                shutil.move(str(file_path), str(backup_file_path))
                print(f"{file_path} moved to {backup_file_path}")
                
            else:
                # File is from today, don't move it
                file_time_str = file_modified_time.strftime(self.sdf_display)
                print(f"File: {file_path.absolute()}\t File Date: {file_time_str} was not moved, try tomorrow")
                
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")


class ClearupMain:
    """
    Python equivalent of fury.main.ClearupMain
    Main entry point for the application.
    """
    
    @staticmethod
    def main():
        """Main method that starts the file cleanup process."""
        try:
            clearup = FileClearup()
            clearup.execute()
        except Exception as e:
            print(f"Error during cleanup execution: {e}")
            sys.exit(1)


class Test001:
    """
    Python equivalent of fury.test.Test001
    Simple test class for date formatting.
    """
    
    @staticmethod
    def main():
        """Test method that prints current date."""
        current_date = datetime.now().strftime('%Y%m%d')
        print(current_date)


def main():
    """
    Command line interface for the file cleanup utility.
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='File Cleanup Manager - Automatically organize old files into dated backup folders'
    )
    parser.add_argument(
        '--test', 
        action='store_true', 
        help='Run test mode (just print current date)'
    )
    parser.add_argument(
        '--config', 
        action='store_true', 
        help='Show current configuration'
    )
    
    args = parser.parse_args()
    
    if args.test:
        Test001.main()
    elif args.config:
        properties = FuryProperties.get_instance()
        print(f"Configuration file: {properties.prop_file}")
        print(f"Directories: {properties.get_property('directory')}")
        print(f"Excluded extensions: {properties.get_property('exceptFile')}")
    else:
        print("File Cleanup Manager - Starting cleanup process...")
        ClearupMain.main()
        print("Cleanup process completed.")


if __name__ == "__main__":
    main()