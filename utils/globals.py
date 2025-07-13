"""
Глобальные переменные и настройки для приложения Dockify.
"""

# Флаг для отключения изображений (используется в демо-режиме)
DISABLE_IMAGES = False

def set_disable_images(value: bool):
    """
    Установить значение флага DISABLE_IMAGES.
    
    Args:
        value: Новое значение флага
    """
    global DISABLE_IMAGES 