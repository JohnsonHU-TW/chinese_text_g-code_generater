from PIL import Image
import cairosvg
from xml.etree import ElementTree as ET


def adjust_svg_stroke_width(input_svg, output_svg, scale_factor=10):
    tree = ET.parse(input_svg)
    root = tree.getroot()

    for element in root.iter():
        if 'stroke-width' in element.attrib:
            original_width = float(element.attrib['stroke-width'])
            element.attrib['stroke-width'] = str(original_width * scale_factor)
    tree.write(output_svg)


def change_to_png(input_svg, output_png):
    # SVG轉為PNG
    cairosvg.svg2png(url=input_svg, write_to=output_png,
                     output_width=2100, output_height=2970)
    # PIL打開PNG並設置白色背景
    img = Image.open(output_png)
    # 先創建一個白色背景的圖片
    new_image = Image.new('RGB', img.size, (255, 255, 255))
    # 然後將原圖片貼上去
    new_image.paste(img, (0, 0), img)
    # 儲存
    new_image.save(output_png)


'''# 定義輸入和輸出路徑
input_svg = 'outputs/0output.svg'

adjusted_svg = 'outputs/0output.svg'
adjust_svg_stroke_width(input_svg, adjusted_svg)


input_svg = 'outputs/0output.svg'

output_png = 'outputs/0output.png'
change_to_png(input_svg, output_png)'''


