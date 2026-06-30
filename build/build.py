# build/build.py
import os
import sys
import platform
import subprocess
from pathlib import Path
import shutil


def build():
    """Сборка приложения с помощью PyInstaller"""

    # Определяем платформу
    system = platform.system()
    is_windows = system == 'Windows'
    is_mac = system == 'Darwin'
    is_linux = system == 'Linux'

    # Пути
    root = Path(__file__).parent.parent
    src = root / 'src'
    dist = root / 'dist'
    build_dir = root / 'build'

    # Создаем папки
    dist.mkdir(exist_ok=True)
    (build_dir / 'spec').mkdir(parents=True, exist_ok=True)

    # Определяем параметры сборки
    if is_windows:
        icon = str(src / 'resources' / 'icon.ico')
        exe_name = 'CodeWeaver.exe'
    elif is_mac:
        icon = str(src / 'resources' / 'icon.icns')
        exe_name = 'CodeWeaver.app'
    else:
        icon = str(src / 'resources' / 'icon.svg')
        exe_name = 'CodeWeaver'

    # Команда PyInstaller
    cmd = [
        'pyinstaller',
        '--name', 'CodeWeaver',
        '--onefile',
        '--windowed',
        '--add-data', f'{src}/locales:locales',
        '--add-data', f'{src}/resources:resources',
        '--hidden-import', 'json',
        '--hidden-import', 're',
        '--hidden-import', 'fnmatch',
        '--hidden-import', 'dataclasses',
        '--collect-all', 'PyQt5',
    ]

    if is_windows and icon:
        cmd.extend(['--icon', icon])

    if is_mac:
        cmd.extend(['--osx-bundle-identifier', 'com.codeweaver.app'])
        if icon:
            cmd.extend(['--icon', icon])

    cmd.append(str(src / 'codeweaver.py'))

    # Запускаем сборку
    print(f"Building for {system}...")
    result = subprocess.run(cmd, cwd=str(root))

    if result.returncode != 0:
        print("Build failed!")
        sys.exit(1)

    # Копируем результат
    source = root / 'dist' / 'CodeWeaver'
    if is_windows:
        source = root / 'dist' / 'CodeWeaver.exe'
    elif is_mac:
        source = root / 'dist' / 'CodeWeaver.app'

    if source.exists():
        dest = dist / exe_name
        if dest.exists():
            if dest.is_dir():
                shutil.rmtree(dest)
            else:
                dest.unlink()
        shutil.move(str(source), str(dest))
        print(f"Build complete: {dest}")
    else:
        print(f"Build output not found at {source}")
        sys.exit(1)


if __name__ == '__main__':
    build()