"""
diagnostico.py - Corre este script para ver qué está pasando con PyQtWebEngine
"""
import sys
print(f"Python: {sys.version}")
print(f"Ejecutable: {sys.executable}\n")

# Test PyQt5
try:
    import PyQt5
    print(f"✅ PyQt5: {PyQt5.QtCore.PYQT_VERSION_STR}")
except Exception as e:
    print(f"❌ PyQt5: {e}")

# Test PyQtWebEngine - paso a paso
print("\n--- Probando PyQtWebEngine ---")
try:
    import PyQt5.QtWebEngineWidgets
    print("✅ PyQt5.QtWebEngineWidgets importado OK")
except Exception as e:
    print(f"❌ PyQt5.QtWebEngineWidgets: {e}")

try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView
    print("✅ QWebEngineView importado OK")
except Exception as e:
    print(f"❌ QWebEngineView: {e}")

try:
    from PyQt5.QtWebEngineWidgets import QWebEngineSettings
    print("✅ QWebEngineSettings importado OK")
    # Check which attributes exist
    attrs = ["PluginsEnabled", "PdfViewerEnabled", "LocalContentCanAccessFileUrls", "JavascriptEnabled"]
    for attr in attrs:
        has = hasattr(QWebEngineSettings, attr)
        print(f"   {'✅' if has else '⚠️ FALTA'} QWebEngineSettings.{attr}")
except Exception as e:
    print(f"❌ QWebEngineSettings: {e}")

# Test pip list
print("\n--- Paquetes instalados ---")
import subprocess
result = subprocess.run([sys.executable, "-m", "pip", "show", "PyQtWebEngine"],
                       capture_output=True, text=True)
if result.returncode == 0:
    print(result.stdout)
else:
    print("❌ PyQtWebEngine NO está instalado según pip")
    print("   Ejecuta: pip install PyQtWebEngine")
