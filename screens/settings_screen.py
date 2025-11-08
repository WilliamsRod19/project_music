from kivymd.uix.screen import MDScreen
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivy.properties import StringProperty
from utils.config_manager import ConfigManager
from kivy.utils import platform
import os

# Importar plyer para permisos
try:
    from android.permissions import request_permissions, Permission, check_permission
    from android.storage import primary_external_storage_path
    ANDROID = True
except ImportError:
    ANDROID = False

# Importar plyer para Windows/Linux/Mac
try:
    from plyer import filechooser
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False

class SettingsScreen(MDScreen):
    music_folder = StringProperty("")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dialog = None
        
        # Cargar configuración al iniciar
        self.music_folder = ConfigManager.get_music_folder()
        
        # Si es Android, solicitar permisos al iniciar
        if ANDROID:
            self.request_android_permissions()
    
    def request_android_permissions(self):
        """Solicitar permisos de almacenamiento en Android."""
        try:
            request_permissions([
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE
            ])
            print("✅ Permisos de almacenamiento solicitados")
        except Exception as e:
            print(f"Error solicitando permisos: {e}")
    
    def open_file_manager(self):
        """Abrir el selector de carpetas según la plataforma."""
        if ANDROID:
            self.show_android_folder_selector()
        else:
            self.open_desktop_file_manager()
    
    def show_android_folder_selector(self):
        """Mostrar selector de carpetas para Android con opciones predefinidas."""
        # En Android, las carpetas comunes son:
        try:
            external_storage = primary_external_storage_path()
            music_folder = os.path.join(external_storage, 'Music')
            download_folder = os.path.join(external_storage, 'Download')
            documents_folder = os.path.join(external_storage, 'Documents')
            
            # Crear carpeta Music si no existe
            if not os.path.exists(music_folder):
                os.makedirs(music_folder)
            
        except:
            # Fallback si falla
            music_folder = "/storage/emulated/0/Music"
            download_folder = "/storage/emulated/0/Download"
            documents_folder = "/storage/emulated/0/Documents"
        
        # Mostrar diálogo con opciones
        if self.dialog:
            self.dialog.dismiss()
        
        self.dialog = MDDialog(
            title="Selecciona la carpeta de música",
            text="Elige dónde quieres que se guarden y se busquen las canciones:",
            buttons=[
                MDRaisedButton(
                    text="📁 Music",
                    on_release=lambda x: self.select_folder_and_close(music_folder)
                ),
                MDRaisedButton(
                    text="📥 Download",
                    on_release=lambda x: self.select_folder_and_close(download_folder)
                ),
                MDRaisedButton(
                    text="📄 Documents",
                    on_release=lambda x: self.select_folder_and_close(documents_folder)
                ),
                MDFlatButton(
                    text="CANCELAR",
                    on_release=lambda x: self.dialog.dismiss()
                ),
            ],
        )
        self.dialog.open()
    
    def select_folder_and_close(self, path):
        """Seleccionar carpeta y cerrar el diálogo."""
        if self.dialog:
            self.dialog.dismiss()
        self.select_folder(path)
    
    def open_desktop_file_manager(self):
        """Abrir selector de carpetas para Windows/Linux/Mac."""
        if not PLYER_AVAILABLE:
            self.show_dialog(
                "Error", 
                "El selector de carpetas no está disponible.\n\nInstala plyer:\npip install plyer"
            )
            return
        
        try:
            selection = filechooser.choose_dir(
                title="Selecciona la carpeta de música",
                path=self.music_folder if os.path.exists(self.music_folder) else os.path.expanduser("~")
            )
            
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
        # Crear carpeta si no existe (útil en Android)
        if not os.path.exists(path):
            try:
                os.makedirs(path)
                print(f"📁 Carpeta creada: {path}")
            except Exception as e:
                self.show_dialog("Error", f"No se pudo crear la carpeta:\n{str(e)}")
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
            from utils.file_manager import find_music_files
            
            songs = find_music_files(music_folder)
            
            song_list_screen = self.manager.get_screen('list')
            song_list_screen.songs = songs
            
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
        
        ConfigManager.set_theme(theme_style=theme_style)
        print(f"✅ Tema cambiado a: {theme_style}")
    
    def change_primary_color(self, color):
        """Cambiar el color primario del tema."""
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        app.theme_cls.primary_palette = color
        
        ConfigManager.set_theme(primary_color=color)
        print(f"✅ Color primario cambiado a: {color}")
    
    def go_back(self):
        """Volver a la lista de canciones."""
        self.manager.current = 'list'