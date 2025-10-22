# 📦 Empaquetado de MultiWall

Este documento explica cómo generar paquetes AppImage y Flatpak de MultiWall usando Docker.

## 📋 Requisitos previos

- Docker instalado y funcionando
- Icono `icon.png` (512x512) en la raíz del proyecto
- Al menos 2GB de espacio en disco

## 🚀 Construcción rápida

### Generar todos los paquetes

```bash
./build-packages.sh
```

Esto generará:
- `dist/MultiWall-1.0.0-x86_64.AppImage`
- `dist/MultiWall.flatpak`

### Generar solo AppImage

```bash
./build-packages.sh appimage
```

### Generar solo Flatpak

```bash
./build-packages.sh flatpak
```

### Especificar versión

```bash
VERSION=1.2.0 ./build-packages.sh
```

## 📁 Estructura de archivos necesaria

```
multiwall/
├── icon.png                          # Icono principal (512x512)
├── build-packages.sh                 # Script principal
├── docker/
│   ├── Dockerfile.appimage          # Dockerfile para AppImage
│   ├── Dockerfile.flatpak           # Dockerfile para Flatpak
│   ├── build-appimage.sh            # Script de construcción AppImage
│   └── build-flatpak.sh             # Script de construcción Flatpak
├── flatpak/
│   ├── com.latinosoft.MultiWall.yml       # Manifest de Flatpak
│   ├── com.latinosoft.MultiWall.desktop   # Archivo .desktop
│   ├── com.latinosoft.MultiWall.metainfo.xml  # Metadatos
│   └── com.latinosoft.MultiWall.svg       # Icono SVG (fallback)
└── multiwall/                       # Código fuente de la aplicación
```

## 🔧 Instalación de los paquetes

### AppImage

```bash
# Dar permisos de ejecución
chmod +x dist/MultiWall-1.0.0-x86_64.AppImage

# Ejecutar
./dist/MultiWall-1.0.0-x86_64.AppImage

# Opcional: Instalar en el sistema
sudo cp dist/MultiWall-1.0.0-x86_64.AppImage /usr/local/bin/multiwall
```

### Flatpak

```bash
# Instalar para el usuario actual
flatpak install --user dist/MultiWall.flatpak

# O instalar para todo el sistema
sudo flatpak install dist/MultiWall.flatpak

# Ejecutar
flatpak run com.latinosoft.MultiWall
```

## 🐛 Solución de problemas

### El AppImage no se ejecuta

```bash
# Extraer y ejecutar manualmente
./MultiWall-1.0.0-x86_64.AppImage --appimage-extract
./squashfs-root/AppRun
```

### Flatpak falla al construir

```bash
# Limpiar caché de Docker
docker system prune -a

# Reconstruir imagen base
docker build -f docker/Dockerfile.flatpak -t multiwall-flatpak docker/
```

### El icono no aparece

Verifica que `icon.png` existe y tiene el tamaño correcto:
```bash
file icon.png
# Debería mostrar: icon.png: PNG image data, 512 x 512, ...
```

## 📝 Notas

- Los paquetes se generan en el directorio `dist/`
- Las imágenes Docker se cachean para construcciones más rápidas
- El primer build puede tardar 10-15 minutos
- Builds subsecuentes son más rápidos (2-3 minutos)

## 🔄 Limpieza

```bash
# Eliminar paquetes generados
rm -rf dist/

# Eliminar imágenes Docker
docker rmi multiwall-appimage multiwall-flatpak

# Limpiar todo el caché de Docker
docker system prune -a
```