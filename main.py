#Dependencies
import math
import numpy
import multiprocessing.dummy as multiprocessing
import random

#==Global variables==

#Image
img_width = 256
img_height = 256

#minimum and maximum values
minx = -3   #Lowest value for x
miny = -2   #Lowest value for y -> imaginary numbers
maxx = 1    #Highest value fox x
maxy = 2    #Highest value for y -> imaginary numbers

#Anti-aliasing
msaa_samples = 32   #samples for multisample-antialiasing
msaa_xoff_max = (abs(maxx-minx) / img_width)/2
msaa_yoff_max = (abs(maxy-miny) / img_height)/2

#Misc
mt_threadcount = 8 #amount of threads for multithreading
mt_threadheight = int(img_height/mt_threadcount)
z_iters = 100       #amount of iterations to check if a number is in a set
z_threshold = 10     #threshold for numbers to belong in the set or not
finished_rows = 0

#This function determines how many iterations it takes before a number goes past a set threshold
def getBrightness(c):
    z = 0   #start at z = 0
    for iters in range(z_iters):
        z = z * z + c   #feed a point into the function, this gives a value to be fed back into it the next iteration
        if abs(z.real) >= z_threshold or abs(z.imag) > z_threshold: #is the value past the threshold?
            return (255/z_iters) * iters #return the amount it took to go past the threshold
    return 0  #it passed all, so give 0, since it is probably in the center of the figure

#map value in a range, taking in original range and new range, spitting out the new value, like c++ map() function
def mapRange(value, lv, hv, minv, maxv):
    return (((value - lv)/(hv-lv))*(maxv-minv)) + minv

def renderThread(tid):
    global finished_rows
    with open("./threaddump" + str(tid) + '.txt', 'w') as tdump:
        tdump.write('')
    for cy in range(mt_threadheight * tid, mt_threadheight * (tid + 1)):    #start at current division and run until the other starts
        yv = mapRange(cy, 0, img_height, miny, maxy)    #map the current pixel into the graph
        for cx in range(img_width): #loop over x values in this row
            xv = mapRange(cx, 0, img_width, minx, maxx) #map x value to coords
            #xv and yv are the coords, x = real, y = imag
            bright = 0 # pixel brightness, predefined, will be set properly further down. Also functions as reset
            for sample in range(msaa_samples):
                #make random offsets for msaa
                xoff = random.random() * msaa_xoff_max
                yoff = random.random() * msaa_yoff_max
                #determine if negative or positive offset
                yneg = random.randint(0,1)
                xneg = random.randint(0,1)
                #act accordingly
                if xneg:
                    xvo = xv - xoff
                if not xneg:
                    xvo = xv + xoff
                if yneg:
                    yvo = yv - yoff
                if not yneg:
                    yvo = yv + yoff
                #get brightness of offset point
                bright = bright + getBrightness(numpy.complex(xvo, yvo))
            
            bright = round(bright / msaa_samples)
            red = int(round(mapRange(bright * bright, 0, 65025, 0, 255)))
            green = int(round(bright))
            blue = int(round(mapRange(math.sqrt(bright), 0, 16, 0, 255)))
            
            with open("./threaddump" + str(tid) + '.txt', 'a') as tdump:
                tdump.write(str(red) + ' ' + str(green) + ' ' + str(blue) + '\n')
        finished_rows += 1
        print('Rendering at ' + str(round((finished_rows/img_height) * 100, 2)) + '%')
            

def stitchImage():
    with open("./output.ppm", 'w') as img:
        img.write("P3\n" + str(img_width) + " " + str(img_height) + "\n255\n")
    for t in range(mt_threadcount):
        with open("./threaddump" + str(t) + '.txt', 'r') as tdump:
            thread_output = tdump.read()
            with open("./output.ppm", 'a') as img:
                img.write(thread_output)


def renderImage():
    threadPool = multiprocessing.Pool(mt_threadcount)
    threadPool.map(renderThread, range(0, mt_threadcount))
    threadPool.close()
    threadPool.join()
    stitchImage()

renderImage()