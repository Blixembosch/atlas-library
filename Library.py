"""Atlas Library - Geriye Dönük Uyumluluk Giriş Noktası.

Bu dosya `streamlit run Library.py` komutunun sorunsuz çalışmasını sağlamak
amacıyla doğrudan modern modüler `app.py` giriş noktasını çalıştırır.
"""

from __future__ import annotations

import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

# Modern modüler uygulamayı çalıştır
import app