import numpy as np
import matplotlib.pyplot as plt
from skimage import filters, feature, img_as_int
from skimage.filters import scharr_h, scharr_v, sobel_h, sobel_v, gaussian
from skimage.measure import regionprops
import cv2
import math

def get_interest_points(image, feature_width):
    '''
    Returns a set of interest points for the input image

    (Please note that we recommend implementing this function last and using cheat_interest_points()
    to test your implementation of get_features() and match_features())

    Implement the Harris corner detector (See Szeliski 4.1.1) to start with.
    You do not need to worry about scale invariance or keypoint orientation estimation
    for your Harris corner detector.
    You can create additional interest point detector functions (e.g. MSER)
    for extra credit.

    If you're finding spurious (false/fake) interest point detections near the boundaries,
    it is safe to simply suppress the gradients / corners near the edges of
    the image.

    Useful functions: A working solution does not require the use of all of these
    functions, but depending on your implementation, you may find some useful. Please
    reference the documentation for each function/library and feel free to come to hours
    or post on Piazza with any questions

        - skimage.feature.peak_local_max
        - skimage.measure.regionprops


    :params:
    :image: a grayscale or color image (your choice depending on your implementation)
    :feature_width:

    :returns:
    :xs: an np array of the x coordinates of the interest points in the image
    :ys: an np array of the y coordinates of the interest points in the image

    :optional returns (may be useful for extra credit portions):
    :confidences: an np array indicating the confidence (strength) of each interest point
    :scale: an np array indicating the scale of each interest point
    :orientation: an np array indicating the orientation of each interest point

    '''

    # TODO: Your implementation here!

    # These are placeholders - replace with the coordinates of your interest points!
    
    alpha = 0.04
    threshold = 1000
    XCorners = []
    YCorners = []
    RValues = []
    
    ImageRows = image.shape[0]
    ImageColumns = image.shape[1]
    
    imX = cv2.Sobel(image, cv2.CV_64F,1,0,ksize=5)
    imY = cv2.Sobel(image, cv2.CV_64F,0,1,ksize=5)
    Ixx = imX**2
    Iyy = imY**2
    Ixy = imX*imY
    for i in range(16, ImageRows - 16):
        for j in range(16, ImageColumns - 16):
            Ixx1 = Ixx[i-1:i+1, j-1:j+1]
            Iyy1 = Iyy[i-1:i+1, j-1:j+1]
            Ixy1 = Ixy[i-1:i+1, j-1:j+1]
            Ixxsum = Ixx1.sum()
            Iyysum = Iyy1.sum()
            Ixysum = Ixy1.sum()
            Determinant = Ixxsum*Iyysum - Ixysum**2	#计算矩阵的特征值
            Trace = Ixxsum + Iyysum	#计算矩阵的迹
            R = Determinant - alpha*(Trace**2) #角点相应函数R
            #判断每个像素相应函数是否大于阈值R，如果大于阈值则合格。
            if R > threshold:
                XCorners.append(j)
                YCorners.append(i)
                RValues.append(R)
    XCorners = np.asarray(XCorners)
    YCorners = np.asarray(YCorners)
    RValues = np.asarray(RValues)
    NewCorners = ANMS(XCorners, YCorners, RValues, 3025)
    NewCorners = np.asarray(NewCorners)
    x = NewCorners[:,0]
    y = NewCorners[:,1]
    return x,y

def ANMS (x , y, r, maximum):
    i = 0
    j = 0
    NewList = []
    while i < len(x):
        minimum = 1000000000000
        #获得一个harris角点的横纵坐标，称为基础点
        X, Y = x[i], y[i]
        while j < len(x):#遍历除该角点外每一个得分（R值）更高的角点，称为比较点，找到离基础点最近的一个比较点，记录下基础点的横纵坐标和与最近比较点之间的距离
            CX, CY = x[j], y[j]
            if (X != CX and Y != CY) and r[i] < r[j]:
                distance = math.sqrt((CX - X)**2 + (CY - Y)**2)
                if distance < minimum:
                    minimum = distance
            j = j + 1
        NewList.append([X, Y, minimum])
        i = i + 1
        j = 0
    #根据距离大小对基础点进行排序，很显然，距离越小的点说明在该角点周围有更好的角点，所以可以适当舍弃。在舍弃一定数目的得分较小的角点后，就得到了非最大抑制后的harris角点坐标。
    NewList.sort(key = lambda t: t[2])
    NewList = NewList[len(NewList)-maximum:len(NewList)]
    return NewList


