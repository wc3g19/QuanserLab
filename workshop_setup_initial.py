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

from dataclasses import dataclass
import time
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

######################################################
#       CREATE FIRST LINE                            #
######################################################

#region : create conveyors and their supports and tube

# Global variables for tracking actor numbers currently in use
global conveyorANums, standANums, deliveryTubeANums, shredderANums, binANums, armANums, sensorANums, basicShapeANums
conveyorANums = set([])
standANums = set([])
deliveryTubeANums = set([])
shredderANums = set([])
binANums = set([])
armANums = set([])
sensorANums = set([])
basicShapeANums = set([])

def get_next_Actor_Number(actor_num_list):
    '''
    Function that looks at a passed in set and returns the next available actor number
    '''
    if len(actor_num_list) == 0:
        actor_num = 0
    else:
        actor_num = max(actor_num_list) + 1

    return actor_num

def add_actor_number(actor_num_list, actor_num):
    ''''
    Function that adds an actor number to a set if not already in the set
    '''
    if actor_num not in actor_num_list:
        actor_num_list.add(actor_num)
    
    else:
        raise ValueError("Actor number already exists in list")

@dataclass
class Line:
    '''
    Class to store all the actors and their actor numbers for a production line
    '''
    conveyors: dict
    deliveryTubes: dict
    shredders: dict
    arms: dict
    basicShapes: dict
    bins : dict
    colour: int
    colour_str: str
    spawn_sensors : dict
    drop_sensors : dict
    arm_sensors : dict
    offset : np.ndarray
    startTimeSpawn : float = None
    startTimeQarm : float = None
    startTimeColour : float = None
    num_packs : int = 0
    packs_limit : int = 30
    emptying : bool = False
    qarm_state : int = 6
    qarm : QArm = None
    hitSpawn : bool = None
    hitDrop : bool = None
    hitArm : bool = None
    propertiesArm = None
    stopped : bool = None
    notMovingTime : float = None

