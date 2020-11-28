"""This module is used for manually testing functionality while developing i3drsgm module"""
import os
import cv2
from Stereo3D import StereoCalibration
from i3drsgm import I3DRSGM, StereoSupport

if __name__ == "__main__":
    # Get folder containing current script
    #script_folder = os.path.dirname(os.path.realpath(__file__))
    resource_folder = os.path.join("C:\\Code\\I3DR\\pyi3drsgm\\sample_data")

    # Load stereo calibration from yamls
    left_cal_file = os.path.join(resource_folder,"sim_left.yaml")
    right_cal_file = os.path.join(resource_folder,"sim_right.yaml")
    stcal = StereoCalibration()
    stcal.get_cal_from_yaml(left_cal_file,right_cal_file)

    # Initalise I3DRSGM
    print("Intitalising I3DRSGM...")
    i3drsgm = I3DRSGM(I3RSGMApp_folder="C:\\Code\\I3DR\\pyi3drsgm\\3rdparty\\i3drsgm")
    if (i3drsgm.isInit()):
        # Load images from file
        left_img = cv2.imread(os.path.join(resource_folder,"sim_left.png"))
        right_img = cv2.imread(os.path.join(resource_folder,"sim_right.png"))
        left_gray_img = cv2.cvtColor(left_img, cv2.COLOR_BGR2GRAY)
        right_gray_img = cv2.cvtColor(right_img, cv2.COLOR_BGR2GRAY)

        # Get Q from calibration
        Q = stcal.stereo_cal["q"]

        # Set matcher parameters
        i3drsgm.setDisparityRange(0)
        i3drsgm.setDisparityRange(3264)
        i3drsgm.enableInterpolation(False)

        valid = True
        while(valid):
            # Rectify stereo image pair
            left_rect_img, right_rect_img = stcal.rectify_pair(left_gray_img,right_gray_img)
            # Stereo match image pair
            print("Running I3DRSGM on images...")
            valid,disp = i3drsgm.forwardMatch(left_rect_img,right_rect_img)
            if (valid):
                # Downsample disparity image for faster processing
                # Downsample rate is passed through to 'display_disp' and 'depth_from_disp' to compensative for the change in image size
                downsample_rate = 0.5
                disp_resize = cv2.resize(disp,None,fx=downsample_rate,fy=downsample_rate,interpolation=cv2.INTER_NEAREST)

                # Get normalised colormap for visualising disparity
                disp_colormap = StereoSupport.colormap_from_disparity(disp_resize,Q,downsample_rate)

                # Resize colormap image for displaying in window
                disp_colormap_resized = StereoSupport.image_resize(disp_colormap, height=640)
                # Display disparity colormap in OpenCV window
                cv2.imshow("display", disp_colormap_resized)

                # Calculate depth from disparity
                depth = StereoSupport.depth_from_disp(disp_resize,Q,downsample_rate)

                print("Press any key on image window to close")
                cv2.waitKey(0)
                break # We only want to run this once for our purposes but can remove this to run continously

        # Important to close I3DRSGM to clean up memory
        # If program crashes before this has been called then you may need to restart the terminal to clean up memory
        i3drsgm.close()