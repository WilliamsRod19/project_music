from kivymd.uix.screen import MDScreen
from kivy.properties import ListProperty, StringProperty, ObjectProperty
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
import os

class SongItem(MDCard):
    """Widget personalizado para cada canción en la lista."""
    text = StringProperty("")
    callback = ObjectProperty(None)
    song_path = StringProperty("")
    
    def on_release(self):
        """Llamado cuando se hace clic en la card."""
        if self.callback:
            self.callback(self.song_path)

class SongListScreen(MDScreen):
    songs = ListProperty([])
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dialog = None

    def on_pre_enter(self):
        """Llenar la lista cuando se entra a la pantalla."""
        self.ids.song_list.data = [
            {
                'text': os.path.basename(s),
                'song_path': s,
                'callback': self.select_song
            }
            for s in self.songs
        ]

    def select_song(self, song_path):
        """Seleccionar una canción y cambiar al reproductor."""
        player_screen = self.manager.get_screen('player')
        player_screen.load_song(song_path, self.songs)
        self.manager.current = 'player'
    
    def refresh_song_list(self):
        """Refrescar/recargar la lista de canciones desde la carpeta configurada."""
        try:
            from utils.file_manager import find_music_files
            from utils.config_manager import ConfigManager
            
            music_folder = ConfigManager.get_music_folder()
            self.songs = find_music_files(music_folder)
            
            # Actualizar la vista
            self.on_pre_enter()
            
            # Mostrar mensaje
            self.show_message("Lista actualizada", f"{len(self.songs)} canciones encontradas")
            
        except Exception as e:
            print(f"Error al refrescar canciones: {e}")
            self.show_message("Error", "No se pudo actualizar la lista")
    
    def show_message(self, title, text):
        """Mostrar un mensaje temporal."""
        if self.dialog:
            self.dialog.dismiss()
        
        self.dialog = MDDialog(
            title=title,
            text=text,
            buttons=[
                MDFlatButton(
                    text="OK",
                    on_release=lambda x: self.dialog.dismiss()
                ),
            ],
        )
        self.dialog.open()
    
    def open_settings(self):
        """Abrir la pantalla de ajustes."""
        self.manager.current = 'settings'
    
    def open_downloader(self):
        """Abrir la pantalla de descarga."""
        self.manager.current = 'downloader'
    
    def show_about(self):
        """Mostrar información sobre la app."""
        if self.dialog:
            self.dialog.dismiss()
        
        self.dialog = MDDialog(
            title="Acerca de",
            text="Music Player v1.0\n\nDesarrollado con Kivy y KivyMD\n\n© 2024",
            buttons=[
                MDFlatButton(
                    text="OK",
                    on_release=lambda x: self.dialog.dismiss()
                ),
            ],
        )
        self.dialog.open()