# Python script to decode a UPC-12 barcode from an image

from PIL import Image, ImageDraw
import sys

IMAGE_PATH = "images/barcode_cropped.png"

def barcode_error():
    print("Barcode incorrctly formatted", file=sys.stderr)
    exit(-1)

# open up the image of the barcode
img = Image.open(IMAGE_PATH)
img = img.convert("L") # convert to greyscale
print(f"Image opened: {img.width}x{img.height}", file=sys.stderr)

# TO DO: detect the barcode pragrammatically and work out how much to rotate image by and where to start reading
img = img.rotate(1.5)
x_initial = 80

# the barcode should have high contrast with the beckground so use a low threshold to try to find the barcode start
# then use a larger threshold to improve reading of the bars

# threshold the image
# TO DO: investigate optimal threshold value
threshold = 120
img_thresh = img.copy()
img_thresh = img_thresh.point( lambda p: 255 if p > threshold else 0 )
# img_thresh.save("threshold.png")

# move through the centre of the image to count the width in pixels of each strip (bar and space) in the barcode
# assume starting in the quiet zone
# TO DO: turn this into a state machine to detect the barcode location and remove quiet zones

y_offsets = [0, 10, 20, -10, -20, 30, -30, -40, -50, -60]
all_bar_widths = []
y_initial = int(img.height/2) - 10

for offset in y_offsets:
    y = y_initial + offset
    img_data = list(img_thresh.getdata())
    last_pixel = img_data[x_initial + (y*img.width)]
    current_bar_width = 0
    bar_widths = []

    for x in range(x_initial, img.width):
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
        
    all_bar_widths.append(bar_widths)
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
for offset in y_offsets:
    d_guide.line(((x_initial, y_initial+offset), (img.width, y_initial+offset)), (255, 0, 0, 200), 1) # horizontal
out_guides = Image.alpha_composite(img_thresh, guide_canvas)
out_guides.save("threshold.png")

# draw locations of each bar
run_total = 0
for bar in bar_widths:
    run_total += bar
    d_bar.line(((x_initial + run_total, 0), (x_initial + run_total, img.height)), (0, 0, 255, 128), 1) 

print(f"Barcode width: {run_total} pixels", file=sys.stderr)
print(f"Avg {round((run_total / ((2*3) + 5 + (4*12))), 2)} pixels per strip")

out_bars = Image.alpha_composite(img_thresh, bar_canvas)
out_bars = Image.alpha_composite(out_bars, guide_canvas)
out_bars.save("threshold_annotated.png")



# bar_widths = bar_widths[1:]
# print(bar_widths[1:])
# print()

# TO DO: average the pixel values for a range of horizontal lines, not just the middle
# could help with reading smaller imperfect images where bars are not straight or take up a small number of pixels

# scale the pixel widths of each bar relative to the first bar
# in a UPC code, the start sequence consists of 3 bars of 1 module each, so can be used to scale the other bars
# bar_widths_scaled = [bar_widths[i] for i in range(len(bar_widths))]

avg_bar_widths = []
for i in range(len(all_bar_widths[0])):
    avg = 0

    for j in range(len(all_bar_widths)):
        avg += all_bar_widths[j][i]

    avg /= len(all_bar_widths)
    avg_bar_widths.append(avg)

print()
print(avg_bar_widths)

avg_bar_widths_scaled = []
for i in range(len(avg_bar_widths)):
    avg_bar_widths_scaled.append(round(avg_bar_widths[i] / avg_bar_widths[1]))
print()
print(avg_bar_widths_scaled[1:])

# remove the start quiet zone
# TO DO: use a state machine to read the barcode so this is not necessary
avg_bar_widths_scaled = avg_bar_widths_scaled[1:]

# clamp the widths of bars between 1 and 4
for i in range(len(avg_bar_widths_scaled)):
    if avg_bar_widths_scaled[i] < 1:
        avg_bar_widths_scaled[i] = 1

    if avg_bar_widths_scaled[i] > 4:
        avg_bar_widths_scaled[i] = 4

# split the bars into groups, checking the start, middle and end sequences and validating length of each number
# these consist of 3 bars of 1 module each
# numbers consist of 4 bars with a total width of 7 modules per number

# check that the barcode has the correct number of bars
# 3 for start and end sequence, 5 for midddle sequence and 4 for each of the 12 numbers
if len(avg_bar_widths_scaled) != (((2*3) + 5 + (4*12))):
    print(f"Barcode length: {len(avg_bar_widths_scaled)} - expected {((2*3) + 5 + (4*12))}")
    barcode_error()

# check start sequence
if avg_bar_widths_scaled[0:3] != [1, 1, 1]:
    print(avg_bar_widths_scaled[0:2])
    barcode_error()

# break the first half of the barcode into numbers, removing start sequence
barcode_numbers = []
avg_bar_widths_scaled = avg_bar_widths_scaled[3:]
for i in range(6):
    barcode_numbers.append(avg_bar_widths_scaled[:4])
    avg_bar_widths_scaled = avg_bar_widths_scaled[4:]

# check and remove middle sequence
if avg_bar_widths_scaled[0:5] != [1, 1, 1, 1, 1]:
    print(avg_bar_widths_scaled[0:5])
    barcode_error()

# break the second half of the barcode into numbers, removing middle sequence
avg_bar_widths_scaled = avg_bar_widths_scaled[5:]
for i in range(6):
    barcode_numbers.append(avg_bar_widths_scaled[:4])
    avg_bar_widths_scaled = avg_bar_widths_scaled[4:]

# TO DO: validate the each number has the correct number of modules
# TO DO: if the number of modules is incorrect, run through the encodings to find the closest fit
for i in range(len(barcode_numbers)):
    num_modules = sum(barcode_numbers[i])
    if num_modules != 7:
        print(f"incorrect number of modules: {num_modules} - {barcode_numbers[i]}")
        # barcode_error()

print()
print("barcode valid")
print(barcode_numbers)
print()

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
        if i == 10 and number_decoded == False:
            print(f"Number could not be decoded, {num}")
            decoded_barcode.append(" ")
            # barcode_error()
            break


print()
print("====================================================")
print(f"Barcode number: {decoded_barcode}")
print("====================================================")
