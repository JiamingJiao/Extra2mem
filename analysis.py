#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cv2 as cv
import numpy as np
import math
import os
import dataProc
import model
import keras.backend as K

def calculateMAE(src1, src2):
    difference = np.subtract(src1, src2)
    absDifference = np.abs(difference)
    mae = np.mean(absDifference)
    return mae

def histEqualizationArray(src, depth = 8):
    maxIntensity = 2**depth - 1
    temp = 0.
    dst = np.zeros((maxIntensity+1), dtype = np.float64)
    pixNum = src.shape[0]*src.shape[1]
    histogram = cv.calcHist([src], [0], None, [maxIntensity+1], [0, maxIntensity+1])
    hitogram = histogram.astype(np.float64)
    for i in range(0, maxIntensity+1):
        dst[i] = temp + maxIntensity*histogram[i]/(pixNum)
        temp = dst[i]
    dst = dst.astype(np.int32)
    return dst

def calculateHistTransArray(srcHist, dstHist, depth = 8):
    maxIntensity = 2**depth - 1
    dst = np.zeros((maxIntensity+1), dtype = np.int32)
    accumulation = 0
    for i in range(0, maxIntensity+1):
        diff = maxIntensity+1
        for j in range(0, maxIntensity + 1):
            if abs(dstHist[j] - srcHist[i])<diff:
                diff = abs(dstHist[j] - srcHist[i])
                dst[i] = j
    return dst

def histSpecification(src, transArray):
    dst = np.zeros(src.shape, dtype = np.int32)
    for i in range(0, src.shape[0]):
        for j in range(0, src.shape[1]):
            dst[i, j] = transArray[src[i, j]]
    return dst

class intermediateLayers(model.networks):
    def __init__(self, src, netName = 'uNet', weightsPath = None, **kwargs):
        super(intermediateLayers, self).__init__(**kwargs)
        self.netName = netName
        if self.netName == 'uNet':
            resizedSrc = np.ndarray((self.imgRows, self.imgCols), dtype = np.float32)
            resizedSrc = cv.resize(src, (self.imgRows, self.imgCols), resizedSrc, 0, 0, cv.INTER_NEAREST)
            self.input = resizedSrc[np.newaxis, :, :, np.newaxis]
            self.network = super(intermediateLayers, self).uNet()
        self.network.load_weights(weightsPath)
        self.inputTensor = self.network.layers[0].input

    def intermediateFeatures(self, layerName):
        layer = self.network.get_layer(layerName)
        layerFunc = K.function([self.inputTensor, K.learning_phase()], [layer.output])
        dst = layerFunc([self.input, 0])[0] # output in test mode, learning_phase = 0
        return dst

    # save all features of one layer in one picture
    def saveFeatures(self, dstPath, startLayer = 3, endLayer = 7):
        allFeatures = np.empty(endLayer-startKayer+1, dtype = object)
        max = -np.inf
        min = np.inf
        #calculation
        for encoderNum in range(startLayer, endLayer+1, 1):
            layerName = 'connection' + '%d'%encoderNum
            allFeatures[encoderNum-startLayer] = self.intermediateFeatures(layerName)
            layerMax = np.amax(allFeatures[encoderNum-startLayer])
            layerMin = np.amin(allFeatures[encoderNum-startLayer])
            if layerMax > max:
                max = layerMax
            if layerMin < min:
                min = layermin
        #normalization and saving
        for encoderNum in range(startLayer, endLayer+1, 1):
            allFeatures[encoderNum-startLayer] = 255*(allFeatures[encoderNum-startLayer]-min)/(max-min)
            layerPath = dstPath + 'layer_%d/'%encoderNum
            featuresNum = allFeatures[encoderNum-startLayer].shape[3]
            for feature in range(1, featuresNum+1, 1):
                cv.imwrite(dstPath + "%d"%feature+".png", allFeatures[encoderNum-startLayer][0, :, :, feature])
