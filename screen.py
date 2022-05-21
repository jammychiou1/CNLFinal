import xlib_helper
from ctypes import *
from PIL import Image
from matplotlib import pyplot as plt
import time
import subprocess

def get_screen():
    w = 960
    h = 640
    size = w * h * 3
    data = (c_ubyte * size)()
    xlib_helper.so_get_screen(xlib_helper.dpy, xlib_helper.window, w, h, data)
    return Image.frombuffer('RGB', (w, h), data, 'raw', 'BGR', 0, 1)

def press(keyname):
    xlib_helper.so_press(xlib_helper.dpy, xlib_helper.window, c_char_p(keyname.encode('utf-8')))
    
def release(keyname):
    xlib_helper.so_release(xlib_helper.dpy, xlib_helper.window, c_char_p(keyname.encode('utf-8')))

if __name__ == '__main__':
    game = subprocess.Popen('./eggnoggplus')
    time.sleep(1)
    xlib_helper.init()
    time.sleep(1)
    press('Left')
    time.sleep(0.03)
    release('Left')
    '''
    then = time.time()
    while True:
        screen = get_screen()
        #plt.imshow(screen)
        #plt.show()
        now = time.time()
        print(1 / (now - then))
        then = now
    '''

