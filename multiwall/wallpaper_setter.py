"""
Module for applying wallpapers that works in both Flatpak and native environments.
"""
import os
import subprocess
from pathlib import Path

from .logger import get_logger

logger = get_logger(__name__)


def is_running_in_flatpak():
    """Detect if running inside a Flatpak container."""
    in_flatpak = os.path.exists('/.flatpak-info')
    logger.debug(f"Running in Flatpak: {in_flatpak}")
    return in_flatpak


def is_running_in_docker():
    """Detect if running inside a Docker container."""
    in_docker = os.path.exists('/.dockerenv')
    logger.debug(f"Running in Docker: {in_docker}")
    return in_docker


def get_wallpaper_path():
    """Get path where wallpaper should be saved based on environment."""
    config_dir = Path.home() / ".config" / "multiwall"
    config_dir.mkdir(parents=True, exist_ok=True)
    wallpaper_path = str(config_dir / "current_wallpaper.jpg")
    logger.debug(f"Wallpaper path: {wallpaper_path}")
    return wallpaper_path


def test_gsettings_access():
    """Test if we can access gsettings."""
    logger.debug("Testing gsettings access...")
    try:
        result = subprocess.run(
            ['gsettings', 'get', 'org.gnome.desktop.background', 'picture-uri'],
            capture_output=True,
            text=True,
            timeout=5
        )
        logger.debug(f"gsettings test return code: {result.returncode}")
        logger.debug(f"gsettings test stdout: {result.stdout.strip()}")
        if result.stderr:
            logger.debug(f"gsettings test stderr: {result.stderr.strip()}")
        
        success = result.returncode == 0
        logger.info(f"gsettings access test: {'PASS' if success else 'FAIL'}")
        return success
    except Exception as e:
        logger.error(f"gsettings test failed with exception: {e}")
        return False


def notify_gnome_wallpaper_change():
    """Notify GNOME Shell that wallpaper changed using D-Bus."""
    logger.debug("Notifying GNOME Shell about wallpaper change...")
    try:
        subprocess.run([
            'dbus-send',
            '--session',
            '--dest=org.gnome.Shell',
            '--type=method_call',
            '/org/gnome/Shell',
            'org.gnome.Shell.Eval',
            'string:Main.loadTheme();'
        ], capture_output=True, timeout=5)
        logger.info("GNOME Shell notification sent")
        return True
    except Exception as e:
        logger.warning(f"Error notifying GNOME Shell: {e}")
        return False


