from PIL import Image, ImageFont, ImageDraw

def watermark_text_image(filename, watermark='twitter_autobase/watermark/photo.png', font='twitter_autobase/watermark/FreeMono.ttf',
        text=str(), ratio=0.1, pos=('right', 'bottom'), output='watermarked.jpg', color=(0,0,0,0),
        stroke_color=(225,225,225,1)):
        
    '''Watermark with photo and text
    :param filename: file photo location -> str
    :param watermark: watermark image location or bool. True: 'watermark/photo', False: without image -> str or bool
    :param font: font location -> str
    :param text: text watermark -> str
    :param ratio: ratio between watermark and photo -> float under 1
    :param pos: (x, y) position, x:'right','center','right', y:'top','center','bottom' -> tuple
    :param output: output file name -> str
    '''

    # CONTROLLER
    posX = pos[0]
    posY = pos[1]
    if watermark is True:
        watermark = 'watermark/photo.png'

    # OPEN PHOTO 
    img = Image.open(filename)
    preset = Image.new("RGBA", (img.width, img.height))
    preset.paste(img, (0,0))

    # ADD WATERMARK

    # Resizing based on ratio
    if img.size[0] > img.size[1]:
        size = round(img.size[1] * ratio), round(img.size[1] * ratio)
    else:
        size = round(img.size[0] * ratio), round(img.size[0] * ratio)

    if watermark != False:
        watermark = (Image.open(watermark)).resize(size)

    # Setting location and font
    font = ImageFont.truetype(font, round(size[0] * 2.5 * ratio))
    draw = ImageDraw.Draw(preset, "RGBA")
    textsize = draw.textsize(text, font=font, stroke_width=round(size[0]*0.2*ratio))

    dictPos = {
        'center': round(img.height * 0.5 - size[0] * 0.5),
        'top'   : round(img.height * 0.01),
        'bottom': round(img.height * 0.99 - size[0]),
        'left'  : round(img.width * 0.01),
        'right' : round(img.width * 0.99 - size[0] - textsize[0])
    }

    if posX == 'center':
        posX = round(img.width * 0.5 - (size[0] + textsize[0]) * 0.5)
    else:
        posX = dictPos[posX]

    posY = dictPos[posY]

    # Paste watermark and write text
    if watermark != False:
        preset.paste(watermark, (posX, posY), mask=watermark)
        draw.text((posX + round(size[0]), posY + round((size[0]- textsize[1]) * 0.5)),
            text, font=font, fill=color, stroke_width=round(size[0]*0.2*ratio), stroke_fill=stroke_color)
    else:
        draw.text((posX + round(size[0]*0.5), posY + round((size[0]- textsize[1]) * 0.5)),
            text, font=font, fill=color, stroke_width=round(size[0]*0.2*ratio), stroke_fill=stroke_color)

    # preset.mode = 'RGB'
    preset = preset.convert('RGB')
    preset.save(output)
    img.close()
    preset.close()
    if watermark != False:
        watermark.close()


if __name__ == "__main__":
    from sys import argv
    # Ignore vscode problems message on these lines
    # argv e.g 'python3 app.py 'autobase_reborn' right,bottom photo.png 0.103 100,0,0,1 0,225,225,1 watermarked.jpg'
    script, text, font, pos, watermark, ratio, color, stroke_color, output = argv
    ratio = float(ratio)
    pos = tuple([i for i in pos.split(",")])
    if watermark == 'False':
        exec(f"watermark = {watermark}")
    elif watermark != 'True':
        exec(f"watermark = '{watermark}'")
    else:
        raise Exception("argv['watermark'] must be filename or False")

    color = tuple([int(i) for i in [float(i) for i in color.split(",")]])
    stroke_color = tuple(int(i) for i in [float(i) for i in stroke_color.split(",")])
    watermark_text_image("filename.jpg", watermark, text=text, font=font,
            color=color, stroke_color=stroke_color, ratio=ratio, pos=pos, output=output)