import numpy as np
import cv2 as cv

# Nastavimo kamero
cap = cv.VideoCapture(0)

# Pridobimo širino in višino kamere
w = cap.get(cv.CAP_PROP_FRAME_WIDTH)
h = cap.get(cv.CAP_PROP_FRAME_HEIGHT)
# Naredimo izračun potreben za število korakov pri obedlovanju slike
h = int(h/2)
w = int(w/2)

# Koordinate za izbiro barve kože
xG1 = 0
yG1 = 0
xG2 = 0
yG2 = 0

# Spremenljivke za preverjanje
flipCoords = False
setRec = False
colorSet = False

# Timer za izris pravokotnika za izbiro barve
timer = 30

# Spremenljivke za meje barve
spodnjaG = np.ndarray((1,3))
zgornjaG = np.ndarray((1,3))

# Preverjenje ali smo izračunali število korakov za obdelati sliko in število korakov za obdelati
stepSet = False
stepW = 0
stepH = 0
steps = 0
stepW2 = 0
stepH2 = 0

# Določimo sliko
def doloci_barvo_koze(slika, levo_zgoraj, desno_spodaj):
    # Izberemo sliko
    (height, width, depth) = slika[levo_zgoraj[0]:desno_spodaj[0],levo_zgoraj[1]:desno_spodaj[1]].shape
    # Izračunamo povprečje za celo sliko, za vse barve
    mean = np.mean(slika[levo_zgoraj[0]:desno_spodaj[0],levo_zgoraj[1]:desno_spodaj[1]], axis=(0, 1))
    # Izračunamo standardni odklon in določimo nižjo in višjo vrednost
    stds = np.std(mean)
    meanL = mean - 3*stds
    meanH = mean + 3*stds
    return (meanL,meanH)

# Zmanjšamo sliko
def zmanjsaj_sliko(slika):
    obdelanaSlika = slika[h-130:h+130, w-150:w+150]
    return obdelanaSlika

# Obdelujemo sliko
def obdelaj_sliko(slika, okno_sirina, okno_visina,barva_koze_spodaj, barva_koze_zgoraj):
    global stepSet, stepW, stepH, steps, stepW2, stepH2
    # Preverjamo, če smo že delali izračune, da se izvaja hitreje
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
    # Se premikamo skozi sliko in štejemo piksle s funkcijo
    for i in range(steps):
        for j in range(steps):
            stPiklsov = prestej_piksle_z_barvo_koze(slika[int(stepW2*i):int(stepW2*i+stepW),int(stepH2*j):int(stepH2*j+stepH)],barva_koze_spodaj,barva_koze_zgoraj)
            # Preverimo, če je največ ujemajočih pikslov na tej podsliki
            if stPiklsov > maxIJV:
                maxI = i
                maxJ = j
                maxIJV = stPiklsov
    # Vrnemo koordinate najbol ujemajoče slike
    return [int(stepW2*maxJ), int(stepH2*maxI)], [int(stepW2*maxJ+stepW), int(stepH2*maxI+stepH)]

# Štejemo piklse v določenih razponih
def prestej_piksle_z_barvo_koze(podslika, barva_koze_spodaj, barva_koze_zgoraj):
    # Nastavimo masko na vse piksle, ki so v določenih razponih barv
    mask = np.all((barva_koze_spodaj <= podslika) & (podslika <= barva_koze_zgoraj), axis=-1)
    # Preštejemo piksle v maski
    numOfPixels = np.sum(mask)
    return numOfPixels

# Nastavimo koordinate za določanje barve, z mouse click
def clickDown(event, x, y, flags, param):
    global yG1, xG1, yG2, xG2, flipCoords, setRec
    if event == cv.EVENT_LBUTTONDOWN:
        print("Click on position ({},{})".format(x,y))
        # If stavek če izbiramo levo zograj ali desno spodaj
        if flipCoords:
            # Če je narobno zaporedje klikov, zamenjamo levo zgoraj in desno spodaj
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

# Če se kamera ne odpre
if not cap.isOpened():
    print("Cannot open camera")
    exit()

# Loop za zajemanje slike
while True:
    # Beremo sliko
    ret, frame = cap.read()

    # Preverimo če smo dobili sliko
    if not ret:
        print("Can't receive frame (stream end?). Exiting ...")
        break
    
    # Obrnemo sliko
    frame = cv.flip(frame, 1)

    # Pomanjšamo sliko
    frame = zmanjsaj_sliko(frame)

    # Preverjamo če rišemo kvadrat za izbiro barve kože
    if setRec:
        imgDraw = np.zeros(frame.shape, np.uint8)
        imgDraw = cv.rectangle(imgDraw, (xG1-1,yG2), (xG2,yG1-1), (0,255,0), 1)
        frame = frame | imgDraw
        timer -= 1
        # Ko poteče timer za določanje barve se določi barva in kvadrat se ne riše več
        if timer == 0:
            spodnjaG, zgornjaG = doloci_barvo_koze(frame,(yG1,xG1),(yG2,xG2))
            print("Skin color: ({}; {})".format(spodnjaG, zgornjaG))
            setRec = False
            colorSet = True
            timer = 30

    # Če smo določili barvo
    if colorSet:
        # Pridobimo dve koordinati najboljšega ujemanja
        p1, p2 = obdelaj_sliko(frame, 0.3, 0.3, spodnjaG, zgornjaG)
        # Narišemo kvadrat in nastavimo sliko
        imgDraw = np.zeros(frame.shape, np.uint8)
        imgDraw = cv.rectangle(imgDraw, (p1[0], p1[1]), (p2[0], p2[1]), (0, 0, 255), 3)
        frame = frame | imgDraw

    # Prikažemo sliko
    cv.imshow('frame', frame)

    # Callback za mouse click
    cv.setMouseCallback("frame", clickDown)

    # S tipko q zaustavimo delovanje
    if cv.waitKey(1) == ord('q'):
        break

# Konec delovanja
cap.release()
cv.destroyAllWindows()