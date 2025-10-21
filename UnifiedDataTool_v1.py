"""
Instructions:
----To start Program: 
        Run this file and paste the absolute path of the video file that is used to prepare dataset
        A window will open with the same name as the file, this is the tool window

----To Select boxes for detection:
        left click the boxes or drag the mouse over boxes while left clicking
        
----To remove boxes from detection:
        right click the boxes or drag the mouse over boxes while right clicking
        
        remove all using escape or 0

----To Save Detection in current frame:
        press \ or |
            
----To Save Detection in current frame and move to next frame:
        press Enter
        Note: DO NOT press Enter if you are just viewing the video and not saving
            This WILL OVERWRITE exitsing detections for that frame
        
----To move video forward or backward without saving detections:
        for Forward press greater than(>) symbol on keyboard
        for Backward press less than(<) symbol on keyboard  
        
        for Time-based movement, use the slider in the window
        
        These will not modify existsing detections on the frame
        
----To toggle loading old detection 
        press d or D
        
        
----To print frame Number 
        press f or F
        
----   
        
----To Exit
        press Q or q
Overlay color meanings:
1. Green:- Newly selected detections that will be inserted
2. Orange\Yellow:- Existing detections that WILL continue to be inserted
3. Red:- Existing detections that WILL NOT be inserted. I.e., These detections will not be saved for current frame
"""

import cv2 as cv
import numpy as np
import json
import os

class OverlayColor:
    BLUE=0
    GREEN=1
    RED=2
    
def overlayDetections(img:cv.typing.MatLike,detections:np.ndarray,OverlayChannel=OverlayColor.GREEN,onCopy=True,darkeningFactor=1):
    # print(img.shape)
    if(img.shape[0]!=480 or img.shape[1]!=640):
        raise ValueError("Unsupported image size")
    if(onCopy):
        img=img.copy()
    scaledDetections=cv.resize(detections,(640,480),interpolation=cv.INTER_NEAREST)
    # print(scaledDetections.shape)
    
    # imgHalf=img>>1
    # seperatedImageChannels=[np.zeros_like(scaledDetections)]*3
    # seperatedImageChannels[OverlayChannel]=scaledDetections
    # detectionColorImage=np.stack(seperatedImageChannels,2)>>1
    # # detectionColorImage=np.stack([np.zeros_like(scaledDetections),scaledDetections,np.zeros_like(scaledDetections)],2)>>1
    # img=imgHalf+detectionColorImage
    
    imgChannel=img[:,:,OverlayChannel]
    imgChannelHalf=(imgChannel>>darkeningFactor)|(256>>darkeningFactor)
    img[:,:,OverlayChannel]=(imgChannel&~scaledDetections)|(imgChannelHalf&scaledDetections)
    
    #lines
    blockSize=1<<5
    img[::blockSize,:,0]=255
    # img[blockSize-1::blockSize,:,1]=255
    img[:,::blockSize,2]=255
    # img[:,blockSize-1::blockSize,1]=255
    return img

