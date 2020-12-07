"""
I3DRSGM python package

This module is for using I3DR Semi-Global Matcher in Python.
"""
import os
import subprocess
import shutil
import numpy as np
import cv2
import wget
import zipfile
import sys

# Exceptions
'''
class ImageSizeNotEqual(Exception):
    """Image size not equal exception"""
    def __str__(self):
        return "Image sizes must be equal"
'''


class StereoSupport:
    def __init__(self):
        pass

    @staticmethod
    def scale_disparity(disparity):
        # Normalise disparity by min and max value in image
        minV, maxV, _, _ = cv2.minMaxLoc(disparity)
        if (maxV - minV != 0):
            scaled_disp = cv2.convertScaleAbs(
                disparity,
                alpha=255.0/(maxV - minV),
                beta=-minV * 255.0/(maxV - minV))
            return scaled_disp
        else:
            return np.zeros(disparity.shape, np.uint8)

    @staticmethod
    def image_resize(image, width=None, height=None, inter=cv2.INTER_AREA):
        """
        Resize image based on height or width while maintaning aspect ratio
        :param image: image matrix
        :param width:
            desired width of output image
            (can only use width or height not both)
        :param height:
            desired height of output image
            (can only use width or height not both)
        :param inter: opencv resize method (default: cv2.INTER_AREA)
        :type image: numpy
        :type width: int
        :type height: int
        :type inter: int
        """
        # initialize the dimensions of the image to be resized and
        # grab the image size
        dim = None
        (h, w) = image.shape[:2]

        # if both the width and height are None, then return the
        # original image
        if width is None and height is None:
            return image

        # check to see if the width is None
        if width is None:
            # calculate the ratio of the height and construct the
            # dimensions
            r = height / float(h)
            dim = (int(w * r), height)

        # otherwise, the height is None
        else:
            # calculate the ratio of the width and construct the
            # dimensions
            r = width / float(w)
            dim = (width, int(h * r))

        # resize the image
        resized = cv2.resize(image, dim, interpolation=inter)

        # return the resized image
        return resized

    @staticmethod
    def reprojectImageTo3D(disp, Q, downsample_rate=1.0):
        # Get important values from Q matrix
        wz = Q[2, 3]
        q03 = Q[0, 3]
        q13 = Q[1, 3]
        q32 = Q[3, 2]
        q33 = Q[3, 3]

        # Calculate downsample factor to correct
        # for downsampling applied to disparity image
        # This make sure that the disparity value
        # is not effected by the donwnsampling
        downsample_factor = 1/downsample_rate

        # Calculate W from key values in Q matrix
        w = (disp * q32) + q33
        # Calculate Z channel of depth image
        z = wz / w
        # Fill x,y channel the same size as Z
        y = np.full_like(z, 1)
        x = np.full_like(z, 1)

        # Calculate x and y elements
        # Downsample factor is applied to compensate
        # for using a downsampled disparity image
        # this is needed as the index of the pixel
        # (i and j) is used in the calculation
        num_rows, num_cols = disp.shape
        for i in range(0, num_rows):
            for j in range(0, num_cols):
                x[i, j] = ((j * downsample_factor) + q03) / w[i, j]
                y[i, j] = ((i * downsample_factor) + q13) / w[i, j]

        # Combine x,y,z into depth image
        depth = cv2.merge((x, y, z))

        return depth

    @staticmethod
    def depth_from_disp(disp, Q, downsample_rate=1.0):

        # Get important values from Q matrix
        q32 = Q[3, 2]
        q33 = Q[3, 3]

        # I3DRSGM returns negative disparity so invert
        disparity16 = -disp.astype(np.float32)

        # Calculate W from key values in Q matrix
        w = (disparity16 * q32) + q33

        # Find elements in W less than 0 (invalid as would be behind camera)
        w_zero_mask = w <= 0
        # Filter disparity image to only allow valid disparities
        disparity16[w_zero_mask != 0] = 0.0

        # Find elements in W eq to 99999 (invalid disparity signifier)
        d_inf_mask = disparity16 == 99999
        # Filter disparity image to only allow valid disparities
        disparity16[d_inf_mask != 0] = 0.0

        # Calculate min max disparity (ignoring zeros)
        masked_a = np.ma.masked_equal(disparity16, 0.0, copy=False)
        minDisp = masked_a.min()
        maxDisp = masked_a.max()

        # Replace invalid disparities with minium disparity
        disparity16[w_zero_mask != 0] = minDisp
        # Replace invalid disparities with maximum disparity
        disparity16[d_inf_mask != 0] = maxDisp

        # Generate depth from disparity
        print("Generating depth from disparity...")
        depth = StereoSupport.reprojectImageTo3D(
            disparity16, Q, downsample_rate)

        # Filter depth image to only allow valid disparities
        depth[w_zero_mask != 0] = [0, 0, 0]

        # Split depth image into x,y,z channels
        x, y, z = cv2.split(depth)
        # Filter z to remove invalid values
        z[w_zero_mask != 0] = 0.0
        z[d_inf_mask != 0] = 0.0
        # Re-combine depth image
        depth = cv2.merge((x, y, z))

        # Calculate min max depth
        masked_depth = np.ma.masked_equal(z, 0.0, copy=False)
        minDepth = masked_depth.min()
        maxDepth = masked_depth.max()
        print("Depth range: "+str(minDepth)+"m, "+str(maxDepth)+"m")

        return depth

    @staticmethod
    def colormap_from_disparity(disp, Q, downsample_rate=1.0):
        # Display normalised disparity with colormap in OpenCV windows

        # Get important values from Q matrix
        q32 = Q[3, 2]
        q33 = Q[3, 3]

        # I3DRSGM returns negative disparity so invert
        disparity16 = -disp.astype(np.float32)

        # Calculate W from key values in Q matrix
        w = (disparity16 * q32) + q33

        # Find elements in W less than 0 (invalid as would be behind camera)
        w_zero_mask = w <= 0
        # Filter disparity image to only allow valid disparities
        disparity16[w_zero_mask != 0] = 0.0

        # Find elements in W eq to 99999 (invalid disparity signifier)
        d_inf_mask = disparity16 == 99999
        # Filter disparity image to only allow valid disparities
        disparity16[d_inf_mask != 0] = 0.0

        # Calculate min max disparity (ignoring zeros)
        masked_a = np.ma.masked_equal(disparity16, 0.0, copy=False)
        minDisp = masked_a.min()
        maxDisp = masked_a.max()

        # Replace invalid disparities with minium disparity
        disparity16[w_zero_mask != 0] = minDisp
        # Replace invalid disparities with maximum disparity
        disparity16[d_inf_mask != 0] = maxDisp
        # Normalise disparity
        disp_scaled = StereoSupport.scale_disparity(disparity16)

        print("Applying colormap to disparity...")

        # Apply color map to disparity
        disp_colormap = cv2.applyColorMap(disp_scaled, cv2.COLORMAP_JET)
        # Filter out invalid disparities from colormap
        disp_colormap[w_zero_mask != 0] = [0, 0, 0]
        disp_colormap[d_inf_mask != 0] = [0, 0, 0]

        return disp_colormap


