# Python script to decode a UPC-12 barcode from an image

from PIL import Image
import sys
from barcode_reader import BarcodeReader

IMAGE_PATH = "images/barcode_photo.png"

if __name__ == "__main__":
    # open up the image of the barcode
    img = Image.open(IMAGE_PATH)
    img = img.convert("L") # convert to greyscale
    print(f"Image opened: {img.width}x{img.height}\n", file=sys.stderr)

    # TO DO: detect the barcode pragrammatically and work out how much to rotate image by and where to start reading
    img = img.rotate(1.5)

    bc = BarcodeReader(img, debug=True)
    bc.start_x = 80
    bc.y_offsets = [-95, -75, -55, -35, -15, 0, 15, 35, 55, 75]
    decoded_barcode = bc.decode()

    print()
    print("====================================================")
    print(f"Barcode number: {decoded_barcode}")
    print("{:012d}".format(int(''.join(map(str, decoded_barcode)))))
    print("====================================================")
