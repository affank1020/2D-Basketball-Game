import random
import time
from tkinter import *
from tkinter import messagebox
from PIL import Image, ImageTk
import math as math
import tkinter as tk


#IMPORTANT SETTINGS
MAX_FORCE = 25
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720

import json

#load json data and set settings to variables
with open('data.json') as f:
    data = json.load(f)

settings = data['settings']
SKY_COLOUR = settings['SKY_COLOUR']
INCR_POWER = settings['INCR_POWER']
DECR_POWER = settings['DECR_POWER']
RIGHT_ANGLE_START = settings['RIGHT_ANGLE_START']
LEFT_ANGLE_START = settings['LEFT_ANGLE_START']
RIGHT_ANGLE_STOP = settings['RIGHT_ANGLE_STOP']
LEFT_ANGLE_STOP = settings['LEFT_ANGLE_STOP']
SHOOT_BALL = settings['SHOOT_BALL']
BASKETBALL_DESIGN = settings['BALL_DESIGN']
BOSS_KEY = settings['BOSS_KEY']

window = Tk()

window.resizable(False, False)
window.title("Buzzer Beater")
window.geometry(str(WINDOW_WIDTH) + "x" + str(WINDOW_HEIGHT))
window.update()

obstacles = []

#load images
hoop = PhotoImage(file='images/BasketballHoop.png') #source - https://www.deviantart.com/digitemb-shop/art/Orange-Rim-Basketball-Net-Vector-892840986
arrowImg = PhotoImage(file='images/Arrow.png')
ballImg = PhotoImage(file=BASKETBALL_DESIGN) #source - https://opengameart.org/content/sports-balls
pauseImg = PhotoImage(file='images/Pause.png')#source - https://www.iconsdb.com/white-icons/pause-icon.html
playImg = PhotoImage(file='images/Play.png') #source - https://www.iconsdb.com/white-icons/play-icon.html
resetImg = PhotoImage(file='images/Reset.png') #source - https://www.iconsdb.com/white-icons/undo-icon.html
loadingImg = PhotoImage(file='images/LoadingCircle.png')
leaveImg = PhotoImage(file='images/Leave.png') #source - https://www.iconsdb.com/white-icons/door-8-icon.html
wasdImg = PhotoImage(file='images/wasdKeys.png') #source - https://opengameart.org/content/keyboard-keys-1
arrowkeysImg = PhotoImage(file='images/arrowKeys.png') #source - https://opengameart.org/content/keyboard-keys-1
profileImg = PhotoImage(file='images/profileIcon.png') #source - https://www.iconsdb.com/white-icons/user-6-icon.html
bossKeyImg = PhotoImage(file='images/bossKeyImage.png')
iceImg = PhotoImage(file='images/Ice.png') #source - https://gallery.yopriceville.com/Free-Clipart-Pictures/Winter-PNG/Icicles_PNG_Clip_Art_Image-1503670586#google_vignette

#set tkinter icon to basketball image
window.iconphoto(False, ballImg)

def MoveWidget(widget, desX, desY, speed):
    '''Moves a widget to a desired position at a desired speed'''
    #check if widget has not been destroyed whilst it is moving
    if widget.winfo_exists():
        curX, curY = widget.winfo_x(), widget.winfo_y()
        if curX < desX:
            #desired x is to the right of current x
            newX = curX + speed
        else:
            #desired x is to the left of current x
            newX = curX - speed

        if curY < desY:
            #desired y is below current y
            newY = curY + speed
        else:
            #desired y is above current y
            newY = curY - speed

        widget.place(x=newX, y=newY)
        if newX != desX or newY != desY:
            widget.after(10, lambda: MoveWidget(widget, desX, desY, speed)) #Recursive function to keep moving widget until it reaches desired position

class BossKey:
    def __init__(self, window):
        self.window = window
        self.bossKeyActive = False
        self.bossKey = None
        self.bossKeyBind = BOSS_KEY

    def BossKey(self, event):
        '''Boss key function which is called when the boss key is pressed'''
        if self.bossKeyActive == False:
            self.bossKeyActive = True
            
            #set window to size of image
            self.window.geometry(str(bossKeyImg.width()) + "x" + str(bossKeyImg.height()))
            self.window.title("Microsoft Excel 2010")
            self.window.update()
            bossKey = Label(self.window, image=bossKeyImg, background='grey')
            bossKey.place(x=0, y=0)
            self.bossKey = bossKey
            #bring boss key to front every 100ms to avoid it being overlapped by other widgets
            window.after(100, lambda: self.BringBossKeyToFront())
            
        else:
            self.bossKeyActive = False
            #reset window size and title
            self.window.geometry(str(WINDOW_WIDTH) + "x" + str(WINDOW_HEIGHT))
            self.window.title("Buzzer Beater")
            self.window.update()
            self.bossKey.destroy()

    def BringBossKeyToFront(self):
        '''Brings boss key image to the front of the window'''
        if self.bossKeyActive:
            #brings boss key image to the front of the window
            self.bossKey.lift()
            window.after(100, lambda: self.BringBossKeyToFront())

    def UpdateBossKey(self, newBossKey):
        '''Updates the boss key to a new key'''
        #If boss key is edited in settings, unbind then rebind
        self.UnbindBossKey()
        self.bossKeyBind = newBossKey
        self.BindBossKey()

    def BindBossKey(self):
        '''Binds the boss key to the window'''
        #boss key control is CTRL + SHIFT + key
        self.window.bind('<Control-'+ self.bossKeyBind + ">", self.BossKey)

    def UnbindBossKey(self):
        '''Unbinds the boss key from the window'''
        self.window.unbind('<Control-'+ self.bossKeyBind + ">")

bossKey = BossKey(window)
bossKey.BindBossKey()

#Levels and stages =======================================================

