import os
import shutil
from pathlib import Path

from django.core.management.base import BaseCommand, CommandParser


class Command(BaseCommand):
    """
    Management command to clean up project by removing __pycache__ directories
    and migration files (except __init__.py), while skipping virtualenv folders.
    """
    help = "Cleans project by removing __pycache__ directories and migration files (except __init__.py), skipping venv"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help="Simulate cleanup without actually deleting files"
        )
        parser.add_argument(
            '--skip-pycache',
            action='store_true',
            help="Skip __pycache__ directory cleanup"
        )
        parser.add_argument(
            '--skip-migrations',
            action='store_true',
            help="Skip migrations cleanup"
        )
        parser.add_argument(
            '--exclude-dirs',
            nargs='+',
            default=['venv', '.venv', 'env'],
            help="Directories to exclude (default: venv, .venv, env)"
        )

    def handle(self, *args, **options) -> None:
        self.root_dir = Path(__file__).resolve().parent.parent.parent.parent
        self.dry_run = options['dry_run']
        self.exclude_dirs = options['exclude_dirs']
        
        if not options['skip_pycache']:
            self.clean_pycache()
        
        if not options['skip_migrations']:
            self.clean_migrations()
        
        self.stdout.write(self.style.SUCCESS("Cleanup completed!"))

    def clean_pycache(self) -> None:
        """Delete all __pycache__ directories, excluding virtualenv folders."""
        for dirpath, dirnames, _ in os.walk(self.root_dir, topdown=True):
            # Skip excluded directories
            dirnames[:] = [d for d in dirnames if d not in self.exclude_dirs]
            
            if "__pycache__" in dirnames:
                pycache_path = Path(dirpath) / "__pycache__"
                self._delete_path(pycache_path, is_dir=True)

    def clean_migrations(self) -> None:
        """Delete migration files, excluding virtualenv folders."""
        for dirpath, dirnames, filenames in os.walk(self.root_dir, topdown=True):
            # Skip excluded directories
            dirnames[:] = [d for d in dirnames if d not in self.exclude_dirs]
            
            path_parts = Path(dirpath).parts
            if "migrations" in path_parts:
                for filename in filenames:
                    if filename != "__init__.py" and filename.endswith(".py"):
                        file_path = Path(dirpath) / filename
                        self._delete_path(file_path)

    def _delete_path(self, path: Path, is_dir: bool = False) -> None:
        """Delete a file or directory with proper error handling."""
        if self.dry_run:
            self.stdout.write(f"[DRY RUN] Would delete: {path}")
            return
            
        try:
            if is_dir:
                shutil.rmtree(path)
            else:
                os.remove(path)
            self.stdout.write(self.style.SUCCESS(f"Deleted: {path}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error deleting {path}: {e}"))