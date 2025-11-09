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
        print("✅ Módulos de Android cargados correctamente")
    except ImportError as e:
        print(f"⚠️ Módulos de Android no disponibles: {e}")

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
            print(f"📁 Carpeta inicial configurada: {self.music_folder}")
    
    def request_android_permissions(self):
        """Solicitar permisos de almacenamiento en Android."""
        try:
            request_permissions([
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE
            ])
            print("✅ Permisos de almacenamiento solicitados")
        except Exception as e:
            print(f"❌ Error solicitando permisos: {e}")
    
    def open_file_manager(self):
        """Abrir el selector de carpetas según la plataforma."""
        print(f"🔧 Abriendo selector de carpetas (Android: {ANDROID})")
        
        if ANDROID:
            self.open_android_folder_picker()
        else:
            self.open_desktop_file_manager()
    
    def open_android_folder_picker(self):
        """Abrir el explorador de archivos nativo de Android (SAF)."""
        try:
            print("📂 Iniciando Storage Access Framework...")
            
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
                print("📍 Carpeta inicial configurada: Music")
            except Exception as e:
                print(f"⚠️ No se pudo configurar carpeta inicial: {e}")
            
            # Iniciar el selector
            mActivity.startActivityForResult(intent, 42)
            print("✅ Selector de carpetas abierto")
            
        except Exception as e:
            print(f"❌ Error abriendo selector de Android: {e}")
            import traceback
            traceback.print_exc()
            self.show_dialog("Error", f"No se pudo abrir el selector:\n{str(e)}")
    
    def on_activity_result(self, request_code, result_code, intent):
        """Callback cuando el usuario selecciona una carpeta en Android."""
        print(f"📨 Activity result recibido - Code: {request_code}, Result: {result_code}")
        
        if request_code != 42:
            print("⏭️ No es nuestro request code, ignorando")
            return
        
        # result_code -1 = RESULT_OK (el usuario seleccionó algo)
        if result_code == -1 and intent is not None:
            try:
                # Obtener la URI de la carpeta seleccionada
                tree_uri = intent.getData()
                uri_string = tree_uri.toString()
                
                # Decodificar caracteres especiales (%3A -> :, %2F -> /)
                uri_string = uri_string.replace("%3A", ":").replace("%2F", "/").replace("%20", " ")
                
                print(f"📂 URI decodificado: {uri_string}")
                
                # Extraer el path del URI
                path = None
                
                # Caso 1: URIs con "primary:" (almacenamiento interno)
                if "primary:" in uri_string:
                    print("🔍 Detectado almacenamiento primario (internal storage)")
                    
                    # Intentar extraer desde "tree/primary:"
                    if "/tree/primary:" in uri_string:
                        parts = uri_string.split("/tree/primary:")
                        if len(parts) > 1:
                            relative_path = parts[1].split("/document/")[0]
                            
                            external_storage = primary_external_storage_path()
                            path = os.path.join(external_storage, relative_path)
                            print(f"📁 Path extraído (tree): {path}")
                    
                    # Si no funcionó, intentar desde "document/primary:"
                    elif "/document/primary:" in uri_string:
                        parts = uri_string.split("/document/primary:")
                        if len(parts) > 1:
                            relative_path = parts[1]
                            
                            external_storage = primary_external_storage_path()
                            path = os.path.join(external_storage, relative_path)
                            print(f"📁 Path extraído (document): {path}")
                    
                    # Último intento: buscar cualquier "primary:"
                    else:
                        parts = uri_string.split("primary:")
                        if len(parts) > 1:
                            relative_path = parts[-1].split("/")[0]
                            
                            external_storage = primary_external_storage_path()
                            path = os.path.join(external_storage, relative_path)
                            print(f"📁 Path extraído (genérico): {path}")
                
                # Caso 2: URIs con números (tarjetas SD)
                elif any(char.isdigit() for char in uri_string.split(":")[0]):
                    print("💾 Detectado almacenamiento externo (SD card)")
                    # Usar Clock.schedule_once para mostrar el diálogo en el thread principal
                    from kivy.clock import Clock
                    Clock.schedule_once(lambda dt: self.show_dialog(
                        "Almacenamiento externo",
                        "La carpeta seleccionada está en almacenamiento externo (tarjeta SD).\n\nPor favor selecciona una carpeta del almacenamiento interno."
                    ), 0)
                    return
                
                # Si se obtuvo un path, usarlo (desde el thread principal de Kivy)
                if path:
                    print(f"✅ Path final extraído: {path}")
                    # Usar Clock.schedule_once para ejecutar en el thread principal
                    from kivy.clock import Clock
                    Clock.schedule_once(lambda dt: self.select_folder(path), 0)
                else:
                    print(f"❌ No se pudo convertir el URI: {uri_string}")
                    from kivy.clock import Clock
                    Clock.schedule_once(lambda dt: self.show_dialog(
                        "No se pudo determinar la ruta",
                        f"URI recibido:\n{uri_string}\n\nPor favor intenta con otra carpeta."
                    ), 0)
                        
            except Exception as e:
                print(f"❌ Error procesando carpeta seleccionada: {e}")
                import traceback
                traceback.print_exc()
                from kivy.clock import Clock
                Clock.schedule_once(lambda dt: self.show_dialog("Error", f"Error al procesar la carpeta:\n{str(e)}"), 0)
        else:
            print("❌ Usuario canceló la selección o result_code incorrecto")
    
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
        print(f"🔄 Intentando seleccionar carpeta: {path}")
        
        # Verificar si la carpeta existe
        exists = os.path.exists(path)
        is_dir = os.path.isdir(path) if exists else False
        
        print(f"   📊 Existe: {exists}")
        print(f"   📊 Es directorio: {is_dir}")
        
        if not exists:
            try:
                os.makedirs(path)
                print(f"✅ Carpeta creada: {path}")
            except Exception as e:
                print(f"⚠️ No se pudo crear la carpeta: {e}")
        
        if exists and not is_dir:
            self.show_dialog("Error", f"La ruta no es una carpeta:\n{path}")
            return
        
        # Actualizar la propiedad
        self.music_folder = path
        print(f"🔄 music_folder actualizado a: {self.music_folder}")
        
        # Guardar en la configuración
        if ConfigManager.set_music_folder(path):
            print(f"✅ Carpeta guardada en configuración: {path}")
            
            # Recargar la lista de canciones
            self.reload_song_list(path)
            
            # Contar archivos
            try:
                files = os.listdir(path)
                audio_files = [f for f in files if f.lower().endswith(('.mp3', '.m4a', '.flac', '.wav', '.ogg'))]
                print(f"📊 Archivos de audio encontrados: {len(audio_files)}")
                
                self.show_dialog(
                    "¡Carpeta actualizada!", 
                    f"Carpeta de música:\n{path}\n\n{len(audio_files)} archivo(s) de audio encontrado(s)."
                )
            except Exception as e:
                print(f"⚠️ No se pudo listar archivos: {e}")
                self.show_dialog(
                    "¡Carpeta actualizada!", 
                    f"Carpeta de música:\n{path}"
                )
        else:
            print(f"❌ No se pudo guardar en configuración")
            self.show_dialog("Error", "No se pudo guardar la configuración")
    
    def reload_song_list(self, music_folder):
        """Recargar la lista de canciones desde la nueva carpeta."""
        try:
            from utils.file_manager import find_music_files
            
            print(f"🔄 Buscando canciones en: {music_folder}")
            songs = find_music_files(music_folder)
            print(f"✅ Canciones encontradas: {len(songs)}")
            
            song_list_screen = self.manager.get_screen('list')
            song_list_screen.songs = songs
            
            if hasattr(song_list_screen, 'on_pre_enter'):
                song_list_screen.on_pre_enter()
            
            print(f"✅ Lista de reproducción actualizada")
            
        except Exception as e:
            print(f"❌ Error al recargar canciones: {e}")
            import traceback
            traceback.print_exc()
    
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