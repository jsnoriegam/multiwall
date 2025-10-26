# Changelog

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [0.3.6] - 2025-10-26

### Mejorado
- Cambio de id para publicación en flathub

## [0.3.5] - 2025-10-25

### Añadido
- Diálogo "Acerca de" con información de la aplicación
- Botones para limpiar fondos de pantalla de cada monitor

### Mejorado
- Interfaz de usuario más intuitiva con opciones de limpieza rápida

## [0.3.3] - 2025-10-24

### Mejorado
- Empaquetadas las fuentes para evitar inconsistencias - Bundled fonts to prevent inconsistencies.
- Optimizada la generación del appimage

## [0.3.2] - 2025-10-23

### Añadido
- Números de monitor en el preview para identificación visual

## [0.3.1] - 2025-10-23

### Añadido
- Implementado archivo de logs

## [0.3.0] - 2025-10-23

### Añadido
- Panel lateral con miniaturas de imágenes
- Navegación visual de carpetas para selección de wallpapers
- Selector de carpetas personalizado con árbol de directorios
- Botones de actualización y cambio de carpeta en sidebar

### Mejorado
- Experiencia de usuario más fluida con selección visual
- Detección automática del directorio de imágenes del sistema
- Soporte inicial para imágenes en formato AVIF

### Soporte de Formatos
- PNG, JPG, JPEG
- BMP, WebP
- GIF
- AVIF

## [0.2.5] - 2025-10-22

### Añadido
- Primera versión publica funcional
- Soporte multi-idioma
- Vista previa en tiempo real de la configuración
- Auto-guardado de configuración
- Múltiples modos de visualización:
  - Rellenar (Fill)
  - Ajustar (Fit)
  - Estirar (Stretch)
  - Centrar (Center)
  - Mosaico (Tile)
- Selector de color de fondo personalizado

### Soporte de Formatos
- PNG, JPG, JPEG
- BMP, WebP
- GIF

---

## Notas de Desarrollo

### Empaquetado
- **AppImage**: Paquete universal para distribuciones Linux
- **Flatpak**: Sandbox con aislamiento completo
- **Docker**: Soporte para desarrollo y testing

### Dependencias
- Python 3.10+
- GTK4
- PyGObject
- Pillow (con soporte AVIF)
- pyyaml
- python-i18n

### Plataformas Soportadas
- Linux con GNOME (X11/Wayland)
- Otros escritorios con soporte gsettings

---

## Enlaces

- [Repositorio](https://github.com/jsnoriegam/multiwall)
- [Reportar Issues](https://github.com/jsnoriegam/multiwall/issues)
- [Buy Me A Coffee](https://www.buymeacoffee.com/jsnoriegam)