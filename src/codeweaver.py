# src/codeweaver.py
import os
import sys
import json
import subprocess
from pathlib import Path
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# ============================================================
# ВСТРОЕННЫЙ CodeWeaver (код из репозитория)
# ============================================================

import re
import fnmatch
from typing import List, Optional, Set
from dataclasses import dataclass
from pathlib import Path as PathLib


@dataclass
class FileInfo:
    path: str
    is_dir: bool
    rel_path: str


class CodeWeaverEngine:
    """Встроенный движок CodeWeaver"""

    def __init__(self):
        self.ignore_patterns = []
        self.include_patterns = []
        self.root_dir = ""
        self.output_file = ""
        self.included_paths = []
        self.excluded_paths = []

    def generate(self, root_dir: str, output_file: str, ignore_patterns: List[str] = None,
                 include_patterns: List[str] = None) -> str:
        """Генерирует Markdown документацию"""
        self.root_dir = root_dir
        self.output_file = output_file
        self.ignore_patterns = ignore_patterns or []
        self.include_patterns = include_patterns or []
        self.included_paths = []
        self.excluded_paths = []

        # Сканируем файлы
        files = self._scan_directory(root_dir)

        # Фильтруем
        files = self._filter_files(files)

        # Генерируем Markdown
        content = self._generate_markdown(files, root_dir)

        # Сохраняем
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)

        return output_file

    def _scan_directory(self, root_dir: str) -> List[FileInfo]:
        """Рекурсивно сканирует директорию"""
        files = []
        root_path = PathLib(root_dir)

        for item in root_path.rglob('*'):
            rel_path = str(item.relative_to(root_path))
            files.append(FileInfo(
                path=str(item),
                is_dir=item.is_dir(),
                rel_path=rel_path.replace('\\', '/')
            ))

        return files

    def _filter_files(self, files: List[FileInfo]) -> List[FileInfo]:
        """Фильтрует файлы по include/ignore паттернам"""
        filtered = []

        for file in files:
            # Игнорируем корневую папку
            if file.rel_path == '.' or file.rel_path == '':
                continue

            # Проверяем ignore паттерны
            should_ignore = False
            for pattern in self.ignore_patterns:
                if fnmatch.fnmatch(file.rel_path, pattern) or re.search(pattern, file.rel_path):
                    should_ignore = True
                    break

            if should_ignore:
                self.excluded_paths.append(file.rel_path)
                continue

            # Если есть include паттерны, проверяем их
            if self.include_patterns:
                should_include = False
                for pattern in self.include_patterns:
                    if fnmatch.fnmatch(file.rel_path, pattern) or re.search(pattern, file.rel_path):
                        should_include = True
                        break

                if not should_include:
                    self.excluded_paths.append(file.rel_path)
                    continue

            # Если это папка, пропускаем (будет в tree view)
            if file.is_dir:
                continue

            self.included_paths.append(file.rel_path)
            filtered.append(file)

        return filtered

    def _generate_markdown(self, files: List[FileInfo], root_dir: str) -> str:
        """Генерирует Markdown с деревом и содержимым"""
        lines = []

        # Заголовок
        lines.append("# CodeBase Documentation")
        lines.append("")
        lines.append(f"Generated from: `{root_dir}`")
        lines.append("")

        # Tree View
        lines.append("## Tree View")
        lines.append("```")
        lines.append(self._generate_tree(root_dir))
        lines.append("```")
        lines.append("")

        # Content
        lines.append("## Content")
        lines.append("")

        for file_info in sorted(files, key=lambda x: x.rel_path):
            lines.append(f"### {file_info.rel_path}")
            lines.append("")

            # Определяем язык для блока кода
            ext = PathLib(file_info.path).suffix.lower()
            lang = self._get_language(ext)

            lines.append(f"```{lang}")
            try:
                with open(file_info.path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                    lines.append(content)
            except Exception as e:
                lines.append(f"[Ошибка чтения файла: {e}]")
            lines.append("```")
            lines.append("")

        return '\n'.join(lines)

    def _generate_tree(self, root_dir: str) -> str:
        """Генерирует дерево директорий"""
        root = PathLib(root_dir)
        lines = []

        # Собираем все пути
        all_paths = set()
        for file_info in self.included_paths:
            parts = file_info.split('/')
            for i in range(len(parts)):
                all_paths.add('/'.join(parts[:i + 1]))

        # Сортируем и строим дерево
        all_paths = sorted(all_paths)

        # Строим дерево
        def build_tree(paths):
            tree = {}
            for path in paths:
                parts = path.split('/')
                current = tree
                for part in parts:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
            return tree

        tree = build_tree(all_paths)

        def render_tree(tree, prefix=""):
            result = []
            items = sorted(tree.items())
            for i, (name, subtree) in enumerate(items):
                is_last = (i == len(items) - 1)
                if is_last:
                    result.append(f"{prefix}└── {name}")
                    result.extend(render_tree(subtree, prefix + "    "))
                else:
                    result.append(f"{prefix}├── {name}")
                    result.extend(render_tree(subtree, prefix + "│   "))
            return result

        lines = render_tree(tree)
        return '\n'.join(lines)

    def _get_language(self, ext: str) -> str:
        """Определяет язык для подсветки по расширению"""
        lang_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.html': 'html',
            '.css': 'css',
            '.json': 'json',
            '.xml': 'xml',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.md': 'markdown',
            '.sh': 'bash',
            '.bat': 'batch',
            '.ps1': 'powershell',
            '.go': 'go',
            '.rs': 'rust',
            '.c': 'c',
            '.cpp': 'cpp',
            '.h': 'c',
            '.hpp': 'cpp',
            '.java': 'java',
            '.kt': 'kotlin',
            '.swift': 'swift',
            '.rb': 'ruby',
            '.php': 'php',
            '.sql': 'sql',
            '.csv': 'csv',
            '.txt': 'text',
        }
        return lang_map.get(ext, 'text')


