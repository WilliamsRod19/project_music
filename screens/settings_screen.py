from kivymd.uix.screen import MDScreen
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivy.properties import StringProperty
from utils.config_manager import ConfigManager
import os

# Importar plyer para usar el selector nativo del sistema
try:
    from plyer import filechooser
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False
    print("⚠️ plyer no disponible. Instala con: pip install plyer")

class SettingsScreen(MDScreen):
    music_folder = StringProperty("")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dialog = None
        
        # Cargar configuración al iniciar
        self.music_folder = ConfigManager.get_music_folder()
    
    def open_file_manager(self):
        """Abrir el selector de carpetas del sistema operativo."""
        if not PLYER_AVAILABLE:
            self.show_dialog(
                "Error", 
                "El selector de carpetas no está disponible.\n\nInstala plyer:\npip install plyer"
            )
            return
        
        try:
            # Usar el selector nativo del sistema
            # En Windows abrirá el explorador de Windows
            # En Linux/Mac abrirá el selector nativo
            selection = filechooser.choose_dir(
                title="Selecciona la carpeta de música",
                path=self.music_folder if os.path.exists(self.music_folder) else os.path.expanduser("~")
            )
            
            # selection es una lista de carpetas seleccionadas
            if selection and len(selection) > 0:
                selected_folder = selection[0]
                self.select_folder(selected_folder)
            else:
                print("No se seleccionó ninguna carpeta")
                
        except Exception as e:
            print(f"Error al abrir selector de carpetas: {e}")
            self.show_dialog("Error", f"No se pudo abrir el selector:\n{str(e)}")
    
    def select_folder(self, path):
        """Guardar la carpeta seleccionada."""
        if not os.path.exists(path):
            self.show_dialog("Error", f"La carpeta no existe:\n{path}")
            return
        
        if not os.path.isdir(path):
            self.show_dialog("Error", f"La ruta no es una carpeta:\n{path}")
            return
        
        # Actualizar la propiedad
        self.music_folder = path
        
        # Guardar en la configuración
        if ConfigManager.set_music_folder(path):
            print(f"✅ Carpeta de música guardada: {path}")
            
            # Recargar la lista de canciones automáticamente
            self.reload_song_list(path)
            
            self.show_dialog(
                "¡Carpeta actualizada!", 
                f"Carpeta de música:\n{path}\n\nLa lista de canciones se ha actualizado."
            )
        else:
            self.show_dialog("Error", "No se pudo guardar la configuración")
    
    def reload_song_list(self, music_folder):
        """Recargar la lista de canciones desde la nueva carpeta."""
        try:
            # Importar aquí para evitar imports circulares
            from utils.file_manager import find_music_files
            
            # Buscar canciones en la nueva carpeta
            songs = find_music_files(music_folder)
            
            # Actualizar la lista en SongListScreen
            song_list_screen = self.manager.get_screen('list')
            song_list_screen.songs = songs
            
            # Si está en esa pantalla, refrescar la vista
            if hasattr(song_list_screen, 'on_pre_enter'):
                song_list_screen.on_pre_enter()
            
            print(f"✅ Lista actualizada: {len(songs)} canciones encontradas")
            
        except Exception as e:
            print(f"Error al recargar canciones: {e}")
    
    def show_dialog(self, title, text):
        """Mostrar un diálogo simple."""
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
    
    def change_theme(self, theme_style):
        """Cambiar entre tema claro y oscuro."""
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        app.theme_cls.theme_style = theme_style
        
        # Guardar en la configuración
        ConfigManager.set_theme(theme_style=theme_style)
        print(f"✅ Tema cambiado a: {theme_style}")
    
    def change_primary_color(self, color):
        """Cambiar el color primario del tema."""
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        app.theme_cls.primary_palette = color
        
        # Guardar en la configuración
        ConfigManager.set_theme(primary_color=color)
        print(f"✅ Color primario cambiado a: {color}")
    
    def go_back(self):
        """Volver a la lista de canciones."""
        self.manager.current = 'list'