class Level:
    def __init__(self, scoreSettings, levelSettings, hoopSettings, groundSettings, arrowSettings, basketballSettings, powerBarSettings, obstacleSettings):
        self.levelSettings = levelSettings
        self.hoopSettings = hoopSettings
        self.groundSettings = groundSettings
        self.arrowSettings = arrowSettings
        self.basketballSettings = basketballSettings
        self.powerBarSettings = powerBarSettings
        self.scoreSettings = scoreSettings
        self.obstacleSettings = obstacleSettings

        self.groundColour = groundSettings.groundColour
        self.skyColour = groundSettings.skyColour
        self.maxAngle = arrowSettings.maxAngle
        self.minAngle = arrowSettings.minAngle

        self.rememberAngle = arrowSettings.initialAngle
        self.rememberPower = 0.5 * MAX_FORCE
        self.levelOver = False
        self.isPaused = False
        self.ballShot = False
        self.infoLabel = None
        self.resetButton = None
        self.timer = None
        self.levelObstacles = []

        self.cheatCodeActive = False

    def LoadLevel(self):
        '''Loads the level'''
        self.skyColour = self.groundSettings.skyColour
        window.configure(background=self.skyColour)

        window.bind('<Control-t>', self.SlowDownTime) #3 cheat codes
        window.bind('<Control-o>', self.PlusOneSecond)
        window.bind('<Control-m>', self.MinusOneSecond)

        #load all obstacles specfici to the level
        for levelObs in self.obstacleSettings.obstacles:
            obs = Obstacle(widget = Label(window, bg=levelObs.background, width=levelObs.width, height = levelObs.height), x=levelObs.x, y=levelObs.y, name=levelObs.name, frictionCoefficient=levelObs.frictionCoefficient)
            obstacles.append(obs)
            obs.widget.place(x=obs.x, y=obs.y)
            self.levelObstacles.append(obs)

        basketballHoop = BasketballHoop(x=self.hoopSettings.x, y=self.hoopSettings.y, height=self.hoopSettings.height, level=self)
        basketballHoop.createHoopObjects()
        self.basketballHoop = basketballHoop

        #ice is used for the cheat code
        #spawn it off screen, will be moved later in and out of the screen as the cheat code is activated
        self.ice1 = Label(window, image=iceImg, background=self.skyColour)
        self.ice1.place(x=180, y=-100, width=320)

        self.ice2 = Label(window, image=iceImg, background=self.skyColour)
        self.ice2.place(x=765, y=-100, width=320)

        timerLabel = Label(window, text="Time: " + str(self.scoreSettings.time), font=("Arial", 30), background=self.skyColour, fg = 'gold')
        timerLabel.place(x=window.winfo_width()/2 - 100, y=0)
        self.timer = Timer(widget=timerLabel)
        self.ballShot = False
    
        self.CreateGameElements()

        window.update()

        #rotate arrow function resets the position of the arrow to the correct position
        #rotating once back and forth cancels each other out to maintain intiial angle, but resets the position as required
        self.arrow.RotateArrow('Right')
        self.arrow.RotateArrow('Left')
        self.basketball.UpdateReferences(self.powerBar, self.arrow)

        self.leaveButton = self.CreateLeaveButton()
        self.pauseButton = self.CreatePauseButton()
        messagebox.showinfo("Level " + str(self.levelSettings.levelNumber) + ": " + self.levelSettings.levelName, self.levelSettings.levelDescription)

        self.timer.startTime = self.scoreSettings.time
        self.isPaused = False
        self.levelOver = False
        #self.RestartTimer()
        self.timer.widget.after(10, self.UpdateTimer) # update timer every 10ms
    
    def SlowDownTime(self, event):
        '''Cheat code to slow down time'''
        if self.cheatCodeActive == False:
            self.cheatCodeActive = True
            MoveWidget(self.ice1, 180, -30, 5) #move icicles into screen
            MoveWidget(self.ice2, 765, -30, 5)
        else:
            self.cheatCodeActive = False
            MoveWidget(self.ice1, 180, -100, 5) #move icicles out of screen
            MoveWidget(self.ice2, 765, -100, 5)

    def PlusOneSecond(self, event):
        '''Cheat code to add one second to the timer'''
        self.timer.startTime += 1 #add one second to timer

    def MinusOneSecond(self, event):
        '''Cheat code to minus one second from the timer'''
        self.timer.startTime -= 1 #minus one second from timer

    def BackToLevelSelect(self):
        '''Returns to the level select menu'''
        #if the game is paused, new levels are loaded in paused state so unpause before leaving the current level
        if self.isPaused:
            self.PauseLevel(event = None)
        self.ClearLevel()
        LevelSelectMenu(window=window, stages=stages, currentStage=self.levelSettings.stageNumber)

    def UpdateTimer(self):
        '''Updates the timer every 10ms'''
        if self.isPaused == False and self.levelOver == False:
            #cheat code slows down time
            if self.cheatCodeActive:
                self.timer.startTime -= 0.001
            else:
                self.timer.startTime -= 0.01 
            self.timer.widget.config(text="Time: " + str(round(self.timer.startTime, 2)))
            #If timer passes gold time, change the colour to silver, same for bronze
            if self.timer.startTime > self.scoreSettings.goldTime:
                self.timer.widget.config(fg='gold')
            elif self.timer.startTime < self.scoreSettings.goldTime and self.timer.startTime > self.scoreSettings.silverTime:
                self.timer.widget.config(fg='#DCDCDC')
            elif self.timer.startTime < self.scoreSettings.silverTime and self.timer.startTime > self.scoreSettings.bronzeTime:
                self.timer.widget.config(fg='#CD7F32')

            if self.timer.startTime > 0.01:
                #keep reducing until timer reaches 0.01
                self.timer.widget.after(10, self.UpdateTimer) 
            else:
                self.timer.widget.config(fg='red')
                #If the ball has not yet been shot, timer has ran out
                if self.ballShot == False:
                    self.TimerRunsOut()
                else:
                    #otherwise, keep the game alive in case ball is still moving
                    #after few seconds, show a bit of text in the corner saying to reset the game using the reset button
                    infoLabel = Label(window, text="Click the reset button on the left", font=("Arial", 15), background=self.skyColour, fg = 'white')
                    infoLabel.place(x=window.winfo_width() -300, y=-50)
                    self.infoLabel = infoLabel
                    if infoLabel is not None:
                        window.after(3000, lambda: MoveWidget(infoLabel, window.winfo_width() - 300, 20, 5))

    def ClearLevel(self):
        '''Clears the level'''
        #sometimes have to check if is not none to make sure the object is still there otherwise error is thrown when trying to destroy it
        if self.timer is not None:
            self.timer.widget.after_cancel(self.timer.widget)
            self.timer.widget.destroy()
        self.basketball.Destroy()
        self.leaveButton.destroy()
        self.pauseButton.destroy()
        self.ice1.destroy()
        self.ice2.destroy()
        if self.arrow:
            self.arrow.DestroyArrows()
        if self.powerBar:
            self.powerBar.destroy()
        if self.resetButton:
            self.resetButton.destroy()

        for levelObs in self.levelObstacles:
            levelObs.widget.destroy()
        self.levelObstacles.clear()
        obstacles.clear()
        self.basketballHoop.Destroy()
        window.unbind('<Control-t>') #unbind cheat code
        window.unbind('<Control-o>')
        window.unbind('<Control-m>')
        window.unbind(LEFT_ANGLE_START)
        window.unbind(RIGHT_ANGLE_START)
        window.unbind(LEFT_ANGLE_STOP)
        window.unbind(RIGHT_ANGLE_STOP)
        window.unbind(INCR_POWER)
        window.unbind(DECR_POWER)
        window.unbind(SHOOT_BALL)


        self.ground.colour = 'green'
        self.ground.widget.config(bg='green')
        self.skyColour = 'sky blue'
        window.configure(background=self.skyColour) #reset sky/ground colour because in stage 3, colours change to space theme

    def RestartTimer(self):
        '''Restarts the timer'''
        self.timer.startTime = self.scoreSettings.time
        self.timer.widget.after(10, self.UpdateTimer)

    def ResetLevel(self, event):
        '''Resets the level'''
        if self.isPaused:
            self.PauseLevel(event = None)
        self.levelOver = False

        if self.infoLabel is not None:
            self.infoLabel.destroy()

        self.isPaused = True
        self.ballShot = False
        self.basketball.Destroy()

        if self.arrow is not None:
            self.arrow.DestroyArrows()
        
        if self.powerBar is not None:
            self.powerBar.destroy()

        if self.resetButton is not None:
            self.resetButton.destroy()

        self.pauseButton.config(state='normal')
        self.leaveButton.config(state='normal')

        self.CreateGameElements()
        window.update()
        self.arrow.RotateArrow('Right')
        self.arrow.RotateArrow('Left')
        self.arrow.StopRotateArrow()
        self.basketball.UpdateReferences(self.powerBar, self.arrow)

        self.timer.widget.config(text="Time: " + str(self.scoreSettings.time), fg='gold')
        self.timer.widget.place(x=window.winfo_width()/2 - 100, y=0)
        messagebox.showinfo("Level " + str(self.levelSettings.levelNumber) + ": " + self.levelSettings.levelName, self.levelSettings.levelDescription)
        self.isPaused = False
        self.RestartTimer()

    def CreateBasketball(self):
        '''Creates the basketball'''
        basketball = Basketball(startX=self.basketballSettings.startX, startY=self.basketballSettings.startY, mass=self.basketballSettings.mass, gravity=self.basketballSettings.gravity, timeDelay=self.basketballSettings.timeDelay, friction=self.basketballSettings.friction, level=self, skyColour=self.skyColour)
        basketball.CreateBasketball()
        basketball.UpdateGroundReference(self.ground)
        self.basketball = basketball
        self.basketballHoop.UpdateHoopScorePosition()
        basketball.ResetBallPosition()

    def PauseLevel(self, event):
        '''Pauses the level'''
        self.isPaused = not self.isPaused
        if self.isPaused:
            if self.ballShot:
                self.basketball.SetPhysicsMemory()
                #keep current physics variables in memory when pausing
                window.after_cancel(self.basketball.physicsID)
            else:
                self.UnbindKeys()
                self.UnbindScreenControls()
            self.pauseButton.config(image=playImg)
        else:
            if self.ballShot:
                #load physics memory and start the physics again
                self.basketball.LoadPhysicsMemory()
                self.basketball.physicsID = window.after(int(self.basketball.timeDelay * 1000), lambda: self.basketball.BallPhysics(obstacles))
            else:
                self.BindKeys()
            self.pauseButton.config(image=pauseImg)
            self.timer.widget.after(10, self.UpdateTimer) #Start the timer again

    def CreateResetButton(self):
        '''Creates the reset button'''
        resetButton = Button(window, image=resetImg, width=50, height=50, font=("Arial", 20), background='grey', fg='white')
        resetButton.place(x = 10, y = 180, anchor='w')
        resetButton.bind('<Button-1>', self.ResetLevel)
        self.resetButton = resetButton

    def CreatePauseButton(self):
        '''Creates the pause button'''
        pauseButton = Button(window, image=pauseImg, width=50, height=50, font=("Arial", 20), background='grey', fg='white')
        pauseButton.place(x = 10, y = 110, anchor='w')
        pauseButton.bind('<Button-1>', self.PauseLevel)
        return pauseButton

    def CreateLeaveButton(self):
        '''Creates the leave button'''
        leaveButton = Button(window, image=leaveImg, width=50, height=50, command=lambda: self.BackToLevelSelect(),font=("Arial", 20), background='grey', fg='white')
        leaveButton.place(x = 10, y = 40, anchor='w')
        return leaveButton

    def HoopScored(self):
        '''Called when the hoop is scored'''
        if self.levelOver == False:
            self.UnbindKeys()

            if self.infoLabel is not None:
                self.infoLabel.destroy()
            self.levelOver = True
            self.pauseButton.config(state='disable')
            self.resetButton.config(state='disable')
            self.leaveButton.config(state='disable')
            window.after(50, lambda: MoveWidget(self.timer.widget, self.timer.widget.winfo_x(), self.timer.widget.winfo_y() - 100, 5))
            window.after(1000, lambda: self.ShowDropDownMenu())

    def TimerRunsOut(self):
        '''Called when the timer runs out'''
        self.UnbindKeys()
        self.leaveButton.config(state='disable')
        self.levelOver = True
        window.after(50, lambda: MoveWidget(self.timer.widget, self.timer.widget.winfo_x(), self.timer.widget.winfo_y() - 100, 5))
        window.after(1000, lambda: self.ShowDropDownMenu(win=False))

    def CreateGameElements(self):
        '''Creates the game elements'''
        self.ground = Ground(width=self.groundSettings.width, height=self.groundSettings.height, colour=self.groundColour)
        self.ground.CreateGround()

        self.CreateBasketball()

        self.arrow = Arrow(myBasketball=self.basketball, level=self)
        self.arrow.CreateArrow()
        self.arrow.CreateAngleControls()
        self.arrow.SetArrowAngle(self.arrowSettings.initialAngle)

        self.powerBar = PowerBar(noFillColour=self.powerBarSettings.noFillColour, fillColour=self.powerBarSettings.fillColour, width=self.powerBarSettings.width, height=self.powerBarSettings.height, x=self.powerBarSettings.x, y=self.powerBarSettings.y)
        self.powerBar.CreatePowerBar()

    def UnbindKeys(self):
        '''Unbinds the keys'''
        window.unbind(SHOOT_BALL)
        window.unbind(RIGHT_ANGLE_START)
        window.unbind(LEFT_ANGLE_START)
        window.unbind(RIGHT_ANGLE_STOP)
        window.unbind(LEFT_ANGLE_STOP)
        window.unbind(INCR_POWER)
        window.unbind(DECR_POWER)

    def UnbindScreenControls(self):
        '''Unbinds the screen controls'''
        self.arrow.rotateLeftButton.unbind('<ButtonPress-1>')
        self.arrow.rotateRightButton.unbind('<ButtonPress-1>')
        self.arrow.rotateLeftButton.unbind('<ButtonRelease-1>')
        self.arrow.rotateRightButton.unbind('<ButtonRelease-1>')
        self.powerBar.powerBarObj.unbind('<B1-Motion>')

    def BindKeys(self):
        '''Binds the keys'''
        window.bind(SHOOT_BALL, self.basketball.BallClicked)
        window.bind(RIGHT_ANGLE_START, lambda event: self.arrow.StartRotateArrowRight(usingKey=True))
        window.bind(LEFT_ANGLE_START, lambda event: self.arrow.StartRotateArrowLeft(usingKey=True))
        window.bind(RIGHT_ANGLE_STOP, lambda event: self.arrow.StopRotateArrow())
        window.bind(LEFT_ANGLE_STOP, lambda event: self.arrow.StopRotateArrow())
        window.bind(INCR_POWER, lambda event: self.powerBar.IncreasePower())
        window.bind(DECR_POWER, lambda event: self.powerBar.DecreasePower())

        self.arrow.rotateLeftButton.bind('<ButtonPress-1>', lambda event: self.arrow.StartRotateArrowLeft(usingKey=False))
        self.arrow.rotateRightButton.bind('<ButtonPress-1>', lambda event: self.arrow.StartRotateArrowRight(usingKey=False))
        self.arrow.rotateLeftButton.bind('<ButtonRelease-1>', lambda event: self.arrow.StopRotateArrow())
        self.arrow.rotateRightButton.bind('<ButtonRelease-1>', lambda event: self.arrow.StopRotateArrow())
        self.powerBar.powerBarObj.bind('<B1-Motion>', self.powerBar.UpdateRectanglePosition)

    def ShowDropDownMenu(self, win = True):
        '''Shows the drop down menu'''
        self.menu = DropDownMenu(window, self)
        self.RestartTimer()
        if win:
            self.menu.CreateWinButtons()
        else:
            self.menu.CreateLoseButtons()
 
class Stage:
    def __init__(self, name, number, levels):
        self.name = name
        self.levels = levels
        self.number = number

#=========================================================================

#Menus ===================================================================

class MainMenu:
    def __init__(self, window):
        self.window = window
        self.menuBucketLeftEdge = None
        self.menuBucketRightEdge = None

        #title
        self.title = Label(window, text="Buzzer Beater", font=("Arial", 60), background=SKY_COLOUR, fg='red')
        self.title.place(x=950, y=50, anchor='n')
        
        #Create a ground object to display the ground
        ground = Ground(width=700, height=100, colour='green')
        ground.CreateGround()
        
        hoop1 = Label(window, image=hoop, background=SKY_COLOUR)
        hoop1.place(x=140, y=220)
        self.hoop1 = hoop1

        hoop2 = Label(window, image=hoop, background=SKY_COLOUR)
        hoop2.place(x=390, y=320)
        self.hoop2 = hoop2
        
        hoop3 = Label(window, image=hoop, background=SKY_COLOUR)
        hoop3.place(x=640, y=420)
        self.hoop3 = hoop3

        #Create a basketball for animations
        basketball = Basketball(startX=1050, startY=700, mass=10, gravity=35, timeDelay=0.0075, friction=0.55, level=None, skyColour='sky blue')
        basketball.CreateBasketball()
        basketball.UpdateGroundReference(ground)
        basketball.BallPhysics(obstacles)
        basketball.ResetBallPosition()
        self.basketball = basketball

        #light blue background
        window.configure(background=SKY_COLOUR)

        #more buttons
        self.playButton = Button(window, text="Play", command=lambda: self.playAnimation(1), width=10, height=1, font=("Arial", 20), background='grey', fg='white')
        self.playButton.place(x=100, y=350)
        
        self.setttingsButton = Button(window, text="Settings", command=lambda: self.playAnimation(2), width=10, height=1, font=("Arial", 20), background='grey', fg='white')
        self.setttingsButton.place(x=350, y=450)

        self.quitButton = Button(window, text="Quit", command=lambda: self.playAnimation(3), width=10, height=1, font=("Arial", 20), background='grey', fg='white')
        self.quitButton.place(x=600, y=550)
        window.update()

        #sometimes ball is spawned at (0,0)
        #so update window and reset it back to desired position
        self.basketball.ResetBallPosition()

        self.profileButton = Button(window, image=profileImg, command=lambda: self.LoadProfile(), width=50, height=50, font=("Arial", 15), background='grey', fg='white')
        self.profileButton.place(x=1200, y=550)

    def playAnimation(self, hoopNum):
        '''Plays the animation to throw the ball into the hoop'''
        self.playButton.config(state='disable')
        self.quitButton.config(state='disable')
        self.setttingsButton.config(state='disable')

        #the main menu option basically triggers a force on the ball which throws it into one of the 3 hoops positioned above the buttons
        #the hoopNum parameter is used to determine which hoop the ball should go into

        loading = LoadingImage(window=window, fromX=20, fromY=-20, toX=20, toY=20, lifetime=3, speed=2)
        loading.PlayLoadingAnimation()
        if hoopNum == 1:
            #positions and forces which are hard-coded to throw the ball into the correct hoop
            x1 = 135
            x2 = 240
            y = 220
            force = 22
            angle = 120
        elif hoopNum == 2:
            x1 = 380
            x2 = 490
            y = 320
            force = 20
            angle = 115
        elif hoopNum == 3:
            x1 = 630
            x2 = 740
            y = 420
            force = 16
            angle = 110

        #edges of the hoop are invisible but are needed to make the ball bounce into the hoop nicely
        menuBucketLeftEdge = Obstacle(widget = Label(window, bg=SKY_COLOUR), x=x1, y=y, name="menuBucketLeftEdge", frictionCoefficient=1)
        menuBucketLeftEdge.widget.place(x=x1, y=y, width=10, height=50)
        menuBucketRightEdge = Obstacle(widget = Label(window, bg=SKY_COLOUR), x=x2, y=y, name="menuBucketRightEdge", frictionCoefficient=1)
        menuBucketRightEdge.widget.place(x=x2, y=y, width=10, height=50)

        self.menuBucketLeftEdge = menuBucketLeftEdge
        self.menuBucketRightEdge = menuBucketRightEdge

        obstacles.append(menuBucketLeftEdge)
        obstacles.append(menuBucketRightEdge)
        self.basketball.ApplyForce(force, math.radians(angle), True)

        if hoopNum == 1:
            window.after(3000, self.PlayGameNow)
        elif hoopNum == 2:
            window.after(3000, self.PlaySettingsNow)
        elif hoopNum == 3:
            window.after(3000, self.QuitGameNow)

    def QuitGameNow(self):
        '''Quits the game'''
        window.destroy()

    def PlayGameNow(self):
        '''Plays the level select menu'''
        self.ClearMenu()
        self.basketball.Destroy()
        LevelSelectMenu(window, stages=stages)

    def PlaySettingsNow(self):
        '''Plays the settings menu'''
        self.ClearMenu()
        self.basketball.Destroy()
        SettingsMenu(window)
    
    def ClearMenu(self):
        '''Clears the menu'''
        obstacles.clear()
        if self.menuBucketLeftEdge is not None:
            self.menuBucketLeftEdge.widget.destroy()

        if self.menuBucketRightEdge is not None:
            self.menuBucketRightEdge.widget.destroy()

        self.title.destroy()
        self.playButton.destroy()
        self.quitButton.destroy()
        self.profileButton.destroy()
        self.setttingsButton.destroy()
        self.hoop1.destroy()
        self.hoop2.destroy()
        self.hoop3.destroy()

    def LoadProfile(self):
        '''Loads the profile menu'''
        self.ClearMenu()
        self.basketball.Destroy()
        ProfileMenu(window)

