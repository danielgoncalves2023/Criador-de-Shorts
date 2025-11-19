# rotas/__init__.py
from .transcricao import transcricao_bp
from .youtube import youtube_bp
from .analise import analise_bp
from .biblioteca import biblioteca_bp
import importlib.util
import sys
import os

# Importa o blueprint de áudio
audio_path = os.path.join(os.path.dirname(__file__), 'baixar-audio.py')
spec = importlib.util.spec_from_file_location('baixar_audio', audio_path)
baixar_audio = importlib.util.module_from_spec(spec)
sys.modules['baixar_audio'] = baixar_audio
spec.loader.exec_module(baixar_audio)
audio_bp = baixar_audio.audio_bp

# Importa o blueprint de shorts
shorts_path = os.path.join(os.path.dirname(__file__), 'baixar-shorts.py')
spec_shorts = importlib.util.spec_from_file_location('baixar_shorts', shorts_path)
baixar_shorts = importlib.util.module_from_spec(spec_shorts)
sys.modules['baixar_shorts'] = baixar_shorts
spec_shorts.loader.exec_module(baixar_shorts)
shorts_bp = baixar_shorts.shorts_bp

# Importa o blueprint de processar-video
processar_path = os.path.join(os.path.dirname(__file__), 'processar-video.py')
spec_processar = importlib.util.spec_from_file_location('processar_video', processar_path)
processar_video = importlib.util.module_from_spec(spec_processar)
sys.modules['processar_video'] = processar_video
spec_processar.loader.exec_module(processar_video)
processar_bp = processar_video.processar_bp

__all__ = [
    'youtube_bp',
    'transcricao_bp',
    'audio_bp',
    'analise_bp',
    'shorts_bp',
    'processar_bp',
    'biblioteca_bp'
]