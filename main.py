# Python script to decode a UPC-12 barcode from an image

from PIL import Image, ImageDraw
import sys

IMAGE_PATH = "images/barcode.png"

def barcode_error():
    print("Barcode incorrctly formatted", file=sys.stderr)
    exit(-1)

# open up the image of the barcode
img = Image.open(IMAGE_PATH)
img = img.convert("L") # convert to greyscale
print(f"Image opened: {img.width}x{img.height}")

# TO DO: detect the barcode pragrammatically and work out how much to rotate image by
# img = img.rotate(1.5)

# threshold the image
threshold = 100
img_thresh = img.copy()
img_thresh = img_thresh.point( lambda p: 255 if p > threshold else 0 )
# img_thresh.save("threshold.png")

# move through the centre of the image to count the width in pixels of each strip (bar and space) in the barcode
# assume starting in the quiet zone
# TO DO: turn this into a state machine to detect the barcode location and remove quiet zones
y = int(img.height/2)
img_data = list(img_thresh.getdata())
last_pixel = img_data[y*img.width]
current_bar_width = 0
bar_widths = []

for x in range(img.width):
    index = int(x + (y*img.width))
    pixel = img_data[index]
    colour = 1 if pixel == 255 else 0

    if pixel == last_pixel:
        current_bar_width += 1
    else:
        bar_widths.append(current_bar_width)
        current_bar_width = 1

    last_pixel = pixel
    print(colour, end="")
    
print()
print()

# PIL drawing context to draw the red guide marker on the image
guide_canvas = Image.new("RGBA", img_thresh.size, (255, 255, 255, 0))
d_guide = ImageDraw.Draw(guide_canvas)

# PIL drawing context to add annotations for each bar
bar_canvas = Image.new("RGBA", img_thresh.size, (255, 255, 255, 0))
d_bar = ImageDraw.Draw(bar_canvas)


img_thresh = img_thresh.convert("RGBA") # convert to RGBA to allow coloured pixels with transparency to be drawn
# d = ImageDraw.Draw(img_thresh) # drawing context
d_guide.line(((0, img.height/2), (img.width, img.height/2)), (255, 0, 0, 200), 1) # horizontal
out_guides = Image.alpha_composite(img_thresh, guide_canvas)
out_guides.save("threshold.png")

# draw locations of each bar
run_total = 0
for bar in bar_widths:
    run_total += bar
    d_bar.line(((run_total, 0), (run_total, img.height)), (0, 0, 255, 128), 1) 

out_bars = Image.alpha_composite(img_thresh, bar_canvas)
out_bars = Image.alpha_composite(out_bars, guide_canvas)
out_bars.save("threshold_annotated.png")



# bar_widths = bar_widths[1:]
print(bar_widths[1:])
print()

# TO DO: average the pixel values for a range of horizontal lines, not just the middle
# could help with reading smaller imperfect images where bars are not straight or take up a small number of pixels

# scale the pixel widths of each bar relative to the first bar
# in a UPC code, the start sequence consists of 3 bars of 1 module each, so can be used to scale the other bars
# bar_widths_scaled = [bar_widths[i] for i in range(len(bar_widths))]
bar_widths_scaled = []
for i in range(len(bar_widths)):
    bar_widths_scaled.append(round(bar_widths[i] / bar_widths[1]))
print(bar_widths_scaled[1:])

# remove the start quiet zone
# TO DO: use a state machine to read the barcode so this is not necessary
bar_widths_scaled = bar_widths_scaled[1:]

# split the bars into groups, checking the start, middle and end sequences and validating length of each number
# these consist of 3 bars of 1 module each
# numbers consist of 4 bars with a total width of 7 modules per number

# check that the barcode has the correct number of bars
# 3 for start and end sequence, 5 for midddle sequence and 4 for each of the 12 numbers
if len(bar_widths_scaled) != (((2*3) + 5 + (4*12))):
    print(f"Barcode length: {len(bar_widths_scaled)} - expected {((2*3) + 5 + (4*12))}")
    barcode_error()

# check start sequence
if bar_widths_scaled[0:3] != [1, 1, 1]:
    print(bar_widths_scaled[0:2])
    barcode_error()

# break the first half of the barcode into numbers, removing start sequence
barcode_numbers = []
bar_widths_scaled = bar_widths_scaled[3:]
for i in range(6):
    barcode_numbers.append(bar_widths_scaled[:4])
    bar_widths_scaled = bar_widths_scaled[4:]

# check and remove middle sequence
if bar_widths_scaled[0:5] != [1, 1, 1, 1, 1]:
    print(bar_widths_scaled[0:5])
    barcode_error()

# break the second half of the barcode into numbers, removing middle sequence
barcode_numbers_right = []
bar_widths_scaled = bar_widths_scaled[5:]
for i in range(6):
    barcode_numbers.append(bar_widths_scaled[:4])
    bar_widths_scaled = bar_widths_scaled[4:]

# TO DO: validate the each number has the correct number of modules

print("barcode valid")
print(barcode_numbers)

# decode the numbers from the barcode
# encodings from wikipedia: https://en.wikipedia.org/wiki/Universal_Product_Code#Encoding
encodings = [
    [3, 2, 1, 1],
    [2, 2, 2, 1],
    [2, 1, 2, 2],
    [1, 4, 1, 1],
    [1, 1, 3, 2],
    [1, 2, 3, 1],
    [1, 1, 1, 4],
    [1, 3, 1, 2],
    [1, 2, 1, 3],
    [3, 1, 1, 2],
]

decoded_barcode = []

for num in barcode_numbers:
    number_decoded = False
    i = 0
    while not number_decoded:
        enc = encodings[i]
        if enc == num:
            decoded_barcode.append(i)
            number_decoded = True

        i += 1
        if i == 10:
            print(f"Number could not be decoded, {num}")
            barcode_error()


print()
print("====================================================")
print(f"Barcode number: {decoded_barcode}")
print("====================================================")