class ProfileMenu:
    def __init__(self, window):
        self.window = window
        self.profileEntry = None
        self.profileMenuOpen = False
        self.curLeaderboard = ''
        self.leaderboardWidgets = []

        #Get list of account names in data.json
        data = json.load(open('data.json'))
        self.accounts = []
        #Get numer of accounts
        self.numOfAccounts = int(data['accounts']['accountCount'])
        self.currentAccount = int(data['accounts']['currentAccount']) - 1

        for i in range(1, self.numOfAccounts + 1):
            self.accounts.append(data['accounts'][str(i)])


        self.CreateProfileButtons()

    def CreateProfileButtons(self):
        '''Creates the profile buttons for the profile menu'''
        self.backButton = Button(window, text="Back", command=lambda: self.Back(), width=8, height=1, font=("Arial", 20), background='grey', fg='white')
        self.backButton.place(x=100, y=550, anchor='n')

        self.canvas = Canvas(window, width=window.winfo_width() - 250, height=window.winfo_height() - 300, background='grey')
        self.canvas.place(x=window.winfo_width()/2, y=50, anchor='n')

        self.profileButton = Button(window, text="Profile", command=lambda: self.CreateProfileMenu(), width=10, height=1, font=("Arial", 20), background='grey', fg='white')
        self.profileButton.place(x=150, y=80)
        self.leaderboardButton = Button(window, text="Leaderboard", command=lambda: self.CreateLeaderboardMenu(), width=10, height=1, font=("Arial", 20), background='grey', fg='white')
        self.leaderboardButton.place(x=150, y=160)
        self.divider = Label(window, bg='white')
        self.divider.place(x=340, y=80, width=10, height=365)

        self.CreateProfileMenu()

    def CreateProfileMenu(self):
        '''Creates the profile menu'''
        if self.profileMenuOpen == False:
            self.ClearLeaderboardMenu()
            self.profileMenuOpen = True

            self.currentName = Label(window, text="Name: " + self.accounts[self.currentAccount]['username'], font=("Arial", 20), background='grey', fg='white')
            self.currentName.place(x=400, y=100)
            self.bronzeCount = Label(window, text="Bronze Badges: " + str(self.accounts[self.currentAccount]['Bronze']), font=("Arial", 20), background='grey', fg='#cd7f32')
            self.bronzeCount.place(x=400, y=150)
            self.silverCount = Label(window, text="Silver Badges: " + str(self.accounts[self.currentAccount]['Silver']), font=("Arial", 20), background='grey', fg='#c0c0c0')
            self.silverCount.place(x=400, y=185)
            self.goldCount = Label(window, text="Gold Badges: " + str(self.accounts[self.currentAccount]['Gold']), font=("Arial", 20), background='grey', fg='gold')
            self.goldCount.place(x=400, y=220)
            self.buzzerbeaterCount = Label(window, text="Buzzer Beaters: " + str(self.accounts[self.currentAccount]['Buzzer Beater']), font=("Arial", 20), background='grey', fg='red')
            self.buzzerbeaterCount.place(x=400, y=255)

            self.changeProfile = Button(window, text="Change Profile", command=lambda: self.ChangeProfilePrompt(), width=15, height=1, font=("Arial", 15), background='grey', fg='white')
            self.changeProfile.place(x=400, y=300)

    def ChangeProfilePrompt(self):
        '''Prompts the user to enter a new profile name'''
        self.profileEntry = Entry(window, width=20, font=("Arial", 20))
        self.profileEntry.place(x=400, y=350)
        self.profileEntry.focus_set()
        self.profileEntry.bind('<Return>', lambda event: self.ChangeProfile())
        self.profileEntry.bind('<Escape>', lambda event: self.CancelChangeProfile())
        self.confirmChangeProfile = Button(window, text="Confirm", command=lambda: self.ChangeProfile(), width=10, height=1, font=("Arial", 15), background='grey', fg='white')
        self.confirmChangeProfile.place(x=400, y=400)
        self.cancelChangeProfile = Button(window, text="Cancel", command=lambda: self.CancelChangeProfile(), width=10, height=1, font=("Arial", 15), background='grey', fg='white')
        self.cancelChangeProfile.place(x=550, y=400)

    def ChangeProfile(self):
        '''Changes the profile name'''
        found = False
        data = json.load(open('data.json'))
        for account in self.accounts:
            if account['username'] == self.profileEntry.get():
                self.currentAccount = self.accounts.index(account)
                found = True
                break

        if found == False:
            #if account does not exist, create a new one
            self.numOfAccounts += 1
            self.currentAccount = self.numOfAccounts - 1
            data['accounts']['accountCount'] = self.numOfAccounts
            data['accounts'][str(self.numOfAccounts)] = {
                "username": self.profileEntry.get(), 
                "Bronze": 0, 
                "Silver": 0, 
                "Gold": 0, 
                "Buzzer Beater": 0,
                "stages":{
                    "stage1": {
                        "level1": "N/A",
                        "level2": "N/A",
                        "level3": "N/A",
                        "level4": "N/A",
                        "level5": "N/A"
                    },
                    "stage2": {
                        "level1": "N/A",
                        "level2": "N/A",
                        "level3": "N/A",
                        "level4": "N/A",
                        "level5": "N/A"
                    },
                    "stage3": {
                        "level1": "N/A",
                        "level2": "N/A",
                        "level3": "N/A",
                        "level4": "N/A",
                        "level5": "N/A"
                    }
                }
            }
            self.accounts.append(data['accounts'][str(self.numOfAccounts)])
    
        data['accounts']['currentAccount'] = self.currentAccount + 1
        with open('data.json', 'w') as outfile:
            json.dump(data, outfile, indent=4)

        #update profile menu based on account stats
        self.currentName.config(text="Name: " + self.profileEntry.get())
        self.bronzeCount.config(text="Bronze Badges: " + str(self.accounts[self.currentAccount]['Bronze']))
        self.silverCount.config(text="Silver Badges: " + str(self.accounts[self.currentAccount]['Silver']))
        self.goldCount.config(text="Gold Badges: " + str(self.accounts[self.currentAccount]['Gold']))
        self.buzzerbeaterCount.config(text="Buzzer Beaters: " + str(self.accounts[self.currentAccount]['Buzzer Beater']))

        #get rid of login stuff
        self.CancelChangeProfile()

    def CancelChangeProfile(self):
        '''Cancels the profile change'''
        self.profileEntry.destroy()
        self.confirmChangeProfile.destroy()
        self.cancelChangeProfile.destroy()

    def CreateLeaderboardMenu(self):
        '''Creates the leaderboard menu'''
        if self.profileMenuOpen == True:
            self.ClearProfileMenu()
            self.profileMenuOpen = False

            self.buzzerbeaterBoard = Button(window, text="Buzzer Beaters", command=lambda: self.CreateLeaderboard('Buzzer Beater'), width=15, height=1, font=("Arial", 15), background='grey', fg='white')
            self.buzzerbeaterBoard.place(x=380, y=80)
            self.goldBadgesBoard = Button(window, text="Golds", command=lambda: self.CreateLeaderboard('Gold'), width=15, height=1, font=("Arial", 15), background='grey', fg='white')
            self.goldBadgesBoard.place(x=380, y=130)
            self.silverBadgesBoard = Button(window, text="Silvers", command=lambda: self.CreateLeaderboard('Silver'), width=15, height=1, font=("Arial", 15), background='grey', fg='white')
            self.silverBadgesBoard.place(x=380, y=180)
            self.bronzeBadgesBoard = Button(window, text="Bronzes", command=lambda: self.CreateLeaderboard('Bronze'), width=15, height=1, font=("Arial", 15), background='grey', fg='white')
            self.bronzeBadgesBoard.place(x=380, y=230)

            #default is buzzer beaters
            self.CreateLeaderboard('Buzzer Beater')
        
    def ClearCurrentBoard(self):
        '''Clears the current leaderboard'''
        for widget in self.leaderboardWidgets:
            widget.destroy()
        self.leaderboardWidgets.clear()

    def CreateLeaderboard(self, badge):
        '''Creates the leaderboard'''
        if self.curLeaderboard != badge:
            self.ClearCurrentBoard()
            self.curLeaderboard = badge
            data = json.load(open('data.json'))
            accounts = []
            for i in range(1, self.numOfAccounts + 1):
                accounts.append(data['accounts'][str(i)])

            #set colour of badge text
            if badge == 'Buzzer Beater':
                colour = 'red'
            elif badge == 'Gold':
                colour = 'gold'
            elif badge == 'Silver':
                colour = '#c0c0c0'
            elif badge == 'Bronze':
                colour = '#cd7f32'

            #Sort accounts by buzzer beaters
            accounts.sort(key=lambda x: x[badge], reverse=True)
            curBadge = Label(window, text=badge + "s", font=("Arial", 20), background='grey', fg=colour)
            curBadge.place(x=600, y=70)
            self.leaderboardWidgets.append(curBadge)
            #Display table of all accounts and their buzzer beaters to the right of the buttons all ordered with name and rank and value in current leaderboard
            for i in range(0, self.numOfAccounts):
                accountLabel = Label(window, text=str(i + 1) + ". " + accounts[i]['username'] + ": " + str(accounts[i][badge]), font=("Arial", 15), background='grey', fg='white')
                accountLabel.place(x=600, y=110 + (i * 30))
                self.leaderboardWidgets.append(accountLabel)

    def ClearWholeMenu(self):
        '''Clears the whole menu'''
        self.backButton.destroy()
        self.profileButton.destroy()
        self.leaderboardButton.destroy()
        self.divider.destroy()
        self.canvas.destroy()

    def ClearProfileMenu(self):
        '''Clears the profile menu'''
        self.currentName.destroy()
        self.bronzeCount.destroy()
        self.silverCount.destroy()
        self.goldCount.destroy()
        self.buzzerbeaterCount.destroy()
        self.changeProfile.destroy()
        if self.profileEntry is not None:
            self.CancelChangeProfile()

    def ClearLeaderboardMenu(self):
        '''Clears the leaderboard menu'''
        if self.curLeaderboard != '':
            self.buzzerbeaterBoard.destroy()
            self.goldBadgesBoard.destroy()
            self.silverBadgesBoard.destroy()
            self.bronzeBadgesBoard.destroy()
            self.ClearCurrentBoard()

    def Back(self):
        '''Returns to the main menu'''
        self.ClearWholeMenu()
        if self.profileMenuOpen == True:
            self.ClearProfileMenu()
        else:
            self.ClearLeaderboardMenu()
            
        MainMenu(window)

