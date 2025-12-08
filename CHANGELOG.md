# Changelog

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [0.4.0] - 2025-10-31

### Añadido
- 🌓 **Sistema de Pestañas para Modo Claro/Oscuro**: Ahora puedes configurar wallpapers diferentes para cada modo de tema
  - Pestaña "☀️ Modo Claro" para configurar el wallpaper del tema claro
  - Pestaña "🌙 Modo Oscuro" para configurar el wallpaper del tema oscuro
  - Previews independientes para cada modo
  - Configuraciones de monitores separadas por modo
- 🎨 **Lógica Inteligente de Aplicación**:
  - Aplicar desde Modo Claro: Establece el wallpaper para **ambos** modos (claro y oscuro)
  - Aplicar desde Modo Oscuro: Establece el wallpaper **solo** para el modo oscuro
- 💾 **Guardado Automático por Modo**: Las configuraciones de ambos modos se guardan independientemente

### Mejorado
- 🔄 Transición suave entre pestañas con efecto crossfade
- 🖼️ Sistema de previews más robusto con actualización independiente
- 📝 Controles de monitores que se adaptan automáticamente al modo seleccionado
- 🗂️ Estructura de configuración mejorada para soportar múltiples modos

### Técnico
- Refactorización de `app.py` para soportar dual-mode configuration
- Nuevo parámetro `dark_mode` en `wallpaper_setter.py`
- Actualización de traducciones (ES/EN) con nuevas etiquetas para modos
- Mejora en la gestión de estado con configuraciones separadas

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

## 🌟 Características Destacadas de 0.4.0

### Casos de Uso Típicos

**Escenario 1: Mismo wallpaper para ambos modos**
1. Configura tu wallpaper en la pestaña "☀️ Modo Claro"
2. Aplica el fondo
3. ✅ Se establece automáticamente para claro y oscuro

**Escenario 2: Wallpapers diferentes por modo**
1. Configura wallpaper brillante en "☀️ Modo Claro" y aplica
2. Cambia a la pestaña "🌙 Modo Oscuro"
3. Configura un wallpaper más oscuro/diferente
4. Aplica desde modo oscuro
5. ✅ Ahora tienes wallpapers distintos que cambian con el tema del sistema

**Escenario 3: Multi-monitor con temas**
1. Configura diferentes imágenes por monitor en cada modo
2. Cada monitor puede tener su propia imagen en modo claro y otra en modo oscuro
3. El sistema cambiará automáticamente todos los monitores al cambiar el tema

---

## Enlaces

- [Repositorio](https://github.com/jsnoriegam/multiwall)
- [Reportar Issues](https://github.com/jsnoriegam/multiwall/issues)
- [Buy Me A Coffee](https://www.buymeacoffee.com/jsnoriegam)