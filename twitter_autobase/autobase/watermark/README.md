## Run on main (top-level code execute)
- filename.jpg must be exists on this folder. It's image that will be watermarked. <br> 
`python3 app.py text font position watermark_image ratio text_color text_stroke_color output` <br>
text: str <br>
font: str <br>
position: x,y -> tuple, x:left, center, right. y:top, center, bottom <br>
watermark_image: filename(str) or False <br>
ratio: float number under 1 <br>
text_color: r,g,b,a -> tuple of RGBA color <br>
text_stroke_color: r,g,b,a -> tuple of RGBA color <br>
output: output filename -> str <br>
example: `python3 app.py 'autobase_reborn' FreeMono.ttf right,bottom photo.png 0.103 100,0,0,1 0,225,225,1 watermarked.jpg`

## Change watermark photo or font:
### Watermark
1. photo's size must be square
2. file name of the photo must be 'photo.png'
3. or edit `watermark_image` function's parameter on app.py, watermark="twitter_autobase/watermark/yourphoto.png"

### Font
1. put in this folder
2. edit `watermark_image` function's parameter on app.py, font="twitter_autobase/watermark/yourfont.ttf"
3. you can setting the size & color of the font on `font` object, `draw.textsize` and `draw.text` function