def apply_wallpaper_native(image_path):
    """
    Apply wallpaper using gsettings (native method).
    
    Args:
        image_path: Full path to wallpaper image
        
    Returns:
        tuple: (success: bool, message: str)
    """
    logger.info("Attempting to apply wallpaper with native gsettings...")
    
    try:
        # Test read access first
        if not test_gsettings_access():
            return False, "Cannot access gsettings"
        
        picture_uri = f'file://{image_path}'
        logger.debug(f"Picture URI: {picture_uri}")
        
        # Set picture-uri
        logger.debug("Setting picture-uri...")
        result = subprocess.run([
            'gsettings', 'set', 'org.gnome.desktop.background',
            'picture-uri', picture_uri
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            logger.error(f"Failed to set picture-uri: {result.stderr}")
            return False, f"Error setting picture-uri: {result.stderr}"
        logger.debug("picture-uri set successfully")
        
        # Set picture-uri-dark
        logger.debug("Setting picture-uri-dark...")
        result = subprocess.run([
            'gsettings', 'set', 'org.gnome.desktop.background',
            'picture-uri-dark', picture_uri
        ], capture_output=True, text=True, timeout=10)
        logger.debug(f"picture-uri-dark set (return code: {result.returncode})")
        
        # Set picture-options to spanned
        logger.debug("Setting picture-options to 'spanned'...")
        result = subprocess.run([
            'gsettings', 'set', 'org.gnome.desktop.background',
            'picture-options', 'spanned'
        ], capture_output=True, text=True, timeout=10)
        logger.debug(f"picture-options set (return code: {result.returncode})")
        
        # Verify application
        logger.debug("Verifying wallpaper was applied...")
        result = subprocess.run([
            'gsettings', 'get', 'org.gnome.desktop.background',
            'picture-uri'
        ], capture_output=True, text=True, timeout=5)
        current_uri = result.stdout.strip()
        logger.info(f"Current picture-uri: {current_uri}")
        
        # Notify GNOME Shell
        notify_gnome_wallpaper_change()
        
        logger.info("Wallpaper applied successfully with gsettings")
        return True, "Wallpaper applied successfully with gsettings"
        
    except subprocess.TimeoutExpired:
        logger.error("Timeout executing gsettings command")
        return False, "Timeout executing gsettings"
    except subprocess.CalledProcessError as e:
        logger.error(f"gsettings command failed: {e}")
        return False, f"Error with gsettings: {e}"
    except Exception as e:
        logger.error(f"Unexpected error applying wallpaper: {e}", exc_info=True)
        return False, f"Unexpected error: {e}"


def create_manual_instructions(image_path):
    """
    Create a shell script with manual instructions for applying wallpaper.
    
    Args:
        image_path: Path to wallpaper image
        
    Returns:
        str: Path to created script or None if failed
    """
    logger.debug("Creating manual application script...")
    script_path = Path(image_path).parent / "apply_wallpaper.sh"
    script_content = f"""#!/bin/bash
# Script to apply MultiWall wallpaper

echo "Applying wallpaper..."
gsettings set org.gnome.desktop.background picture-uri 'file://{image_path}'
gsettings set org.gnome.desktop.background picture-uri-dark 'file://{image_path}'
gsettings set org.gnome.desktop.background picture-options 'spanned'
echo "✅ Wallpaper applied successfully"
echo "Image: {image_path}"
"""
    try:
        script_path.write_text(script_content)
        script_path.chmod(0o755)
        logger.info(f"Manual script created: {script_path}")
        return str(script_path)
    except Exception as e:
        logger.error(f"Error creating manual script: {e}")
        return None


def apply_wallpaper(image_path):
    """
    Apply wallpaper using the appropriate method based on environment.
    
    Args:
        image_path: Path to wallpaper image
        
    Returns:
        tuple: (success: bool, message: str, script_path: str or None)
    """
    logger.info("="*60)
    logger.info("Starting wallpaper application process")
    logger.info(f"Image path: {image_path}")
    logger.info(f"In Flatpak: {is_running_in_flatpak()}")
    logger.info(f"In Docker: {is_running_in_docker()}")
    logger.info(f"File exists: {os.path.exists(image_path)}")
    if os.path.exists(image_path):
        logger.info(f"File size: {os.path.getsize(image_path)} bytes")
    logger.info("="*60)
    
    if not os.path.exists(image_path):
        logger.error(f"Wallpaper file does not exist: {image_path}")
        return False, f"File does not exist: {image_path}", None
    
    # If running in Flatpak
    if is_running_in_flatpak():
        logger.info("Flatpak mode detected")
        
        # Image is already in the correct path from get_wallpaper_path()
        final_path = image_path
        logger.debug(f"Path for GNOME: {final_path}")
        
        # Try direct gsettings (may not work in sandbox)
        logger.info("Trying direct gsettings as fallback...")
        success, message = apply_wallpaper_native(final_path)
        if success:
            logger.info("Wallpaper applied successfully from Flatpak")
            return True, message, None
        logger.warning(f"Direct gsettings failed: {message}")
        
        # If all fails, provide manual instructions
        script_path = create_manual_instructions(final_path)
        manual_msg = (
            f"⚠️ Could not apply automatically from Flatpak.\n\n"
            f"Wallpaper was generated at:\n{final_path}\n\n"
            f"To apply manually:\n"
            f"1. Open a terminal OUTSIDE of Flatpak\n"
            f"2. Run: bash {script_path}\n\n"
            f"Or open GNOME Settings > Appearance\n"
            f"and select the image manually."
        )
        logger.info("Providing manual application instructions")
        return False, manual_msg, script_path
    
    # If running in Docker or native
    else:
        logger.info("Native/Docker mode detected")
        success, message = apply_wallpaper_native(image_path)
        if success:
            logger.info("Wallpaper applied successfully")
            return True, message, None
        
        # Create fallback script
        script_path = create_manual_instructions(image_path)
        fallback_msg = (
            f"⚠️ gsettings failed: {message}\n\n"
            f"To apply the wallpaper, run:\n"
            f"bash {script_path}"
        )
        logger.warning("gsettings failed, providing manual script")
        return False, fallback_msg, script_path