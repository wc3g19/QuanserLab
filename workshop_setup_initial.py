# Note use this method to get your qvl libraries to ensure you're using the
# latest version in GitHub. It is inserted first in the list to take precedence
# over all other libraries in your python path.
import sys
sys.path.insert(0, "../")

from qvl.qlabs import QuanserInteractiveLabs
from qvl.conveyor_curved import QLabsConveyorCurved
from qvl.conveyor_straight import QLabsConveyorStraight
from qvl.widget import QLabsWidget
from qvl.delivery_tube import QLabsDeliveryTube
from qvl.basic_shape import QLabsBasicShape
from qvl.shredder import QLabsShredder
from qvl.generic_sensor import QLabsGenericSensor
from qvl.qarm import QLabsQArm
from qvl.real_time import QLabsRealTime
import pal.resources.rtmodels as rtmodels
import time
import math
import struct
import numpy as np
import random
import cv2
import os
from random import randrange
import pandas as pd
import shutil
from controller import *
########## Backup Creation ###########
destination = "\\\\filestore.soton.ac.uk\\users\\" + os.getlogin() + "\\mydocuments\\Quanser Labs Documents"
def saveFile():

    currentFilePath = os.path.realpath(__file__)
    fileName = os.path.basename(currentFilePath)

    if not os.access(destination, os.F_OK):
        os.mkdir(destination, 0o700)
    saveLocation = os.path.join(destination, fileName)
    shutil.copy(src=currentFilePath, dst=saveLocation)
saveFile()
########## Main setup script ##########

# Core variables
scriptStartTime = time.strftime("%d_%m_%Y-%H.%M.%S", time.gmtime())
scriptStartTimeSec = int(time.time())

waitTime = 1.0

qlabs = QuanserInteractiveLabs()
print("Connecting to QLabs...")
try:
    qlabs.open("localhost")
except:
    print("Unable to connect to QLabs")

print("Connected")

qlabs.destroy_all_spawned_actors()
QLabsRealTime().terminate_all_real_time_models()


__qalDirPath = os.environ['RTMODELS_DIR']

QARMS = os.path.normpath(
    os.path.join(__qalDirPath, 'QArms'))

#region : create conveyors and their supports and tube

########## Create two conveyors ##########
firstConvey = QLabsConveyorStraight(qlabs)
num = firstConvey.spawn_id_degrees(actorNumber = 0,
                                    location = [-0.12, 0, 0.3],
                                    rotation = [0, 0, 0],
                                    scale = [1,1,1],
                                    configuration = 2)
firstConvey.set_speed(0.1)

secondConvey = QLabsConveyorStraight(qlabs)
num = secondConvey.spawn_id_degrees(actorNumber = 1,
                                    location = [-1.1, 0, 0.3],
                                    rotation = [0, 0, 0],
                                    scale = [1,1,1],
                                    configuration = 2)
secondConvey.set_speed(0.1)

thirdConvey = QLabsConveyorStraight(qlabs)
num = thirdConvey.spawn_id_degrees(actorNumber = 3,
                                    location = [0.85, 0, 0.3],
                                    rotation = [0, 0, 0],
                                    scale = [1,1,1],
                                    configuration = 2)
thirdConvey.set_speed(0.1)

# Create a simple supports for the conveyors
firstStand = QLabsBasicShape(qlabs)
firstStand.spawn_id_and_parent_with_relative_transform(actorNumber = 98,
                                                        location = [0.5, 0, -0.15],
                                                        rotation = [0, 0, 0],
                                                        scale = [0.95, 0.3, 0.3],
                                                        configuration = 0,
                                                        parentClassID = firstConvey.classID,
                                                        parentActorNumber = 0,
                                                        parentComponent = 0,
                                                        waitForConfirmation = True)
firstStand.set_material_properties(color = [0.3, 0.3, 0.3],
                                    roughness = 0.4,
                                    metallic = False)

secondStand = QLabsBasicShape(qlabs)
secondStand.spawn_id_and_parent_with_relative_transform(actorNumber = 99,
                                                        location = [0.5, 0, -0.15],
                                                        rotation = [0, 0, 0],
                                                        scale = [0.95, 0.3, 0.3],
                                                        configuration = 0,
                                                        parentClassID = secondConvey.classID,
                                                        parentActorNumber = 1,
                                                        parentComponent = 0,
                                                        waitForConfirmation = True)
