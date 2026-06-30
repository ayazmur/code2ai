# CodeWeaver 🧬

[![Build](https://github.com/yourusername/codeweaver/actions/workflows/build.yml/badge.svg)](https://github.com/yourusername/codeweaver/actions/workflows/build.yml)
[![Release](https://github.com/yourusername/codeweaver/actions/workflows/release.yml/badge.svg)](https://github.com/yourusername/codeweaver/actions/workflows/release.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📝 Описание

CodeWeaver - это утилита для генерации документации кода с удобным графическим интерфейсом. 
Поддерживает множество языков программирования и позволяет быстро создавать Markdown-документацию 
со структурой проекта и содержимым файлов.

## ✨ Особенности

- 🚀 Быстрая генерация документации
- 🌍 Поддержка русского и английского языков
- 🌓 Темная и светлая темы
- 📂 Интуитивно понятный интерфейс
- 🔍 Автоматическое определение языков
- 📋 Копирование в буфер обмена
- 🎯 Гибкая система игнорирования файлов

## 📦 Установка

### Из релизов (рекомендуется)

Скачайте последнюю версию из [раздела релизов](https://github.com/yourusername/codeweaver/releases)

### Из исходников

```bash
git clone https://github.com/yourusername/codeweaver.git
cd codeweaver
pip install -r requirements.txt
python src/codeweaver.py
```
🔧 Использование
Выберите папку с исходным кодом

Укажите папку для сохранения документации

Настройте паттерны игнорирования (опционально)

Нажмите "Сгенерировать"

Готовая документация будет сохранена в указанную папку

📁 Формат документации
Документация создается в формате Markdown и включает:

Дерево проекта

Содержимое всех файлов с подсветкой синтаксиса

🛠 Разработка
Для сборки приложения:
```bash
pip install pyinstaller
python build/build.py
```
🤝 Вклад
Приветствуются pull requests и issues. Для крупных изменений, пожалуйста, сначала создайте issue для обсуждения.

📄 Лицензия
MIT License - см. файл LICENSE

❤️ Благодарности
PyQt5 за отличный GUI фреймворк

GitHub Actions за автоматическую сборку

Всем пользователям за обратную связь

## Автоматический выпуск релизов

Когда вы пушите тег вида `v1.0.0`, GitHub Actions автоматически:
1. Собирает приложение для Windows, Linux и macOS
2. Создает релиз на странице репозитория
3. Загружает собранные файлы в релиз

Чтобы создать новый релиз:

```bash
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```
Сборка иконок
Для Windows нужен .ico файл, для macOS - .icns.
Вы можете конвертировать SVG в эти форматы с помощью онлайн-конвертеров или ImageMagick:
```bash
# Windows
convert icon.svg -resize 256x256 icon.ico

# macOS
convert icon.svg -resize 512x512 icon.icns
```
Оптимизация производительности
Для быстрой работы приложения:

Используйте небольшие паттерны игнорирования

Избегайте сканирования больших папок (node_modules, venv)

Используйте быстрые шаблоны для популярных фреймворков

Приложение использует многопоточность для генерации документации, что позволяет интерфейсу оставаться отзывчивым.