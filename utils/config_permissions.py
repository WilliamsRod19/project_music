from kivy.utils import platform
from android.permissions import request_permissions, Permission

def get_permissions():
    if platform == "android":
        try:
            request_permissions([
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE
            ])
            print("Permisos solicitados correctamente.")
        except Exception as e:
            print(f"Error pidiendo permisos: {e}")