secondStand.set_material_properties(color = [0.3, 0.3, 0.3],
                                    roughness = 0.4,
                                    metallic = False)

thirdStand = QLabsBasicShape(qlabs)
thirdStand.spawn_id_and_parent_with_relative_transform(actorNumber = 990,
                                                        location = [0.5, 0, -0.15],
                                                        rotation = [0, 0, 0],
                                                        scale = [0.95, 0.3, 0.3],
                                                        configuration = 0,
                                                        parentClassID = thirdConvey.classID,
                                                        parentActorNumber = 3,
                                                        parentComponent = 0,
                                                        waitForConfirmation = True)
thirdStand.set_material_properties(color = [0.3, 0.3, 0.3],
                                    roughness = 0.4,
                                    metallic = False)



########## Create a widget tube ##########
deliveryTube = QLabsDeliveryTube(qlabs)
deliveryTube.spawn_id_degrees(actorNumber = 1,
                                location = [1.75, 0, 8],
                                rotation = [0, 180, 0],
                                scale = [1, 1, 1],
                                configuration = 1,
                                waitForConfirmation = True)
deliveryTube.set_height(height = 7)
#endregion



time.sleep(1)

#region : create bins and shredders

########## Create two shredders ##########
shredder = QLabsShredder(qlabs)
shredder.spawn(location=[1.35, -.5, -0.2], scale=[1.7,1.7,2.7], configuration=shredder.GREEN)

########## Create a disposal bin ##########
conveyorBinRed = QLabsBasicShape(qlabs)
conveyorBinRed.spawn_id_box_walls_from_center_degrees(actorNumbers = [2, 3, 4, 5, 6],
                                                    centerLocation = [-1.28, 0, 0],
                                                    yaw = 0,
                                                    xSize = 0.3, ySize = 0.3, zHeight = 0.2,
                                                    wallThickness = 0.01,
                                                    floorThickness = 0.1,
                                                    wallColor = [0.5, 0, 0],
                                                    floorColor = [0.5, 0, 0],
                                                    waitForConfirmation = True)

GreenCover = QLabsBasicShape(qlabs)
GreenCover.spawn_id(50, [1.35, -0.5, .18], scale=[.3,.3,.04])
GreenCover.set_material_properties(color=[0,.5,0])
GreenCover.set_physics_properties(enableDynamics=False, dynamicFriction=0, frictionCombineMode=GreenCover.COMBINE_MIN, restitution= .5, restitutionCombineMode=GreenCover.COMBINE_MAX)



#endregion

#region : create arms and supports
# ########## Create an arm ##########
firstArm = QLabsQArm(qlabs)
firstArm.spawn_id_degrees(actorNumber = 10,
                            location = [1, -0.5, 0.3],
                            rotation = [0, 0, 0],
                            scale = [1, 1, 1],
                            configuration = 0,
                            waitForConfirmation = True)

# Create a simple support for the arm
firstArmStand = QLabsBasicShape(qlabs)
firstArmStand.spawn_id_and_parent_with_relative_transform(actorNumber = 100,
                                                            location = [0, 0, -0.15],
                                                            rotation = [0, 0, 0],
                                                            scale = [0.3, 0.3, 0.3],
                                                            configuration = 0,
                                                            parentClassID = firstArm.classID,
                                                            parentActorNumber = 10,
                                                            parentComponent = 0,
                                                            waitForConfirmation = True)
firstArmStand.set_material_properties(color = [0.3, 0.3, 0.3],
                                        roughness = 0.4, metallic = False)


#endregion

#region : Create beam sensors
########## Create beam sensors ##########
beamSensorSpawn = QLabsGenericSensor(qlabs)
beamSensorSpawn.spawn_id_degrees(actorNumber = 101,
                            location=[1.65, .3, 0.45],
                            rotation=[0, 0, -90],
                            scale=[1, 1, 1],
                            configuration = 0,
                            waitForConfirmation = True)

beamSensorSpawn.show_sensor(showBeam=True,
                        showOriginIcon=True,
                        iconScale=0.1,
                        waitForConfirmation=True)
beamSensorSpawn.set_beam_size(startDistance=0,
                            endDistance=0.5,
                            heightOrRadius=0.01,
                            width=0.01,
                            waitForConfirmation=True)