class LevelSelectMenu:
    def __init__(self, window, stages, currentStage = 1):
        self.levelWidgets = []
        self.newWidgets = []
        self.stages = stages
        self.currentStage = currentStage
        self.t = 1/30
        self.createAnimCounter = 0
        self.leftButton = None
        self.rightButton = None
        self.deleteCounter = 0
        self.repeatTracker = None
        self.repeatTrackerCreate = None
        self.window = window
        self.CreateLevelSelectMenu(name=stages[self.currentStage - 1].name, number=stages[self.currentStage - 1].number, levels=stages[self.currentStage - 1].levels)

    def LoadLevel(self, level):
        '''Loads the level'''
        self.ClearLevelSelectMenu()
        level.LoadLevel()

    def NextStage(self):
        '''Loads the next stage'''
        if self.currentStage < len(self.stages):
            self.currentStage += 1
            self.PlayAnimationRight()

    def PreviousStage(self):
        '''Loads the previous stage'''
        if self.currentStage > 1:
            self.currentStage -= 1
            self.PlayAnimationLeft()

    #these animation functions manage the animation of the level select menu when switching between stages
    #first all current widgets are moved off screen and destroyed
    #then new widgets are created off screen and moved into position
    #separate functions for right and left but same method

    def PlayAnimationLeft(self):
        '''Plays the animation to move the level select menu to the left'''
        t = self.t
        for button in self.levelWidgets:
            if button.winfo_exists():
                newPos = (1-t) * button.winfo_x() + t * (button.winfo_x() + 900)
                button.place(x=newPos, y=button.winfo_y())
                if button.winfo_x() > window.winfo_width() + 5:
                    button.destroy()
                    self.deleteCounter += 1

        if self.deleteCounter == 10:
            self.ClearLevelSelectMenu()
            self.CreateLevelSelectMenu(self.stages[self.currentStage - 1].name, self.stages[self.currentStage - 1].number, self.stages[self.currentStage - 1].levels, comeFromRight=False)
            self.deleteCounter = 0
            window.after_cancel(self.repeatTracker)
        else:
            self.repeatTracker = window.after(10, self.PlayAnimationLeft)

    def PlayAnimationCreateLeft(self):
        '''Plays the animation to create the level select menu from the right and bring to the left'''
        self.createAnimCounter += 1
        breakLoop = False
        t = self.t
        for button in self.newWidgets:
            if button.winfo_exists():
                newPos = button.winfo_x() + 30
                button.place(x=newPos, y=button.winfo_y())
                if button.winfo_x() > 800:
                    breakLoop = True
        if breakLoop:
            self.window.after_cancel(self.repeatTrackerCreate)
            self.createAnimCounter = 0
        else:
            self.repeatTrackerCreate = self.window.after(10, self.PlayAnimationCreateLeft)

    def PlayAnimationRight(self):
        '''Plays the animation to move the level select menu to the right'''
        t = self.t
        for button in self.levelWidgets:
            if button.winfo_exists():
                newPos = (1-t) * button.winfo_x() + t * (button.winfo_x() - 900)
                button.place(x=newPos, y=button.winfo_y())
                if button.winfo_x() < -5:
                    button.destroy()
                    self.deleteCounter += 1

        if self.deleteCounter == 10:
            self.ClearLevelSelectMenu()
            self.CreateLevelSelectMenu(self.stages[self.currentStage - 1].name, self.stages[self.currentStage - 1].number, self.stages[self.currentStage - 1].levels, comeFromRight=True)
            self.deleteCounter = 0
            self.window.after_cancel(self.repeatTracker)
        else:
            self.repeatTracker = self.window.after(10, self.PlayAnimationRight)

    def PlayAnimationCreateRight(self):
        '''Plays the animation to create the level select menu from the left and bring to the right'''
        self.createAnimCounter += 1
        breakLoop = False
        t = self.t
        for button in self.newWidgets:
            if button.winfo_exists():
                newPos = (1-t) * button.winfo_x() + t * (button.winfo_x() - 900)
                button.place(x=newPos, y=button.winfo_y())
                if button.winfo_x() < 310:
                    breakLoop = True
        if breakLoop:
            self.window.after_cancel(self.repeatTrackerCreate)
            self.createAnimCounter = 0
        else:
            self.repeatTrackerCreate = self.window.after(10, self.PlayAnimationCreateRight)

    def ClearLevelSelectMenu(self):
        '''Clears the level select menu'''
        self.stageLabel.destroy()
        self.backButton.destroy()
        for w in self.levelWidgets:
            w.destroy()

        if self.leftButton is not None:
            self.leftButton.destroy()

        if self.rightButton is not None:
            self.rightButton.destroy()
    
    def BackToMainMenu(self):
        '''Returns to the main menu'''
        self.ClearLevelSelectMenu()
        MainMenu(window)

    def CreateLevelSelectMenu(self, name, number, levels, comeFromRight = None):
        '''Creates the level select menu'''
        counter = 1

        stageLabel = Label(window, text="Stage " + str(stages[self.currentStage - 1].number) + ": " + stages[self.currentStage - 1].name, font=("Arial", 30), background=SKY_COLOUR, fg='white')
        stageLabel.place(x=0, y=50, width=window.winfo_width(), height=100)
        self.stageLabel = stageLabel

        backButton = Button(window, text="Back", width=10, height=1, font=("Arial", 20), background='grey', fg='white')
        backButton.place(x=10, y=window.winfo_height() - 160, width=100, height=50)
        backButton.bind('<Button-1>', lambda event: self.BackToMainMenu())
        self.backButton = backButton

        if self.currentStage > 1:
            leftButton = Button(window, text="<", width=3, height=1, font=("Arial", 20), background='grey', fg='white')
            leftButton.place(x=0, y=50, width=50, height=100)
            self.leftButton = leftButton
            leftButton.bind('<Button-1>', lambda event: self.PreviousStage())

        if self.currentStage < len(self.stages):
            rightButton = Button(window, text=">", width=3, height=1, font=("Arial", 20), background='grey', fg='white')
            rightButton.place(x=window.winfo_width() - 50, y=50, width=50, height=100)
            self.rightButton = rightButton
            rightButton.bind('<Button-1>', lambda event: self.NextStage())

        if comeFromRight:
            xCounterIncr = 900
        elif comeFromRight == False:
            xCounterIncr = -900
        else:
            xCounterIncr = 0

        xCounter = 245 + xCounterIncr
        yCounter = 250
        self.newWidgets.clear()

        data = json.load(open('data.json'))
        levelData = data['accounts'][str(data['accounts']['currentAccount'])]['stages']['stage' + str(self.currentStage)]

        for level in levels:
            levelButton = tk.Button(window, text="Level " + str(level.levelSettings.levelNumber), command=lambda level=level: self.LoadLevel(level=level), width=10, height=1, font=("Arial", 20), background='grey', fg='white')
            levelButton.place(x=xCounter, y=yCounter)

            #additional label beneath each level detailing the high score achieved by this account on that level
            levelResult = levelData['level' + str(level.levelSettings.levelNumber)]
            if levelResult == "N/A":
                textColour = 'white'
            elif levelResult == "Bronze":
                textColour = '#cd7f32'
            elif levelResult == "Silver":
                textColour = '#c0c0c0'
            elif levelResult == "Gold":
                textColour = 'gold'
            elif levelResult == "Buzzer Beater":
                textColour = 'red' 

            resultLabel = Label(window, text=levelResult, font=("Arial", 15), width=15, height=1, background='grey', fg=textColour)
            resultLabel.place(x=xCounter + 5, y=yCounter + 50)
            self.levelWidgets.append(levelButton)
            self.levelWidgets.append(resultLabel)
            xCounter += 300
            counter += 1
            if counter > 3:
                xCounter = 395 + xCounterIncr
                yCounter += 200
                counter = 1

            self.newWidgets.append(levelButton)
            self.newWidgets.append(resultLabel)
        #If using buttons to navigate the level select menu
        if comeFromRight is not None:
            if(comeFromRight): #If coming from the right, animate the buttons coming in from the right
                self.repeatTrackerCreate = window.after(10, self.PlayAnimationCreateRight)
            else:
                self.repeatTrackerCreate = window.after(10, self.PlayAnimationCreateLeft)

class SettingsMenu:
    def __init__(self, window):
        self.curControlsWASD = True
        self.window = window

        self.ballDesigns = ["images/basketball1.png", "images/basketball2.png", "images/basketball3.png", "images/basketball4.png", "images/basketball5.png"]
        self.currentBallDesignIndex = 0
        self.CreateSettingsMenu()

    def CreateSettingsMenu(self):
        '''Creates the settings menu'''
        self.backButton = Button(window, text="Back", width=10, height=1, font=("Arial", 20), background='grey', fg='white')
        self.backButton.place(x=10, y=window.winfo_height() - 160, width=100, height=50)
        self.backButton.bind('<Button-1>', lambda event: self.BackToMainMenu())

        self.canvas = Canvas(window, width=window.winfo_width() - 250, height=window.winfo_height() - 400, bg='grey')
        self.canvas.place(x=window.winfo_width()/2, y=50, anchor='n')

        #set currentBallDesignIndex to the index in the ballDesigns array at which the value matches BASKETBALL_Design
        self.currentBallDesignIndex = self.ballDesigns.index(BASKETBALL_DESIGN)
        self.ballImg = Image.open(self.ballDesigns[self.currentBallDesignIndex])
        self.ball = Label(window, image=ballImg, background='grey')
        self.ball.place(x=225, y=100)

        self.leftArrow = Button(window, text="<", width=5, height=1, font=("Arial", 20), background='grey', fg='white')
        self.leftArrow.place(x=160, y=110, width=50, height=50)
        self.leftArrow.bind('<Button-1>', lambda event: self.ChangeBall(-1))
        self.rightArrow = Button(window, text=">", width=5, height=1, font=("Arial", 20), background='grey', fg='white')
        self.rightArrow.place(x=300, y=110, width=50, height=50)
        self.rightArrow.bind('<Button-1>', lambda event: self.ChangeBall(1))

        self.wasdLabel = Label(window, image=wasdImg, font=("Arial", 20), background='dark green', fg='white')
        self.wasdLabel.place(x=500, y=70)
        self.wasdLabel.bind('<Button-1>', lambda event: self.SelectWASD())

        self.wasdText = Label(window, text="W - Increase power\nA - Turn arrow left\nS - Decrease power\nD - Turn arrow right", font=("Arial", 17), background='grey', fg='white', justify='left')
        self.wasdText.place(x=500, y=250, anchor='w')

        self.arrowkeyText = Label(window, text="Up - Increase power\nLeft - Turn arrow left\nDown - Decrease power\nRight - Turn arrow right", font=("Arial", 17), background='grey', fg='white', justify='left')
        self.arrowkeyText.place(x=800, y=250, anchor='w')

        self.arrowkeysLabel = Label(window, image=arrowkeysImg, font=("Arial", 20), background='grey', fg='white')
        self.arrowkeysLabel.place(x=800, y=70)
        self.arrowkeysLabel.bind('<Button-1>', lambda event: self.SelectArrowKeys())

        self.bossKey = StringVar(window)
        self.bossKey.set(BOSS_KEY)

        self.shootKey = StringVar(window)
        if SHOOT_BALL == "<KeyPress-space>":
            self.shootKey.set("Space")
        elif SHOOT_BALL == "<KeyPress-Return>":
            self.shootKey.set("Enter")

        self.bosskeyDropBox = OptionMenu(window, self.bossKey, "Q", "E", "R", "T", "Y", "U", "I", "O", "P", "F", "G", "H", "J", "K", "L", "Z", "X", "C", "V", "B", "N", "M")
        self.bosskeyDropBox.place(x=320, y=220, anchor='w')

        self.shootKeyDropBox = OptionMenu(window, self.shootKey,"Shoot Key: ", "Space", "Enter")
        self.shootKeyDropBox.place(x=320, y=280, anchor='w')

        self.bossKeyLabel = Label(window, text="Boss Key\n(Ctrl + Shift + ): ", font=("Arial", 13), background='grey', fg='white', justify='left')
        self.bossKeyLabel.place(x=160, y=220, anchor='w')

        self.shootKeyLabel = Label(window, text="Shoot Ball Key:", font=("Arial", 13), background='grey', fg='white')
        self.shootKeyLabel.place(x=160, y=280, anchor='w')

        if INCR_POWER == "<KeyPress-Up>":
            self.SelectArrowKeys()
        else:
            self.SelectWASD()

    def SelectWASD(self):
        '''Selects WASD controls'''
        if not self.curControlsWASD:
            self.wasdLabel.config(background='dark green')
            self.arrowkeysLabel.config(background='grey')
            self.curControlsWASD = True

    def SelectArrowKeys(self):
        '''Selects arrow key controls'''
        if self.curControlsWASD:
            self.curControlsWASD = False
            self.arrowkeysLabel.config(background='dark green')
            self.wasdLabel.config(background='grey')

    def ChangeBall(self, direction):
        '''Changes the ball design'''
        self.currentBallDesignIndex += direction
        if self.currentBallDesignIndex < 0:
            self.currentBallDesignIndex = len(self.ballDesigns) - 1
        elif self.currentBallDesignIndex >= len(self.ballDesigns):
            self.currentBallDesignIndex = 0

        self.ballImg = Image.open(self.ballDesigns[self.currentBallDesignIndex])
        self.ballImgTk = ImageTk.PhotoImage(self.ballImg)
        self.ball.config(image=self.ballImgTk)

        #Modify the data.json file by updating the ball design to the newly selected file path
        with open('data.json', 'r') as f:
            data = json.load(f)
        settings = data['settings']
        settings['BALL_DESIGN'] = self.ballDesigns[self.currentBallDesignIndex]
        with open('data.json', 'w') as f:
            json.dump(data, f, indent=4)

    def BackToMainMenu(self):
        '''Returns to the main menu'''
        self.backButton.destroy()
        self.canvas.destroy()
        self.ball.destroy()
        self.leftArrow.destroy()
        self.rightArrow.destroy()
        self.wasdLabel.destroy()
        self.wasdText.destroy()
        self.arrowkeyText.destroy()
        self.arrowkeysLabel.destroy()
        self.bosskeyDropBox.destroy()
        self.shootKeyDropBox.destroy()
        self.bossKeyLabel.destroy()
        self.shootKeyLabel.destroy()

        self.UpdateSettingsFile()
        MainMenu(window)

    def UpdateSettingsFile(self):
        '''Updates the settings file with the new settings'''
        global SKY_COLOUR, INCR_POWER, DECR_POWER, RIGHT_ANGLE_START, LEFT_ANGLE_START, RIGHT_ANGLE_STOP, LEFT_ANGLE_STOP, SHOOT_BALL, BASKETBALL_DESIGN, ballImg
        
        #Update controls based on curControlsWASD
        if self.curControlsWASD:
            INCR_POWER = '<KeyPress-w>'
            DECR_POWER = '<KeyPress-s>'
            RIGHT_ANGLE_START = '<KeyPress-d>'
            LEFT_ANGLE_START = '<KeyPress-a>'
            RIGHT_ANGLE_STOP = '<KeyRelease-d>'
            LEFT_ANGLE_STOP = '<KeyRelease-a>'
        else:
            INCR_POWER = '<KeyPress-Up>'
            DECR_POWER = '<KeyPress-Down>'
            RIGHT_ANGLE_START = '<KeyPress-Right>'
            LEFT_ANGLE_START = '<KeyPress-Left>'
            RIGHT_ANGLE_STOP = '<KeyRelease-Right>'
            LEFT_ANGLE_STOP = '<KeyRelease-Left>'

        
        bossKey.UpdateBossKey(self.bossKey.get())

        if self.shootKey.get() == "Space":
            SHOOT_BALL = '<KeyPress-space>'
        else:
            SHOOT_BALL = '<KeyPress-Return>'
        
        with open('data.json', 'r') as f:
            data = json.load(f)
        settings = data['settings']
        settings['BALL_DESIGN'] = self.ballDesigns[self.currentBallDesignIndex]
        settings['INCR_POWER'] = INCR_POWER
        settings['DECR_POWER'] = DECR_POWER
        settings['RIGHT_ANGLE_START'] = RIGHT_ANGLE_START
        settings['LEFT_ANGLE_START'] = LEFT_ANGLE_START
        settings['RIGHT_ANGLE_STOP'] = RIGHT_ANGLE_STOP
        settings['LEFT_ANGLE_STOP'] = LEFT_ANGLE_STOP
        settings['SHOOT_BALL'] = SHOOT_BALL
        settings['BOSS_KEY'] = self.bossKey.get()

        with open('data.json', 'w') as f:
            json.dump(data, f, indent=4)

        SKY_COLOUR = settings['SKY_COLOUR']
        INCR_POWER = settings['INCR_POWER']
        DECR_POWER = settings['DECR_POWER']
        RIGHT_ANGLE_START = settings['RIGHT_ANGLE_START']
        LEFT_ANGLE_START = settings['LEFT_ANGLE_START']
        RIGHT_ANGLE_STOP = settings['RIGHT_ANGLE_STOP']
        LEFT_ANGLE_STOP = settings['LEFT_ANGLE_STOP']
        SHOOT_BALL = settings['SHOOT_BALL']
        BASKETBALL_DESIGN = settings['BALL_DESIGN']

        ballImg = PhotoImage(file=BASKETBALL_DESIGN)

