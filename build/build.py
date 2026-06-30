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
        icon = src / 'resources' / 'icon.ico'
        exe_name = 'CodeWeaver.exe'
    elif is_mac:
        icon = src / 'resources' / 'icon.icns'
        exe_name = 'CodeWeaver.app'
    else:
        icon = src / 'resources' / 'icon.svg'
        exe_name = 'CodeWeaver'

    # Проверяем существование файлов
    main_script = src / 'codeweaver.py'
    if not main_script.exists():
        print(f"Error: {main_script} not found!")
        sys.exit(1)

    # Проверяем существование locales
    locales_dir = src / 'resources' / 'locales'
    if not locales_dir.exists():
        print(f"Error: {locales_dir} not found!")
        sys.exit(1)

    # Формируем команду PyInstaller
    cmd = [
        'pyinstaller',
        '--name', 'CodeWeaver',
        '--onefile',
        '--windowed',
        '--noconfirm',
    ]

    # Добавляем данные в зависимости от платформы
    if is_windows:
        # Для Windows используем ; как разделитель
        cmd.extend([
            '--add-data', f'{src / "resources" / "locales"};locales',
            '--add-data', f'{src / "resources"};resources',
        ])
    else:
        # Для Linux/macOS используем : как разделитель
        cmd.extend([
            '--add-data', f'{src / "resources" / "locales"}:locales',
            '--add-data', f'{src / "resources"}:resources',
        ])

    # Добавляем скрытые импорты
    cmd.extend([
        '--hidden-import', 'json',
        '--hidden-import', 're',
        '--hidden-import', 'fnmatch',
        '--hidden-import', 'dataclasses',
    ])

    # Добавляем PyQt5
    cmd.extend([
        '--collect-all', 'PyQt5',
        '--collect-all', 'PyQt5.QtCore',
        '--collect-all', 'PyQt5.QtGui',
        '--collect-all', 'PyQt5.QtWidgets',
    ])

    # Исключаем ненужное
    cmd.extend([
        '--exclude-module', 'tkinter',
        '--exclude-module', 'test',
        '--exclude-module', 'pydoc',
    ])

    # Добавляем иконку если есть
    if icon.exists():
        cmd.extend(['--icon', str(icon)])
    else:
        print(f"Warning: Icon not found at {icon}")

    # Добавляем основной файл
    cmd.append(str(main_script))

    # Выводим команду для отладки
    print(f"Running: {' '.join(cmd)}")
    print(f"Working directory: {root}")

    # Запускаем сборку
    print(f"Building for {system}...")
    result = subprocess.run(cmd, cwd=str(root), shell=is_windows)

    if result.returncode != 0:
        print("Build failed!")
        sys.exit(1)

    # Проверяем результат
    dist_path = root / 'dist'
    if not dist_path.exists():
        print(f"Error: dist folder not found at {dist_path}")
        sys.exit(1)

    # Ищем собранный файл
    source = None
    if is_windows:
        source = dist_path / 'CodeWeaver.exe'
    elif is_mac:
        source = dist_path / 'CodeWeaver.app'
    else:
        source = dist_path / 'CodeWeaver'

    if not source or not source.exists():
        print(f"Error: Build output not found at {source}")
        print("Contents of dist folder:")
        for item in dist_path.iterdir():
            print(f"  - {item.name}")
        sys.exit(1)

    # Копируем в целевое место
    dest = dist / exe_name
    if dest.exists():
        if dest.is_dir():
            shutil.rmtree(dest)
        else:
            dest.unlink()

    # Используем copy вместо move для надежности
    if dest.is_dir():
        shutil.copytree(source, dest)
    else:
        shutil.copy2(source, dest)

    print(f"Build complete: {dest}")
    print(f"File size: {dest.stat().st_size / 1024 / 1024:.2f} MB")


if __name__ == '__main__':
    build()