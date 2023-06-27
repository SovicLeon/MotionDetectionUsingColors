import numpy as np
import cv2 as cv

# Set up the camera
cap = cv.VideoCapture(0)

# Get the width and height of the camera
w = cap.get(cv.CAP_PROP_FRAME_WIDTH)
h = cap.get(cv.CAP_PROP_FRAME_HEIGHT)
# Calculate the necessary steps for image processing
h = int(h / 2)
w = int(w / 2)

# Coordinates for selecting skin color
xG1 = 0
yG1 = 0
xG2 = 0
yG2 = 0

# Variables for checking
flipCoords = False
setRec = False
colorSet = False

# Timer for drawing the color selection rectangle
timer = 30

# Variables for color range
spodnjaG = np.ndarray((1, 3))
zgornjaG = np.ndarray((1, 3))

# Check if we have calculated the steps for image processing
stepSet = False
stepW = 0
stepH = 0
steps = 0
stepW2 = 0
stepH2 = 0

# Define the color selection region in the image
def doloci_barvo_koze(slika, levo_zgoraj, desno_spodaj):
    # Select the image region
    (height, width, depth) = slika[levo_zgoraj[0]:desno_spodaj[0], levo_zgoraj[1]:desno_spodaj[1]].shape
    # Calculate the average for the entire region, for all color channels
    mean = np.mean(slika[levo_zgoraj[0]:desno_spodaj[0], levo_zgoraj[1]:desno_spodaj[1]], axis=(0, 1))
    # Calculate the standard deviation and determine the lower and upper bounds
    stds = np.std(mean)
    meanL = mean - 3 * stds
    meanH = mean + 3 * stds
    return (meanL, meanH)

# Resize the image
def zmanjsaj_sliko(slika):
    obdelanaSlika = slika[h - 130:h + 130, w - 150:w + 150]
    return obdelanaSlika

# Process the image
def obdelaj_sliko(slika, okno_sirina, okno_visina, barva_koze_spodaj, barva_koze_zgoraj):
    global stepSet, stepW, stepH, steps, stepW2, stepH2
    # Check if we have already calculated the steps to speed up execution
    if not stepSet:
        (height, width, depth) = slika.shape
        stepW = width * okno_sirina
        stepH = height * okno_visina
        steps = int(width / stepW)
        steps = steps * 2
        stepW2 = stepW / 2
        stepH2 = stepH / 2
        stepSet = True
    maxI = 0
    maxJ = 0
    maxIJV = 0
    # Iterate through the image and count pixels using the given function
    for i in range(steps):
        for j in range(steps):
            stPiklsov = prestej_piksle_z_barvo_koze(
                slika[int(stepW2 * i):int(stepW2 * i + stepW), int(stepH2 * j):int(stepH2 * j + stepH)],
                barva_koze_spodaj, barva_koze_zgoraj)
            # Check if the current sub-image has the maximum matching pixels
            if stPiklsov > maxIJV:
                maxI = i
                maxJ = j
                maxIJV = stPiklsov
    # Return the coordinates of the best matching region
    return [int(stepW2 * maxJ), int(stepH2 * maxI)], [int(stepW2 * maxJ + stepW), int(stepH2 * maxI + stepH)]

# Count pixels within a specified color range
def prestej_piksle_z_barvo_koze(podslika, barva_koze_spodaj, barva_koze_zgoraj):
    # Set the mask to all pixels within the specified color range
    mask = np.all((barva_koze_spodaj <= podslika) & (podslika <= barva_koze_zgoraj), axis=-1)
    # Count the pixels in the mask
    numOfPixels = np.sum(mask)
    return numOfPixels

# Set the coordinates for color selection using mouse click
def clickDown(event, x, y, flags, param):
    global yG1, xG1, yG2, xG2, flipCoords, setRec
    if event == cv.EVENT_LBUTTONDOWN:
        print("Click on position ({}, {})".format(x, y))
        # If statement to select the top left or bottom right coordinate
        if flipCoords:
            # If the click order is reversed, swap the top left and bottom right coordinates
            if y < yG1:
                xG2 = xG1
                xG1 = x
                yG2 = yG1
                yG1 = y
            else:
                xG2 = x
                yG2 = y
            flipCoords = False
            setRec = True
        else:
            xG1 = x
            yG1 = y
            flipCoords = True
            setRec = False

# If the camera fails to open
if not cap.isOpened():
    print("Cannot open camera")
    exit()

# Image capture loop
while True:
    # Read the image
    ret, frame = cap.read()

    # Check if we have received the image
    if not ret:
        print("Can't receive frame (stream end?). Exiting ...")
        break

    # Flip the image
    frame = cv.flip(frame, 1)

    # Resize the image
    frame = zmanjsaj_sliko(frame)

    # Check if we are drawing a rectangle for skin color selection
    if setRec:
        imgDraw = np.zeros(frame.shape, np.uint8)
        imgDraw = cv.rectangle(imgDraw, (xG1 - 1, yG2), (xG2, yG1 - 1), (0, 255, 0), 1)
        frame = frame | imgDraw
        timer -= 1
        # When the timer for color selection expires, determine the color and stop drawing the rectangle
        if timer == 0:
            spodnjaG, zgornjaG = doloci_barvo_koze(frame, (yG1, xG1), (yG2, xG2))
            print("Skin color: ({}; {})".format(spodnjaG, zgornjaG))
            setRec = False
            colorSet = True
            timer = 30

    # If the color is set, process the image
    if colorSet:
        koordinatiG1, koordinatiG2 = obdelaj_sliko(frame, 0.4, 0.4, spodnjaG, zgornjaG)
        frame = cv.rectangle(frame, tuple(koordinatiG1), tuple(koordinatiG2), (0, 0, 255), 2)

    # Display the resulting frame
    cv.imshow('frame', frame)

    # Check if the 'q' key is pressed to exit the loop
    if cv.waitKey(1) & 0xFF == ord('q'):
        break

# Release the capture and close all windows
cap.release()
cv.destroyAllWindows()