class DropDownMenu:
    def __init__(self, window, level):
        self.window = window
        self.level = level
        self.menu = Canvas(window, width=500, height=350, bg='grey')
        self.menu.place(x=window.winfo_width()/2, y = -100, anchor='n')
        window.after(10, self.AnimateMenu)

    def AnimateMenu(self):
        '''Animates the menu to slide down from the top of the screen'''
        if self.menu.winfo_y() < 100:
            self.menu.place(y=self.menu.winfo_y() + 10)
            self.window.after(10, self.AnimateMenu)

    def CreateWinButtons(self):
        '''Creates the menu buttons to display on level completion'''
        levelCompletedLabel = Label(self.menu, text="Level " + str(self.level.levelSettings.levelNumber) + " Completed", font=("Arial", 20), background='grey', fg='white')
        levelCompletedLabel.place(x=250, y=10, anchor='n')

        timeLeftLabel = Label(self.menu, text="Time Left: " + str(round(self.level.timer.startTime, 2)), font=("Arial", 20), background='grey', fg='white')
        timeLeftLabel.place(x=250, y=50, anchor='n')

        badgeLabel = Label(self.menu, text="Badge: ", font=("Arial", 20), background='grey', fg='white')
        badgeLabel.place(x=250, y=90, anchor='n')
        
        newResult = ""
        #if time is less than gold time, display gold badge
        if self.level.timer.startTime < 0.01:
            badgeLabel.config(text="Badge: BUZZER BEATER!", fg='red')
            newResult = 'Buzzer Beater'
        elif self.level.timer.startTime < self.level.scoreSettings.silverTime:
            badgeLabel.config(text="Badge: Bronze!", fg='#CD7F32')
            newResult = 'Bronze'
        elif self.level.timer.startTime < self.level.scoreSettings.goldTime and self.level.timer.startTime > self.level.scoreSettings.silverTime:
            badgeLabel.config(text="Badge: Silver!", fg='#DCDCDC')
            newResult = 'Silver'
        elif self.level.timer.startTime > self.level.scoreSettings.goldTime:
            badgeLabel.config(text="Badge: Gold!", fg='gold')
            newResult = 'Gold'

        data = json.load(open('data.json'))
        ranking = ['Bronze', 'Silver', 'Gold', 'Buzzer Beater']
        curResult = data['accounts'][str(data['accounts']['currentAccount'])]['stages']['stage' + str(self.level.levelSettings.stageNumber)]['level' + str(self.level.levelSettings.levelNumber)]
        newHighScore = False


        if curResult == "N/A":
            newHighScore = True
        else:
            if ranking.index(newResult) > ranking.index(curResult):
                newHighScore = True


        if newHighScore:
            data['accounts'][str(data['accounts']['currentAccount'])]['stages']['stage' + str(self.level.levelSettings.stageNumber)]['level' + str(self.level.levelSettings.levelNumber)] = newResult
            data['accounts'][str(data['accounts']['currentAccount'])][newResult] += 1
            if curResult != "N/A":
                data['accounts'][str(data['accounts']['currentAccount'])][curResult] -= 1
            with open('data.json', 'w') as outfile:
                json.dump(data, outfile, indent=4)

            Label(self.menu, text="New High Score!", font=("Arial", 20), background='grey', fg='white').place(x=250, y=130, anchor='n')

        if self.level.levelSettings.levelNumber != 5:
            nextLevelButton = Button(self.menu, text="Next Level", command=lambda: self.NextLevel(), width=20, height=1, font=("Arial", 20), background='grey', fg='white')
            nextLevelButton.place(x=250, y=170, anchor='n')

        restartButton = Button(self.menu, text="Restart", command=lambda: self.ResetLevel(), width=20, height=1, font=("Arial", 20), background='grey', fg='white')
        restartButton.place(x=250, y=220, anchor='n')

        quitButton = Button(self.menu, text="Quit", command=lambda: self.Quit(), width=20, height=1, font=("Arial", 20), background='grey', fg='white')
        quitButton.place(x=250, y=270, anchor='n')

    def CreateLoseButtons(self):
        '''Creates the menu buttons to display when losing a level'''
        levelFailedLabel = Label(self.menu, text="Level " + str(self.level.levelSettings.levelNumber) + " Failed", font=("Arial", 20), background='grey', fg='white')
        levelFailedLabel.place(x=250, y=10, anchor='n')

        loseLabel = Label(self.menu, text="Timer ran out", font=("Arial", 20), background='grey', fg='white')
        loseLabel.place(x=250, y=50, anchor='n')
        
        restartButton = Button(self.menu, text="Restart", command=lambda: self.ResetLevel(), width=20, height=1, font=("Arial", 20), background='grey', fg='white')
        restartButton.place(x=250, y=220, anchor='n')

        quitButton = Button(self.menu, text="Quit", command=lambda: self.Quit(), width=20, height=1, font=("Arial", 20), background='grey', fg='white')
        quitButton.place(x=250, y=270, anchor='n')

    def NextLevel(self):
        '''Loads the next level'''
        self.menu.destroy()
        self.level.ClearLevel()
        nextLevelNum = self.level.levelSettings.levelNumber
        curStage = stages[self.level.levelSettings.stageNumber - 1]
        nextLevel = curStage.levels[nextLevelNum]
        nextLevel.LoadLevel()

    def ResetLevel(self):
        '''Resets the level'''
        self.menu.destroy()
        self.level.ResetLevel(event=None)

    def Quit(self):
        '''Quits the game and goes to the level select menu'''
        self.menu.destroy()
        self.level.RestartTimer()  
        self.level.ClearLevel()
        LevelSelectMenu(window=window, stages=stages)

    def destroy(self):
        '''Destroys the menu'''
        self.menu.destroy()

#========================================================================

#Settings classes =======================================================

class ScoreSettings:
    '''Stores the score settings for a level'''
    def __init__(self, time, goldTime, silverTime, bronzeTime):
        self.time = time
        self.goldTime = goldTime
        self.silverTime = silverTime
        self.bronzeTime = bronzeTime

class LevelSettings:
    '''Stores the level settings for a level'''
    def __init__(self, levelNumber, levelName, levelDescription, stageNumber):
        self.levelNumber = levelNumber
        self.levelName = levelName
        self.levelDescription = levelDescription
        self.stageNumber = stageNumber

class HoopSettings:
    '''Stores the hoop settings for a level'''
    def __init__(self, x, y, height):
        self.x = x
        self.y = y
        self.height = height

class GroundSettings:
    '''Stores the ground settings for a level'''
    def __init__(self, width, height, groundColour, skyColour):
        self.width = width
        self.height = height
        self.groundColour = groundColour
        self.skyColour = skyColour

class ArrowSettings:
    '''Stores the arrow settings for a level'''
    def __init__(self, initialAngle, minAngle, maxAngle):
        self.initialAngle = initialAngle
        self.minAngle = minAngle
        self.maxAngle = maxAngle
        
class BasketballSettings:
    '''Stores the basketball settings for a level'''
    def __init__(self, startX, startY, mass, gravity, timeDelay, friction, skyColour):
        self.startX = startX
        self.startY = startY
        self.mass = mass
        self.gravity = gravity
        self.timeDelay = timeDelay
        self.friction = friction
        self.skyColour = skyColour

class PowerBarSettings:
    '''Stores the power bar settings for a level'''
    def __init__(self, noFillColour, fillColour, width, height, x, y):
        self.noFillColour = noFillColour
        self.fillColour = fillColour
        self.width = width
        self.height = height
        self.x = x
        self.y = y

class ObstacleSettings:
    '''Stores the obstacle settings for a level'''
    def __init__(self, obstacles):
        self.obstacles = obstacles

#========================================================================

#Level components =======================================================

class Timer:
    '''Timer class for the level'''
    def __init__(self, widget):
        self.widget = widget
        self.startTime = 10

class Ground:
    def __init__(self, width, height, colour):
        self.width = width
        self.height = height
        self.colour = colour

    def CreateGround(self):
        '''Creates the ground'''
        groundObj = Label(window, bg=self.colour, width=self.width, height=self.height)
        #place ground to cover lower part of screen
        groundObj.place(x=0, y=window.winfo_height() - self.height)
        self.widget = groundObj

class Arrow:
    def __init__(self, myBasketball, level):

        self.basketball = myBasketball
        self.level = level

        self.fireAngle = 0
        self.repeatTracker = None

        self.repeatTimeDelay = 50
        self.repeatTimeDelayMax = 50
        self.repeatTimeDelayMin = 10
        self.repeatTimeDelayChange = 3
        self.keyPressed = False

    def CreateArrow(self):
        '''Creates the arrow'''
        global arrowImg
        arrowObj = Label(window, image=arrowImg, background=self.level.skyColour)
        arrowObj.place(x=0, y=0)
        self.widget = arrowObj

    def CreateAngleControls(self):
        '''Creates the angle controls for the arrow'''
        buttonFrame = Frame(window, bg=self.level.groundColour)
        buttonFrame.pack(side=BOTTOM)
        self.buttonFrame = buttonFrame

        rotateLeftButton = Button(buttonFrame, text="<",width=3, height=1, font=("Arial", 20), background='grey', fg='white')
        rotateLeftButton.pack(side=LEFT, anchor='w', pady=20, padx=50)
        rotateLeftButton.bind('<ButtonPress-1>', lambda event: self.StartRotateArrowLeft(usingKey=False))
        rotateLeftButton.bind('<ButtonRelease-1>', lambda event: self.StopRotateArrow())

        #Bind A and D keys to rotate the arrow
        window.bind(LEFT_ANGLE_START, lambda event: self.StartRotateArrowLeft(usingKey=True))
        window.bind(RIGHT_ANGLE_START, lambda event: self.StartRotateArrowRight(usingKey=True))
        window.bind(LEFT_ANGLE_STOP, lambda event: self.StopRotateArrow())
        window.bind(RIGHT_ANGLE_STOP, lambda event: self.StopRotateArrow())

        rotateRightButton = Button(buttonFrame, text=">", width=3, height=1, font=("Arial", 20), background='grey', fg='white')
        rotateRightButton.pack(side=RIGHT, anchor='e', pady=20, padx=50)
        rotateRightButton.bind('<ButtonPress-1>', lambda event: self.StartRotateArrowRight(usingKey=False))
        rotateRightButton.bind('<ButtonRelease-1>', lambda event: self.StopRotateArrow())

        self.rotateLeftButton = rotateLeftButton
        self.rotateRightButton = rotateRightButton

    def StopRotateArrow(self):
        '''Stops rotating the arrow'''
        self.keyPressed = False
        self.repeatTimeDelay = self.repeatTimeDelayMax
        #when controlling arrow angle, the speed at which the angle turns increases the longer it is held down
        # this is done by decreasing the repeatTimeDelay variable
        #when the key/buton is released, the repeatTimeDelay is reset to the max value
        if self.repeatTracker is not None:
            window.after_cancel(self.repeatTracker)
            self.repeatTracker = None

    def StartRotateArrowLeft(self, usingKey = False):
        '''Starts rotating the arrow left'''
        if usingKey:
            #if using keyboard keys,bug occurs with creating multiple window.after and program bugs out
            #so keyPressed is used to prevent this
            self.keyPressed = True
            self.RotateArrow('Left')
            if not self.keyPressed:
                self.repeatTracker = window.after(self.repeatTimeDelay, self.StartRotateArrowLeft)
        else:
            #if on screen controls are used, just play normally
            self.RotateArrow('Left')
            self.repeatTracker = window.after(self.repeatTimeDelay, self.StartRotateArrowLeft)

    def StartRotateArrowRight(self, usingKey = False):
        '''Starts rotating the arrow right'''
        if usingKey:
            self.keyPressed = True
            self.RotateArrow('Right')
            if not self.keyPressed:
                self.repeatTracker = window.after(self.repeatTimeDelay, self.StartRotateArrowRight)
        else:
            self.RotateArrow('Right')
            self.repeatTracker = window.after(self.repeatTimeDelay, self.StartRotateArrowRight)

    def DestroyArrows(self):
        '''Destroys the arrow and its controls'''
        self.buttonFrame.destroy()
        self.rotateLeftButton.destroy()
        self.rotateRightButton.destroy()
        self.widget.destroy()

    def SetArrowAngle(self, angle):
        '''Sets the angle of the arrow'''
        self.fireAngle = angle
        arrow = Image.open('images/Arrow.png')
        arrow = arrow.rotate(self.fireAngle, expand=True)
        arrowTk = ImageTk.PhotoImage(arrow)

        #distance between the arrow and the ball
        distance = 80
        
        #ball center
        ballCenterX = self.basketball.ballWidget.winfo_x() + self.basketball.ballWidget.winfo_width() / 2
        ballCenterY = self.basketball.ballWidget.winfo_y() + self.basketball.ballWidget.winfo_height() / 2

        #convert to radians
        fireAngleRadians = math.radians(self.fireAngle)

        #move the arrow so that it is in the correct position relative to the ball dpeending on the angle
        arrowOffsetX = distance * math.cos(fireAngleRadians)
        arrowOffsetY = -distance * math.sin(fireAngleRadians) #use minus because y coordinates increase as you go down the screen

        arrowCenterX = ballCenterX + arrowOffsetX
        arrowCenterY = ballCenterY + arrowOffsetY

        #x coordinates of objects are calculated based on the top left of the screen so get x and y of arrow based on arrow center
        arrowX = arrowCenterX - arrowTk.width() / 2
        arrowY = arrowCenterY - arrowTk.height() / 2

        self.widget.config(image=arrowTk)
        self.widget.image = arrowTk
        self.widget.place(x=arrowX, y=arrowY)

    def RotateArrow(self, direction):
        '''Rotates the arrow'''
        if self.repeatTimeDelay > self.repeatTimeDelayMin:
            self.repeatTimeDelay -= self.repeatTimeDelayChange
            #increase speed at which arrow turns the longer it is held down

        if direction == 'Left':
            if self.fireAngle < self.level.maxAngle:
                self.fireAngle += 5  #bigger = faster
        elif direction == 'Right':
            if self.fireAngle > self.level.minAngle:
                self.fireAngle -= 5

        self.SetArrowAngle(self.fireAngle)

