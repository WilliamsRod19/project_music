from kivymd.uix.screen import MDScreen
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivy.properties import StringProperty, BooleanProperty
from utils.config_manager import ConfigManager
import os
import threading

class DownloaderScreen(MDScreen):
    url_input = StringProperty("")
    download_status = StringProperty("Esperando URL...")
    is_downloading = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dialog = None
    
    def start_download(self, url):
        """Iniciar la descarga de YouTube."""
        if not url or not url.strip():
            self.show_dialog("Error", "Por favor ingresa una URL válida")
            return
        
        if not ("youtube.com" in url or "youtu.be" in url):
            self.show_dialog("Error", "Por favor ingresa una URL de YouTube válida")
            return
        
        # Verificar que existe la carpeta de música
        music_folder = ConfigManager.get_music_folder()
        if not os.path.exists(music_folder):
            self.show_dialog("Error", f"La carpeta de música no existe:\n{music_folder}\n\nConfigúrala en Ajustes")
            return
        
        self.is_downloading = True
        self.download_status = "Descargando..."
        
        # Ejecutar descarga en un thread separado para no bloquear la UI
        thread = threading.Thread(target=self._download_thread, args=(url, music_folder))
        thread.daemon = True
        thread.start()
    
    def _download_thread(self, url, output_folder):
        """Thread que realiza la descarga usando yt-dlp."""
        import sys
        import io
        from kivy.clock import Clock

        try:
            import yt_dlp

            # Guardar stdout/stderr originales
            old_stdout, old_stderr = sys.stdout, sys.stderr

            # Crear buffers para que yt-dlp no intente escribir en la consola Kivy
            sys.stdout, sys.stderr = io.StringIO(), io.StringIO()

            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': os.path.join(output_folder, '%(title)s.%(ext)s'),
                'quiet': True,           # 👈 silencio total
                'no_warnings': True,     # 👈 sin advertencias
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'Desconocido')

                Clock.schedule_once(
                    lambda dt: self._download_complete(True, f"✅ Descargado: {title}"),
                    0
                )

        except ImportError:
            Clock.schedule_once(
                lambda dt: self._download_complete(
                    False,
                    "❌ yt-dlp no está instalado.\nInstálalo con: pip install yt-dlp"
                ),
                0
            )

        except Exception as e:
            error_msg = str(e)
            if "ffmpeg" in error_msg.lower():
                error_msg = "❌ FFmpeg no está instalado.\nDescárgalo de: https://ffmpeg.org/download.html"
            else:
                error_msg = f"❌ Error: {error_msg}"

            Clock.schedule_once(lambda dt: self._download_complete(False, error_msg), 0)

        finally:
            # Restaurar stdout/stderr originales para no afectar Kivy
            sys.stdout, sys.stderr = old_stdout, old_stderr
    
    def _download_complete(self, success, message):
        """ Callback cuando termina la descarga. """
        self.is_downloading = False
        self.download_status = message
        
        if success:
            # Recargar la lista de canciones automáticamente
            self.reload_song_list()
            
            self.show_dialog("Éxito", message + "\n\nLa canción ya está disponible en tu lista.")
            self.url_input = ""  # Limpiar el campo
        else:
            self.show_dialog("Error", message)
            print(message)
    
    def reload_song_list(self):
        """Recargar la lista de canciones después de descargar."""
        try:
            from utils.file_manager import find_music_files
            from utils.config_manager import ConfigManager
            
            music_folder = ConfigManager.get_music_folder()
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
    
    def go_back(self):
        """Volver a la lista de canciones."""
        self.manager.current = 'list'