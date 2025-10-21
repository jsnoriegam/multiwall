FROM python:3.14-trixie

# Configurar locales UTF-8 PRIMERO (crítico para emojis)
RUN apt update && apt install -y locales && \
    sed -i '/es_CO.UTF-8/s/^# //g' /etc/locale.gen && \
    sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen es_CO.UTF-8 en_US.UTF-8 && \
    update-locale LANG=es_CO.UTF-8

# Variables de entorno para UTF-8 (antes de instalar paquetes)
ENV LANG=es_CO.UTF-8
ENV LC_ALL=es_CO.UTF-8
ENV LANGUAGE=es_CO:es
ENV PYTHONIOENCODING=utf-8

# Dependencias nativas para GTK4, Cairo, Wayland + fuentes de emojis + dconf + xdg-user-dirs
RUN apt update && apt install -y \
    python3-gi python3-gi-cairo gir1.2-gtk-4.0 \
    libcairo2-dev libgirepository-2.0-dev pkg-config \
    libwayland-client0 libwayland-cursor0 libwayland-egl1 \
    libxkbcommon0 libdbus-1-3 \
    fonts-noto-color-emoji \
    fonts-noto-mono \
    fontconfig \
    dconf-cli dconf-gsettings-backend gsettings-desktop-schemas \
    xdg-user-dirs \
    && fc-cache -fv \
    && apt clean && rm -rf /var/lib/apt/lists/*

WORKDIR /srv

# Copiamos el entrypoint que gestionará el venv dinámico
COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Variables de entorno
ENV PATH="/app/.venv/bin:$PATH"
ENV GDK_BACKEND=wayland

# Crear usuario no-root con UID/GID flexibles
RUN useradd -m -s /bin/bash appuser && \
    mkdir -p /app && \
    chown -R appuser:appuser /app /srv

ENTRYPOINT ["entrypoint.sh"]
CMD ["python", "main.py"]