def generate_module(offset=np.array([0, 0, 0]), colour=2, num_conveyors = 2):
    '''
    Generic function to create a module with n-conveyors, shredders, bins, arms and sensors
    This function uses the same.

    Inputs:
        offset : np.ndarray : The offset from the original module to spawn the new module- default is [0, 0, 0]
        colour : int : The colour of the objects to be spawned and picked - default is 2
        num_conveyors : int : The number of conveyors to spawn - default is 2

    Outputs:
        results : Line : A class that stores all the actors and their actor numbers for a production line
    '''
    conveyors = {}
    deliveryTubes = {}
    shredders = {}
    arms = {}
    basicShapes = {}
    bins = {}
    spawn_sensors = {}
    drop_sensors = {}
    arm_sensors = {}

    ######################################
    ########## Create Conveyors ##########
    ######################################

    separation = 0.98   # Separation between conveyors

    for i in range(num_conveyors):
        # Itterates over the number of conveyors to spawn

        next_an = get_next_Actor_Number(conveyorANums)  # Get the next actor number
        add_actor_number(conveyorANums, next_an)        # Add the actor number to the set

        firstConvey = QLabsConveyorStraight(qlabs)
        firstConvey.spawn_id_degrees(actorNumber = next_an,
                                            location = offset + np.array([0.85, 0, 0.3]) - i*np.array([separation, 0, 0]),
                                            rotation = [0, 0, 0],
                                            scale = [1,1,1],
                                            configuration = 2)
        firstConvey.set_speed(0.1)

        conveyors[firstConvey] = next_an                # Add the conveyor to the dictionary

    #####################################
    ########## Create Supports ##########
    #####################################

    for i in conveyors:
        # Itterates over all conveyors and creates a support for each.

        next_an = get_next_Actor_Number(basicShapeANums)    # Get the next actor number
        add_actor_number(basicShapeANums, next_an)          # Add the actor number to the set
        parent_AN = conveyors[i]                            # Get the parent conveyor actor number

        stand = QLabsBasicShape(qlabs)
        stand.spawn_id_and_parent_with_relative_transform(actorNumber = next_an,
                                                                location = [0.5, 0, -0.15],
                                                                rotation = [0, 0, 0],
                                                                scale = [0.95, 0.3, 0.3],
                                                                configuration = 0,
                                                                parentClassID = i.classID,
                                                                parentActorNumber = parent_AN,
                                                                parentComponent = 0,
                                                                waitForConfirmation = True)
        stand.set_material_properties(color = [0.3, 0.3, 0.3],
                                            roughness = 0.4,
                                            metallic = False)
        
        basicShapes[stand] = next_an                        # Add the support to the dictionary

    ########################################
    ########## Create Widget Tube ##########
    ########################################

    next_an = get_next_Actor_Number(deliveryTubeANums)  # Get the next actor number
    add_actor_number(deliveryTubeANums, next_an)        # Add the actor number to the set

    deliveryTube = QLabsDeliveryTube(qlabs)
    deliveryTube.spawn_id_degrees(actorNumber = next_an,
                                    location = offset + np.array([1.75, 0, 8]),
                                    rotation = [0, 180, 0],
                                    scale = [1, 1, 1],
                                    configuration = 1,
                                    waitForConfirmation = True)
    deliveryTube.set_height(height = 7)

    deliveryTubes[deliveryTube] = next_an             # Add the delivery tube to the dictionary

    time.sleep(1)

    #####################################
    ########## Create Shredder ##########
    #####################################

    next_an = get_next_Actor_Number(shredderANums)  # Get the next actor number
    add_actor_number(shredderANums, next_an)        # Add the actor number to the set

    shredder = QLabsShredder(qlabs)
    if colour == 2:
        colour_str = 'blue'
        shredder.spawn(location=offset + np.array([1.35, -0.5, -0.2]), scale=[1.7,1.7,2.7], configuration=shredder.BLUE)
    elif colour == 1:
        colour_str = 'green'
        shredder.spawn(location=offset + np.array([1.35, -0.5, -0.2]), scale=[1.7,1.7,2.7], configuration=shredder.GREEN)
    else:
        colour_str = 'red'
        shredder.spawn(location=offset + np.array([1.35, -0.5, -0.2]), scale=[1.7,1.7,2.7], configuration=shredder.RED)

    shredders[next_an] = shredder                   # Add the shredder to the dictionary

    #################################
    ########## Create Bins ##########
    #################################

    actor_nums = []     # List to store the actor numbers for the bin components
    for i in range(5):
        next_an = get_next_Actor_Number(basicShapeANums)    # Get the next actor number
        add_actor_number(basicShapeANums, next_an)          # Add the actor number to the set
        actor_nums.append(next_an)                          # Add the actor number to the list

    conveyorBinRed = QLabsBasicShape(qlabs)
    conveyorBinRed.spawn_id_box_walls_from_center_degrees(actorNumbers = actor_nums,
                                                        centerLocation = offset + np.array([0.85-0.17, 0, 0]) - (num_conveyors-1)*np.array([separation, 0, 0]),
                                                        yaw = 0,
                                                        xSize = 0.3, ySize = 0.3, zHeight = 0.2,
                                                        wallThickness = 0.01,
                                                        floorThickness = 0.1,
                                                        wallColor = [0.5, 0, 0],
                                                        floorColor = [0.5, 0, 0],
                                                        waitForConfirmation = True)
    
    basicShapes[conveyorBinRed] = actor_nums                # Add the bin to the dictionary

    next_an = get_next_Actor_Number(basicShapeANums)        # Get the next actor number
    add_actor_number(basicShapeANums, next_an)              # Add the actor number to the set

    BlueCover = QLabsBasicShape(qlabs)
    BlueCover.spawn_id(next_an, location=offset + np.array([1.35, -0.5, .18]), scale=[.3,.3,.04])
    BlueCover.set_material_properties(color=[0,0,.5])
    BlueCover.set_physics_properties(enableDynamics=False, dynamicFriction=0, frictionCombineMode=BlueCover.COMBINE_MIN, restitution= .5, restitutionCombineMode=BlueCover.COMBINE_MAX)

    bins[BlueCover] = next_an                               # Add the bin to the dictionary    

    ###################################
    ########## Create an Arm ##########
    ###################################

    next_an = get_next_Actor_Number(armANums)       # Get the next actor number
    add_actor_number(armANums, next_an)             # Add the actor number to the set

    Arm = QLabsQArm(qlabs)
    Arm.spawn_id_degrees(actorNumber = next_an,
                                location = offset + np.array([1, -0.5, 0.3]),
                                rotation = [0, 0, 0],
                                scale = [1, 1, 1],
                                configuration = 0,
                                waitForConfirmation = True)
    
    arms[Arm] = next_an                             # Add the arm to the dictionary

    # Create a simple support for the arm

    next_an = get_next_Actor_Number(basicShapeANums)    # Get the next actor number
    add_actor_number(basicShapeANums, next_an)          # Add the actor number to the set

    secondArmStand = QLabsBasicShape(qlabs)
    secondArmStand.spawn_id_and_parent_with_relative_transform(actorNumber = next_an,
                                                                location = [0, 0, -0.15],
                                                                rotation = [0, 0, 0],
                                                                scale = [0.3, 0.3, 0.3],
                                                                configuration = 0,
                                                                parentClassID = Arm.classID,
                                                                parentActorNumber = arms[Arm],
                                                                parentComponent = 0,
                                                                waitForConfirmation = True)
    secondArmStand.set_material_properties(color = [0.3, 0.3, 0.3],
                                            roughness = 0.4, metallic = False)

    basicShapes[secondArmStand] = next_an               # Add the support to the dictionary

    ####################################
    ########## Create Sensors ##########
    ####################################
    # Spawn Sensor
    next_an = get_next_Actor_Number(sensorANums)    # Get the next actor number
    add_actor_number(sensorANums, next_an)          # Add the actor number to the set

    beamSensorSpawn = QLabsGenericSensor(qlabs)
    beamSensorSpawn.spawn_id_degrees(actorNumber = next_an,
                                location=offset + np.array([1.65, .3, 0.45]),
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

    spawn_sensors[beamSensorSpawn] = next_an      # Add the sensor to the dictionary

    # Drop Sensor
    next_an = get_next_Actor_Number(sensorANums)    # Get the next actor number
    add_actor_number(sensorANums, next_an)          # Add the actor number to the set

    beamSensorDrop = QLabsGenericSensor(qlabs)
    beamSensorDrop.spawn_id_degrees(actorNumber = next_an,
                                location=offset + np.array([1.8, 0, 0.43]),
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

    drop_sensors[beamSensorDrop] = next_an      # Add the sensor to the dictionary

    # Arm Sensor
    next_an = get_next_Actor_Number(sensorANums)    # Get the next actor number
    add_actor_number(sensorANums, next_an)          # Add the actor number to the set

    beamSensorArm2 = QLabsGenericSensor(qlabs)
    beamSensorArm2.spawn_id_degrees(actorNumber = next_an,
                                location=offset + np.array([1, .3, 0.45]),
                                rotation=[0, 0, -90],
                                scale=[1, 1, 1],
                                configuration = 0,
                                waitForConfirmation = True)

    beamSensorArm2.show_sensor(showBeam=True,
                            showOriginIcon=True,
                            iconScale=0.1,
                            waitForConfirmation=True)
    beamSensorArm2.set_beam_size(startDistance=0,
                                endDistance=0.5,
                                heightOrRadius=0.01,
                                width=0.01,
                                waitForConfirmation=True)
    
    arm_sensors[beamSensorArm2] = next_an       # Add the sensor to the dictionary

    # Generate a Line class to store all required data for running the line
    results = Line(conveyors, deliveryTubes, shredders, arms, basicShapes, bins, colour, colour_str, spawn_sensors, drop_sensors, arm_sensors, offset)
    
    # Return the Line class
    return results

#############################
######## Spawn Lines ########
#############################
number_of_lines = 4
lines = []

for i in range(number_of_lines):
    if i == 0:
        line = generate_module(num_conveyors=1)
    else:
        line = generate_module(offset=i*np.array([0, 1.5, 0]), num_conveyors=1)
    
    lines.append(line)

print(armANums)

###################################
######## Start spawn model ########
###################################
cylinder = QLabsWidget(qlabs)
start_index = 18900
for i in range(number_of_lines):
    print(i, start_index)
    QLabsRealTime().start_real_time_model(QARMS+'/QArm_Spawn%i' % (i), actorNumber=i, additionalArguments='-uri_hil tcpip://localhost:%i -uri_video tcpip://localhost:%i' % (start_index, start_index+1))

    start_index += 2

def createCylinder(cylinderNo, offset=np.array([0, 0, 0])):
        value = ['green', 'blue', 'red']   ## uncomment these 6 lines and comment out the 3 below to implement dual cell type simulation
        color = [[0,1,0], [0,0,1], [1,0,0]]

        position = cylinderNo - 1

        cylinder.spawn(location = offset + np.array([1.75, 0, 1]),
               rotation = [0, 0, 0],
               scale = [.05, .05, .05],
               configuration = cylinder.CYLINDER,
               color = color[position],
               measuredMass = 1,
               properties=value[position])
        cylinderNo += 1

        return cylinderNo

def moveConveyors(line, speed):
    # Do not change these if statments, may change var names if new conveyors added
    if line.stopped == True and speed == 0:
        if elapsed_time(line.notMovingTime) > 60:
            speed = 0.1
    if line.stopped == False and speed  == 0:
        line.notMovingTime = time.time()
        line.stopped = True
    if speed != 0:
        line.notMovingTime = time.time()
        line.stopped = False

    for i in line.conveyors:
        i.set_speed(speed)

    return line

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

def findObj(lines):
    '''
    This funcition has the same operation as the example given.
    It is extended such that it performs all logic on a 'Line' class.
    We can therefore loop over a list of 'Line' classes and perform the same logic on each.

    Inputs:
        lines : list : A list of 'Line' classes
    '''
    start_index = 18900             # start index required for the qarm model
    for line in lines:
        # Initialise line variables for each line in lines
        line.notMovingTime = time.time()
        line.stopped = False
        line.qarm = createQarm(start_index)
        pickAndPlace(line.qarm, line.qarm_state)
        line = moveConveyors(line, 0.1)
        createCylinder(line.colour, offset=line.offset)
        line.startTimeSpawn = line.startTimeQarm = line.startTimeColour = time.time()

        start_index += 2

    itter_start = time.time()
    itterations = 0
    while True:
        itterations += 1
        print('Current seconds per iteration %.4f' %((time.time() - itter_start)/itterations))
        for i in lines:
            # Detect hits for all sensors
            spawn_sensor = next(iter(i.spawn_sensors))
            _, i.hitSpawn, _,_,_,_ = spawn_sensor.test_beam_hit_widget()
            drop_sensor = next(iter(i.drop_sensors))
            _, i.hitDrop, _,_,_,_ = drop_sensor.test_beam_hit_widget()
            arm_sensor = next(iter(i.arm_sensors))
            _, i.hitArm, _,_,_, i.propertiesArm = arm_sensor.test_beam_hit_widget()

            # Checks if a new cell can be spawned
            if i.hitSpawn and not i.hitDrop:
                if elapsed_time(i.startTimeSpawn) > 1:
                    createCylinder(i.colour, offset=i.offset)
                    i.startTimeSpawn = time.time()
            
            # Checks if the arm can pick up a cell
            if i.hitArm and i.propertiesArm == i.colour_str:
                i = moveConveyors(i, 0)
                if not i.emptying and i.qarm_state == 6:
                    i.qarm_state = 0
                    pickAndPlace(i.qarm, i.qarm_state)
                    i.startTimeQarm = time.time()
            
            if i.qarm_state < 6:
                if elapsed_time(i.startTimeQarm) > 1:
                    i.qarm_state += 1
                    pickAndPlace(i.qarm, i.qarm_state)
                    i.startTimeQarm += 1
                    
                    if i.qarm_state == 4:
                        i = moveConveyors(i, 0.1)
                    
                    if i.qarm_state == 5:
                        i.num_packs += 1
            
            # Checks if the bin is full
            if i.num_packs == i.packs_limit:
                i.emptying = True
                i.num_packs = 0
                i.startTimeColour = time.time()
            
            # empties the bin if full
            if i.emptying:
                emptied = emptyBins(coverObject=next(iter(i.bins)), startTime=i.startTimeColour, timeToMove=2, timeOpened=2)
                if emptied:
                    i.emptying = False
                    i.num_packs = 0

findObj(lines)
