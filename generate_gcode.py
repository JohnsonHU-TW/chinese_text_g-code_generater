# -*- coding: utf-8 -*-
"""
筆跡算法源於Github:LingDong-大神的傑作
倉儲位置https://github.com/LingDong-/chinese-hershey-font
此程式撰寫：JiaSheng HU TW
開始日期：2024-11-25

資料來源：Github、ChatGPT

程式說明：
讀取teststrings.txt後輸出中文字筆跡路徑之G-code碼，大小為A4，單位為mm/s
"""
from PIL import Image, ImageFont, ImageDraw
import math
import sys
from util import *
import svgwrite
from svg.path import parse_path
from xml.dom import minidom
import os
from view_img import adjust_svg_stroke_width, change_to_png


class params_set:
    width = 100
    height = 100
    strw = 7
    ngradient = 4


def im2mtx(im):
    w, h = im.size
    data = list(im.getdata())
    mtx = {}
    for i in range(0, len(data)):
        mtx[i % w, i // w] = 1 if data[i] > 250 else 0
    mtx['size'] = (w, h)
    return mtx


def rastBox(l, f, w=100, h=100):
    def getbound(im):
        px = im.load()
        xmin = im.size[0]
        xmax = 0
        ymin = im.size[1]
        ymax = 0
        for x in range(im.size[0]):
            for y in range(im.size[1]):
                if (px[x, y] > 128):
                    if x < xmin: xmin = x
                    if x > xmax: xmax = x
                    if y < ymin: ymin = y
                    if y > ymax: ymax = y
        return xmin, ymin, xmax, ymax

    font = ImageFont.truetype(f, h)
    im0 = Image.new("L", (int(w * 1.5), int(h * 1.5)))
    dr0 = ImageDraw.Draw(im0)
    dr0.text((int(w * 0.1), int(h * 0.1)), l, 255, font=font)

    xmin, ymin, xmax, ymax = getbound(im0)
    xmin = min(xmin, int(w * 0.25))
    xmax = max(xmax, int(w * 0.75))
    ymin = min(ymin, int(h * 0.25))
    ymax = max(ymax, int(h * 0.75))

    im = Image.new("L", (w, h))
    im.paste(im0, box=(-xmin, -ymin))
    im = im.resize((int(w ** 2 * 1.0 / (xmax - xmin)), int(h ** 2 * 1.0 / (ymax - ymin))), resample=Image.BILINEAR)
    im = im.crop((0, 0, w, h))
    return im2mtx(im)


def scanRast(mtx, strw=10, ngradient=2):
    w, h = mtx['size']
    segs = []

    steptypes = [
                    (0, 1), (1, 0),
                    (1, 1), (-1, 1),
                    (1, 2), (2, 1), (-1, 2), (-2, 1),
                    (1, 3), (3, 1), (-1, 3), (-3, 1),
                    (1, 4), (4, 1), (-1, 4), (-4, 1),
                ][:ngradient * 4]

    for step in steptypes:
        ini = []
        if step[0] < 0:
            ini += [(w - 1, y) for y in range(h)]
        elif step[0] > 0:
            ini += [(0, y) for y in range(h)]

        if step[1] < 0:
            ini += [(x, h - 1) for x in range(w)]
        elif step[1] > 0:
            ini += [(x, 0) for x in range(w)]

        for i in range(0, len(ini)):
            x = ini[i][0]
            y = ini[i][1]
            flip = False
            while x < w and y < h and x >= 0 and y >= 0:
                if mtx[x, y] == 1:
                    if flip == False:
                        flip = True
                        segs.append([(x, y)])
                else:
                    if flip == True:
                        flip = False
                        segs[-1].append((x, y))
                x += step[0]
                y += step[1]
            if flip == True:
                segs[-1].append((x, y))

    def near(seg0, seg1):
        return distance(seg0[0], seg1[0]) < strw \
            and distance(seg0[1], seg1[1]) < strw

    def scal(seg, s):
        return [(seg[0][0] * s, seg[0][1] * s),
                (seg[1][0] * s, seg[1][1] * s)]

    def adds(seg0, seg1):
        return [(seg0[0][0] + seg1[0][0], seg0[0][1] + seg1[0][1]),
                (seg0[1][0] + seg1[1][0], seg0[1][1] + seg1[1][1])]

    def angs(seg):
        return math.atan2(seg[0][1] - seg[1][1], seg[0][0] - seg[1][0])

    segs = [s for s in segs if distance(s[0], s[1]) > strw * 0.5]

    gpsegs = []
    for i in range(len(segs)):
        grouped = False
        d = distance(segs[i][0], segs[i][1])
        for j in range(len(gpsegs)):
            if near(segs[i], gpsegs[j]['mean']):
                l = float(len(gpsegs[j]['list']))
                gpsegs[j]['list'].append(segs[i])
                gpsegs[j]['mean'] = adds(
                    scal(gpsegs[j]['mean'], l / (l + 1)),
                    scal(segs[i], 1 / (l + 1)))

                if d > gpsegs[j]['max'][1]:
                    gpsegs[j]['max'] = (segs[i], d)

                grouped = True
        if grouped == False:
            gpsegs.append({
                'list': [segs[i]],
                'mean': segs[i],
                'max': (segs[i], d)
            })
    ssegs = []
    for i in range(0, len(gpsegs)):
        s = gpsegs[i]['max'][0]
        ssegs.append(s)


    for i in range(0, len(ssegs)):
        for j in range(0, len(ssegs)):
            if i != j and ssegs[j] != None:
                if distance(ssegs[i][0], ssegs[i][1]) < distance(ssegs[j][0], ssegs[j][1]):
                    (lx0, ly0), d0, b0 = pt2seg(ssegs[i][0], ssegs[j])
                    (lx1, ly1), d1, b1 = pt2seg(ssegs[i][1], ssegs[j])
                    m = 1
                    if d0 < strw * m and d1 < strw * m and (b0 < strw * m and b1 < strw * m):
                        ssegs[i] = None
                        break
    ssegs = [s for s in ssegs if s != None]


    for i in range(0, len(ssegs)):
        for j in range(0, len(ssegs)):
            if i != j and ssegs[j] != None:
                d0 = distance(ssegs[i][0], ssegs[j][0])
                d1 = distance(ssegs[i][1], ssegs[j][1])
                m = 1
                if d0 < strw * m and d1 < strw * m:
                    ssegs[i] = None
                    break
    ssegs = [s for s in ssegs if s != None]


    for i in range(0, len(ssegs)):
        for j in range(0, len(ssegs)):
            if i != j and ssegs[j] != None:

                seg0 = ssegs[i][-2:]
                seg1 = ssegs[j][:2]

                ir = intersect(seg0, seg1)
                if ir != None:
                    (x, y), (od0, od1) = ir
                ang = vecang(seg0, seg1)

                d = distance(ssegs[i][-1], ssegs[j][0])
                if d < strw or (ir != None and od0 == od1 == 0) or ang < math.pi / 4:
                    (lx0, ly0), d0, b0 = pt2seg(ssegs[i][-1], seg1)
                    (lx1, ly1), d1, b1 = pt2seg(ssegs[j][0], seg0)
                    m = 1
                    if d0 < strw * m and d1 < strw * m and (b0 < 1 and b1 < 1):
                        ssegs[j] = ssegs[i][:-1] \
                                   + [lerp(ssegs[i][-1], ssegs[j][0], 0.5)] \
                                   + ssegs[j][1:]
                        ssegs[i] = None

                        break

    ssegs = [s for s in ssegs if s != None]

    return ssegs


def gen_text_vector(fonts):
    w, h = params_set.width, params_set.height
    corpus = open("strings.txt", 'r', encoding='utf-8').readlines()[-1]  # 直接讀取最後一行

    text_vector = []
    for i in range(0, len(corpus)):
        ch = corpus[i]
        sys.stdout.flush()
        rbox = rastBox(ch, f=fonts, w=w, h=h)
        vector = scanRast(
            rbox,
            strw=params_set.strw,
            ngradient=params_set.ngradient
        )
        text_vector.append(vector)

    return text_vector


def draw_lines_to_svg(text_vector, font_size, padding, x_space, y_space):
    """
    繪製線段到 SVG，並在四周空出 100px 的空白區域。
    """
    filename = "output.svg"
    original_width = 2100
    original_height = 2970
    font_scale = 100/font_size
    canvas_width = original_width - 2*padding
    canvas_height = original_height - 2*padding

    max_text = (canvas_width//(font_size + x_space))*(canvas_height//(font_size + y_space))
    x_max_width = canvas_width//(font_size + x_space)
    pages = math.ceil(len(text_vector)/max_text)
    print('字數', len(text_vector))
    print('X軸最大字數', x_max_width, '單頁最大字數', max_text, '頁數', pages)
    print(canvas_width, canvas_height)

    for page in range(pages): # tiny: 較簡易的svg標準
        dwg = svgwrite.Drawing(f'outputs/{page+1}{filename}', profile='tiny', size=(f"{original_width}px", f"{original_height}px"))
        x = 0
        y = 0
        text_vectorx = text_vector[page*max_text:max_text + page*max_text]
        for i, group in enumerate(text_vectorx):
            # 一個group是一個字
            for line in group:
                # line是筆劃、line[0][0]/10 辨識完的字是100px，縮小為1/10倍、位置為第x個字，間距為字寬加文字間距，加稿紙留邊
                # move to:　M
                path_data = f"M {line[0][0]/font_scale + x*(font_size + x_space) + padding} {line[0][1]/font_scale + y*(font_size + y_space) + padding} "
                # path_data初始點
                for point in line[1:]:
                    # points移到下一點
                    # Line to: L
                    path_data += f"L {point[0]/font_scale + x*(font_size + x_space) + padding} {point[1]/font_scale + y*(font_size + y_space) + padding} "
                dwg.add(dwg.path(d=path_data, fill='none', stroke='black', stroke_width=1))
            x+=1
            if (i + 1)%x_max_width == 0:
                y+=1
                x=0
        dwg.save()


def svg_to_gcode(svg_file, gcode_file, feed_rate=4000, traval_speed=10000, pen_angles=45):
    doc = minidom.parse(svg_file)
    svg_element = doc.getElementsByTagName('svg')[0]

    canvas_height = None
    if svg_element.hasAttribute('viewBox'):
        viewBox = svg_element.getAttribute('viewBox').split()
        if len(viewBox) == 4:
            canvas_height = float(viewBox[3])/10
    elif svg_element.hasAttribute('height'):
        canvas_height = float(svg_element.getAttribute('height').replace("px", ""))/10

    path_strings = [path.getAttribute('d') for path in doc.getElementsByTagName('path')]
    doc.unlink()

    gcode_lines = list()
    gcode_lines.append("G21")
    gcode_lines.append("G90")
    gcode_lines.append(f"G1 F{feed_rate}")
    gcode_lines.append("M3 S40")
    for path_string in path_strings:
        path = parse_path(path_string)
        for segment in path:
            if hasattr(segment, 'start'): # 如果是起點，使用G0移動，並確保筆抬起
                start = segment.start
                start_y = canvas_height - (start.imag * 0.1)  # 翻轉Y坐標
                gcode_lines.append(f"M3 S{pen_angles}")
                gcode_lines.append(f"G0 F{traval_speed} X{start.real * 0.1:.3f} Y{start_y:.3f}")
            if hasattr(segment, 'end'): # 如果是線段，使用G1移動，並放下筆
                end = segment.end
                end_y = canvas_height - (end.imag * 0.1)  # 翻轉Y坐標
                gcode_lines.append(f"M3 S10")
                gcode_lines.append(f"G1 F{feed_rate} X{end.real * 0.1:.3f} Y{end_y:.3f}")
        gcode_lines.append("M3 S10")  # 確保每條路徑結束後抬筆
    gcode_lines.append("M3 S45")
    gcode_lines.append(f"G1 F{traval_speed} X0 Y0")
    gcode_lines.append("M3 S10")  # 確保每條路徑結束後抬筆
    gcode_lines.append(f" ")


    # 儲存
    with open(gcode_file, "w") as f:
        f.write("\n".join(gcode_lines))
    print(f"G-code 已儲存到 {gcode_file}")


def gen_main(font_type="fonts/msjhl.ttc", x_space=10, y_space=10, padding=100, font_size=200, feed_rate=10000, traval_speed=10000):
    text_vector = gen_text_vector(font_type)

    draw_lines_to_svg(text_vector, font_size, padding, x_space, y_space)

    folder_path = "outputs"

    svg_files = [os.path.splitext(file)[0] for file in os.listdir(folder_path) if file.endswith(".svg")]

    for svg_file in svg_files:
        print(svg_file)
        svg_to_gcode(f"outputs/{svg_file}.svg", f"outputs/{svg_file}.gcode", feed_rate=feed_rate, traval_speed=traval_speed, pen_angles=40)
        adjust_svg_stroke_width(f"outputs/{svg_file}.svg", f"outputs/{svg_file}.svg")
        change_to_png(f"outputs/{svg_file}.svg", f"outputs/{svg_file}.png")

# gen_main(font_type="fonts/msjhl.ttc", x_space=10, y_space=10, padding=100, font_size=200, feed_rate=10000, traval_speed=10000)

'''font_type = "fonts/msjhl.ttc"
x_space = 10  # X軸文字間距px
y_space = 10
padding = 100  # 稿紙四周留白px
font_size = 200  # 文字大小px'''