class PowerBar:
    def __init__(self, noFillColour, fillColour, width, height, x, y):
        self.noFillColour = noFillColour
        self.fillColour = fillColour
        self.width = width
        self.height = height
        self.x = x
        self.y = y

        self.power = 0.5 * MAX_FORCE

    def UpdateRectanglePosition(self, event):
        '''Updates the position of the power bar rectangle when the mouse is dragged'''
        y = min(event.y, self.height) #if mouse is dragged off the power bar, set y to the height of the power bar
        #powerBarObj is a canvas so set coordinates based on power given
        #start at self.x bottom left
        #bottom right is self.width
        #top is y
        self.powerBarObj.coords(self.powerBarFilling, self.x, y, self.width, self.height)

        self.power = ((self.powerBarObj.coords(self.powerBarFilling)[3] - self.powerBarObj.coords(self.powerBarFilling)[1])/self.height) * MAX_FORCE

    def SetPower(self, power):
        '''Sets the power of the power bar'''
        self.power = power
        #self.power/MAX_FORCE gives the percentage of the power bar that should be filled
        self.powerBarObj.coords(self.powerBarFilling, self.x, self.height - ((self.power/MAX_FORCE) * self.height), self.width, self.height)

    def IncreasePower(self):
        '''Increases the power of the power bar'''
        if self.power < MAX_FORCE:
            self.SetPower(self.power + 1)

    def DecreasePower(self):
        '''Decreases the power of the power bar'''
        if self.power > 0:
            self.SetPower(self.power - 1)

    def CreatePowerBar(self):
        '''Creates the power bar'''
        powerBarObj = Canvas(window, width=self.width, height=self.height, bg='grey')
        powerBarObj.pack(side=LEFT, padx=10)
        powerBarFilling = powerBarObj.create_rectangle(self.x, self.height/2, self.width, self.height, fill='red')
        powerBarObj.bind('<B1-Motion>', self.UpdateRectanglePosition)
        self.powerBarObj = powerBarObj
        self.powerBarFilling = powerBarFilling

        #bind w and s keys to change the power
        window.bind(INCR_POWER, lambda event: self.IncreasePower())
        window.bind(DECR_POWER, lambda event: self.DecreasePower())

    def destroy(self):
        '''Destroys the power bar'''
        self.powerBarObj.destroy()

class Obstacle:
    '''Obstacle class for the level'''
    def __init__(self, widget, x, y, name, frictionCoefficient):
        self.widget = widget
        self.x = x
        self.y = y
        self.name = name 
        self.frictionCoefficient = frictionCoefficient

class LevelObstacle:
    #level obstacle is used to define obstacles specific to levels
    #these are added to the level's obstacles array
    #and loaded in at the start when a level is loaded
    def __init__(self, x, y, width, height, background, name, frictionCoefficient):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.background = background
        self.name = name 
        self.frictionCoefficient = frictionCoefficient

class BasketballHoop:
    def __init__(self, x, y, height, level):
        self.x = x
        self.y = y
        self.height = height
        self.level = level

        self.basketball = None

    def UpdateHoopScorePosition(self):
        '''Updates the hoop score position'''
        self.basketball = self.level.basketball
        self.basketball.hoopScorePos = self.hoopScorePos
    
    def createHoopObjects(self):
        '''Creates the hoop objects'''
        global obstacles

        hoopObj = Label(window, image=hoop, background=self.level.skyColour)
        hoopObj.place(x=self.x, y=self.y)
        window.update()

        #create hoop components with rectangles
        hoopLeftEdge = Label(window, bg=self.level.skyColour) #invisible
        hoopLeftEdge.place(x=hoopObj.winfo_x() - 7, y=self.y, width=7, height=20)
        hoopStand = Label(window, bg='black')
        hoopStand.place(x=hoopObj.winfo_x() + hoopObj.winfo_width() + 15, y=self.y + 100, width=10, height=window.winfo_height() - self.y)
        hoopBackboard = Label(window, bg='grey')
        hoopBackboard.place(x=hoopObj.winfo_x() + hoopObj.winfo_width() - 2, y=self.y - self.height, width=40, height=self.height + 120)
        hoopScorePos = Label(window, bg='yellow')
        hoopScorePos.place(x=hoopObj.winfo_x() + 50, y=self.y + 3, width=15, height=1)

        #dont add the hoopStand as obstacle, just visual object which the ball can roll over
        hoopLeftEdgeObstacle = Obstacle(widget=hoopLeftEdge, x=hoopLeftEdge.winfo_x(), y=hoopLeftEdge.winfo_y(), name="hoopLeftEdge", frictionCoefficient=1)
        hoopBackboardObstacle = Obstacle(widget=hoopBackboard, x=hoopBackboard.winfo_x(), y=hoopBackboard.winfo_y(), name="hoopBackboard", frictionCoefficient=1)
        hoopScorePosObstacle = Obstacle(widget=hoopScorePos, x=hoopScorePos.winfo_x(), y=hoopScorePos.winfo_y(), name="hoopScorePosition", frictionCoefficient=1)

        self.hoopScorePos = hoopScorePosObstacle
        self.hoopStand = hoopStand
        self.hoopObj = hoopObj
        self.hoopLeftEdge = hoopLeftEdge
        self.hoopBackboard = hoopBackboard

        #hoopScorePos will be used individiually to check if the ball is colliding with it
        #so it is not actually an obstacle which the ball can collide with
        obstacles.append(hoopLeftEdgeObstacle)
        obstacles.append(hoopBackboardObstacle)

    def Destroy(self):
        '''Destroys the hoop objects'''
        self.hoopScorePos.widget.destroy()
        self.hoopBackboard.destroy()
        self.hoopLeftEdge.destroy()
        self.hoopStand.destroy()
        self.hoopObj.destroy()

class Basketball:
    def __init__(self, startX, startY, mass, gravity, timeDelay, friction, level, skyColour):
        self.mass = mass
        self.gravity = gravity
        self.timeDelay = timeDelay
        self.friction = friction
        self.startX = startX
        self.startY = startY
        self.level = level

        self.velocityX = 0
        self.velocityY = 0
        self.direction = 1
        self.accelerationX = 0
        self.accelerationY = 0

        self.weight = self.mass * self.gravity
        self.verticalResF = self.weight
        self.horizontalResF = 0
        self.impulseX = 0
        self.impulseY = 0
        self.frictionCoefficient = 0.5
        self.scoringFix = False
        self.physicsID = None

        self.hoopScorePos = None

        self.lastCollision = None
        self.collisionCooldown = 0.25
        self.lastCollisionTime = None

        self.skyColour = skyColour

    def SetPhysicsMemory(self):
        '''Save the current physics values so that they can be restored later'''
        self.memVelocityX = self.velocityX
        self.memVelocityY = self.velocityY
        self.memAccelerationX = self.accelerationX
        self.memAccelerationY = self.accelerationY
        self.memHorizontalResF = self.horizontalResF
        self.memVerticalResF = self.verticalResF

    def LoadPhysicsMemory(self):
        '''load stored physics values to replace the current ones'''
        self.velocityX = self.memVelocityX
        self.velocityY = self.memVelocityY
        self.accelerationX = self.memAccelerationX
        self.accelerationY = self.memAccelerationY
        self.horizontalResF = self.memHorizontalResF
        self.verticalResF = self.memVerticalResF

    def ResetBallPosition(self):
        '''Resets the ball position'''
        #reset the velocity of the ball to 0 and place it back at where it should start
        self.velocityX = 0
        self.velocityY = 0
        
        self.ballWidget.place(x=self.startX, y=self.startY)
        #if we are in a level, bind the shoot button, otherwise the ball is in the main menu and should instead be controlled by animations
        #hence the check of self.level is not None
        if self.level is not None:
            window.bind(SHOOT_BALL, self.BallClicked)

    def CreateBasketball(self):
        '''Creates the basketball'''
        ballObj = Label(window, image=ballImg, background=self.skyColour)
        if self.level is not None:
            window.bind(SHOOT_BALL, self.BallClicked)
        ballObj.place(x=self.startX, y=self.startY)
        self.ballWidget = ballObj

    def ApplyForce(self, force, angle, isImpulse):
        '''Applies a force to the ball'''
        #impulse means the force is only there for a short period of time
        #immediately after force is applied, the impulse is reset to 0
        #non impulse force is like weight, it always acts on the object
        if isImpulse:
            self.impulseX += force * math.cos(angle)
            self.impulseY -= force * math.sin(angle)
        else:
            self.horizontalResF += force * math.cos(angle)
            self.verticalResF += force * math.sin(angle)

    def BallPhysics(self, obstacles):
        '''Calculates the physics of the ball'''
        if (self.level is not None and not self.level.isPaused) or self.level is None:
            ballObj = self.ballWidget
            groundObj = self.groundWidget

            x = ballObj.winfo_x()
            y = ballObj.winfo_y()

            #a new frame occurs every self.timeDelay seconds
            #right now self.timeDelay is 0.0075 seconds
            #so frame rate is 1/0.0075 = 133.33 frames per second

            #rearranging f=ma to get a=f/m to calculate acceleration in both directions
            self.accelerationX = self.horizontalResF / self.mass
            self.accelerationY = self.verticalResF / self.mass

            #v = u + at to calculate velocity in both directions at the current frame and add impulse at the end because thats the only way it seems to work realistically
            self.velocityX = self.velocityX + (self.accelerationX * self.timeDelay) + self.impulseX
            self.velocityY = self.velocityY + (self.accelerationY * self.timeDelay) + self.impulseY

            #reset impulse here
            self.impulseX = 0
            self.impulseY = 0

            #s = ut + 1/2(at^2) to calculate the distance travelled in both directions during the time between the previous frame and the new frame 
            x += (self.velocityX * (self.timeDelay * 100)) + (0.5 * self.accelerationX * (math.pow((self.timeDelay), 2)))
            y += (self.velocityY * (self.timeDelay * 100)) + (0.5 * self.accelerationY * (math.pow((self.timeDelay), 2)))

            #if the ball goes below the ground level, set it to the ground son it gives fof the illusion of rolling (assuming it doesnt have the velocity to bounce back up)
            if y + ballObj.winfo_height() > groundObj.winfo_y():
                y = groundObj.winfo_y() - ballObj.winfo_height()
                self.velocityY *= -self.friction

            #check if the hoopScorePos actually exists
            #if the ball was on the main menu, it wouldnt exist so error would have been thrown
            if self.hoopScorePos is not None:
                if self.IsColliding(self.hoopScorePos.widget):
                    if self.scoringFix == False:
                        #Ignroe the first one because the ball happens to be colliding with the hoopScorePos when it is first created
                        self.scoringFix = True
                    else:
                        #scoring fix check makes sure this is the actual collision we want
                        #check if the level isnt yet over to avoid repeated code
                        if self.level.levelOver == False:
                            ballCenterY = self.ballWidget.winfo_y() + (self.ballWidget.winfo_height() / 2)
                            rectangleTopY = self.hoopScorePos.widget.winfo_y()

                            #use buffer to make it easier to score
                            #buffer is a range around the hoopScorePos where the ball will be considered to have scored
                            buffer = 50

                            if ballCenterY >= rectangleTopY - buffer:
                                print("Scored")   
                                self.level.HoopScored()
                            self.level.levelOver = True

            #hoopScorePos check is done, now check the rest of the obstacles and the ball should bounce off these
            for obstacleNotWidget in obstacles:
                #lastCollision checks and time of last collision checks are there to prevent the ball from colliding with the same object multiple times in a row
                #without this, the ball may phase into an obstacle and get stuck
                if self.IsColliding(obstacleNotWidget.widget) and (self.lastCollision != obstacleNotWidget or time.time() - self.lastCollisionTime > self.collisionCooldown):
                    if obstacleNotWidget.name != "hoopScorePosition":
                        obstacle = obstacleNotWidget.widget

                        ballCenterX = self.ballWidget.winfo_x() + (self.ballWidget.winfo_width() / 2)
                        ballCenterY = self.ballWidget.winfo_y() + (self.ballWidget.winfo_height() / 2)
                        obstacleCenterX = obstacle.winfo_x() + (obstacle.winfo_width() / 2)
                        obstacleCenterY = obstacle.winfo_y() + (obstacle.winfo_height() / 2)

                        if(ballCenterX < obstacleCenterX):
                            #the ball is to the left of the obstacle
                            self.velocityX = -abs(self.velocityX)
                        elif(ballCenterX > obstacleCenterX):
                            #the ball is to the right of the obstacle
                            self.velocityX = abs(self.velocityX)
                        elif(ballCenterY < obstacleCenterY):
                            #the ball is above the obstacle
                            self.velocityY = -abs(self.velocityY)
                        elif(ballCenterY > obstacleCenterY):
                            #the ball is below the obstacle
                            self.velocityY = abs(self.velocityY)
                            
                    #apply friction to the ball based on the obstacle it collided with
                    self.velocityX *= obstacleNotWidget.frictionCoefficient
                    self.velocityY *= obstacleNotWidget.frictionCoefficient

                    #set the details of the collision with the ball to make sure it doesnt collide with this obstacle IMMEDIATELY after
                    #cooldown time is only 0.25 seconds which is realistic based on maximum speeds of the ball
                    self.lastCollision = obstacleNotWidget
                    self.lastCollisionTime = time.time()
                    time.sleep(0.01)

            #finally after all physics calculations done, place the ball at the new position
            self.ballWidget.place(x=x, y=y)
            #schedule the same function to run again after self.timeDelay seconds
            #window.after takes time in milliseconds so multiply by 1000
            self.physicsID = window.after(int(self.timeDelay * 1000), lambda: self.BallPhysics(obstacles))

    def IsColliding(self, obstacle):
        '''Checks if the ball is colliding with an obstacle'''
        ballX = self.ballWidget.winfo_x()
        ballY = self.ballWidget.winfo_y()
        ballWidth = self.ballWidget.winfo_width()
        ballHeight = self.ballWidget.winfo_height()

        obstacleX = obstacle.winfo_x()
        obstacleY = obstacle.winfo_y()
        obstacleWidth = obstacle.winfo_width()
        obstacleHeight = obstacle.winfo_height()

        totalBallX = ballX + ballWidth #total is basically the x coordinate of the right side of the ball
        totalBallY = ballY + ballHeight #this is basically the y coordinate of the bottom of the ball
        totalObstacleX = obstacleX + obstacleWidth #same as above but for the obstacle
        totalObstacleY = obstacleY + obstacleHeight

        buffer = 10 #used buffer again to make it easier to collide with obstacles

        #series of calculations to check if the ball is overlapping with the obstacle
        if (totalBallX < obstacleX - buffer or totalBallY < obstacleY - buffer or totalObstacleX < ballX - buffer or totalObstacleY < ballY - buffer):
            return False
        else:
            return True

    def UpdateReferences(self, myPowerBar, myArrow):
        '''Updates the references of the ball to power bar and arrow'''
        self.powerBar = myPowerBar
        self.arrow = myArrow

    def UpdateGroundReference(self, myGround):
        '''Updates the reference of the ball to the ground'''
        self.groundWidget = myGround.widget

    def BallClicked(self, event):
        '''Shoots the ball when the shoot key is clicked'''
        if self.powerBar is None or self.arrow is None:
            return
        force = self.powerBar.power #get the power from the power bar
        print(force)
        angle = self.arrow.fireAngle #get the angle from the arrow
        self.BallPhysics(obstacles) #start the physics of the ball
        self.ApplyForce(force, math.radians(angle), True) #apply the force to the ball

        self.level.rememberAngle = self.arrow.fireAngle
        self.level.rememberPower = self.powerBar.power #keep details of force and angle in memory in case they are used in other code?
        self.level.ballShot = True
        self.level.CreateResetButton() #reset button for the level only appears when the ball is in motion
        #Destroy everything
        self.powerBar.destroy()
        window.unbind(SHOOT_BALL)
        self.arrow.DestroyArrows()

    def Destroy(self):
        '''Destroys the ball'''
        #check if physics are actually active before cancelling
        if self.physicsID is not None:
            window.after_cancel(self.physicsID)
        self.ballWidget.destroy()

