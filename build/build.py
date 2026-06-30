# build/build.py
import os
import sys
import platform
import subprocess
from pathlib import Path
import shutil

def create_icons():
    """Создает иконки для разных платформ если их нет"""
    src_dir = Path(__file__).parent.parent / 'src' / 'resources'

    # Проверяем наличие SVG
    svg_path = src_dir / 'icon.svg'
    if not svg_path.exists():
        print("Warning: icon.svg not found")
        return

    # Создаем ICO для Windows (используя библиотеку PIL или конвертер)
    try:
        from PIL import Image
        img = Image.open(svg_path)

        # Создаем ICO
        ico_path = src_dir / 'icon.ico'
        if not ico_path.exists():
            # Сохраняем как ICO с несколькими размерами
            img.save(ico_path, format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
            print(f"Created icon.ico")
    except ImportError:
        print("PIL not installed, skipping icon creation")
    except Exception as e:
        print(f"Error creating icons: {e}")

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

    # Проверяем существование файлов
    if not (src / 'codeweaver.py').exists():
        print(f"Error: {src / 'codeweaver.py'} not found!")
        sys.exit(1)

    # Проверяем существование locales
    locales_dir = src / 'resources' / 'locales'
    if not locales_dir.exists():
        print(f"Error: {locales_dir} not found!")
        sys.exit(1)

    # Команда PyInstaller
    cmd = [
        'pyinstaller',
        '--name', 'CodeWeaver',
        '--onefile',
        '--windowed',
        # Правильные пути к данным
        '--add-data', f'{src}/resources/locales;locales',  # Для Windows используем ;
        '--add-data', f'{src}/resources;resources',
        '--hidden-import', 'json',
        '--hidden-import', 're',
        '--hidden-import', 'fnmatch',
        '--hidden-import', 'dataclasses',
        '--collect-all', 'PyQt5',
        '--collect-all', 'PyQt5.QtCore',
        '--collect-all', 'PyQt5.QtGui',
        '--collect-all', 'PyQt5.QtWidgets',
        # Исключаем ненужное
        '--exclude-module', 'tkinter',
        '--exclude-module', 'test',
        '--exclude-module', 'pydoc',
    ]

    if is_windows and icon and Path(icon).exists():
        cmd.extend(['--icon', icon])
    elif is_windows:
        print("Warning: icon.ico not found, building without icon")

    if is_mac:
        cmd.extend(['--osx-bundle-identifier', 'com.codeweaver.app'])
        if icon and Path(icon).exists():
            cmd.extend(['--icon', icon])
        elif is_mac:
            print("Warning: icon.icns not found, building without icon")

    # Добавляем путь к основному файлу
    main_script = str(src / 'codeweaver.py')
    if not Path(main_script).exists():
        print(f"Error: {main_script} not found!")
        sys.exit(1)

    cmd.append(main_script)

    # Выводим команду для отладки
    print(f"Running: {' '.join(cmd)}")
    print(f"Working directory: {root}")

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
        # Показываем содержимое dist для отладки
        dist_path = root / 'dist'
        if dist_path.exists():
            print(f"Contents of {dist_path}:")
            for item in dist_path.iterdir():
                print(f"  - {item}")
        sys.exit(1)


if __name__ == '__main__':
    build()