def get_features(image, x, y, feature_width):
    '''
    Returns a set of feature descriptors for a given set of interest points.

    (Please note that we reccomend implementing this function after you have implemented
    match_features)

    To start with, you might want to simply use normalized patches as your
    local feature. This is very simple to code and works OK. However, to get
    full credit you will need to implement the more effective SIFT-like descriptor
    (See Szeliski 4.1.2 or the original publications at
    http://www.cs.ubc.ca/~lowe/keypoints/)

    Your implementation does not need to exactly match the SIFT reference.
    Here are the key properties your (baseline) descriptor should have:
    (1) a 4x4 grid of cells, each descriptor_window_image_width/4.
    (2) each cell should have a histogram of the local distribution of
        gradients in 8 orientations. Appending these histograms together will
        give you 4x4 x 8 = 128 dimensions.
    (3) Each feature should be normalized to unit length

    You do not need to perform the interpolation in which each gradient
    measurement contributes to multiple orientation bins in multiple cells
    As described in Szeliski, a single gradient measurement creates a
    weighted contribution to the 4 nearest cells and the 2 nearest
    orientation bins within each cell, for 8 total contributions. This type
    of interpolation probably will help, though.

    You do not have to explicitly compute the gradient orientation at each
    pixel (although you are free to do so). You can instead filter with
    oriented filters (e.g. a filter that responds to edges with a specific
    orientation). All of your SIFT-like feature can be constructed entirely
    from filtering fairly quickly in this way.

    You do not need to do the normalize -> threshold -> normalize again
    operation as detailed in Szeliski and the SIFT paper. It can help, though.

    Another simple trick which can help is to raise each element of the final
    feature vector to some power that is less than one.

    Useful functions: A working solution does not require the use of all of these
    functions, but depending on your implementation, you may find some useful. Please
    reference the documentation for each function/library and feel free to come to hours
    or post on Piazza with any questions

        - skimage.filters (library)


    :params:
    :image: a grayscale or color image (your choice depending on your implementation)
    :x: np array of x coordinates of interest points
    :y: np array of y coordinates of interest points
    :feature_width: in pixels, is the local feature width. You can assume
                    that feature_width will be a multiple of 4 (i.e. every cell of your
                    local SIFT-like feature will have an integer width and height).
    If you want to detect and describe features at multiple scales or
    particular orientations you can add input arguments.

    :returns:
    :features: np array of computed features. It should be of size
            [len(x) * feature dimensionality] (for standard SIFT feature
            dimensionality is 128)

    '''

    # TODO: Your implementation here! 

    # This is a placeholder - replace this with your features!
    # Convert to integers for indexing 
    xs = np.round(x).astype(int)
    ys = np.round(y).astype(int)

    # Define helper functions for readabilty and avoid copy-pasting
    def get_window(y, x):
        """
         Helper to get indices of the feature_width square
        """
        rows = (x - (feature_width/2 -1), x + feature_width/2)
        if rows[0] < 0:
            rows = (0, rows[1] - rows[0])
        if rows[1] >= image.shape[0]:
            rows = (rows[0]  + (image.shape[0] -1 - rows[1]), image.shape[0] - 1)
        cols = (y - (feature_width/2 -1), y + feature_width/2)
        if cols[0] < 0:
            cols = (0, cols[1] - cols[0])
        if cols[1] >= image.shape[1]:
            cols = (cols[0]  - (cols[1] + 1 - image.shape[1]), image.shape[1] - 1)
        return int(rows[0]), int(rows[1]) + 1, int(cols[0]), int(cols[1]) + 1

    def get_current_window(i, j, matrix):
        """
        Helper to get sub square of size feature_width/4 
        From the square matrix of size feature_width
        """
        return matrix[int(i*feature_width/4):
                    int((i+1)*feature_width/4),
                    int(j*feature_width/4):
                    int((j+1)*feature_width/4)]

    def rotate_by_dominant_angle(angles, grads):
        hist, bin_edges = np.histogram(angles, bins= 36, range=(0, 2*np.pi), weights=grads)
        angles -= bin_edges[np.argmax(hist)]
        angles[ angles < 0 ] += 2 * np.pi
    
    # Initialize features tensor, with an easily indexable shape
    features = np.zeros((len(xs), 4, 4, 8))
    # Get gradients and angles by filters (approximation)
    sigma = 0.8
    filtered_image = gaussian(image, sigma)
    dx = scharr_v(filtered_image)
    dy = scharr_h(filtered_image)
    gradient = np.sqrt(np.square(dx) + np.square(dy))
    angles = np.arctan2(dy, dx)
    angles[angles < 0 ] += 2*np.pi

    for n, (x, y) in enumerate(zip(xs, ys)):
        # Feature square 
        i1, i2, j1, j2 = get_window(x, y)
        grad_window = gradient[i1:i2, j1:j2]
        angle_window = angles[i1:i2, j1:j2]
        # Loop over sub feature squares 
        for i in range(int(feature_width/4)):
            for j in range(int(feature_width/4)):
                # Enhancement: a Gaussian fall-off function window
                current_grad = get_current_window(i, j, grad_window).flatten()
                current_angle = get_current_window(i, j, angle_window).flatten()
                features[n, i, j] = np.histogram(current_angle, bins=8,
                 range=(0, 2*np.pi), weights=current_grad)[0]
                
    features = features.reshape((len(xs), -1,))
    dividend = np.linalg.norm(features, axis=1).reshape(-1, 1)
    # Rare cases where the gradients are all zeros in the window
    # Results in np.nan from division by zero.
    dividend[dividend == 0 ] = 1
    features = features / dividend
    thresh = 0.25
    features[ features >= thresh ] = thresh
    features  = features ** 0.8
    # features = features / features.sum(axis = 1).reshape(-1, 1)
    return features


