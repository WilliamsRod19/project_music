from kivymd.uix.screen import MDScreen
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivy.properties import StringProperty
from utils.config_manager import ConfigManager
from kivy.utils import platform
import os

# Importar módulos de Android
ANDROID = False
if platform == 'android':
    try:
        from android.permissions import request_permissions, Permission
        from android.storage import primary_external_storage_path
        from android import activity, mActivity
        from jnius import autoclass, cast
        ANDROID = True
    except ImportError:
        print("⚠️ Módulos de Android no disponibles")

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
        
        # Si es Android, configurar el callback y solicitar permisos
        if ANDROID:
            activity.bind(on_activity_result=self.on_activity_result)
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
            self.open_android_folder_picker()
        else:
            self.open_desktop_file_manager()
    
    def open_android_folder_picker(self):
        """Abrir el explorador de archivos nativo de Android (SAF)."""
        try:
            Intent = autoclass('android.content.Intent')
            
            # Crear intent para seleccionar carpeta
            intent = Intent(Intent.ACTION_OPEN_DOCUMENT_TREE)
            
            # Opcional: establecer una carpeta inicial
            try:
                Uri = autoclass('android.net.Uri')
                DocumentsContract = autoclass('android.provider.DocumentsContract')
                
                # Intentar abrir en la carpeta Music por defecto
                initial_uri = Uri.parse("content://com.android.externalstorage.documents/tree/primary:Music")
                intent.putExtra(DocumentsContract.EXTRA_INITIAL_URI, initial_uri)
            except:
                pass  # Si falla, abrirá en la carpeta raíz
            
            # Iniciar el selector
            mActivity.startActivityForResult(intent, 42)
            print("📂 Abriendo selector de carpetas de Android...")
            
        except Exception as e:
            print(f"Error abriendo selector de Android: {e}")
            self.show_dialog("Error", f"No se pudo abrir el selector:\n{str(e)}")
    
    def on_activity_result(self, request_code, result_code, intent):
        """Callback cuando el usuario selecciona una carpeta en Android."""
        if request_code != 42:
            return
        
        # result_code -1 = RESULT_OK (el usuario seleccionó algo)
        if result_code == -1 and intent is not None:
            try:
                # Obtener la URI de la carpeta seleccionada
                tree_uri = intent.getData()
                
                # Convertir URI a path real
                path = self.convert_uri_to_path(tree_uri)
                
                if path:
                    print(f"📁 Carpeta seleccionada: {path}")
                    self.select_folder(path)
                else:
                    # Si no se puede convertir, usar la URI directamente
                    uri_string = tree_uri.toString()
                    print(f"📁 URI seleccionada: {uri_string}")
                    
                    # Intentar extraer el path del URI
                    if "primary:" in uri_string:
                        parts = uri_string.split("primary:")
                        if len(parts) > 1:
                            relative_path = parts[-1].replace("%20", " ").replace("%2F", "/")
                            external_storage = primary_external_storage_path()
                            path = os.path.join(external_storage, relative_path)
                            print(f"📁 Path extraído: {path}")
                            self.select_folder(path)
                        else:
                            self.show_dialog("Error", "No se pudo determinar la ruta de la carpeta")
                    else:
                        self.show_dialog("Error", "No se pudo determinar la ruta de la carpeta")
                        
            except Exception as e:
                print(f"Error procesando carpeta seleccionada: {e}")
                import traceback
                traceback.print_exc()
                self.show_dialog("Error", f"Error al procesar la carpeta:\n{str(e)}")
        else:
            print("❌ Usuario canceló la selección")
    
    def convert_uri_to_path(self, uri):
        """Intentar convertir un URI de Android a un path del sistema de archivos."""
        try:
            uri_string = uri.toString()
            
            if "primary:" in uri_string:
                parts = uri_string.split("primary:")
                if len(parts) > 1:
                    relative_path = parts[-1]
                    relative_path = relative_path.split("/document/")[0] if "/document/" in relative_path else relative_path
                    relative_path = relative_path.replace("%20", " ").replace("%2F", "/")
                    
                    external_storage = primary_external_storage_path()
                    full_path = os.path.join(external_storage, relative_path)
                    
                    return full_path
            
            return None
            
        except Exception as e:
            print(f"Error convirtiendo URI: {e}")
            return None
    
    def open_desktop_file_manager(self):
        """Abrir selector de carpetas para Windows/Linux/Mac."""
        if not PLYER_AVAILABLE:
            self.show_dialog("Error", "El selector de carpetas no está disponible.")
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
        if not os.path.exists(path):
            try:
                os.makedirs(path)
                print(f"📁 Carpeta creada: {path}")
            except Exception as e:
                print(f"⚠️ No se pudo crear la carpeta: {e}")
        
        if os.path.exists(path) and not os.path.isdir(path):
            self.show_dialog("Error", f"La ruta no es una carpeta:\n{path}")
            return
        
        self.music_folder = path
        
        if ConfigManager.set_music_folder(path):
            print(f"✅ Carpeta de música guardada: {path}")
            self.reload_song_list(path)
            self.show_dialog("¡Carpeta actualizada!", f"Carpeta de música:\n{path}\n\nLa lista de canciones se ha actualizado.")
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