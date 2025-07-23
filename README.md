# Barcode Scanner
Scan a UPC-12 barcode in python from an image.

## To Do's
- Try reading the barcode over multiple lines to allow averages to be taken for bar widths
- Implement detection of the barcode in a busy image (could use edge detection or trying multiple threshold values)
- Refactor to read the barcode using a state machine that allows the numbers to be decoded on the fly
- Refactor to a library that can be reused in other projects
- Update implementation to work with EAN-13 barcodes (these are equvalent to UPC when the initial digit is 0, but are encoded differently for other starting numbers)