def match_features(im1_features, im2_features):
    '''
    Implements the Nearest Neighbor Distance Ratio Test to assign matches between interest points
    in two images.

    Please implement the "Nearest Neighbor Distance Ratio (NNDR) Test" ,
    Equation 4.18 in Section 4.1.3 of Szeliski.

    For extra credit you can implement spatial verification of matches.

    Please assign a confidence, else the evaluation function will not work. Remember that
    the NNDR test will return a number close to 1 for feature points with similar distances.
    Think about how confidence relates to NNDR.

    This function does not need to be symmetric (e.g., it can produce
    different numbers of matches depending on the order of the arguments).

    A match is between a feature in im1_features and a feature in im2_features. We can
    represent this match as a the index of the feature in im1_features and the index
    of the feature in im2_features

    Useful functions: A working solution does not require the use of all of these
    functions, but depending on your implementation, you may find some useful. Please
    reference the documentation for each function/library and feel free to come to hours
    or post on Piazza with any questions

        - zip (python built in function)

    :params:
    :im1_features: an np array of features returned from get_features() for interest points in image1
    :im2_features: an np array of features returned from get_features() for interest points in image2

    :returns:
    :matches: an np array of dimension k x 2 where k is the number of matches. The first
            column is an index into im1_features and the second column is an index into im2_features
    :confidences: an np array with a real valued confidence for each match
    '''

    # TODO: Your implementation here!

    # These are placeholders - replace with your matches and confidences!
    
    # Initialize variables
    matches = []
    confidences = []
    
    # Loop over the number of features in the first image
    for i in range(im1_features.shape[0]):
        # Calculate the euclidean distance between feature vector i in 1st image and all other feature vectors
        # second image
        distances = np.sqrt(((im1_features[i,:]-im2_features)**2).sum(axis = 1))

        # sort the distances in ascending order, while retaining the index of that distance
        ind_sorted = np.argsort(distances)
        # If the ratio between the 2 smallest distances is less than 0.8
        # add the smallest distance to the best matches
        if (distances[ind_sorted[0]] < 0.9 * distances[ind_sorted[1]]):
        # append the index of im1_feature, and its corresponding best matching im2_feature's index
            matches.append([i, ind_sorted[0]])
            confidences.append(1.0  - distances[ind_sorted[0]]/distances[ind_sorted[1]])
          # How can I measure confidence?
    confidences = np.asarray(confidences)
    confidences[np.isnan(confidences)] = np.min(confidences[~np.isnan(confidences)])     

    return np.asarray(matches), confidences