# ============================================================
# Локализация
# ============================================================

class Translator:
    def __init__(self):
        self.language = 'en'
        self.translations = {}
        self.load_translations()

    def load_translations(self):
        locales_dir = Path(__file__).parent / 'locales'

        for lang_file in locales_dir.glob('*.json'):
            try:
                with open(lang_file, 'r', encoding='utf-8') as f:
                    lang_data = json.load(f)
                    self.translations[lang_file.stem] = lang_data
            except Exception as e:
                print(f"Error loading {lang_file}: {e}")

    def set_language(self, lang):
        if lang in self.translations:
            self.language = lang
            return True
        return False

    def tr(self, key, default=None):
        if self.language in self.translations:
            if key in self.translations[self.language]:
                return self.translations[self.language][key]
        if default is not None:
            return default
        return key


# Глобальный экземпляр
translator = Translator()


def tr(key, default=None):
    return translator.tr(key, default)


# ============================================================
# GUI
# ============================================================

class CodeWeaverGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.output_path = None
        self.engine = CodeWeaverEngine()
        self.is_dark = True
        self.initUI()
        self.load_config()

    def initUI(self):
        self.setWindowTitle("CodeWeaver")
        self.setFixedSize(540, 520)

        screen = QApplication.primaryScreen().geometry()
        self.move((screen.width() - 540) // 2, (screen.height() - 520) // 2)

        self.setup_styles()

        main = QVBoxLayout()
        main.setContentsMargins(20, 16, 20, 16)
        main.setSpacing(10)

        # HEADER
        header = QHBoxLayout()
        header.setSpacing(8)
        title = QLabel("🧬 CodeWeaver")
        title.setObjectName("title")
        header.addWidget(title)
        subtitle = QLabel(tr("subtitle", "Documentation Generator"))
        subtitle.setObjectName("subtitle")
        header.addWidget(subtitle)
        header.addStretch()

        # Настройки
        settings_btn = QPushButton("⚙️")
        settings_btn.setObjectName("ghost")
        settings_btn.setFixedSize(32, 32)
        settings_btn.clicked.connect(self.show_settings)
        header.addWidget(settings_btn)

        main.addLayout(header)

        # ПУТИ
        paths = QGroupBox(tr("paths", "Paths"))
        paths_layout = QVBoxLayout()
        paths_layout.setSpacing(6)
        paths_layout.setContentsMargins(12, 10, 12, 10)

        # Входная
        input_row = QHBoxLayout()
        input_row.setSpacing(6)
        input_label = QLabel(tr("input", "Source Code"))
        input_label.setObjectName("label")
        input_label.setFixedWidth(70)
        input_row.addWidget(input_label)
        self.input_dir = QLineEdit()
        self.input_dir.setPlaceholderText(tr("select_folder", "Select code folder..."))
        input_row.addWidget(self.input_dir, 1)
        btn_in = QPushButton("📂")
        btn_in.setObjectName("ghost")
        btn_in.setFixedSize(28, 28)
        btn_in.clicked.connect(lambda: self.select_folder(self.input_dir))
        input_row.addWidget(btn_in)
        paths_layout.addLayout(input_row)

        # Выходная
        output_row = QHBoxLayout()
        output_row.setSpacing(6)
        output_label = QLabel(tr("output", "Save to"))
        output_label.setObjectName("label")
        output_label.setFixedWidth(70)
        output_row.addWidget(output_label)
        self.output_dir = QLineEdit()
        self.output_dir.setPlaceholderText(tr("select_folder", "Select folder to save..."))
        output_row.addWidget(self.output_dir, 1)
        btn_out = QPushButton("📂")
        btn_out.setObjectName("ghost")
        btn_out.setFixedSize(28, 28)
        btn_out.clicked.connect(lambda: self.select_folder(self.output_dir))
        output_row.addWidget(btn_out)
        paths_layout.addLayout(output_row)

        # Имя файла
        file_row = QHBoxLayout()
        file_row.setSpacing(6)
        file_label = QLabel(tr("filename", "Filename"))
        file_label.setObjectName("label")
        file_label.setFixedWidth(70)
        file_row.addWidget(file_label)
        self.output_file = QLineEdit("codebase.md")
        self.output_file.setFixedWidth(150)
        file_row.addWidget(self.output_file)
        file_row.addStretch()
        paths_layout.addLayout(file_row)

        paths.setLayout(paths_layout)
        main.addWidget(paths)

        # ИГНОРИРОВАНИЕ
        ignore = QGroupBox(tr("ignore", "Ignore Patterns"))
        ignore_layout = QVBoxLayout()
        ignore_layout.setSpacing(4)
        ignore_layout.setContentsMargins(12, 10, 12, 10)

        self.ignore_edit = QTextEdit()
        self.ignore_edit.setMaximumHeight(44)
        self.ignore_edit.setPlaceholderText("\\.pyc$  __pycache__  \\.log$")
        ignore_layout.addWidget(self.ignore_edit)

        chips = QHBoxLayout()
        chips.setSpacing(4)
        chips_label = QLabel(tr("templates", "Quick templates:"))
        chips_label.setObjectName("label")
        chips.addWidget(chips_label)
        chips.addStretch()

        templates = [
            ("Python", "\\.pyc$\\n__pycache__"),
            ("Node", "node_modules\\n\\.npm"),
            ("Git", "\\.git.*"),
            ("IDE", "\\.idea\\n\\.vscode"),
        ]

        for name, pattern in templates:
            chip = QPushButton(name)
            chip.setObjectName("ghost")
            chip.setStyleSheet("""
                QPushButton {
                    background: #252525;
                    border: 1px solid #333;
                    border-radius: 12px;
                    padding: 2px 12px;
                    font-size: 8pt;
                    color: #aaa;
                    min-height: 20px;
                }
                QPushButton:hover {
                    background: #333;
                    border-color: #10a37f;
                    color: #10a37f;
                }
            """)
            chip.setCursor(Qt.PointingHandCursor)
            chip.clicked.connect(lambda checked, p=pattern: self.add_ignore_template(p))
            chips.addWidget(chip)

        ignore_layout.addLayout(chips)
        ignore.setLayout(ignore_layout)
        main.addWidget(ignore)

        # КНОПКИ
        buttons = QHBoxLayout()
        buttons.setSpacing(8)

        self.gen_btn = QPushButton("🚀 " + tr("generate", "Generate"))
        self.gen_btn.setObjectName("primary")
        self.gen_btn.clicked.connect(self.generate)
        buttons.addWidget(self.gen_btn, 2)

        self.copy_btn = QPushButton("📋 " + tr("copy", "Copy"))
        self.copy_btn.setObjectName("secondary")
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        buttons.addWidget(self.copy_btn, 1)

        self.open_btn = QPushButton("📂 " + tr("open", "Open"))
        self.open_btn.setObjectName("secondary")
        self.open_btn.clicked.connect(self.open_output_folder)
        buttons.addWidget(self.open_btn, 1)

        main.addLayout(buttons)

        # СТАТУС
        status_widget = QWidget()
        status_widget.setStyleSheet("QWidget { background: #1f1f1f; border-radius: 8px; }")
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(12, 6, 12, 6)

        self.status = QLabel("✨ " + tr("ready", "Ready"))
        self.status.setStyleSheet("color: #888; font-size: 8pt;")
        status_layout.addWidget(self.status, 1)

        self.progress = QProgressBar()
        self.progress.setMaximum(0)
        self.progress.setVisible(False)
        self.progress.setFixedHeight(3)
        status_layout.addWidget(self.progress)

        status_widget.setLayout(status_layout)
        main.addWidget(status_widget)

        # FOOTER
        footer = QHBoxLayout()
        footer.setContentsMargins(0, 0, 0, 0)
        ver = QLabel("v2.0")
        ver.setStyleSheet("color: #333; font-size: 7pt;")
        footer.addWidget(ver)
        footer.addStretch()
        love = QLabel("❤️")
        love.setStyleSheet("color: #333; font-size: 8pt;")
        footer.addWidget(love)
        main.addLayout(footer)

        self.setLayout(main)

        QShortcut(QKeySequence("Ctrl+Return"), self).activated.connect(self.generate)
        QShortcut(QKeySequence("Ctrl+C"), self).activated.connect(self.copy_to_clipboard)

    def setup_styles(self):
        if self.is_dark:
            self.setStyleSheet("""
                QWidget {
                    background: #1a1a1a;
                    color: #e0e0e0;
                    font-family: 'Segoe UI', -apple-system, sans-serif;
                }
                QLabel {
                    color: #c0c0c0;
                    font-size: 9pt;
                }
                QLabel#title {
                    font-size: 22pt;
                    font-weight: 700;
                    color: #10a37f;
                    letter-spacing: -0.5px;
                }
                QLabel#subtitle {
                    color: #888;
                    font-size: 10pt;
                    font-weight: 400;
                }
                QLabel#label {
                    color: #999;
                    font-size: 8pt;
                    font-weight: 600;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }
                QLineEdit {
                    background: #252525;
                    color: #e0e0e0;
                    border: 1px solid #333;
                    border-radius: 8px;
                    padding: 7px 12px;
                    font-size: 9pt;
                }
                QLineEdit:focus {
                    border: 1.5px solid #10a37f;
                }
                QPushButton {
                    border: none;
                    border-radius: 8px;
                    font-size: 9pt;
                    font-weight: 500;
                    padding: 6px 12px;
                    min-height: 28px;
                }
                QPushButton:hover { opacity: 0.9; }
                QPushButton:pressed { opacity: 0.8; }
                QPushButton#primary {
                    background: #10a37f;
                    color: white;
                    font-weight: 600;
                    min-height: 32px;
                }
                QPushButton#primary:hover { background: #0d8f70; }
                QPushButton#primary:disabled { background: #333; color: #666; }
                QPushButton#secondary {
                    background: transparent;
                    color: #aaa;
                    border: 1px solid #333;
                }
                QPushButton#secondary:hover { background: #252525; border-color: #555; }
                QPushButton#ghost {
                    background: transparent;
                    color: #888;
                    padding: 4px 8px;
                    font-size: 8pt;
                }
                QPushButton#ghost:hover { background: #252525; }
                QGroupBox {
                    border: 1px solid #2a2a2a;
                    border-radius: 10px;
                    margin-top: 6px;
                    padding-top: 6px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 12px;
                    padding: 0 6px;
                    color: #888;
                    font-size: 8pt;
                    font-weight: 600;
                    text-transform: uppercase;
                    letter-spacing: 0.3px;
                }
                QTextEdit {
                    background: #252525;
                    color: #e0e0e0;
                    border: 1px solid #333;
                    border-radius: 8px;
                    padding: 6px 10px;
                    font-family: 'Consolas', monospace;
                    font-size: 8pt;
                }
                QTextEdit:focus {
                    border: 1.5px solid #10a37f;
                }
                QProgressBar {
                    background: #252525;
                    border: none;
                    border-radius: 3px;
                    height: 3px;
                }
                QProgressBar::chunk {
                    background: #10a37f;
                    border-radius: 3px;
                }
            """)
        else:
            self.setStyleSheet("""
                QWidget {
                    background: #f5f5f5;
                    color: #333;
                    font-family: 'Segoe UI', -apple-system, sans-serif;
                }
                QLabel {
                    color: #555;
                    font-size: 9pt;
                }
                QLabel#title {
                    font-size: 22pt;
                    font-weight: 700;
                    color: #10a37f;
                    letter-spacing: -0.5px;
                }
                QLabel#subtitle {
                    color: #888;
                    font-size: 10pt;
                    font-weight: 400;
                }
                QLabel#label {
                    color: #666;
                    font-size: 8pt;
                    font-weight: 600;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }
                QLineEdit {
                    background: white;
                    color: #333;
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    padding: 7px 12px;
                    font-size: 9pt;
                }
                QLineEdit:focus {
                    border: 1.5px solid #10a37f;
                }
                QPushButton {
                    border: none;
                    border-radius: 8px;
                    font-size: 9pt;
                    font-weight: 500;
                    padding: 6px 12px;
                    min-height: 28px;
                }
                QPushButton:hover { opacity: 0.9; }
                QPushButton:pressed { opacity: 0.8; }
                QPushButton#primary {
                    background: #10a37f;
                    color: white;
                    font-weight: 600;
                    min-height: 32px;
                }
                QPushButton#primary:hover { background: #0d8f70; }
                QPushButton#primary:disabled { background: #ccc; color: #999; }
                QPushButton#secondary {
                    background: transparent;
                    color: #666;
                    border: 1px solid #ddd;
                }
                QPushButton#secondary:hover { background: #eee; border-color: #ccc; }
                QPushButton#ghost {
                    background: transparent;
                    color: #888;
                    padding: 4px 8px;
                    font-size: 8pt;
                }
                QPushButton#ghost:hover { background: #eee; }
                QGroupBox {
                    border: 1px solid #e0e0e0;
                    border-radius: 10px;
                    margin-top: 6px;
                    padding-top: 6px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 12px;
                    padding: 0 6px;
                    color: #888;
                    font-size: 8pt;
                    font-weight: 600;
                    text-transform: uppercase;
                    letter-spacing: 0.3px;
                }
                QTextEdit {
                    background: white;
                    color: #333;
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    padding: 6px 10px;
                    font-family: 'Consolas', monospace;
                    font-size: 8pt;
                }
                QTextEdit:focus {
                    border: 1.5px solid #10a37f;
                }
                QProgressBar {
                    background: #e0e0e0;
                    border: none;
                    border-radius: 3px;
                    height: 3px;
                }
                QProgressBar::chunk {
                    background: #10a37f;
                    border-radius: 3px;
                }
            """)

    def show_settings(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(tr("settings", "Settings"))
        dialog.setFixedSize(300, 200)
        dialog.setStyleSheet(self.styleSheet())

        layout = QVBoxLayout()

        # Язык
        lang_group = QGroupBox(tr("language", "Language"))
        lang_layout = QVBoxLayout()

        self.lang_combo = QComboBox()
        self.lang_combo.addItem("English", "en")
        self.lang_combo.addItem("Русский", "ru")
        self.lang_combo.setCurrentIndex(0 if translator.language == 'en' else 1)
        lang_layout.addWidget(self.lang_combo)
        lang_group.setLayout(lang_layout)
        layout.addWidget(lang_group)

        # Тема
        theme_group = QGroupBox(tr("theme", "Theme"))
        theme_layout = QVBoxLayout()

        self.theme_combo = QComboBox()
        self.theme_combo.addItem(tr("dark", "Dark"), "dark")
        self.theme_combo.addItem(tr("light", "Light"), "light")
        self.theme_combo.setCurrentIndex(0 if self.is_dark else 1)
        theme_layout.addWidget(self.theme_combo)
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)

        # Кнопки
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton(tr("apply", "Apply"))
        ok_btn.setObjectName("primary")
        ok_btn.clicked.connect(lambda: self.apply_settings(dialog))
        btn_layout.addWidget(ok_btn)

        cancel_btn = QPushButton(tr("cancel", "Cancel"))
        cancel_btn.setObjectName("secondary")
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

        dialog.setLayout(layout)
        dialog.exec_()

    def apply_settings(self, dialog):
        # Язык
        lang = self.lang_combo.currentData()
        translator.set_language(lang)

        # Тема
        theme = self.theme_combo.currentData()
        self.is_dark = (theme == 'dark')
        self.setup_styles()

        # Обновляем текст кнопок
        self.gen_btn.setText("🚀 " + tr("generate", "Generate"))
        self.copy_btn.setText("📋 " + tr("copy", "Copy"))
        self.open_btn.setText("📂 " + tr("open", "Open"))
        self.status.setText("✨ " + tr("ready", "Ready"))

        # Обновляем заголовки
        self.findChild(QLabel, "subtitle").setText(tr("subtitle", "Documentation Generator"))

        self.save_config()
        dialog.accept()

    def select_folder(self, line_edit):
        start = line_edit.text() or str(Path.home())
        if not Path(start).exists():
            start = str(Path.home())

        folder = QFileDialog.getExistingDirectory(
            self, tr("select_folder", "Select folder"), start, QFileDialog.ShowDirsOnly
        )
        if folder:
            line_edit.setText(folder)
            if line_edit == self.input_dir and not self.output_dir.text():
                self.output_dir.setText(str(Path(folder).parent / "documentation"))

    def add_ignore_template(self, pattern):
        current = self.ignore_edit.toPlainText()
        existing = [p.strip() for p in current.split('\n') if p.strip()]
        new_patterns = pattern.split('\\n')
        added = False
        for p in new_patterns:
            if p and p not in existing:
                existing.append(p)
                added = True
        if added:
            self.ignore_edit.setText('\n'.join(existing))
            self.status.setText("✅ " + tr("template_added", "Template added"))
            QTimer.singleShot(1200, lambda: self.status.setText("✨ " + tr("ready", "Ready")))

    def load_config(self):
        cfg = Path("config.json")
        if cfg.exists():
            try:
                with open(cfg, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'input_dir' in data:
                        self.input_dir.setText(data['input_dir'])
                    if 'output_dir' in data:
                        self.output_dir.setText(data['output_dir'])
                    if 'output_file' in data:
                        self.output_file.setText(data['output_file'])
                    if 'language' in data:
                        translator.set_language(data['language'])
                    if 'theme' in data:
                        self.is_dark = (data['theme'] == 'dark')
                        self.setup_styles()
            except:
                pass

        ig = Path("ignore.txt")
        if ig.exists():
            try:
                with open(ig, 'r', encoding='utf-8-sig') as f:
                    patterns = [l.strip() for l in f if l.strip() and not l.startswith('#')]
                    self.ignore_edit.setText('\n'.join(patterns))
            except:
                pass

    def save_config(self):
        try:
            data = {
                'input_dir': self.input_dir.text().strip(),
                'output_dir': self.output_dir.text().strip(),
                'output_file': self.output_file.text().strip(),
                'language': translator.language,
                'theme': 'dark' if self.is_dark else 'light'
            }
            with open("config.json", 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

            with open("ignore.txt", 'w', encoding='utf-8') as f:
                f.write(self.ignore_edit.toPlainText())
        except:
            pass

    def generate(self):
        input_dir = self.input_dir.text().strip()
        output_dir = self.output_dir.text().strip()
        output_file = self.output_file.text().strip()

        if not input_dir:
            QMessageBox.warning(self, tr("error", "Error"), tr("input_error", "Please specify input folder"))
            return
        if not output_dir:
            QMessageBox.warning(self, tr("error", "Error"), tr("output_error", "Please specify output folder"))
            return
        if not Path(input_dir).exists():
            QMessageBox.warning(self, tr("error", "Error"),
                                f"{tr('folder_not_found', 'Folder not found')}:\n{input_dir}")
            return

        self.save_config()

        ignore = [p.strip() for p in self.ignore_edit.toPlainText().split('\n') if p.strip()]

        Path(output_dir).mkdir(parents=True, exist_ok=True)
        output_path = Path(output_dir) / output_file

        self.status.setText("⏳ " + tr("generating", "Generating..."))
        self.progress.setVisible(True)
        self.gen_btn.setEnabled(False)
        self.gen_btn.setText("⏳...")

        # Запускаем в отдельном потоке
        self.thread = QThread()
        self.worker = CodeWeaverWorker(self.engine, input_dir, str(output_path), ignore)
        self.worker.moveToThread(self.thread)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.thread.started.connect(self.worker.run)
        self.thread.start()

    def on_finished(self, path):
        self.progress.setVisible(False)
        self.gen_btn.setEnabled(True)
        self.gen_btn.setText("🚀 " + tr("generate", "Generate"))
        self.status.setText(f"✅ {Path(path).name}")
        self.output_path = path
        self.copy_to_clipboard(silent=True)
        QMessageBox.information(self, tr("success", "Success"), f"{tr('saved', 'Documentation saved')}:\n{path}")

    def on_error(self, error):
        self.progress.setVisible(False)
        self.gen_btn.setEnabled(True)
        self.gen_btn.setText("🚀 " + tr("generate", "Generate"))
        self.status.setText("❌ " + tr("error", "Error"))
        QMessageBox.critical(self, tr("error", "Error"), error)

    def copy_to_clipboard(self, silent=False):
        if not hasattr(self, 'output_path') or not self.output_path:
            if not silent:
                QMessageBox.information(self, tr("info", "Info"), tr("generate_first", "Please generate first"))
            return

        try:
            if not Path(self.output_path).exists():
                if not silent:
                    QMessageBox.warning(self, tr("error", "Error"), tr("file_not_found", "File not found"))
                return

            content = None
            for enc in ['utf-8', 'utf-8-sig', 'cp1251', 'latin-1']:
                try:
                    with open(self.output_path, 'r', encoding=enc) as f:
                        content = f.read()
                    break
                except:
                    continue

            if content is None:
                raise Exception("Failed to read file")

            QApplication.clipboard().setText(content)
            self.status.setText(f"📋 {tr('copied', 'Copied')} ({len(content)} {tr('chars', 'chars')})")

            if not silent:
                QMessageBox.information(
                    self,
                    tr("copied", "Copied"),
                    f"{tr('copied_to_clipboard', 'Copied to clipboard!')}\n\n{tr('size', 'Size')}: {len(content)} {tr('chars', 'chars')}"
                )
        except Exception as e:
            if not silent:
                QMessageBox.warning(self, tr("error", "Error"), f"{tr('copy_failed', 'Failed to copy')}: {e}")

    def open_output_folder(self):
        if hasattr(self, 'output_path') and self.output_path:
            path = Path(self.output_path)
            if path.exists():
                os.startfile(str(path.parent))
                return

        out = self.output_dir.text().strip()
        if out and Path(out).exists():
            os.startfile(out)
        else:
            QMessageBox.warning(self, tr("error", "Error"), tr("folder_not_found", "Folder not found"))


class CodeWeaverWorker(QObject):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, engine, input_dir, output_path, ignore_patterns):
        super().__init__()
        self.engine = engine
        self.input_dir = input_dir
        self.output_path = output_path
        self.ignore_patterns = ignore_patterns

    def run(self):
        try:
            self.engine.generate(
                root_dir=self.input_dir,
                output_file=self.output_path,
                ignore_patterns=self.ignore_patterns
            )
            self.finished.emit(self.output_path)
        except Exception as e:
            self.error.emit(str(e))


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    if sys.platform == 'win32':
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('codeweaver')
        except:
            pass

    win = CodeWeaverGUI()
    win.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()