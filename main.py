from PIL import Image, ImageFilter, ImageDraw

IMAGE_PATH = "images/barcode_cropped.png"

# open up the image of the barcode
img = Image.open(IMAGE_PATH)
img = img.convert("L") # convert to greyscale

img = img.rotate(1)

# # apply an edge enhancement to the image using laplacian kernel
# edge_kernel = ImageFilter.Kernel((3, 3), (-1, -1, -1, -1, 8, -1, -1, -1, -1), 1, 0)
# img_edge = img.filter(edge_kernel)
# img_edge = img_edge.convert("RGB")
# img_edge.save("EDGE_sample.png")


# threshold the image
threshold = 100
img_thresh = img.copy()
img_thresh = img_thresh.point( lambda p: 255 if p > threshold else 0 )
img_thresh = img_thresh.convert("RGB") # convert back to RGB to allow coloured pixels to be drawn

# draw on the thresholded image
d = ImageDraw.Draw(img_thresh)
d.line(((0, img.height/2), (img.width, img.height/2)), (255, 0, 0), 1)

img_thresh.save("threshold.png")

