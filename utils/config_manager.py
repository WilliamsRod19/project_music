import json
import os

class ConfigManager:
    """Gestiona la configuración de la app (carpeta de música, tema, etc.)"""
    
    CONFIG_FILE = "music_player_config.json"
    
    @staticmethod
    def load_config():
        """Cargar configuración desde el archivo JSON."""
        if os.path.exists(ConfigManager.CONFIG_FILE):
            try:
                with open(ConfigManager.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        # Configuración por defecto
        return {
            'music_folder': os.path.expanduser("~/Music"),
            'theme_style': 'Dark',
            'primary_color': 'Blue'
        }
    
    @staticmethod
    def save_config(config):
        """Guardar configuración en el archivo JSON."""
        try:
            with open(ConfigManager.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error guardando configuración: {e}")
            return False
    
    @staticmethod
    def get_music_folder():
        """Obtener la carpeta de música configurada."""
        config = ConfigManager.load_config()
        return config.get('music_folder', os.path.expanduser("~/Music"))
    
    @staticmethod
    def set_music_folder(folder_path):
        """Establecer la carpeta de música."""
        config = ConfigManager.load_config()
        config['music_folder'] = folder_path
        return ConfigManager.save_config(config)
    
    @staticmethod
    def get_theme():
        """Obtener configuración del tema."""
        config = ConfigManager.load_config()
        return {
            'theme_style': config.get('theme_style', 'Dark'),
            'primary_color': config.get('primary_color', 'Blue')
        }
    
    @staticmethod
    def set_theme(theme_style=None, primary_color=None):
        """Establecer el tema."""
        config = ConfigManager.load_config()
        if theme_style:
            config['theme_style'] = theme_style
        if primary_color:
            config['primary_color'] = primary_color
        return ConfigManager.save_config(config)