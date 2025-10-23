"""
Módulo para aplicar wallpapers que funciona tanto en Flatpak como nativo.
"""
import os
import subprocess
from pathlib import Path
import shutil


def is_running_in_flatpak():
    """Detecta si estamos corriendo dentro de un Flatpak."""
    return os.path.exists('/.flatpak-info')


def is_running_in_docker():
    """Detecta si estamos corriendo dentro de Docker."""
    return os.path.exists('/.dockerenv')


def get_wallpaper_path():
    """Obtiene la ruta donde guardar el wallpaper según el entorno."""
    config_dir = Path.home() / ".config" / "multiwall"
    config_dir.mkdir(parents=True, exist_ok=True)
    return str(config_dir / "current_wallpaper.jpg")


def test_gsettings_access():
    """Prueba si podemos acceder a gsettings."""
    try:
        result = subprocess.run(
            ['gsettings', 'get', 'org.gnome.desktop.background', 'picture-uri'],
            capture_output=True,
            text=True,
            timeout=5
        )
        print(f"[DEBUG] gsettings test - return code: {result.returncode}")
        print(f"[DEBUG] gsettings test - stdout: {result.stdout}")
        print(f"[DEBUG] gsettings test - stderr: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"[DEBUG] gsettings test failed: {e}")
        return False


def notify_gnome_wallpaper_change():
    """Notifica a GNOME Shell que el wallpaper cambió usando D-Bus."""
    print("[DEBUG] Notificando a GNOME Shell sobre el cambio de wallpaper...")
    try:
        # Intentar recargar la configuración de GNOME
        subprocess.run([
            'dbus-send',
            '--session',
            '--dest=org.gnome.Shell',
            '--type=method_call',
            '/org/gnome/Shell',
            'org.gnome.Shell.Eval',
            'string:Main.loadTheme();'
        ], capture_output=True, timeout=5)
        print("[DEBUG] Notificación enviada a GNOME Shell")
        return True
    except Exception as e:
        print(f"[DEBUG] Error notificando a GNOME Shell: {e}")
        return False


def apply_wallpaper_native(image_path):
    """Aplica el wallpaper usando gsettings (método nativo)."""
    print(f"[DEBUG] Intentando aplicar con gsettings nativo...")
    try:
        # Probar lectura primero
        if not test_gsettings_access():
            return False, "No se puede acceder a gsettings"
        
        picture_uri = f'file://{image_path}'
        
        print(f"[DEBUG] URI con cache-busting: {picture_uri}")
        
        # picture-uri
        result = subprocess.run([
            'gsettings', 'set', 'org.gnome.desktop.background',
            'picture-uri', picture_uri
        ], capture_output=True, text=True, timeout=10)
        print(f"[DEBUG] picture-uri - return code: {result.returncode}")
        print(f"[DEBUG] picture-uri - stderr: {result.stderr}")
        
        if result.returncode != 0:
            return False, f"Error al establecer picture-uri: {result.stderr}"
        
        # picture-uri-dark
        result = subprocess.run([
            'gsettings', 'set', 'org.gnome.desktop.background',
            'picture-uri-dark', picture_uri
        ], capture_output=True, text=True, timeout=10)
        print(f"[DEBUG] picture-uri-dark - return code: {result.returncode}")
        
        # picture-options
        result = subprocess.run([
            'gsettings', 'set', 'org.gnome.desktop.background',
            'picture-options', 'spanned'
        ], capture_output=True, text=True, timeout=10)
        print(f"[DEBUG] picture-options - return code: {result.returncode}")
        
        # Verificar que se aplicó
        result = subprocess.run([
            'gsettings', 'get', 'org.gnome.desktop.background',
            'picture-uri'
        ], capture_output=True, text=True, timeout=5)
        print(f"[DEBUG] Verificación - current picture-uri: {result.stdout}")
        
        # Notificar a GNOME Shell
        notify_gnome_wallpaper_change()
        
        return True, "Wallpaper aplicado exitosamente con gsettings"
    except subprocess.TimeoutExpired:
        return False, "Timeout ejecutando gsettings"
    except subprocess.CalledProcessError as e:
        return False, f"Error con gsettings: {e}"
    except Exception as e:
        return False, f"Error inesperado: {e}"

def create_manual_instructions(image_path):
    """Crea instrucciones manuales para aplicar el wallpaper."""
    script_path = Path(image_path).parent / "apply_wallpaper.sh"
    script_content = f"""#!/bin/bash
# Script para aplicar el wallpaper de MultiWall

echo "Aplicando wallpaper..."
gsettings set org.gnome.desktop.background picture-uri 'file://{image_path}'
gsettings set org.gnome.desktop.background picture-uri-dark 'file://{image_path}'
gsettings set org.gnome.desktop.background picture-options 'spanned'
echo "✅ Wallpaper aplicado correctamente"
echo "Imagen: {image_path}"
"""
    try:
        script_path.write_text(script_content)
        script_path.chmod(0o755)
        return str(script_path)
    except Exception as e:
        print(f"[DEBUG] Error creando script: {e}")
        return None


def apply_wallpaper(image_path):
    """
    Aplica el wallpaper usando el método apropiado según el entorno.
    
    Returns:
        tuple: (success: bool, message: str, script_path: str or None)
    """
    print(f"\n{'='*60}")
    print(f"[DEBUG] Iniciando aplicación de wallpaper")
    print(f"[DEBUG] Ruta de imagen: {image_path}")
    print(f"[DEBUG] En Flatpak: {is_running_in_flatpak()}")
    print(f"[DEBUG] En Docker: {is_running_in_docker()}")
    print(f"[DEBUG] Archivo existe: {os.path.exists(image_path)}")
    print(f"[DEBUG] Tamaño archivo: {os.path.getsize(image_path) if os.path.exists(image_path) else 'N/A'} bytes")
    print(f"{'='*60}\n")
    
    if not os.path.exists(image_path):
        return False, f"El archivo no existe: {image_path}", None
    
    # Si estamos en Flatpak
    if is_running_in_flatpak():
        print("[DEBUG] Modo Flatpak detectado")
        
        # No necesitamos copiar, la imagen ya está en la ruta correcta de get_wallpaper_path()
        final_path = image_path
        print(f"[DEBUG] Ruta para GNOME: {final_path}")
        
        # Aplicamos gsettings directo (puede no funcionar en sandbox)
        print(f"[DEBUG] Intentando gsettings directo como fallback...")
        success, message = apply_wallpaper_native(final_path)
        if success:
            return True, message, None
        print(f"[DEBUG] gsettings directo falló: {message}")
        
        # Si todo falla, dar instrucciones manuales
        script_path = create_manual_instructions(final_path)
        manual_msg = (
            f"⚠️ No se pudo aplicar automáticamente desde el Flatpak.\n\n"
            f"El wallpaper fue generado en:\n{final_path}\n\n"
            f"Para aplicarlo manualmente:\n"
            f"1. Abre una terminal FUERA del Flatpak\n"
            f"2. Ejecuta: bash {script_path}\n\n"
            f"O bien, abre Configuración de GNOME > Apariencia\n"
            f"y selecciona la imagen manualmente."
        )
        return False, manual_msg, script_path
    
    # Si estamos en Docker o nativo
    else:
        print("[DEBUG] Modo nativo/Docker detectado")
        success, message = apply_wallpaper_native(image_path)
        if success:
            return True, message, None
        
        # Crear script de respaldo
        script_path = create_manual_instructions(image_path)
        fallback_msg = (
            f"⚠️ gsettings falló: {message}\n\n"
            f"Para aplicar el wallpaper, ejecuta:\n"
            f"bash {script_path}"
        )
        return False, fallback_msg, script_path