beamSensorDrop = QLabsGenericSensor(qlabs)
beamSensorDrop.spawn_id_degrees(actorNumber = 105,
                            location=[1.8, 0, 0.43],
                            rotation=[0, 0, 180],
                            scale=[1, 1, 1],
                            configuration = 0,
                            waitForConfirmation = True)

beamSensorDrop.show_sensor(showBeam=False,
                        showOriginIcon=False,
                        iconScale=0.1,
                        waitForConfirmation=True)
beamSensorDrop.set_beam_size(startDistance=0,
                            endDistance=0.12,
                            heightOrRadius=0.01,
                            width=0.01,
                            waitForConfirmation=True)



beamSensorArm1 = QLabsGenericSensor(qlabs)
beamSensorArm1.spawn_id_degrees(actorNumber = 102,
                            location=[1, .3, 0.45],
                            rotation=[0, 0, -90],
                            scale=[1, 1, 1],
                            configuration = 0,
                            waitForConfirmation = True)

beamSensorArm1.show_sensor(showBeam=True,
                        showOriginIcon=True,
                        iconScale=0.1,
                        waitForConfirmation=True)
beamSensorArm1.set_beam_size(startDistance=0,
                            endDistance=0.5,
                            heightOrRadius=0.01,
                            width=0.01,
                            waitForConfirmation=True)


#endregion


# Spawn a cylinder
cylinder = QLabsWidget(qlabs)

# # Start spawn model
QLabsRealTime().start_real_time_model(QARMS+'/QArm_Spawn0', actorNumber=10, additionalArguments='-uri_hil tcpip://localhost:18900 -uri_video tcpip://localhost:18901')
# QLabsRealTime().start_real_time_model(QARMS+'/QArm_Spawn1', actorNumber=11, additionalArguments='-uri_hil tcpip://localhost:18902 -uri_video tcpip://localhost:18903')



def createCylinder(cylinderNo):
        # value = ['green', 'blue', 'red']   ## uncomment these 6 lines and comment out the 3 below to implement dual cell type simulation
        # color = [[0,1,0], [0,0,1], [1,0,0]]
        # if cylinderNo % 2 == 0:
        #     position = 1
        # else:
        #     position = 0
        value = ['green', 'red']
        color = [[0,1,0], [1,0,0]]
        position = 0

        failedCell = randrange(2000)
        if failedCell == 1:
            position = 1            ## change when using dual cell simulation


        cylinder.spawn(location = [1.75, 0, 1],
               rotation = [0, 0, 0],
               scale = [.05, .05, .05],
               configuration = cylinder.CYLINDER,
               color = color[position],
               measuredMass = 1,
               properties=value[position])
        cylinderNo += 1
        return cylinderNo



def moveConveyors(speed, stopped, notMovingTime):
    if stopped == True and speed == 0:
        if elapsed_time(notMovingTime) > 60:
            speed = 0.1
    if stopped == False and speed  == 0:
        notMovingTime = time.time()
        stopped = True
    if speed != 0:
        notMovingTime = time.time()
        stopped = False
        
    firstConvey.set_speed(speed)
    secondConvey.set_speed(speed)
    thirdConvey.set_speed(speed)
    return stopped, notMovingTime


def elapsed_time(startTime):
        return time.time() - startTime

def emptyBins(coverObject, startTime, timeToMove, timeOpened):
    out = False
    _,location,_,_ = coverObject.get_world_transform()
    if elapsed_time(startTime) < timeToMove:
        y = elapsed_time(startTime) * -(.3/timeToMove)
        coverObject.set_transform(location = [location[0], -0.5+y, location[2]], rotation=[0,0,0], scale=[.3,.3,.04], waitForConfirmation=False)
    elif elapsed_time(startTime)<(timeToMove + timeOpened):
        pass
    elif elapsed_time(startTime) < (timeToMove*2 + timeOpened):
        y = (elapsed_time(startTime)-(timeToMove + timeOpened)) * -(.3/timeToMove)
        coverObject.set_transform(location = [location[0], -0.8-y, location[2]], rotation=[0,0,0], scale=[.3,.3,.04], waitForConfirmation=False)
    else:
        out = True

    return out



def recordResults(data, greenObjects):
    newRow = {'Elapsed Time (s)':int(elapsed_time(scriptStartTimeSec)), 'Green':greenObjects}
    data = data._append(newRow, ignore_index=True)
    pd.DataFrame.to_csv(data, (destination + "\\Results_" + scriptStartTime + ".csv"), index=False)
    return data