class LoadingImage:
    '''Class for the loading image'''
    def __init__(self, window, fromX, fromY, toX, toY, lifetime, speed):
        self.window = window
        self.fromX = fromX
        self.fromY = fromY
        self.toX = toX
        self.toY = toY
        self.lifetime = lifetime
        self.rotation = 0
        self.speed = speed

        self.loadingImg = Image.open('images/LoadingCircle.png')
        self.loadingImgTk = ImageTk.PhotoImage(self.loadingImg)
        self.loading = Label(window, image=self.loadingImgTk, background=SKY_COLOUR, width=80, height=80)
        self.loading.place(x=fromX, y=fromY)
        self.startTime = time.time()

    def PlayLoadingAnimation(self):
        '''Plays the loading animation'''
        #after lifetime passes destroy the icon
        if time.time() - self.startTime > self.lifetime:
            self.loading.destroy()
        else:
            #rotate loading icon so the user is aware the prorgam has not crashed and is just loading
            self.rotation = (self.rotation + 20) % 360 #20 is the amount of degrees to rotate by
            rotatedImg = self.loadingImg.rotate(self.rotation, expand=True)
            self.loadingImgTk = ImageTk.PhotoImage(rotatedImg)
            self.loading.config(image=self.loadingImgTk)

            #move loading icon towards desired position
            differenceX = self.toX - self.loading.winfo_x()
            differenceY = self.toY - self.loading.winfo_y()
            x = (differenceX / self.speed) + self.loading.winfo_x()
            y = (differenceY / self.speed) + self.loading.winfo_y()
            self.loading.place(x=x, y=y)

            #continue function for recursion
            self.window.after(50, self.PlayLoadingAnimation)

#========================================================================

Level1 = Level(
    ScoreSettings(time=5, goldTime=4, silverTime=3, bronzeTime=2),
    LevelSettings(levelNumber=1, levelName="Dunk", levelDescription="Dunk the ball into the hoop", stageNumber=1),
    HoopSettings(x=800, y=300, height=100),
    GroundSettings(width=700, height=100, groundColour='green', skyColour='sky blue'),
    ArrowSettings(initialAngle=360, minAngle=180, maxAngle=360),
    BasketballSettings(startX=700, startY=120, mass=10, gravity=35, timeDelay=0.0075, friction=0.55, skyColour='sky blue'),
    PowerBarSettings(noFillColour='grey', fillColour='red', width=35, height=200, x=0, y=0),
    ObstacleSettings(obstacles=[])
)

Level2 = Level(
    ScoreSettings(time=10, goldTime=8.5, silverTime=6, bronzeTime=5),
    LevelSettings(levelNumber=2, levelName="3-Pointer", levelDescription="Make the 3 points", stageNumber=1),
    HoopSettings(x=1000, y=300, height=100),
    GroundSettings(width=700, height=100, groundColour='green', skyColour='sky blue'),
    ArrowSettings(initialAngle=5, minAngle=0, maxAngle=180),
    BasketballSettings(startX=600, startY=555, mass=10, gravity=35, timeDelay=0.0075, friction=0.55, skyColour='sky blue'),
    PowerBarSettings(noFillColour='grey', fillColour='red', width=35, height=200, x=0, y=0),
    ObstacleSettings(obstacles=[])
)

Level3 = Level(
    ScoreSettings(time=10, goldTime=8.5, silverTime=6, bronzeTime=5),
    LevelSettings(levelNumber=3, levelName="Half Court", levelDescription="Make the half-court shot", stageNumber=1),
    HoopSettings(x=1000, y=300, height=100),
    GroundSettings(width=700, height=100, groundColour='green', skyColour='sky blue'),
    ArrowSettings(initialAngle=5, minAngle=0, maxAngle=180),
    BasketballSettings(startX=450, startY=555, mass=10, gravity=35, timeDelay=0.0075, friction=0.55, skyColour='sky blue'),
    PowerBarSettings(noFillColour='grey', fillColour='red', width=35, height=200, x=0, y=0),
    ObstacleSettings(obstacles=[])
)

Level4 = Level(
    ScoreSettings(time=10, goldTime=8.5, silverTime=6, bronzeTime=5),
    LevelSettings(levelNumber=4, levelName="Full Court", levelDescription="Make the full-court shot", stageNumber=1),
    HoopSettings(x=1000, y=300, height=100),
    GroundSettings(width=700, height=100, groundColour='green', skyColour='sky blue'),
    ArrowSettings(initialAngle=5, minAngle=0, maxAngle=180),
    BasketballSettings(startX=50, startY=555, mass=10, gravity=35, timeDelay=0.0075, friction=0.55, skyColour='sky blue'),
    PowerBarSettings(noFillColour='grey', fillColour='red', width=35, height=200, x=0, y=0),
    ObstacleSettings(obstacles=[])
)

Level5 = Level(
    ScoreSettings(time=10, goldTime=8.5, silverTime=6, bronzeTime=5),
    LevelSettings(levelNumber=5, levelName="Behind the hoop", levelDescription="Score from behind the hoop", stageNumber=1),
    HoopSettings(x=600, y=300, height=100),
    GroundSettings(width=700, height=100, groundColour='green', skyColour='sky blue'),
    ArrowSettings(initialAngle=170, minAngle=0, maxAngle=180),
    BasketballSettings(startX=900, startY=555, mass=10, gravity=35, timeDelay=0.0075, friction=0.55, skyColour='sky blue'),
    PowerBarSettings(noFillColour='grey', fillColour='red', width=35, height=200, x=0, y=0),
    ObstacleSettings(obstacles=[])
)

Level6 = Level(
    ScoreSettings(time=10, goldTime=8.5, silverTime=6, bronzeTime=5),
    LevelSettings(levelNumber=1, levelName="Off the roof", levelDescription="Get it in the hoop from the rooftop", stageNumber=2),
    HoopSettings(x=900, y=400, height=100),
    GroundSettings(width=700, height=100, groundColour='green', skyColour='sky blue'),
    ArrowSettings(initialAngle=5, minAngle=15, maxAngle=165),
    BasketballSettings(startX=200, startY=135, mass=10, gravity=35, timeDelay=0.0075, friction=0.55, skyColour='sky blue'),
    PowerBarSettings(noFillColour='grey', fillColour='red', width=35, height=200, x=0, y=0),
    ObstacleSettings(obstacles=[
        LevelObstacle(
            width=40,
            height=500,
            background='brown',
            x=70,
            y=200,
            name="roof",
            frictionCoefficient=0.55
        ),
        LevelObstacle(
            width=10,
            height=5,
            background='#ADD8E6',
            x=100,
            y=300,
            name="window",
            frictionCoefficient=0.55
        ),
        LevelObstacle(
            width=10,
            height=5,
            background='#ADD8E6',
            x=250,
            y=300,
            name="window",
            frictionCoefficient=0.55
        ),
        LevelObstacle(
            width=7,
            height=10,
            background='#5C4033',
            x=190,
            y=500,
            name="Door",
            frictionCoefficient=0.55
        )
    ])
)

Level7 = Level(
    ScoreSettings(time=10, goldTime=8, silverTime=6, bronzeTime=5),
    LevelSettings(levelNumber=2, levelName="House Layup", levelDescription="Rebound off the house wall into the hoop", stageNumber=2),
    HoopSettings(x=850, y=300, height=100),
    GroundSettings(width=700, height=100, groundColour='green', skyColour='sky blue'),
    ArrowSettings(initialAngle=175, minAngle=100, maxAngle=180),
    BasketballSettings(startX=820, startY=555, mass=10, gravity=35, timeDelay=0.0075, friction=0.55, skyColour='sky blue'),
    PowerBarSettings(noFillColour='grey', fillColour='red', width=35, height=200, x=0, y=0),
    ObstacleSettings(obstacles=[
        LevelObstacle(
            width=40,
            height=500,
            background='brown',
            x=220,
            y=200,
            name="roof",
            frictionCoefficient=0.75
        ),
        LevelObstacle(
            width=10,
            height=5,
            background='#ADD8E6',
            x=250,
            y=300,
            name="window",
            frictionCoefficient=0.55
        ),
        LevelObstacle(
            width=10,
            height=5,
            background='#ADD8E6',
            x=400,
            y=300,
            name="window",
            frictionCoefficient=0.55
        ),
        LevelObstacle(
            width=7,
            height=10,
            background='#5C4033',
            x=340,
            y=500,
            name="Door",
            frictionCoefficient=0.55
        )
    ])
)

