from kivy.lang import Builder
from kivymd.app import MDApp
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager
from kivy.utils import platform
from screens.song_list_screen import SongListScreen
from screens.player_screen import PlayerScreen
from screens.settings_screen import SettingsScreen
from screens.downloader_screen import DownloaderScreen
from utils.file_manager import find_music_files
from utils.config_manager import ConfigManager
from utils.config_permissions import get_permissions
import os

class MainApp(MDApp):
    def build(self):
        #solicitar permisos en Android
        if platform == "android":
            get_permissions()

        # Cargar tema desde la configuración
        theme_config = ConfigManager.get_theme()
        self.theme_cls.theme_style = theme_config['theme_style']
        self.theme_cls.primary_palette = theme_config['primary_color']
        
        Builder.load_file("musicapp.kv")

        sm = ScreenManager()

        # Usar la carpeta configurada o la por defecto
        music_path = ConfigManager.get_music_folder()
        songs = find_music_files(music_path)

        song_list_screen = SongListScreen(name='list')
        song_list_screen.songs = songs
        player_screen = PlayerScreen(name='player')
        settings_screen = SettingsScreen(name='settings')
        downloader_screen = DownloaderScreen(name='downloader')

        sm.add_widget(song_list_screen)
        sm.add_widget(player_screen)
        sm.add_widget(settings_screen)
        sm.add_widget(downloader_screen)
        
        sm.current = 'list'
        return sm

    def on_start(self):
        # ✅ Pedir permisos aquí, no en build()
        if platform == "android":
            Clock.schedule_once(lambda dt: get_permissions(), 1)

if __name__ == '__main__':
    MainApp().run()