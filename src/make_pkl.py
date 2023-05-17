#usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pickle

file_path=os.path.expanduser('~/catkin_ws/src/receptionist/config')
with open(file_path + '/guest_feature.pkl', "wb") as f:
    feature_dic = {"guest1":{"name":"","drink":"","age":""},
                "guest2":{"name":"","drink":"","age":""}}
    pickle.dump(feature_dic, f)
