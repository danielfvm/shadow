import enum

class BackgroundMode(enum.Enum):
    WINDOW = "window"
    BACKGROUND = "background"
    ROOT = "root"

class QualityMode(enum.Enum):
    PIXEL = "pixel"
    SMOOTH = "smooth"

class Config():
    SPEED: float = 1.0
    OPACITY: float = 1.0
    BACKGROUND_MODE = BackgroundMode.BACKGROUND
    DISPLAY = None
    FRAMELIMIT: int = 60
    QUALITY: float = 1.0
    QUALITY_MODE = QualityMode.SMOOTH

