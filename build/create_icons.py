# build/create_icons.py
from pathlib import Path
import sys


def create_icons():
    """Создает иконки для разных платформ"""
    root = Path(__file__).parent.parent
    resources = root / 'src' / 'resources'

    # Создаем пустую иконку если нет SVG
    svg_path = resources / 'icon.svg'
    if not svg_path.exists():
        print("Creating placeholder icon.svg...")
        svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <rect width="512" height="512" rx="96" fill="#10a37f"/>
  <text x="256" y="320" font-family="Arial" font-size="200" fill="white" text-anchor="middle">🧬</text>
</svg>'''
        svg_path.write_text(svg_content, encoding='utf-8')

    # Пытаемся создать ICO через PIL
    try:
        from PIL import Image
        import cairosvg

        # Конвертируем SVG в PNG
        png_path = resources / 'icon.png'
        cairosvg.svg2png(url=str(svg_path), write_to=str(png_path), output_width=256, output_height=256)

        # Создаем ICO
        ico_path = resources / 'icon.ico'
        img = Image.open(png_path)
        img.save(ico_path, format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
        print(f"Created icon.ico at {ico_path}")

        # Удаляем временный PNG
        png_path.unlink()

    except ImportError as e:
        print(f"Warning: Could not create icons: {e}")
        print("Install required packages: pip install Pillow cairosvg")
    except Exception as e:
        print(f"Error creating icons: {e}")


if __name__ == '__main__':
    create_icons()