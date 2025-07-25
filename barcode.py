# python module to decode a UPC-12 barcode from an image

from PIL import Image, ImageDraw
import sys

def barcode_error(err_msg: str) -> None:
    print("Barcode incorrctly formatted", file=sys.stderr)
    print(err_msg)
    exit(-1)

class BarcodeReader:
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
    
    low_threshold = 20
    high_threshold = 150

    # construct the barcode class with a PIL image containing a barcode
    def __init__(self, img: Image, debug: bool = False):
        self.img = img.convert("L") # ensure image is greyscale
        self.debug = debug
        
        self.img_thresh = Image
        self.all_bar_widths = []
        self.avg_bar_widths = []
        self.raw_avg_bar_module_widths = []
        self.avg_bar_module_widths = []
        self.barcode_numbers = []
        self.decoded_barcode = []

    # apply a threshold to the barcode image
    def threshold_image(self, threshold: int) -> Image:
        # the barcode should have high contrast with the beckground so use a low threshold to try to find the barcode start
        # then use a larger threshold to improve reading of the bars, assuming the list starts with the first bar
        
        img_thresh = self.img.copy()
        img_thresh = img_thresh.point( lambda p: 255 if p > threshold else 0 )

        return img_thresh
    
    # measure the widths of bars over a number of y coordinates
    def read_image_lines(self) -> list:
        # TO DO: detect the barcode pragrammatically and work out where to start reading
        x_initial = 80
        y_offsets = [0, 10, 20, -10, -20, 30, -30, -40, -50, -60]
        y_initial = int(self.img.height/2)

        for offset in y_offsets:
            y = y_initial + offset
            bar_widths = self.read_image_line(x_initial, self.img.width, y)
            self.all_bar_widths.append(bar_widths)
            
        return self.all_bar_widths

    # read along the image along a given y coordinate to count the widt in pixels of each barcode strip (bars and spaces)
    def read_image_line(self, start_x: int, end_x: int, y: int) -> list:
        # assume starting in the quiet zone
        # TO DO: turn this into a state machine to detect the barcode location and remove quiet zones
        
        img_data = list(self.img_thresh.getdata())
        last_pixel = img_data[start_x + (y*self.img.width)]
        current_bar_width = 0
        bar_widths = []

        for x in range(start_x, end_x):
            index = int(x + (y*self.img.width))
            pixel = img_data[index]

            if pixel == last_pixel:
                current_bar_width += 1
            else:
                bar_widths.append(current_bar_width)
                current_bar_width = 1

            last_pixel = pixel
        
        return bar_widths  

    # calculate the average widths of barcode bars from the different measurements
    def average_bar_widths(self) -> list:
        # find the smallest number of bars detected on each line
        # this should remove errors due to any spurious bars picked up after the barcode
        min_length = len(self.all_bar_widths[0])
        for i in range(1, len(self.all_bar_widths)):
            current_length = len(self.all_bar_widths[i])
            if current_length < min_length:
                min_length = current_length
        
        for i in range(min_length):
            avg = 0

            for j in range(len(self.all_bar_widths)):
                avg += self.all_bar_widths[j][i]

            avg /= len(self.all_bar_widths)
            self.avg_bar_widths.append(avg)

        return self.avg_bar_widths

    # scale the width of each bar from pixels to modules
    def scale_bar_widths(self) -> list:
        # in a UPC code, the start sequence consists of 3 bars of 1 module each, so can be used as a known reference to scale the other bars
        for i in range(len(self.avg_bar_widths)):
            self.raw_avg_bar_module_widths.append(self.avg_bar_widths[i] / self.avg_bar_widths[1])

        # remove the start quiet zone
        # TO DO: use a state machine to read the barcode so this is not necessary
        self.raw_avg_bar_module_widths = self.raw_avg_bar_module_widths[1:]

        return self.raw_avg_bar_module_widths
    
    # round and clamp the scaled bar widths to the nearest integer
    def clamp_bar_widths(self) -> list:
        self.avg_bar_module_widths = [round(x) for x in self.raw_avg_bar_module_widths]

        # clamp the widths of bars between 1 and 4
        for i in range(len(self.avg_bar_module_widths)):
            if self.avg_bar_module_widths[i] < 1:
                self.avg_bar_module_widths[i] = 1

            if self.avg_bar_module_widths[i] > 4:
                self.avg_bar_module_widths[i] = 4

        return self.avg_bar_module_widths
    
    def read_bars(self) -> list:
        # split the bars into groups, checking the start, middle and end sequences and validating length of each number
        # these consist of 3 bars of 1 module each
        # numbers consist of 4 bars with a total width of 7 modules per number

        # check that the barcode has the correct number of bars
        # 3 for start and end sequence, 5 for midddle sequence and 4 for each of the 12 numbers
        if len(self.avg_bar_module_widths) != (((2*3) + 5 + (4*12))):
            barcode_error(f"Barcode length: {len(self.avg_bar_module_widths)} - expected {((2*3) + 5 + (4*12))}")

        # check start sequence
        if self.avg_bar_module_widths[0:3] != [1, 1, 1]:
            barcode_error(f"{self.avg_bar_module_widths[0:2]}")

        # break the first half of the barcode into numbers, removing start sequence
        self.avg_bar_module_widths = self.avg_bar_module_widths[3:]
        for i in range(6):
            self.barcode_numbers.append(self.avg_bar_module_widths[:4])
            self.avg_bar_module_widths = self.avg_bar_module_widths[4:]

        # check and remove middle sequence
        if self.avg_bar_module_widths[0:5] != [1, 1, 1, 1, 1]:
            barcode_error(f"{self.avg_bar_module_widths[0:5]}")

        # break the second half of the barcode into numbers, removing middle sequence
        self.avg_bar_module_widths = self.avg_bar_module_widths[5:]
        for i in range(6):
            self.barcode_numbers.append(self.avg_bar_module_widths[:4])
            self.avg_bar_module_widths = self.avg_bar_module_widths[4:]

        return self.barcode_numbers
    
    # check each of the numbers and attempt to correct any which don't match any encoding
    def check_bars(self) -> list:
        for i in range(len(self.barcode_numbers)):
            num_modules = sum(self.barcode_numbers[i])
            if num_modules != 7:
                # try to find the closest matching encoding
                # count the number of bars that deviate from each of the correct number encodings
                matching_bars = [0 for i in range(len(self.encodings))]
                for j, enc in enumerate(self.encodings):
                    for k in range(4):
                        if enc[k] == self.barcode_numbers[i][k]:
                            matching_bars[j] += 1

                # extract the numbers with the closest match 
                best_match = max(matching_bars)
                potential_matches = []
                for j in range(len(self.encodings)):
                    if matching_bars[j] == best_match:
                        potential_matches.append(j)

                # error between the incorrect bar and the correct bar width
                number_difference = {}

                for num in potential_matches:
                    candidate = self.encodings[num]
                    incorrect_strips = []
                    for j in range(4):
                        if candidate[j] != self.barcode_numbers[i][j]:
                            incorrect_strips.append(j)
        
                    for strip in incorrect_strips:
                        ctrl_offset = 3 if i < 7 else 8 # adjust for the start and middle symbols
                        strip_index = (4*i) + strip + ctrl_offset
                        raw_val = self.raw_avg_bar_module_widths[strip_index]
                        diff = abs(raw_val - self.encodings[num][strip])
                        number_difference[num] = diff

                # find the number sequence with the lowest error and replace the number with the most likely option
                candidate_number = min(number_difference, key=number_difference.get)

                print(f"Number in position {i} not decoded correctly: {self.barcode_numbers[i]}", file=sys.stderr)
                print(f"Inferred as {candidate_number}: {self.encodings[candidate_number]}", file=sys.stderr)

                self.barcode_numbers[i] = self.encodings[candidate_number]

        return self.barcode_numbers

    # decode the numbers from the barcode bars
    def decode_numbers(self) -> list:
        for num in self.barcode_numbers:
            number_decoded = False
            i = 0

            while not number_decoded:
                num_modules = sum(num)
                if num_modules == 7:
                    
                    enc = self.encodings[i]
                    if enc == num:
                        self.decoded_barcode.append(i)
                        number_decoded = True

                    i += 1
                    if i == 10 and number_decoded == False:
                        # barcode_error(f"Number could not be decoded, {num}")
                        num = self.correct_bar(num)
                        break
                else:
                    num = self.correct_bar(num)
            

        return self.decoded_barcode   

    # try to find the closest matching encoding to an incorrectly read bar
    def correct_bar(self, bar: list) -> list:
        
        # count the number of bars that deviate from each of the correct number encodings
        matching_bars = [0 for i in range(len(self.encodings))]
        for i, enc in enumerate(self.encodings):
            for j in range(4):
                if enc[j] == bar[j]:
                    matching_bars[i] += 1

        # extract the numbers with the closest match 
        best_match = max(matching_bars)
        potential_matches = []
        for i in range(len(self.encodings)):
            if matching_bars[i] == best_match:
                potential_matches.append(i)

        # error between the incorrect bar and the correct bar width
        number_difference = {}

        for num in potential_matches:
            candidate = self.encodings[num]
            incorrect_strips = []
            for i in range(4):
                if candidate[i] != self.barcode_numbers[i][i]:
                    incorrect_strips.append(i)

            for strip in incorrect_strips:
                guard_offset = 3 if i < 7 else 8 # adjust for the start and middle guard patterns
                strip_index = (4*i) + strip + guard_offset
                raw_val = self.raw_avg_bar_module_widths[strip_index]
                diff = abs(raw_val - self.encodings[num][strip])
                number_difference[num] = diff

        # find the number sequence with the lowest error and replace the number with the most likely option
        candidate_number = min(number_difference, key=number_difference.get)

        print(f"Number in position {i} not decoded correctly: {self.barcode_numbers[i]}", file=sys.stderr)
        print(f"Inferred as {candidate_number}: {self.encodings[candidate_number]}", file=sys.stderr)

        return self.encodings[candidate_number]

    # output annotated images showing the bars and lines used for measurements
    def annotate_image(self) -> None:
        x_initial = 80
        y_offsets = [0, 5, 10, 15, 20, 25, 30, -5, -10, -15, -20, -25, -30, -35, -40, -45, -50, -55, -60]
        y_initial = int(self.img.height/2) + 20
        # PIL drawing context to draw the red guide marker on the image
        guide_canvas = Image.new("RGBA", self.img_thresh.size, (255, 255, 255, 0))
        d_guide = ImageDraw.Draw(guide_canvas)

        # PIL drawing context to add annotations for each bar
        bar_canvas = Image.new("RGBA", self.img_thresh.size, (255, 255, 255, 0))
        d_bar = ImageDraw.Draw(bar_canvas)

        self.img_thresh = self.img_thresh.convert("RGBA") # convert to RGBA to allow coloured pixels with transparency to be drawn
        # d = ImageDraw.Draw(img_thresh) # drawing context
        for offset in y_offsets:
            d_guide.line(((x_initial, y_initial+offset), (self.img.width, y_initial+offset)), (255, 0, 0, 200), 1) # horizontal
        out_guides = Image.alpha_composite(self.img_thresh, guide_canvas)
        out_guides.save("threshold.png")

        # draw locations of each bar
        run_total = 0
        for bar in self.all_bar_widths[0]:
            run_total += bar
            d_bar.line(((x_initial + run_total, 0), (x_initial + run_total, self.img.height)), (0, 0, 255, 128), 1) 

        print(f"Barcode width: {run_total} pixels", file=sys.stderr)
        print(f"Avg {round((run_total / ((2*3) + 5 + (4*12))), 2)} pixels per strip\n", file=sys.stderr)

        out_bars = Image.alpha_composite(self.img_thresh, bar_canvas)
        out_bars = Image.alpha_composite(out_bars, guide_canvas)
        out_bars.save("threshold_annotated.png")            

    # decode the barcode and return list of numbers
    def decode(self) -> list:
        self.img_thresh = self.threshold_image(self.high_threshold)
        self.read_image_lines()
        self.average_bar_widths()
        self.scale_bar_widths()
        self.clamp_bar_widths()
        self.read_bars()
        self.decode_numbers()

        if self.debug:
            self.annotate_image()

        return self.decoded_barcode
