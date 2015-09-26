#!/usr/bin/python3

# Uses imagemagick to draw galaxy stats as png file

import wand
import wand.image
import wand.color
import wand.drawing
import sqlite3

output_filename = 'galaxy_map.png'
db_filename = 'galaxy.db'

img = wand.image.Image(width=499, height=10, background=wand.color.Color('#fff'))
dr = wand.drawing.Drawing()
sqconn = sqlite3.connect(db_filename)

dr.clear()
for x in range(0, 499):
    for y in range(0, 5):
        q = 'SELECT COUNT(*) FROM planets WHERE s=? AND g=?'
        cur = sqconn.cursor()
        cur.execute(q, (x+1, y+1))
        row = cur.fetchone()
        num_planets = row[0]
        fill_percent = num_planets / 15
        cc = int(255 * fill_percent)
        col = wand.color.Color('rgb({0},{1},{2})'.format(cc,cc,cc))
        dr.fill_color = col
        dr.point(x, y)

dr.draw(img)
img.save(filename=output_filename)
