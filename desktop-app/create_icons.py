"""
Simple script to create app icons from a logo image.
Requires PIL (Pillow) to be installed: pip install pillow
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_default_icon():
    """Create a simple default icon if no logo is provided."""
    
    # Create a 256x256 image with gradient background
    size = 256
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw gradient background (purple to blue)
    for y in range(size):
        color_value = int(102 + (118 - 102) * (y / size))
        color = (color_value, 126, 234, 255)
        draw.rectangle([(0, y), (size, y + 1)], fill=color)
    
    # Draw window icon
    window_margin = 50
    window_size = size - (window_margin * 2)
    
    # Window background
    draw.rounded_rectangle(
        [(window_margin, window_margin), 
         (window_margin + window_size, window_margin + window_size)],
        radius=15,
        fill=(255, 255, 255, 255)
    )
    
    # Window title bar
    draw.rounded_rectangle(
        [(window_margin, window_margin), 
         (window_margin + window_size, window_margin + 30)],
        radius=15,
        fill=(118, 98, 162, 255)
    )
    
    # Window controls (dots)
    dot_y = window_margin + 15
    for i, x_offset in enumerate([20, 40, 60]):
        colors = [(255, 95, 86), (255, 189, 46), (39, 201, 63)]
        draw.ellipse(
            [(window_margin + x_offset - 5, dot_y - 5),
             (window_margin + x_offset + 5, dot_y + 5)],
            fill=colors[i]
        )
    
    # Add "AI" text
    try:
        font_size = 60
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    text = "AI"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = window_margin + (window_size - text_width) // 2
    text_y = window_margin + 30 + (window_size - 30 - text_height) // 2
    
    draw.text((text_x, text_y), text, fill=(102, 126, 234, 255), font=font)
    
    return img

def create_icons_from_image(source_image_path=None):
    """Create icons in various sizes from a source image."""
    
    # Output directory
    output_dir = os.path.join(os.path.dirname(__file__), 'resources')
    os.makedirs(output_dir, exist_ok=True)
    
    # Load or create base image
    if source_image_path and os.path.exists(source_image_path):
        print(f"Loading image from {source_image_path}...")
        img = Image.open(source_image_path)
        img = img.convert('RGBA')
    else:
        print("Creating default icon...")
        img = create_default_icon()
    
    # Resize to 256x256 if needed
    if img.size != (256, 256):
        print("Resizing image to 256x256...")
        img = img.resize((256, 256), Image.Resampling.LANCZOS)
    
    # Save PNG
    png_path = os.path.join(output_dir, 'icon.png')
    img.save(png_path, 'PNG')
    print(f"✅ Created: {png_path}")
    
    # Create larger base image for better quality
    large_img = img.resize((512, 512), Image.Resampling.LANCZOS)
    
    # Create ICO with multiple sizes
    ico_path = os.path.join(output_dir, 'icon.ico')
    
    # Save as ICO with 256x256 size
    large_img.save(ico_path, format='ICO', sizes=[(256, 256)])
    print(f"✅ Created: {ico_path}")
    
    print("\n✨ Icons created successfully!")
    print("You can now build the desktop app with these icons.")

if __name__ == '__main__':
    import sys
    
    print("=" * 50)
    print("Windows-Use Icon Creator")
    print("=" * 50)
    print()
    
    if len(sys.argv) > 1:
        source_path = sys.argv[1]
        if not os.path.exists(source_path):
            print(f"❌ Error: File not found: {source_path}")
            sys.exit(1)
        create_icons_from_image(source_path)
    else:
        print("No source image provided, creating default icon...")
        print("To use a custom logo, run: python create_icons.py path/to/your/logo.png")
        print()
        create_icons_from_image()

