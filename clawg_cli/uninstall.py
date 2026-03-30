"""
CLAWG Uninstaller.

Provides options for:
- Full uninstall: Remove everything including configs and data
- Keep data: Remove code but keep ~/.clawg/ (configs, sessions, logs)
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from clawg_cli.colors import Colors, color

def log_info(msg: str):
    print(f"{color('→', Colors.CYAN)} {msg}")

def log_success(msg: str):
    print(f"{color('✓', Colors.GREEN)} {msg}")

def log_warn(msg: str):
    print(f"{color('⚠', Colors.YELLOW)} {msg}")

def log_error(msg: str):
    print(f"{color('✗', Colors.RED)} {msg}")


def get_project_root() -> Path:
    """Get the project installation directory."""
    return Path(__file__).parent.parent.resolve()


def get_clawg_home() -> Path:
    """Get the clawg home directory (~/.clawg)."""
    return Path(os.getenv("CLAWG_HOME", Path.home() / ".clawg"))


def find_shell_configs() -> list:
    """Find shell configuration files that might have PATH entries."""
    home = Path.home()
    configs = []
    
    candidates = [
        home / ".bashrc",
        home / ".bash_profile",
        home / ".profile",
        home / ".zshrc",
        home / ".zprofile",
    ]
    
    for config in candidates:
        if config.exists():
            configs.append(config)
    
    return configs


def remove_path_from_shell_configs():
    """Remove clawg PATH entries from shell configuration files."""
    configs = find_shell_configs()
    removed_from = []
    
    for config_path in configs:
        try:
            content = config_path.read_text()
            original_content = content
            
            # Remove lines containing clawg or clawg PATH entries
            new_lines = []
            skip_next = False
            
            for line in content.split('\n'):
                # Skip the "# CLAWG" comment and following line
                if '# CLAWG' in line or '# clawg' in line:
                    skip_next = True
                    continue
                if skip_next and ('clawg' in line.lower() and 'PATH' in line):
                    skip_next = False
                    continue
                skip_next = False
                
                # Remove any PATH line containing clawg
                if 'clawg' in line.lower() and ('PATH=' in line or 'path=' in line.lower()):
                    continue
                    
                new_lines.append(line)
            
            new_content = '\n'.join(new_lines)
            
            # Clean up multiple blank lines
            while '\n\n\n' in new_content:
                new_content = new_content.replace('\n\n\n', '\n\n')
            
            if new_content != original_content:
                config_path.write_text(new_content)
                removed_from.append(config_path)
                
        except Exception as e:
            log_warn(f"Could not update {config_path}: {e}")
    
    return removed_from


def remove_wrapper_script():
    """Remove the clawg wrapper script if it exists."""
    wrapper_paths = [
        Path.home() / ".local" / "bin" / "clawg",
        Path("/usr/local/bin/clawg"),
    ]
    
    removed = []
    for wrapper in wrapper_paths:
        if wrapper.exists():
            try:
                # Check if it's our wrapper (contains clawg_cli reference)
                content = wrapper.read_text()
                if 'clawg_cli' in content or 'clawg' in content:
                    wrapper.unlink()
                    removed.append(wrapper)
            except Exception as e:
                log_warn(f"Could not remove {wrapper}: {e}")
    
    return removed


def uninstall_gateway_service():
    """Stop and uninstall the gateway service if running."""
    import platform
    
    if platform.system() != "Linux":
        return False
    
    try:
        from clawg_cli.gateway import get_service_name
        svc_name = get_service_name()
    except Exception:
        svc_name = "clawg-gateway"

    service_file = Path.home() / ".config" / "systemd" / "user" / f"{svc_name}.service"
    
    if not service_file.exists():
        return False
    
    try:
        # Stop the service
        subprocess.run(
            ["systemctl", "--user", "stop", svc_name],
            capture_output=True,
            check=False
        )
        
        # Disable the service
        subprocess.run(
            ["systemctl", "--user", "disable", svc_name],
            capture_output=True,
            check=False
        )
        
        # Remove service file
        service_file.unlink()
        
        # Reload systemd
        subprocess.run(
            ["systemctl", "--user", "daemon-reload"],
            capture_output=True,
            check=False
        )
        
        return True
        
    except Exception as e:
        log_warn(f"Could not fully remove gateway service: {e}")
        return False


def run_uninstall(args):
    """
    Run the uninstall process.
    
    Options:
    - Full uninstall: removes code + ~/.clawg/ (configs, data, logs)
    - Keep data: removes code but keeps ~/.clawg/ for future reinstall
    """
    project_root = get_project_root()
    clawg_home = get_clawg_home()
    
    print()
    print(color("┌─────────────────────────────────────────────────────────┐", Colors.MAGENTA, Colors.BOLD))
    print(color("│            ⚕ CLAWG Uninstaller                  │", Colors.MAGENTA, Colors.BOLD))
    print(color("└─────────────────────────────────────────────────────────┘", Colors.MAGENTA, Colors.BOLD))
    print()
    
    # Show what will be affected
    print(color("Current Installation:", Colors.CYAN, Colors.BOLD))
    print(f"  Code:    {project_root}")
    print(f"  Config:  {clawg_home / 'config.yaml'}")
    print(f"  Secrets: {clawg_home / '.env'}")
    print(f"  Data:    {clawg_home / 'cron/'}, {clawg_home / 'sessions/'}, {clawg_home / 'logs/'}")
    print()
    
    # Ask for confirmation
    print(color("Uninstall Options:", Colors.YELLOW, Colors.BOLD))
    print()
    print("  1) " + color("Keep data", Colors.GREEN) + " - Remove code only, keep configs/sessions/logs")
    print("     (Recommended - you can reinstall later with your settings intact)")
    print()
    print("  2) " + color("Full uninstall", Colors.RED) + " - Remove everything including all data")
    print("     (Warning: This deletes all configs, sessions, and logs permanently)")
    print()
    print("  3) " + color("Cancel", Colors.CYAN) + " - Don't uninstall")
    print()
    
    try:
        choice = input(color("Select option [1/2/3]: ", Colors.BOLD)).strip()
    except (KeyboardInterrupt, EOFError):
        print()
        print("Cancelled.")
        return
    
    if choice == "3" or choice.lower() in ("c", "cancel", "q", "quit", "n", "no"):
        print()
        print("Uninstall cancelled.")
        return
    
    full_uninstall = (choice == "2")
    
    # Final confirmation
    print()
    if full_uninstall:
        print(color("⚠️  WARNING: This will permanently delete ALL clawg data!", Colors.RED, Colors.BOLD))
        print(color("   Including: configs, API keys, sessions, scheduled jobs, logs", Colors.RED))
    else:
        print("This will remove the clawg code but keep your configuration and data.")
    
    print()
    try:
        confirm = input(f"Type '{color('yes', Colors.YELLOW)}' to confirm: ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        print()
        print("Cancelled.")
        return
    
    if confirm != "yes":
        print()
        print("Uninstall cancelled.")
        return
    
    print()
    print(color("Uninstalling...", Colors.CYAN, Colors.BOLD))
    print()
    
    # 1. Stop and uninstall gateway service
    log_info("Checking for gateway service...")
    if uninstall_gateway_service():
        log_success("Gateway service stopped and removed")
    else:
        log_info("No gateway service found")
    
    # 2. Remove PATH entries from shell configs
    log_info("Removing PATH entries from shell configs...")
    removed_configs = remove_path_from_shell_configs()
    if removed_configs:
        for config in removed_configs:
            log_success(f"Updated {config}")
    else:
        log_info("No PATH entries found to remove")
    
    # 3. Remove wrapper script
    log_info("Removing clawg command...")
    removed_wrappers = remove_wrapper_script()
    if removed_wrappers:
        for wrapper in removed_wrappers:
            log_success(f"Removed {wrapper}")
    else:
        log_info("No wrapper script found")
    
    # 4. Remove installation directory (code)
    log_info(f"Removing installation directory...")
    
    # Check if we're running from within the install dir
    # We need to be careful here
    try:
        if project_root.exists():
            # If the install is inside ~/.clawg/, just remove the clawg subdir
            if clawg_home in project_root.parents or project_root.parent == clawg_home:
                shutil.rmtree(project_root)
                log_success(f"Removed {project_root}")
            else:
                # Installation is somewhere else entirely
                shutil.rmtree(project_root)
                log_success(f"Removed {project_root}")
    except Exception as e:
        log_warn(f"Could not fully remove {project_root}: {e}")
        log_info("You may need to manually remove it")
    
    # 5. Optionally remove ~/.clawg/ data directory
    if full_uninstall:
        log_info("Removing configuration and data...")
        try:
            if clawg_home.exists():
                shutil.rmtree(clawg_home)
                log_success(f"Removed {clawg_home}")
        except Exception as e:
            log_warn(f"Could not fully remove {clawg_home}: {e}")
            log_info("You may need to manually remove it")
    else:
        log_info(f"Keeping configuration and data in {clawg_home}")
    
    # Done
    print()
    print(color("┌─────────────────────────────────────────────────────────┐", Colors.GREEN, Colors.BOLD))
    print(color("│              ✓ Uninstall Complete!                      │", Colors.GREEN, Colors.BOLD))
    print(color("└─────────────────────────────────────────────────────────┘", Colors.GREEN, Colors.BOLD))
    print()
    
    if not full_uninstall:
        print(color("Your configuration and data have been preserved:", Colors.CYAN))
        print(f"  {clawg_home}/")
        print()
        print("To reinstall later with your existing settings:")
        print(color("  curl -fsSL https://raw.githubusercontent.com/NousResearch/clawg/main/scripts/install.sh | bash", Colors.DIM))
        print()
    
    print(color("Reload your shell to complete the process:", Colors.YELLOW))
    print("  source ~/.bashrc  # or ~/.zshrc")
    print()
    print("Thank you for using CLAWG! ⚕")
    print()