class I3DRSGMAppAPI:
    def __init__(self, license_file=None):
        # Initialise I3DRSGM App API
        # Get folder containing current script
        script_folder = os.path.dirname(os.path.realpath(__file__))
        # Init variables
        self.init_success = False
        self.PARAM_MIN_DISPARITY = "SET_MIN_DISPARITY"
        self.PARAM_DISPARITY_RANGE = "SET_DISPARITY_RANGE"
        self.PARAM_INTERPOLATION = "SET_INTERPOLATION"
        self.PARAM_WINDOW_SIZE = "SET_WINDOW_SIZE"
        self.PARAM_PYRAMID_LEVEL = "SET_PYRAMID_LEVEL"
        self.param_list = [
            self.PARAM_MIN_DISPARITY, self.PARAM_DISPARITY_RANGE,
            self.PARAM_INTERPOLATION, self.PARAM_WINDOW_SIZE,
            self.PARAM_WINDOW_SIZE, self.PARAM_PYRAMID_LEVEL]

        # Check for valid I3DRSGMApp install
        valid_i3drsgm_app = False
        i3drsgm_app_folder = os.path.join(script_folder, "i3drsgm_app")
        self.I3DRSGMApp = os.path.join(i3drsgm_app_folder, "I3DRSGMApp.exe")
        # Check if I3DRSGMApp folder exists
        if os.path.exists(i3drsgm_app_folder):
            if os.path.exists(i3drsgm_app_folder):
                # TODO: check all dlls are present
                valid_i3drsgm_app = True

        if not valid_i3drsgm_app:
            msg = "Failed to find I3DRSGMApp in python install. "
            msg += "You must be running the online wheel. "
            msg += "Downloading the required files..."
            print(msg)
            self.download_app()

        # Define output folder used for storing images while processing
        script_folder = os.path.dirname(os.path.realpath(__file__))
        tmp_folder = os.path.join(script_folder, 'tmp')
        if not os.path.exists(tmp_folder):
            os.makedirs(os.path.join(tmp_folder))
        self.tmp_folder = tmp_folder

        # Copy license file to I3DRSGM path
        if license_file is not None:
            if os.path.exists(license_file):
                if os.path.isfile(license_file):
                    shutil.copy2(
                        license_file, os.path.dirname(self.I3DRSGMApp))
                else:
                    print("license_file parameter expects a file")
                    self.init_success = False
                    return
            else:
                print("license file does not exist")
                self.init_success = False
                return

        # Start I3DRSGMApp with API argument
        self.appProcess = subprocess.Popen(
            [self.I3DRSGMApp, "api"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        self.init_success = True
        # Send initalisation request to I3DRSGM API
        valid, response = self.apiRequest("INIT")
        if not valid:  # Check init request was successful
            print("Failed to initalise I3DRSGM: "+response)
            self.close()
        self.init_success = valid

    @staticmethod
    def download_app(i3drsgm_app_version="1.0.7", replace=False):
        def bar_progress(current, total, *_):
            """
            Progress bar to display download progress in wget

            Parameters:
                current (int): current byte count
                total (int): total number of bytes
                *_: required by wget but is ignored in this function
            """
            base_progress_msg = "Downloading: %d%% [%d / %d] bytes"
            progress_message = base_progress_msg % (
                current / total * 100, current, total)
            # Don't use print() as it will print in new line every time.
            sys.stdout.write("\r" + progress_message)
            sys.stdout.flush()

        def download_from_release(i3drsgm_app_version):
            script_folder = os.path.dirname(os.path.realpath(__file__))
            zip_filepath = os.path.join(script_folder, "i3drsgm-app.zip")

            base_url = "https://github.com/i3drobotics/i3drsgm"
            base_url += "/releases/download/"
            release_url = "v{}/i3drsgm-{}-app.zip".format(
                i3drsgm_app_version, i3drsgm_app_version)
            url = base_url+release_url

            wget.download(url, zip_filepath, bar=bar_progress)
            # unzip downloaded file
            with zipfile.ZipFile(zip_filepath, "r") as zip_ref:
                zip_ref.extractall(script_folder)
            # removing zip file
            os.remove(zip_filepath)

        script_folder = os.path.dirname(os.path.realpath(__file__))

        # Check for I3DRSGMApp already exists
        i3drsgm_app_exists = False
        i3drsgm_app_folder = os.path.join(script_folder, "i3drsgm_app")
        i3drsgm_app = os.path.join(i3drsgm_app_folder, "I3DRSGMApp.exe")
        # Check if I3DRSGMApp folder exists
        if os.path.exists(i3drsgm_app_folder):
            if os.path.exists(i3drsgm_app):
                # TODO: check all dlls are present
                i3drsgm_app_exists = True

        if not i3drsgm_app_exists:
            download_from_release(i3drsgm_app_version)
        else:
            if replace:
                shutil.rmtree(i3drsgm_app_folder)
                download_from_release(i3drsgm_app_version)

    def isInit(self):
        # Check if class was initalised successfully
        return self.init_success

    def removePrefix(self, text, prefix):
        # Remove prefix from string
        if text.startswith(prefix):
            return text[len(prefix):]
        return text  # or whatever

    def apiWaitResponse(self):
        # Wait for reponse from I3DRSGM app API.
        # This is important to keep the pipe buffer clean
        if self.init_success:
            while True:
                line = self.appProcess.stdout.readline()
                line_str = line.decode("utf-8")
                if (line_str == "API_READY\r\n"):
                    return True, line_str
                elif (line_str.startswith("API_RESPONSE:")):
                    response = self.removePrefix(line_str, "API_RESPONSE:")
                    if (response.startswith("ERROR,")):
                        error_msg = self.removePrefix(response, "ERROR,")
                        return False, error_msg.rstrip()
                    else:
                        return True, response.rstrip()
                elif (line_str == ""):
                    return False, line_str
                else:
                    pass
                    # print("stout:"+line_str)
        else:
            print("Failed to initalise the pyI3DRSGM class. Make sure to initalise the class 'i3rsgm = pyI3DRSGM(...'")
            print("Check valid initalisation with 'isInit' function. E.g. 'i3rsgm.isInit()'")

    def apiRequest(self, cmd):
        # Perform an API requst with the I3DRSGM app
        if (self.init_success):
            valid, response = self.apiWaitResponse()
            if (valid):
                # print("sending api request...")
                self.appProcess.stdin.write((cmd+"\n").encode())
                self.appProcess.stdin.flush()
                # print("waiting for api response...")
                valid, response = self.apiWaitResponse()
            return valid, response
        else:
            print("Failed to initalise the pyI3DRSGM class. Make sure to initalise the class 'i3rsgm = pyI3DRSGM(...'")
            print("Check valid initalisation with 'isInit' function. E.g. 'i3rsgm.isInit()'")
            return False, ""

    def forwardMatchFiles(self, left_filepath, right_filepath,
                          left_cal_filepath=None, right_cal_filepath=None):
        # Stereo match from left and right image filepaths
        if self.init_success:
            if (left_cal_filepath is None or right_cal_filepath is None):
                appOptions = "FORWARD_MATCH,"+left_filepath+","+right_filepath+","+self.tmp_folder
            else:
                appOptions = "FORWARD_MATCH,"+left_filepath+","+right_filepath+","
                appOptions += left_cal_filepath+","+right_cal_filepath+","+self.tmp_folder+",0"
            valid, response = self.apiRequest(appOptions)
            if (not valid):
                print(response)
            return valid
        else:
            print("Failed to initalise the pyI3DRSGM class. Make sure to initalise the class 'i3rsgm = pyI3DRSGM(...'")
            print("Check valid initalisation with 'isInit' function. E.g. 'i3rsgm.isInit()'")
            return valid

    def setParam(self, param, value):
        # Set algorithm parameter with api request
        if (self.init_success):
            if param in self.param_list:
                appOptions = param+","+str(value)
                valid, _ = self.apiRequest(appOptions)
                return valid
            else:
                print("Invalid param {}".format(param))
                return False
        else:
            print("Failed to initalise the pyI3DRSGM class. Make sure to initalise the class 'i3rsgm = pyI3DRSGM(...'")
            print("Check valid initalisation with 'isInit' function. E.g. 'i3rsgm.isInit()'")
            return False

    def close(self):
        # Close connection to app process
        # Required to clean up memory
        self.appProcess.terminate()


class I3DRSGM:
    def __init__(self, license_file=None, replace_api=False):
        if (replace_api):
            I3DRSGMAppAPI.download_app(replace=True)
        # Initalse I3DRSGM
        # Initalise connection to I3DRSGM app API
        self.i3drsgmAppAPI = I3DRSGMAppAPI(license_file)

    def isInit(self):
        # Check I3DRSGM has been initalised
        return self.i3drsgmAppAPI.isInit()

    def forwardMatch(self, left_img, right_img):
        # Stereo matching using a left and right image
        # (expects images to already by rectified)
        if self.isInit():
            left_filepath = os.path.join(
                self.i3drsgmAppAPI.tmp_folder, "left_tmp.png")
            right_filepath = os.path.join(
                self.i3drsgmAppAPI.tmp_folder, "right_tmp.png")
            disp_filepath = os.path.join(
                self.i3drsgmAppAPI.tmp_folder, "disparity.tif")
            cv2.imwrite(left_filepath, left_img)
            cv2.imwrite(right_filepath, right_img)
            valid = self.i3drsgmAppAPI.forwardMatchFiles(
                left_filepath, right_filepath)
            disp = None
            if (valid):
                disp = cv2.imread(disp_filepath, -1)
            return valid, disp
        else:
            print("Failed to initalise the pyI3DRSGM class. Make sure to initalise the class 'i3rsgm = pyI3DRSGM(...'")
            print("Check valid initalisation with 'isInit' function. E.g. 'i3rsgm.isInit()'")
            return valid, None

    def setDisparityRange(self, value):
        # Set disparity range used I3DRSGM algorithm
        if (self.isInit()):
            valid = self.i3drsgmAppAPI.setParam(
                self.i3drsgmAppAPI.PARAM_DISPARITY_RANGE, value)
            return valid
        else:
            print("Failed to initalise the pyI3DRSGM class. Make sure to initalise the class 'i3rsgm = pyI3DRSGM(...'")
            print("Check valid initalisation with 'isInit' function. E.g. 'i3rsgm.isInit()'")
            return False

    def setWindowSize(self, value):
        # Set disparity range used I3DRSGM algorithm
        if (self.isInit()):
            valid = self.i3drsgmAppAPI.setParam(
                self.i3drsgmAppAPI.PARAM_WINDOW_SIZE, value)
            return valid
        else:
            print("Failed to initalise the pyI3DRSGM class. Make sure to initalise the class 'i3rsgm = pyI3DRSGM(...'")
            print("Check valid initalisation with 'isInit' function. E.g. 'i3rsgm.isInit()'")
            return False

    def setPyamidLevel(self, value):
        # Set disparity range used I3DRSGM algorithm
        if (self.isInit()):
            valid = self.i3drsgmAppAPI.setParam(
                self.i3drsgmAppAPI.PARAM_PYRAMID_LEVEL, value)
            return valid
        else:
            print("Failed to initalise the pyI3DRSGM class. Make sure to initalise the class 'i3rsgm = pyI3DRSGM(...'")
            print("Check valid initalisation with 'isInit' function. E.g. 'i3rsgm.isInit()'")
            return False

    def setMinDisparity(self, value):
        # Set minimum disparity used I3DRSGM algorithm
        if (self.isInit()):
            valid = self.i3drsgmAppAPI.setParam(
                self.i3drsgmAppAPI.PARAM_MIN_DISPARITY, value)
            return valid
        else:
            print("Failed to initalise the pyI3DRSGM class. Make sure to initalise the class 'i3rsgm = pyI3DRSGM(...'")
            print("Check valid initalisation with 'isInit' function. E.g. 'i3rsgm.isInit()'")
            return False

    def enableInterpolation(self, enable):
        # Enable interpolation in I3DRSGM algorithm
        if (self.isInit()):
            if (enable):
                val = 1
            else:
                val = 0
            valid = self.i3drsgmAppAPI.setParam(
                self.i3drsgmAppAPI.PARAM_INTERPOLATION, val)
            return valid
        else:
            print("Failed to initalise the pyI3DRSGM class. Make sure to initalise the class 'i3rsgm = pyI3DRSGM(...'")
            print("Check valid initalisation with 'isInit' function. E.g. 'i3rsgm.isInit()'")
            return False

    def close(self):
        # Close connection to I3DRSGM app API
        # Required to clean up memory
        self.i3drsgmAppAPI.close()
