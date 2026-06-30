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

    # PyInstaller всегда создает файл в корне dist с именем, указанным в --name
    pyinstaller_output = dist_path / 'CodeWeaver.exe' if is_windows else dist_path / 'CodeWeaver'

    # На случай если PyInstaller создал с другим расширением
    if is_windows and not pyinstaller_output.exists():
        # Проверяем возможные варианты
        possible_names = ['CodeWeaver.exe', 'CodeWeaver']
        for name in possible_names:
            test_path = dist_path / name
            if test_path.exists():
                pyinstaller_output = test_path
                break

    if not pyinstaller_output.exists():
        print(f"Error: Build output not found")
        print("Contents of dist folder:")
        for item in dist_path.iterdir():
            print(f"  - {item.name}")
        sys.exit(1)

    # Целевой файл уже должен быть в правильном месте, но на всякий случай проверяем
    final_path = dist / exe_name

    # Если файл уже в нужном месте и имеет правильное имя
    if pyinstaller_output == final_path:
        print(f"Build complete: {final_path}")
        if final_path.exists():
            print(f"File size: {final_path.stat().st_size / 1024 / 1024:.2f} MB")
        return

    # Если файл в другом месте - копируем/перемещаем
    if pyinstaller_output != final_path:
        print(f"Moving {pyinstaller_output} to {final_path}")

        # Удаляем существующий файл если есть
        if final_path.exists():
            if final_path.is_dir():
                shutil.rmtree(final_path)
            else:
                final_path.unlink()

        # Копируем или перемещаем
        if pyinstaller_output.is_dir():
            shutil.copytree(pyinstaller_output, final_path)
        else:
            shutil.copy2(pyinstaller_output, final_path)

        # Удаляем исходный файл если это не тот же файл
        if pyinstaller_output != final_path and pyinstaller_output.exists():
            if pyinstaller_output.is_dir():
                shutil.rmtree(pyinstaller_output)
            else:
                pyinstaller_output.unlink()

    print(f"Build complete: {final_path}")
    if final_path.exists():
        print(f"File size: {final_path.stat().st_size / 1024 / 1024:.2f} MB")


if __name__ == '__main__':
    build()