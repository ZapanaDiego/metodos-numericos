"""Registra el visor Panda3D en el catálogo de aplicaciones de Linux."""

import os
from pathlib import Path


def valor_desktop(texto):
    """Escapa el valor de una clave del archivo .desktop."""
    return texto.replace("\\", "\\\\").replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")


def ejecutable_desktop(ruta):
    """Escapa el ejecutable dentro del argumento entre comillas de Exec."""
    texto = str(ruta).replace("%", "%%")
    for caracter in ('\\', '"', '`', '$'):
        texto = texto.replace(caracter, "\\" + caracter)
    return valor_desktop(f'"{texto}"')


def main():
    proyecto = Path(__file__).resolve().parents[1]
    python = proyecto / ".venv" / "bin" / "python"
    if not python.is_file() or not os.access(python, os.X_OK):
        raise SystemExit(f"No se encuentra el Python del proyecto en {python}.")
    datos = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
    destino = datos / "applications" / "gwen-stacy-3d.desktop"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=Gwen Stacy - Simulador 3D\n"
        "Comment=Laboratorio de Euler y Runge-Kutta en Panda3D\n"
        f"Exec={ejecutable_desktop(python)} -m visual.app_panda3d\n"
        f"Path={valor_desktop(str(proyecto))}\n"
        f"TryExec={valor_desktop(str(python))}\n"
        "Icon=applications-science\n"
        "Terminal=false\n"
        "Categories=Education;Physics;\n"
        "StartupWMClass=gwen-stacy-3d\n",
        encoding="utf-8",
    )
    print(destino)


if __name__ == "__main__":
    main()
