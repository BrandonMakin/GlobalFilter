import cv2
import numpy as np

class Desaturate:

    name = "Desaturate"

    attributes = {}

    def run(self, image, heatmap):
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV).astype("float32") # convert image to HSV colorspace. use float32 for more precision
        hsv[:,:,1] *= heatmap # multiply saturation by heatmap
        image = cv2.cvtColor(hsv.astype("uint8"), cv2.COLOR_HSV2BGR) # convert back to uint8 type and BGR colorspace
        return image