Level8 = Level(
    ScoreSettings(time=10, goldTime=8, silverTime=6, bronzeTime=5),
    LevelSettings(levelNumber=3, levelName="Building backboards", levelDescription="Use the skyscraper as a backboard", stageNumber=2),
    HoopSettings(x=320, y=400, height=100),
    GroundSettings(width=700, height=100, groundColour='green', skyColour='sky blue'),
    ArrowSettings(initialAngle=180, minAngle=90, maxAngle=180),
    BasketballSettings(startX=1100, startY=555, mass=10, gravity=35, timeDelay=0.0075, friction=0.55, skyColour='sky blue'),
    PowerBarSettings(noFillColour='grey', fillColour='red', width=35, height=200, x=0, y=0),
    ObstacleSettings(obstacles=[
        LevelObstacle(
            width=18,
            height=500,
            background='grey',
            x=100,
            y=-50,
            name="roof",
            frictionCoefficient=0.75
        ),
        LevelObstacle(
            width=10,
            height=5,
            background='#ADD8E6',
            x=130,
            y=375,
            name="window",
            frictionCoefficient=0.55
        ),
        LevelObstacle(
            width=10,
            height=5,
            background='#ADD8E6',
            x=130,
            y=275,
            name="window",
            frictionCoefficient=0.55
        ),
        LevelObstacle(
            width=10,
            height=5,
            background='#ADD8E6',
            x=130,
            y=175,
            name="window",
            frictionCoefficient=0.55
        ),
        LevelObstacle(
            width=10,
            height=5,
            background='#ADD8E6',
            x=130,
            y=75,
            name="window",
            frictionCoefficient=0.55
        ),
        LevelObstacle(
            width=10,
            height=5,
            background='#ADD8E6',
            x=130,
            y=-25,
            name="window",
            frictionCoefficient=0.55
        ),
        LevelObstacle(
            width=7,
            height=10,
            background='#5C4033',
            x=140,
            y=500,
            name="Door",
            frictionCoefficient=0.55
        )
    ])
)

Level9 = Level(
    ScoreSettings(time=10, goldTime=8, silverTime=6, bronzeTime=5),
    LevelSettings(levelNumber=4, levelName="Tight space", levelDescription="Bounce the ball off both skycrapers and into the hoop", stageNumber=2),
    HoopSettings(x=450, y=400, height=100),
    GroundSettings(width=700, height=100, groundColour='green', skyColour='sky blue'),
    ArrowSettings(initialAngle=0, minAngle=0, maxAngle=90),
    BasketballSettings(startX=600, startY=555, mass=10, gravity=35, timeDelay=0.0075, friction=0.55, skyColour='sky blue'),
    PowerBarSettings(noFillColour='grey', fillColour='red', width=35, height=200, x=0, y=0),
    ObstacleSettings(obstacles=[
        LevelObstacle(
            width=18,
            height=500,
            background='grey',
            x=250,
            y=-50,
            name="roof",
            frictionCoefficient=0.75
        ),
        LevelObstacle(
            width=10,
            height=5,
            background='#ADD8E6',
            x=280,
            y=375,
            name="window",
            frictionCoefficient=0.55
        ),
        LevelObstacle(
            width=10,
            height=5,
            background='#ADD8E6',
            x=280,
            y=275,
            name="window",
            frictionCoefficient=0.55
        ),
        LevelObstacle(
            width=10,
            height=5,
            background='#ADD8E6',
            x=280,
            y=175,
            name="window",
            frictionCoefficient=0.55
        ),
        LevelObstacle(
            width=10,
            height=5,
            background='#ADD8E6',
            x=280,
            y=75,
            name="window",
            frictionCoefficient=0.55
        ),
        LevelObstacle(
            width=10,
            height=5,
            background='#ADD8E6',
            x=280,
            y=-25,
            name="window",
            frictionCoefficient=0.55
        ),
        LevelObstacle(
            width=7,
            height=10,
            background='#5C4033',
            x=290,
            y=500,
            name="Door",
            frictionCoefficient=0.55
        ),
        LevelObstacle(
            width=18,
            height=500,
            background='grey',
            x=900,
            y=-50,
            name="roof",
            frictionCoefficient=0.75
        ),
        LevelObstacle(
            width=10,
            height=5,
            background='#ADD8E6',
            x=930,
            y=375,
            name="window",
            frictionCoefficient=0.55
        ),
        LevelObstacle(
            width=10,
            height=5,
            background='#ADD8E6',
            x=930,
            y=275,
            name="window",
            frictionCoefficient=0.55
        ),
        LevelObstacle(
            width=10,
            height=5,
            background='#ADD8E6',
            x=930,
            y=175,
            name="window",
            frictionCoefficient=0.55
        ),
        LevelObstacle(
            width=10,
            height=5,
            background='#ADD8E6',
            x=930,
            y=75,
            name="window",
            frictionCoefficient=0.55
        ),
        LevelObstacle(
            width=10,
            height=5,
            background='#ADD8E6',
            x=930,
            y=-25,
            name="window",
            frictionCoefficient=0.55
        ),
        LevelObstacle(
            width=7,
            height=10,
            background='#5C4033',
            x=940,
            y=500,
            name="Door",
            frictionCoefficient=0.55
        ),
    ])
)

Level10 = Level(
    ScoreSettings(time=15, goldTime=12, silverTime=10, bronzeTime=9),
    LevelSettings(levelNumber=5, levelName="Trenches", levelDescription="Bounce your way out of the hole and into the hoop", stageNumber=2),
    HoopSettings(x=200, y=400, height=100),
    GroundSettings(width=700, height=100, groundColour='green', skyColour='sky blue'),
    ArrowSettings(initialAngle=15, minAngle=15, maxAngle=90),
    BasketballSettings(startX=750, startY=555, mass=10, gravity=35, timeDelay=0.0075, friction=0.55, skyColour='sky blue'),
    PowerBarSettings(noFillColour='grey', fillColour='red', width=35, height=200, x=0, y=0),
    ObstacleSettings(obstacles=[
        LevelObstacle(
            width=18,
            height=500,
            background='grey',
            x=600,
            y=150,
            name="roof",
            frictionCoefficient=0.95
        ),
        LevelObstacle(
            width=10,
            height=5,
            background='#ADD8E6',
            x=630,
            y=375,
            name="window",
            frictionCoefficient=0.55
        ),
        LevelObstacle(
            width=10,
            height=5,
            background='#ADD8E6',
            x=630,
            y=275,
            name="window",
            frictionCoefficient=0.55
        ),
        LevelObstacle(
            width=10,
            height=5,
            background='#ADD8E6',
            x=630,
            y=175,
            name="window",
            frictionCoefficient=0.55
        ),
        LevelObstacle(
            width=7,
            height=10,
            background='#5C4033',
            x=640,
            y=500,
            name="Door",
            frictionCoefficient=0.55
        ),
        LevelObstacle(
            width=18,
            height=500,
            background='grey',
            x=900,
            y=-50,
            name="roof",
            frictionCoefficient=0.95
        ),
        LevelObstacle(
            width=10,
            height=5,
            background='#ADD8E6',
            x=930,
            y=375,
            name="window",
            frictionCoefficient=0.55
        ),
        LevelObstacle(
            width=10,
            height=5,
            background='#ADD8E6',
            x=930,
            y=275,
            name="window",
            frictionCoefficient=0.55
        ),
        LevelObstacle(
            width=10,
            height=5,
            background='#ADD8E6',
            x=930,
            y=175,
            name="window",
            frictionCoefficient=0.55
        ),
        LevelObstacle(
            width=10,
            height=5,
            background='#ADD8E6',
            x=930,
            y=75,
            name="window",
            frictionCoefficient=0.55
        ),
        LevelObstacle(
            width=10,
            height=5,
            background='#ADD8E6',
            x=930,
            y=-25,
            name="window",
            frictionCoefficient=0.55
        ),
        LevelObstacle(
            width=7,
            height=10,
            background='#5C4033',
            x=940,
            y=500,
            name="Door",
            frictionCoefficient=0.55
        ),
    ])
)

Level11 = Level(
    ScoreSettings(time=15, goldTime=12, silverTime=10, bronzeTime=9),
    LevelSettings(levelNumber=1, levelName="Welcome to the Moon", levelDescription="Hit the first slam dunk on the moon", stageNumber=3),
    HoopSettings(x=750, y=300, height=100),
    GroundSettings(width=700, height=100, groundColour='#F6F1D5', skyColour='#414a4c'),
    ArrowSettings(initialAngle=360, minAngle=180, maxAngle=360),
    BasketballSettings(startX=700, startY=120, mass=5, gravity=5, timeDelay=0.0075, friction=0.75, skyColour='sky blue'),
    PowerBarSettings(noFillColour='grey', fillColour='red', width=35, height=200, x=0, y=0),
    ObstacleSettings(obstacles=[])
)

Level12 = Level(
    ScoreSettings(time=15, goldTime=2, silverTime=10, bronzeTime=9),
    LevelSettings(levelNumber=2, levelName="Down the crater", levelDescription="Lob the ball down the crater and into the hoop", stageNumber=3),
    HoopSettings(x=800, y=300, height=100),
    GroundSettings(width=700, height=100, groundColour='#F6F1D5', skyColour='#414a4c'),
    ArrowSettings(initialAngle=0, minAngle=0, maxAngle=75),
    BasketballSettings(startX=350, startY=80, mass=5, gravity=5, timeDelay=0.0075, friction=0.75, skyColour='sky blue'),
    PowerBarSettings(noFillColour='grey', fillColour='red', width=35, height=200, x=0, y=0),
    ObstacleSettings(obstacles=[
        LevelObstacle(
            width=50,
            height=500,
            background='#F6F1D5',
            x=0,
            y=150,
            name="crater",
            frictionCoefficient=0.95
        ),
    ])
)

Level13 = Level(
    ScoreSettings(time=15, goldTime=12, silverTime=10, bronzeTime=9),
    LevelSettings(levelNumber=3, levelName="Low Gravi-three", levelDescription="Hit a low-gravity 3 pointer", stageNumber=3),
    HoopSettings(x=1000, y=300, height=100),
    GroundSettings(width=700, height=100, groundColour='#F6F1D5', skyColour='#414a4c'),
    ArrowSettings(initialAngle=5, minAngle=0, maxAngle=180),
    BasketballSettings(startX=450, startY=555, mass=5, gravity=5, timeDelay=0.0075, friction=0.75, skyColour='sky blue'),
    PowerBarSettings(noFillColour='grey', fillColour='red', width=35, height=200, x=0, y=0),
    ObstacleSettings(obstacles=[])
)

Level14 = Level(
    ScoreSettings(time=15, goldTime=12, silverTime=10, bronzeTime=9),
    LevelSettings(levelNumber=4, levelName="Straight up", levelDescription="A low gravity rebound, how hard can it be?", stageNumber=3),
    HoopSettings(x=400, y=300, height=100),
    GroundSettings(width=700, height=100, groundColour='#F6F1D5', skyColour='#414a4c'),
    ArrowSettings(initialAngle=175, minAngle=90, maxAngle=180),
    BasketballSettings(startX=300, startY=555, mass=5, gravity=5, timeDelay=0.0075, friction=0.75, skyColour='sky blue'),
    PowerBarSettings(noFillColour='grey', fillColour='red', width=35, height=200, x=0, y=0),
    ObstacleSettings(obstacles=[
        LevelObstacle(
            name='left wall',
            width=10,
            height=500,
            background='#F6F1D5',
            x=0,
            y=-500,
            frictionCoefficient=0.75
        )
    ])
)

Level15 = Level(
    ScoreSettings(time=15, goldTime=12, silverTime=10, bronzeTime=9),
    LevelSettings(levelNumber=5, levelName="Behind the hoop 2.0", levelDescription="Get it in from behind the hoop, but on a different planet", stageNumber=3),
    HoopSettings(x=200, y=300, height=100),
    GroundSettings(width=700, height=100, groundColour='#F6F1D5', skyColour='#414a4c'),
    ArrowSettings(initialAngle=175, minAngle=90, maxAngle=180),
    BasketballSettings(startX=1000, startY=555, mass=5, gravity=5, timeDelay=0.0075, friction=0.75, skyColour='sky blue'),
    PowerBarSettings(noFillColour='grey', fillColour='red', width=35, height=200, x=0, y=0),
    ObstacleSettings(obstacles=[])
)

stage1 = Stage(name="Court", number=1, levels=[Level1, Level2, Level3, Level4, Level5])
stage2 = Stage(name="City", number=2, levels=[Level6, Level7, Level8, Level9, Level10])
stage3 = Stage(name="Moon", number=3, levels=[Level11, Level12, Level13, Level14, Level15])


stages = []
stages.append(stage1)
stages.append(stage2)
stages.append(stage3)

MainMenu(window)

window.mainloop()

#Cheat code: CTRL T

# hoop = Image.open('images/BasketballHoop.png')
# hoop = hoop.resize((100, 100))
# hoop.save('images/BasketballHoop.png')

# arrow = Image.open('images/Arrow.png')
# if arrow.mode != 'RGBA':
#     arrow = arrow.convert('RGBA')
#arrow.save('images/Arrow.png')