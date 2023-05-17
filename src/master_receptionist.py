#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import rospy
import rosparam
import roslib
import smach
import smach_ros
#from fmmmod import FeatureFromVoice, FeatureFromRecog,  LocInfo, SaveInfo
from std_msgs.msg import Float64
from happymimi_msgs.srv import SimpleTrg, StrTrg
from happymimi_navigation.srv import NaviLocation, NaviCoord
#音声
import sp_receptionist as sp

file_path = roslib.packages.get_pkg_dir('happymimi_teleop') + '/src/'
sys.path.insert(0, file_path)
from base_control import BaseControl
# speak
tts_srv = rospy.ServiceProxy('/tts', StrTrg)
# wave_play
wave_srv = rospy.ServiceProxy('/waveplay_srv', StrTrg)

#class MoveInitalPosition(smach.State):#ゲストの検出のための位置へ移動
#    def __init__(self):
#        smach.State.__init__(self,outcomes = ['move_finish']
#                             )
#        self.gen_coord_srv = rospy.Serviceproxy('/human_coord_generator', SimleTrg)
        #self.ap_srv = rospy.ServiceProxy('/approach_person_server', StrTrg)
#        self.navi_srv = rospy.ServiceProxy('navi_location_Server', NaviLocation)
#        self.head_pub = rospy.Publisher('/servo/head',Float64, queue_size = 1)
#        self.bc = BaseControl()

#    def execute(self,userdata):
#        rospy.loginfo("Executing state:MOVE_INITAL_POSITION")
#        guest_num = userdata.g_count_in
#        
#        if guest_num == 0:
           #dooropen
#            pass
#        if guest_num == 1:

#        self.navi_srv('inital position')
#        self.bc.rotateAngle(,0.2)#入り口の方を向く
#        rospy.sleep(0.5)
#        return 'move_finish'

class DiscoverGuests(smach.State):#ゲストの検出、受付
    def __init__(self):
        smach.State.__init__(self, outcomes = ['discover_finish']
                             )
        self.ap_srv = self.rospy.ServiceProxy('/approach_person_server', StrTrg)
        self.head_pub = rospy.ServiceProxy('/servo/head',Float64, queue_size = 1)
        self.find_srv = rospy.ServiceProxy('/recognition/find',RecognitionFind)
        self.head_pub = rospy.Publisher('/servo/head', Float64, queue_size = 1)


    def execute(self,userdata):
        rospy.loginfo("Executing state:DISCOVERGUESTS")
        self.head_pub.publish(-30)
        rospy.sleep(1.0)
        #人の検知
        self.find_result = self.find_srv(RecongnitionFindRequest(target_name = 'person')).result
        rospy.sleep(1.0)
        if self.find_result == True:
            print('found a person')
            request  = RecognitionLocalizeRequest()
            request.target_name  = "person"
            centroid = rt.localizeObject(request).point
            person_height = centroid.z
            self.head_pub.publisg(0)
            rospy.sleep(1.0)
            self.head_pub.publish(20)
            rospy.sleep(1.0)
            wave_srv('/receptionist/hello')
            rospy.sleep(0.5)
            get_feature = sp.GetFeature()
            name = get_feature.getName()
            drink = get_feature.getFavoriteDrink()
            age = get_feature.getAge()#画像認識で可能なら要変更
            wave_srv("/receptionist/ty")
            rospy.sleep(0.5)
            return 'discover_finish'

        else self.find_result == False:
            print("found a person")
            tts_srv("i wait person")
            continue


class IntroduceGuests(smach.State):#オーナーのもとへ移動、ゲストの紹介
    def __init__(self):
        smach.State.__init__(self, outcomes = ['introduce_finish'],
                             input_keys = ['g_count_in']
                             )
        self.navi_srv = rospy.ServiceProxy('navi_location_Server', NaviLocation)
        self.arm_srv = rospy.ServiceProxy('/servo/arm', StrTrg)
        self.bc = BaseControl()
        self.save_srv = rospy.ServiceProxy('/recognition/save',StrTrg)
        self.sentence_list = []
        

    def execute(self,userdata):
        rospy.loginfo("Executing state:INTRODUCE_GUESTS")
        guest_num = userdata.g_count_in
        self.navi_srv('orner')
        rospy.sleep(1.0)
        #ゲストの方を指す
        #ゲストの位置が分からないからアングルの角度がわからない
        
        introduce = sp.IntroduceOfGuests()
        introduce.main(guest_num)
        self.bc.rotateAngle(180,0.3)
        rospy.sleep(1.0)
        self.arm_srv('origin')
        rospy.sleep(0.5)
        self.arm_srv('carry')
        rospy.sleep(1.0)
        return 'introduce_finish'

