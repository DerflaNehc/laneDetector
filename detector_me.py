import cv2 as cv
import numpy as np
# import matplotlib.pyplot as plt

def do_canny(frame):
    # Converts frame to grayscale because we only need the luminance channel for detecting edges - less computationally expensive
    gray = cv.cvtColor(frame, cv.COLOR_RGB2GRAY)
    # Applies a 5x5 gaussian blur with deviation of 0 to frame - not mandatory since Canny will do this for us
    blur = cv.GaussianBlur(gray, (5, 5), 0)
    # Applies Canny edge detector with minVal of 50 and maxVal of 150
    canny = cv.Canny(blur, 50, 150)
    return canny

def do_segment(frame):
    # Since an image is a multi-directional array containing the relative intensities of each pixel in the image, we can use frame.shape to return a tuple: [number of rows, number of columns, number of channels] of the dimensions of the frame
    # frame.shape[0] give us the number of rows of pixels the frame has. Since height begins from 0 at the top, the y-coordinate of the bottom of the frame is its height
    height = frame.shape[0]
    # Creates a triangular polygon for the mask defined by three (x, y) coordinates
    polygons = np.array([
                            [(150 , height), (1100, height), (650, 300)]
                        ])
    # Creates an image filled with zero intensities with the same dimensions as the frame
    mask = np.zeros_like(frame)
    # Allows the mask to be filled with values of 1 and the other areas to be filled with values of 0
    cv.fillPoly(mask, polygons, 255)
    # A bitwise and operation between the mask and frame keeps only the triangular area of the frame
    segment = cv.bitwise_and(frame, mask)
    return segment

def calculate_lines(frame, lines):
    # Empty arrays to store the coordinates of the left and right lines
    left = []
    right = []
    # Loops through every detected line
    for line in lines:
        # Reshapes line from 2D array to 1D array
        x1, y1, x2, y2 = line.reshape(4)
        # Fits a linear polynomial to the x and y coordinates and returns a vector of coefficients which describe the slope and y-intercept
        parameters = np.polyfit((x1, x2), (y1, y2), 1)
        slope = parameters[0]
        y_intercept = parameters[1]
        # If slope is negative, the line is to the left of the lane, and otherwise, the line is to the right of the lane
        if slope < 0:
            left.append((slope, y_intercept))
        else:
            right.append((slope, y_intercept))
    # Averages out all the values for left and right into a single slope and y-intercept value for each line
    left_avg = np.average(left, axis = 0)
    right_avg = np.average(right, axis = 0)
    # Calculates the x1, y1, x2, y2 coordinates for the left and right lines
    if (not np.isnan(left_avg).all()):
        left_line = calculate_coordinates(frame, left_avg)
    else:
        left_line = np.array([])
    if (not np.isnan(right_avg).all()):
        right_line = calculate_coordinates(frame, right_avg)
    else:
        right_line = np.array([])
    return np.array([left_line, right_line])

def calculate_coordinates(frame, parameters):
    slope, intercept = parameters
    # Sets initial y-coordinate as height from top down (bottom of the frame)
    y1 = frame.shape[0]
    # Sets final y-coordinate as 150 above the bottom of the frame
    y2 = int(y1 - 200)
    # Sets initial x-coordinate as (y1 - b) / m since y1 = mx1 + b
    x1 = int((y1 - intercept) / slope)
    # Sets final x-coordinate as (y2 - b) / m since y2 = mx2 + b
    x2 = int((y2 - intercept) / slope)
    return np.array([x1, y1, x2, y2])

def visualize_lines(frame, lines, allorNah):
    # Creates an image filled with zero intensities with the same dimensions as the frame
    lines_visualize = np.zeros_like(frame)
    # Checks if any lines are detected
    if (any([x.size==0 for x in lines])):
        line2 = np.delete(lines,np.where([x.size==0 for x in lines]))
    else:
        line2 = lines
    if line2 is not None:
        for line in line2:
            x1, y1, x2, y2 = line.reshape(4)

            # Draws lines between two coordinates with green color and 5 thickness
            if allorNah:
                cv.line(lines_visualize, (x1, y1), (x2, y2), (0, 255, 0), 5)
            else:
                cv.line(lines_visualize, (x1, y1), (x2, y2), (0, 0, 255), 5)
    return lines_visualize

# The video feed is read in as a VideoCapture object

cap = cv.imread("images/slight1_lane.jpg")
canny = do_canny(cap)
cv.imshow("canny", canny)
# cv.waitKey(0)

segment = do_segment(canny)
# cv.imshow("segment", segment)

hough = cv.HoughLinesP(segment, 2, np.pi / 180, 100, np.array([]), minLineLength = 100, maxLineGap = 50)
lines_all = visualize_lines(cap, hough,True)
# Averages multiple detected lines from hough into one line for left border of lane and one line for right border of lane
lines = calculate_lines(cap, hough)
# Visualizes the lines
lines_visualize = visualize_lines(cap, lines,False)
# cv.imshow("hough", lines_visualize)

# Overlays lines on frame by taking their weighted sums and adding an arbitrary scalar value of 1 as the gamma argument
output = cv.addWeighted(cap, 0.9, lines_all, 1, 1)
output = cv.addWeighted(output, 0.9, lines_visualize, 1, 1)
# Opens a new window and displays the output frame
cv.imshow("output", output)
cv.waitKey(0)
# The following frees up resources and closes all windows
