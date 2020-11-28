"""This module tests core functionality in i3drsgm module"""
import os
import i3drsgm
from i3drsgm import I3DRSGM

def test_init_dataset():
    """Test initalising I3DRSGM class"""
    i3drsgm_folder = os.path.dirname(i3drsgm.__file__)
    app_folder = os.path.join(i3drsgm_folder,"app")
    tmp_folder = os.path.join(i3drsgm_folder,"tmp")
    I3DRSGM(tmp_folder,app_folder)