class GuideGuests(smach.State):#ゲストのガイド
    def __init__(self):
        smach.State.__init__(self, outcomes = ['guide_finish','all_finish'],
                             input_keys = ['g_count_in'],
                             output_keys =  ['g_count_out'])
        with open(file_path,mode="rb") as f:
            self.feature_dic = pickle.load(f)
        self.bc = BaseControl()
        self.arm_srv = rospy.ServiceProxy('/servo/arm', StrTrg)
        self.navi_srv = rospy.ServiceProxy('navi_location_server', NaviLocation)
        self.head_pub =rospy.Publisher('/servo/head', Float64, queue_size=1)
        

    def execute(self, userdata):
        rospy.loginfo("Executing state:GUIDE_GUESTS")
        guest_num = userdata.g_count_in
        if guest_num == 0:
            
            #空いている椅子を指す
            
            self.bc.rotateAngle(45,0.2)
            rospy.sleep(0.5)
            self.arm_srv('origin')
            rospy.sleep(0.5)
            wave_srv("")#("Please sit in this chair.")
            guest_num += 1
            userdata.g_count_out = guest_num
            self.arm_sry('carry')
            rospy.sleep(0.5)
            self.bc.rotateangle(180,0.2)
            rospy.sleep(0.5)
            self.navi_srv('StartPosition')
            rospy.sleep(0.5)


            return 'guide_finish'
        elif guest_num == 1:#年齢順に
            if self.feature_dic["guest1"]["age"] < self.feature_dic["guest2"]["age"]:
                
                #空いている椅子を指す（ゲスト1に座らせる）
                self.bc.rotateAngle(-45,0.2)
                rospy.sleep(0.5)
                self.arm_srv('origin')
                rospy.sleep(0.5)
                tts_srv("Hi, " + self.feature_dic["guest1"]["name"] +",Please sit in this chair.")
                rospy.arm_srv('carry')
                rospy.sleep(0.5)
                #ゲスト1が座っていた椅子を指す
　　　　　　    self.bc.rotateAngle(45,0.2)
                rospy.sleep(0.5)
                self.arm_srv('origin')
                rospy.sleep(0.5)

                
                tts_srv("Hi, " + self.feature_dic["guest2"]["name"] +",Please sit in this chair.")
                self.arm_srv('carry')
                rospy.sleep(0.5)
                rospy.sleep(0.5)
                self.bc.rotateangle(180,0.2)
                rospy.sleep(0.5)
                self.navi_srv('StartPosition')
                rospy.sleep(0.5)

            else:
                
                #空いている椅子を指す
                self.bc.rotateAngle(-45,0.2)
                rospy.sleep(0.5)
                self.arm_srv('origin')
                rospy.sleep(0.5)
                tts_srv("Hi, " + self.feature_dic["guest1"]["name"] +",Please sit in this chair.")
                rospy.sleep(0.5)
                self.bc.rotateangle(180,0.2)
                rospy.sleep(0.5)
                self.navi_srv('StartPosition')
                rospy.sleep(0.5)

            return 'all_finish'

        


if __name__ == '__main__':
    rospy.init_node('receptionist_master')
    rospy.loginfo("Start receptionist")
    sm_top = smach.StateMachine(outcomes = ['finish_sm_top'])
    sm_top.userdata.guest_count = 0
    with sm_top:
        smach.StateMachine.add(
                'MOVE_INITAL_POSITION',
                MoveInitalPosition(),
                transitions = {'move_finish':'DISCOVERGUESTS_GUEST'},
                remapping = {'g_count_in':'guest_count'})

        smach.StateMachine.add(
                'DISCOVERGUESTS_GUEST',
                DiscoverGuests(),
                transitions = {'discover_finish':'INTRODUCE_GUESTS'},
                remapping = {'g_count_in':'guest_count'})

        smach.StateMachine.add(
                'INTRODUCE_GUESTS',
                IntroduceGuests(),
                transitions = {'introduce_finish':'GUIDE_GUESTS'},
                remapping = {'future_out':'guest_future',
                             'g_count_in':'guest_count'})

        smach.StateMachine.add(
                'GUIDE_GUESTS',
                GuideGuests(),
                transitions = {'guide_finish':'MOVE_INITAL_POSITION',
                               'all_finish':'finish_sm_top'},
                remapping = {'g_count_in':'guest_count',
                             'g_count_out':'guest_count'})

    outcome = sm_top.execute()
#koment