def main(*args,fileName=None):
    if(fileName is None):
        raise AssertionError("File Name not provided!")
    cap=cv.VideoCapture(fileName)
    outputWindowName=os.path.basename(fileName)
    totalFrames=int(cap.get(cv.CAP_PROP_FRAME_COUNT))
    print("Total Frames to annotate:%d"%totalFrames)
    currentFrame=0
    cv.namedWindow(outputWindowName)
    emptyImage=np.zeros((480,640,3),np.uint8)
    cv.imshow(outputWindowName,emptyImage)
    suppressTrackbarCallback=False
    def updateTrackBarTime(frameNumber):
        nonlocal cap,outputWindowName,totalFrames,suppressTrackbarCallback
        percent=((frameNumber+1)*100)//totalFrames
        suppressTrackbarCallback=True;#print("suppressing frame",frameNumber)
        cv.setTrackbarPos("time",outputWindowName,percent)
        pass
    
    def moveToFrameNumber(frameNumber):
        nonlocal cap
        cap.set(cv.CAP_PROP_POS_FRAMES, frameNumber-1)
        pass
    
    def moveVideoByPercentTime(x):
        nonlocal totalFrames,currentFrame,suppressTrackbarCallback,changeFrame
        if(suppressTrackbarCallback):
            suppressTrackbarCallback=False;#print('suppressed',x)
            return
        currentFrame=int((totalFrames-1)*x/100.0);#print("moveVideo, changeFrame")
        changeFrame=True
        # I've designed main loop to call moveToFrameNumber() on non-sequential frame access
        #   So, its not called here 
    
    cv.createTrackbar("time",outputWindowName,0,100,moveVideoByPercentTime)
    
    detections=np.zeros((15,20),dtype=np.uint8)
    oldDetection=detections.copy()
    isHeld=None
    allDetections=["[]"]*totalFrames
    
    def convertTo15x20(x,y):
        return x>>5,y>>5
    def handleMouse(event,x,y,flags,param):
        nonlocal isHeld,detections
        x,y=convertTo15x20(x,y)
        if(event==cv.EVENT_LBUTTONDOWN):
            isHeld=event
        elif(event==cv.EVENT_RBUTTONDOWN):
            isHeld=event
        elif(event==cv.EVENT_LBUTTONUP):
            if(isHeld==cv.EVENT_LBUTTONDOWN):
                isHeld=None
        elif(event==cv.EVENT_RBUTTONUP):
            if(isHeld==cv.EVENT_RBUTTONDOWN):
                isHeld=None
        # elif(event==cv.EVENT_MOUSEMOVE):
        if(y>=0 and y<detections.shape[0] and x>=0 and x<detections.shape[1]):
            if(isHeld==cv.EVENT_LBUTTONDOWN):
                detections[y,x]=255
                # print(x,y)
            elif(isHeld==cv.EVENT_RBUTTONDOWN):
                detections[y,x]=0
                # print("r",x,y)
    cv.setMouseCallback(outputWindowName,handleMouse)
    
    img=None
    changeFrame=False
    lastFrame=None
    default_detection=False
    
    def saveFile():
        JSONFile=os.path.splitext(fileName)[0]+".json"
        with open(JSONFile,mode='w+') as f:
            json.dump(allDetections,f)
    def loadFile():
        nonlocal allDetections,totalFrames
        JSONFile=os.path.splitext(fileName)[0]+".json"
        try:
            if(os.path.exists(JSONFile)):
                with open(JSONFile,mode='r') as f:
                    JSONdata=json.load(f)
                    for i in range(min(totalFrames,len(JSONdata))):
                        allDetections[i]=JSONdata[i]                    
        except Exception as e:print(e)
    loadFile()
    
    def loadOldDetection():
        nonlocal oldDetection,allDetections,currentFrame,detections,default_detection
        oldDetectionData=np.array(eval(allDetections[currentFrame])).T
        oldDetection*=0
        if(len(oldDetectionData)>0):
            oldDetection[oldDetectionData[0],oldDetectionData[1]]=255
        if(default_detection):
            detections=oldDetection.copy()
    try:
        while(True):
            if(img is None or changeFrame):
                changeFrame=False
                if(lastFrame != currentFrame-1):
                    moveToFrameNumber(currentFrame)
                    loadOldDetection()
                    # oldDetectionData=np.array(eval(allDetections[currentFrame])).T
                    # oldDetection*=0
                    # if(len(oldDetectionData)>0):
                    #     oldDetection[oldDetectionData[0],oldDetectionData[1]]=255
                lastFrame=currentFrame
                updateTrackBarTime(currentFrame);#print("main loop, update trach bar")
                _,img=cap.read()
                if not _:
                    break
            # detections[::4,::2]=255
            out=img.copy()
            out=overlayDetections(out,detections)
            out=overlayDetections(out,oldDetection,OverlayColor.RED)
            cv.imshow(outputWindowName,out)
            # key=cv.waitKey(100)
            # print(key)
            # key&=0xff
            # key=chr(key)
            # key=key.lower()
            key=chr(cv.waitKey(10)&0xff).lower()
            
            ESCAPE_KEY=27
            
            if(key=='\r' or key=='\n'):
                asString=np.array2string(np.array(np.nonzero(detections)).T,separator=',').replace("\n ","")
                allDetections[currentFrame]=asString
                oldDetection=detections.copy()
                changeFrame=True
                currentFrame=min(currentFrame+1,totalFrames-1)
            elif(key in '\|'):
                asString=np.array2string(np.array(np.nonzero(detections)).T,separator=',').replace("\n ","")
                allDetections[currentFrame]=asString
                oldDetection=detections.copy()
            elif(key=='q'):
                break;
            elif(key=='d'):
                default_detection=not default_detection
            elif(key=='f'):
                print(currentFrame)
            elif(key in "<,"):
                #move back without saving
                # moveToFrameNumber(currentFrame-1)
                currentFrame=max(0,currentFrame-1)
                changeFrame=True
                loadOldDetection()
                pass
            elif(key in ">."):
                #move forward without saving
                currentFrame=min(currentFrame+1,totalFrames-1)
                changeFrame=True
                loadOldDetection()
                pass
            elif(ord(key) == ESCAPE_KEY or key=='0'):
                detections&=0
                
        print("Saving file")
        saveFile()
    except OSError as e:
        print(e)
    except Exception as e:
        saveFile()
        print(e)
    cap.release()
    cv.destroyAllWindows()
    pass



if __name__=="__main__":
    # main(cameraIndex=1)
    main(fileName=input("Enter Video File Path(absolute) :").strip().strip('"').strip("'"))