def findObj():
    data = pd.DataFrame(columns = ['Elapsed Time (s)', 'Green'])
    update = True
    cylinderNo=1
    ########## Test for object ##########
    ## Relevant code for second cell type has been commented out in the following section
    qarm1_State = 6
    # qarm2_State = 6

    greenBinLimit = 30
    # blueBinLimit = 40
    greenObjects = 0
    # blueObjects = 0
    emptyingGreen = 0
    # emptyingBlue = 0

    startTime = time.time()

    notMovingTime = time.time()
    stopped = False

    # make sure port number matches ones from spawn model start
    qarm1 = createQarm(18900)
    pickAndPlace(qarm1, qarm1_State)

    # qarm2 = createQarm(18902)
    # pickAndPlace(qarm2, qarm2_State)

    stopped, notMovingTime = moveConveyors(0.1, stopped, notMovingTime)

    cylinderNo = createCylinder(cylinderNo)

    startTimeSpawn = startTimeQarm1 = startTimeGreen = startTimeBlue = time.time()
    startTimeSpawn = startTimeQarm1 = startTimeQarm2 = startTimeGreen = startTimeBlue = time.time()
    while True:

        _, hitSpawn, _,_,_,_ = beamSensorSpawn.test_beam_hit_widget()
        _, hitDrop, _,_,_,_ = beamSensorDrop.test_beam_hit_widget()
        _, hitArm1, _,_,_, propertiesArm1 = beamSensorArm1.test_beam_hit_widget()

        if update == True:
            data = recordResults(data, greenObjects)
            update = False
        if hitSpawn and not hitDrop:
            if elapsed_time(startTimeSpawn) > 1:
                cylinderNo = createCylinder(cylinderNo)
                startTimeSpawn = time.time()

        if hitArm1 and propertiesArm1 == 'green':
            stopped, notMovingTime = moveConveyors(0, stopped, notMovingTime)
            if emptyingGreen == 0 and qarm1_State == 6:
                qarm1_State = 0
                pickAndPlace(qarm1, qarm1_State)
                startTimeQarm1 = time.time()

        if qarm1_State < 6:
            if elapsed_time(startTimeQarm1) > 1.5:
                qarm1_State =  qarm1_State + 1
                pickAndPlace(qarm1, qarm1_State)
                startTimeQarm1 = startTimeQarm1 + 1.5

                if qarm1_State == 4:
                    stopped, notMovingTime = moveConveyors(0.1, stopped, notMovingTime)

                if qarm1_State == 5:
                    greenObjects = greenObjects + 1
                    update = True

        # if hitArm2 and propertiesArm2 == 'blue':
        #     stopped, notMovingTime = moveConveyors(0, stopped, notMovingTime)
        #     if emptyingBlue == 0 and qarm2_State == 6:
        #             qarm2_State = 0
        #             pickAndPlace(qarm2, qarm2_State)
        #             startTimeQarm2 = time.time()

        # if qarm2_State < 6:
        #     if elapsed_time(startTimeQarm2) > 1:
        #         qarm2_State =  qarm2_State + 1
        #         pickAndPlace(qarm2, qarm2_State)
        #         startTimeQarm2 = startTimeQarm2 + 1

        #         if qarm2_State == 4:
        #             stopped, notMovingTime = moveConveyors(0.1, stopped, notMovingTime)

        #         if qarm2_State == 5:
        #             blueObjects = blueObjects + 1

        if greenObjects == greenBinLimit:
            emptyingGreen = 1
            greenObjects = 0
            startTimeGreen = time.time()

        if emptyingGreen == 1:
            emptied = emptyBins(coverObject=GreenCover,startTime=startTimeGreen,timeToMove=1,timeOpened = 13)
            if emptied:
                emptyingGreen = 0
                greenObjects = 0

        # if blueObjects == blueBinLimit:
        #     emptyingBlue = 1
        #     blueObjects = 0
        #     startTimeBlue = time.time()

        # if emptyingBlue == 1:
        #     emptied = emptyBins(coverObject=BlueCover,startTime=startTimeBlue,timeToMove=2,timeOpened = 2)
        #     if emptied:
        #         emptyingBlue = 0
        #         blueObjects = 0


findObj()

