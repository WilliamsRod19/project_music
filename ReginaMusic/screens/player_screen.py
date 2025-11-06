from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty, BooleanProperty, NumericProperty
from kivy.clock import Clock
from ffpyplayer.player import MediaPlayer
from mutagen import File as MutagenFile
import os
import random
import logging

# Silenciar warnings molestos de FFmpeg (opcional)
logging.getLogger('libav').setLevel(logging.ERROR)
logging.getLogger('libav.mp3float').setLevel(logging.CRITICAL)

class PlayerScreen(Screen):
    # Propiedades de Kivy
    current_song = StringProperty("")
    shuffle = BooleanProperty(False)
    repeat = BooleanProperty(False)
    duration = NumericProperty(1)
    slider_value = NumericProperty(0)
    is_paused = BooleanProperty(False)
    
    # Propiedades para mostrar el tiempo formateado
    current_time_text = StringProperty("0:00")
    duration_text = StringProperty("0:00")

    # Variables internas
    song_list = []
    index = 0
    player = None
    
    # Control del tiempo (simple)
    start_time = 0.0
    elapsed_time = 0.0
    is_seeking = False
    
    # Eventos del Clock
    progress_event = None
    eof_check_event = None

    # --------------------------------------------------------------------------
    ## OBTENER DURACIÓN REAL
    # --------------------------------------------------------------------------

    def format_time(self, seconds):
        """Convierte segundos a formato MM:SS o HH:MM:SS."""
        seconds = int(seconds)
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes}:{secs:02d}"

    def get_audio_duration(self, filepath):
        """Obtiene la duración REAL del archivo de audio usando mutagen."""
        try:
            audio = MutagenFile(filepath)
            if audio is not None and hasattr(audio.info, 'length'):
                duration = audio.info.length
                print(f"✅ Duración real (mutagen): {duration:.2f}s")
                return duration
        except Exception as e:
            print(f"⚠️ Error al leer con mutagen: {e}")
        
        # Fallback: Estimar por tamaño de archivo
        try:
            file_size = os.path.getsize(filepath)
            duration = file_size / 20000
            print(f"📏 Duración estimada por tamaño: {duration:.2f}s")
            return duration
        except:
            return 180

    # --------------------------------------------------------------------------
    ## CONTROL DE CARGA Y REPRODUCCIÓN
    # --------------------------------------------------------------------------

    def load_song(self, song_path, songs):
        """Carga una nueva canción y comienza la reproducción."""
        self.stop_song()
        
        # Inicializar UI y lista
        self.current_song = os.path.basename(song_path)
        self.song_list = songs
        self.index = songs.index(song_path)
        self.slider_value = 0 
        self.is_paused = False

        # Obtener duración REAL con mutagen
        self.duration = self.get_audio_duration(song_path)
        self.duration_text = self.format_time(self.duration)

        # Crear el reproductor
        try:
            ff_opts = {'paused': False, 'sync': 'audio'}
            self.player = MediaPlayer(song_path, ff_opts=ff_opts)
        except Exception as e:
            print(f"Error al cargar la canción: {e}")
            self.player = None
            return

        # Reiniciar el contador de tiempo
        self.start_time = Clock.get_time()
        self.elapsed_time = 0.0

        # Programar actualizaciones
        if self.progress_event:
            self.progress_event.cancel()
        if self.eof_check_event:
            self.eof_check_event.cancel()
            
        self.progress_event = Clock.schedule_interval(self.update_progress, 0.1)
        self.eof_check_event = Clock.schedule_interval(self.check_eof, 0.5)

    def stop_song(self):
        """Detiene la reproducción y limpia recursos."""
        if self.progress_event:
            self.progress_event.cancel()
            self.progress_event = None
        if self.eof_check_event:
            self.eof_check_event.cancel()
            self.eof_check_event = None
            
        if self.player:
            try:
                self.player.close_player()
            except:
                pass
            self.player = None
            self.is_paused = False

    def play_pause(self):
        """Alterna pausa/reproducción."""
        if self.player:
            self.is_paused = not self.is_paused
            self.player.set_pause(self.is_paused)
            
            if self.is_paused:
                # Al pausar: guardar tiempo transcurrido
                self.elapsed_time += Clock.get_time() - self.start_time
            else:
                # Al reanudar: reiniciar el marcador
                self.start_time = Clock.get_time()

    # --------------------------------------------------------------------------
    ## CONTROL DE PLAYLIST
    # --------------------------------------------------------------------------

    def next_song(self):
        """Pasa a la siguiente canción."""
        if not self.song_list:
            return
        
        # Si REPEAT está activado, repetir la misma canción
        if self.repeat:
            print("🔁 Repitiendo canción actual")
            self.load_song(self.song_list[self.index], self.song_list)
            return
            
        # Si NO hay repeat, continuar con la lógica normal
        if self.shuffle:
            if len(self.song_list) > 1:
                remaining = [i for i in range(len(self.song_list)) if i != self.index]
                if not remaining:
                    self.stop_song()
                    self.slider_value = 1
                    return
                self.index = random.choice(remaining)
            else:
                self.stop_song()
                self.slider_value = 1
                return
        else:
            # Modo normal (sin shuffle, sin repeat)
            self.index += 1
            if self.index >= len(self.song_list):
                # Llegamos al final, detener
                self.index = len(self.song_list) - 1
                self.stop_song()
                self.slider_value = 1
                return
        
        self.load_song(self.song_list[self.index], self.song_list)

    def prev_song(self):
        """Vuelve a la canción anterior."""
        if not self.song_list:
            return
        
        self.index -= 1
        if self.index < 0:
            if self.repeat:
                self.index = len(self.song_list) - 1
            else:
                self.index = 0
        
        self.load_song(self.song_list[self.index], self.song_list)

    # --------------------------------------------------------------------------
    ## ACTUALIZACIÓN DE PROGRESO (SIMPLE)
    # --------------------------------------------------------------------------

    def update_progress(self, dt):
        """Actualiza el slider basado en el tiempo transcurrido."""
        if not self.player or self.is_paused or self.is_seeking:
            return
        
        # Calcular tiempo actual
        current_time = self.elapsed_time + (Clock.get_time() - self.start_time)
        
        # Actualizar slider
        if self.duration > 0:
            self.slider_value = min(current_time / self.duration, 1.0)
        
        # Actualizar el texto del tiempo actual
        self.current_time_text = self.format_time(current_time)

    def check_eof(self, dt):
        """Verifica si la canción terminó."""
        if not self.player:
            return
        
        # Calcular tiempo actual
        current_time = self.elapsed_time + (Clock.get_time() - self.start_time)
        
        # Si superamos la duración, pasar a la siguiente (con margen de 0.5s antes)
        if current_time >= self.duration - 0.5:
            print(f"🔚 Canción terminada ({current_time:.2f}s / {self.duration:.2f}s)")
            
            # IMPORTANTE: Cancelar eventos primero
            if self.eof_check_event:
                self.eof_check_event.cancel()
                self.eof_check_event = None
            if self.progress_event:
                self.progress_event.cancel()
                self.progress_event = None
            
            # Pausar el reproductor ANTES de cerrarlo (evita el crash)
            if self.player:
                try:
                    self.player.set_pause(True)
                except:
                    pass
            
            # Poner el slider al final
            self.slider_value = 1
            
            # Cambiar a la siguiente canción después de un momento
            # stop_song() se encargará de cerrar el reproductor limpiamente
            Clock.schedule_once(lambda dt: self.next_song(), 0.2)

    # --------------------------------------------------------------------------
    ## CONTROL DEL SLIDER
    # --------------------------------------------------------------------------

    def go_back(self):
        """Volver a la lista de canciones."""
        # La música sigue sonando en segundo plano
        self.manager.current = 'list'

    def on_slider_touch_down(self):
        """Usuario presiona el slider."""
        self.is_seeking = True
    
    def on_slider_touch_up(self, value):
        """Usuario suelta el slider."""
        self.seek(value)
        self.is_seeking = False
        
        # Actualizar el tiempo mostrado al hacer seek
        current_time = self.elapsed_time + (Clock.get_time() - self.start_time)
        self.current_time_text = self.format_time(current_time)
                
    def seek(self, value):
        """Cambia la posición de reproducción."""
        if self.player and self.duration > 0:
            pos = value * self.duration
            
            try:
                self.player.seek(pos, relative=False)
                # Reiniciar los contadores de tiempo
                self.elapsed_time = pos
                self.start_time = Clock.get_time()
            except Exception as e:
                print(f"Error en seek: {e}")