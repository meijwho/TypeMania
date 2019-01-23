#this code is based on the structure of 
#https://github.com/viblo/pymunk/blob/master/examples/deformable.py. 
#write file func from
#https://www.cs.cmu.edu/~112/notes/notes-strings.html
#color wheel from
#https://www.mgxcopy.com/mindshare/2015/05/color-theory-basics/


__docformat__ = "reStructuredText"

import sys
import random
import math
import os
import string

import pygame
from pygame.locals import *
from pygame.color import *

import pymunk
from pymunk import Vec2d, BB
import pymunk.pygame_util
import pymunk.autogeometry

rainbowLst = [(255, 255, 52, 255),\
            (251, 189, 3, 255),\
            (252, 154, 3, 255),\
            (254, 84, 9, 255),\
            (255, 40, 19, 255),\
            (228, 6, 187, 255),\
            (135, 2, 176, 255),\
            (62, 2, 165, 255),\
            (3, 72, 255, 255),\
            (4, 147, 207, 255),\
            (1, 188, 113, 255),\
            (143, 228, 6, 255)]

def writeFile(path, contents):
    with open(path, "wt") as f:
        f.write(contents)


def generateBall(space,color):
    mass = 10
    moment = pymunk.moment_for_circle(mass, 3, 10)
    body = pymunk.Body(mass, moment)
    body.position = (8,60)
    shape = pymunk.Circle(body, 5)
    shape.friction = .1
    shape.elasticity = 0.1
    shape.color = color
    space.add(body, shape)
    #print("?",shape.body.position.x,shape.body.position.y)
    return shape
    
#generate letterpath
def generate_geometry(surface, space,color,rainbowMode):
    #if shapes generted overlap, merge together
    for s in space.shapes:
        if hasattr(s, "generated") and s.generated:
            space.remove(s)
    #color sampling
    def sample_func(point):
        try:
            p = int(point.x), int(point.y)
            color = surface.get_at(p)
            return color.hsla[1] # use lightness
        #just in case crashsis
        except:
            return 0 

    line_set = pymunk.autogeometry.PolylineSet()
    #Add a line segment to a polyline set
    def segment_func(v0, v1):
        line_set.collect_segment(v0, v1)
    
    pymunk.autogeometry.march_soft(
        BB(-20,-20,570,870), 300, 300, 90, segment_func, sample_func)
    #smoothing
    for polyline in line_set:
        line = pymunk.autogeometry.simplify_curves(polyline, 0)
        #generate path line by line
        for i in range(len(line)):
            p1 = line[i]
            if i == len(line)-1:
                p2 = line[0]
            else:
                p2 = line[i+1]
            shape = pymunk.Segment(space.static_body, p1, p2, 1)
            shape.set_neighbors(p1,p1)
            shape.friction = 0
            shape.elasticity = 0.5
            if rainbowMode == True:
                shape.color = THECOLORS["black"]
            else:
                shape.color = color
            shape.collision_type
            shape.generated = True
            space.add(shape) 

class Letter(pygame.sprite.Sprite):
    def __init__(self,pos,angle, input,color):
        pygame.sprite.Sprite.__init__(self)
        self.input = input
        self.font = pygame.font.Font(None, 180)
        self.color = color
        self.output = self.font.render(self.input, 1,self.color)
        self.pos = pos
        self.angle = angle
        self.rotated = pygame.transform.rotate(self.output, self.angle)
        self.mask  = pygame.mask.from_surface(self.rotated)
        self.rect = self.output.get_rect(topleft = (self.pos[0]-40,self.pos[1]-50))
        
    def update(self, surface):
        surface.blit(self.rotated, (self.pos[0]-40,self.pos[1]-50))

    def collide(self, blockGroup):
        canPut = True
        #print(self.rect)
        #self.rect.move_ip(offset)
        collidable = pygame.sprite.collide_mask
        collisions = pygame.sprite.spritecollide(self, blockGroup, False,collidable)
        #print(collisions, collidable)
        if collisions:
            canPut= False
        return canPut

class Block(pygame.sprite.Sprite):
    def __init__(self,surface, pos,width,height,color):
        pygame.sprite.Sprite.__init__(self)
        self.pos = pos
        self.width = width
        self.height = height
        self.color = color
        self.block = pygame.Surface((self.width,self.height))
        self.img = pygame.transform.scale(pygame.image.load('block.png').convert_alpha(), (self.width,self.height))
        self.block.fill(self.color[1])
        self.mask  = pygame.mask.from_surface(self.img)
        self.rect = self.img.get_rect(topleft=(pos[0],pos[1]))

    def update(self, surface):
        surface.blit(self.img, (self.pos[0],self.pos[1]))
        surface.blit(self.block, (self.pos[0],self.pos[1]))

class levelTamplate(object):
    def __init__(self,screen,letterLeft,time):
        self.screen = screen
        self.letterLeft = letterLeft
        self.time = time
    
    def drawPlayButton(self):
        return pygame.draw.polygon(self.screen, THECOLORS["black"], 
                            [(265, 40),(265, 12),(285,26)])
    def drawBackButton(self):
        backImg = pygame.image.load('back.png').convert_alpha()
        return self.screen.blit(backImg,(420, 12))
    def drawEraseButton(self):
        eraserImg = pygame.transform.scale(pygame.image.load('erase.png').convert_alpha(), (30,30))
        return self.screen.blit(eraserImg, (50,12))
    def drawBlankButton(self):
        blankImg = pygame.transform.scale(pygame.image.load('blank.png').convert_alpha(), (30,30))
        return self.screen.blit(blankImg, (150,12))
        
    def drawBottomScreen(self):
        titleFont = pygame.font.Font("Helvetica.dfont", 15)
        numberFont = pygame.font.Font("Helvetica.dfont", 20)
        titleText = ["NO. LETTERS LEFT",
                    "TIME",
                    ]
        numberText = [str(self.letterLeft),
                    str(self.time),
                    ]
        x1 = 70
        for line in titleText:
            titleText = titleFont.render(line, 1, THECOLORS["black"])
            self.screen.blit(titleText, (x1, 790))
            x1 += 300
        x2 = 140
        for line in numberText:
            numberText = titleFont.render(line, 1, THECOLORS["black"])
            self.screen.blit(numberText, (x2, 810))
            x2 += 250

def gameIntro(screen, clock, space, canvas, color, rainbowMode):
    draw_options = pymunk.pygame_util.DrawOptions(screen)
    pymunk.pygame_util.positive_y_is_up = False
    intro = True
    balls = []
    space.gravity = 1,980
    fps = 60

    rainbowLst = [(255, 255, 52, 255),\
            (251, 189, 3, 255),\
            (252, 154, 3, 255),\
            (254, 84, 9, 255),\
            (255, 40, 19, 255),\
            (228, 6, 187, 255),\
            (135, 2, 176, 255),\
            (62, 2, 165, 255),\
            (3, 72, 255, 255),\
            (4, 147, 207, 255),\
            (1, 188, 113, 255),\
            (143, 228, 6, 255)]
    pipeC= random.choice(rainbowLst)

    while intro == True:
        screen.fill(color[3])
        #draw starter pipe
        if rainbowMode == False:
            startPipe = pygame.draw.polygon(canvas, color[0], [(1,70),(1,45),(62,103),(50,119)])
            endPipe =  pygame.draw.polygon(canvas, color[0], [(410,800),(410,782),(550,782),(550,800)])
        else:
            startPipe = pygame.draw.polygon(canvas, pipeC, [(1,70),(1,45),(62,103),(50,119)])
            endPipe =  pygame.draw.polygon(canvas, pipeC, [(410,800),(410,782),(550,782),(550,800)])

        startingLetters = pygame.sprite.Group()
        if rainbowMode ==False:
            T = startingLetters.add(Letter((88,146),0,"T",color[0]))
            Y = startingLetters.add(Letter((112,233),0,"Y",color[0]))
            P = startingLetters.add(Letter((135,321),0,"P",color[0]))
            E = startingLetters.add(Letter((139,410),90,"E",color[0]))
            M = startingLetters.add(Letter((229,456),0,"M",color[0]))
            A = startingLetters.add(Letter((225,548),90,"A",color[0]))
            N = startingLetters.add(Letter((313,610),0,"N",color[0]))
            I = startingLetters.add(Letter((369,693),0,"I",color[0]))
            A2 = startingLetters.add(Letter((368,757),90,"A",color[0]))
        else:
            T = startingLetters.add(Letter((88,146),0,"T",(254, 84, 9)))
            Y = startingLetters.add(Letter((112,233),0,"Y",(255, 40, 19)))
            P = startingLetters.add(Letter((135,321),0,"P",(254, 84, 9)))
            E = startingLetters.add(Letter((139,410),90,"E",(135, 2, 176)))
            M = startingLetters.add(Letter((229,456),0,"M",(62, 2, 165)))
            A = startingLetters.add(Letter((225,548),90,"A",(3, 72, 255)))
            N = startingLetters.add(Letter((313,610),0,"N",(4, 147, 207)))
            I = startingLetters.add(Letter((369,693),0,"I",(143, 228, 6)))
            A2 = startingLetters.add(Letter((368,757),90,"A",(255, 255, 52)))
                
        startingLetters.update(canvas)
        generate_geometry(canvas, space,color[0],rainbowMode)

        screen.blit(canvas, (0,0))
        space.debug_draw(draw_options)
        #draw game button
        playImg = pygame.image.load('play.png').convert_alpha()
        playButton = screen.blit(playImg,(350, 300))
        #draw setting button
        settingImg = pygame.image.load('setting.png').convert_alpha()
        settingButton = screen.blit(settingImg,(350, 400))
        #draw exit button
        exitImg = pygame.image.load('exit.png').convert_alpha()
        exitButton = screen.blit(exitImg,(350, 500))

        for event in pygame.event.get():
            if event.type==MOUSEBUTTONDOWN:
                if playButton.collidepoint(event.pos):
                    intro = False
                    canvas.fill(color[3])
                    generate_geometry(canvas, space,color[0],rainbowMode)
                    levels(screen, clock, space, canvas, color,rainbowMode)
                elif settingButton.collidepoint(event.pos):
                    intro = False
                    canvas.fill(color[3])
                    generate_geometry(canvas, space,color[0],rainbowMode)
                    settingPg(screen, clock, space, canvas, color,rainbowMode)
                    
                elif exitButton.collidepoint(event.pos):
                    sys.exit(0)
            
            elif event.type == QUIT or \
                event.type == KEYDOWN and event.key == K_ESCAPE:  
                sys.exit(0)

        pygame.display.flip()
        space.step(1./fps)
        clock.tick(fps)
        pygame.display.set_caption("Type Mania")

def settingPg(screen, clock, space, canvas, color, rainbowMode):

    draw_options = pymunk.pygame_util.DrawOptions(screen)
    pymunk.pygame_util.positive_y_is_up = False
    settin = True
    space.gravity = 1,980
    fps = 60
    while settin == True:

        screen.fill(color[3])

        startingLetters = pygame.sprite.Group()
        A = startingLetters.add(Letter((150,210),0,"A",color[0]))
                
        startingLetters.update(canvas)
        generate_geometry(canvas, space,color[0],rainbowMode)
        

        screen.blit(canvas, (0,0))
        space.debug_draw(draw_options)
        #draw wheel
        letterWheelImg =  pygame.transform.scale(pygame.image.load('colorwheele.png').convert_alpha(),(150,150))
        letterMask = pygame.mask.from_surface(letterWheelImg)
        letterWheelImg.get_rect(topleft = (2500, 150))
        letterWheel = screen.blit(letterWheelImg,(350, 150))
        
        blockWheelImg =  pygame.transform.scale(pygame.image.load('colorwheele.png').convert_alpha(),(150,150))
        blockMask = pygame.mask.from_surface(blockWheelImg)
        blockWheelImg.get_rect(topleft = (350, 350))
        blockWheel = screen.blit(blockWheelImg,(350, 350))

        ballWheelImg =  pygame.transform.scale(pygame.image.load('colorwheele.png').convert_alpha(),(150,150))
        ballMask = pygame.mask.from_surface(ballWheelImg)
        ballWheelImg.get_rect(topleft = (350, 550))
        ballWheel = screen.blit(ballWheelImg,(350, 550))

        blockSample = pygame.draw.rect(screen, color[1],(120,380,100,80))
        ballSample = pygame.draw.circle(screen, color[2],(160,610),30)

        backImg = pygame.image.load('back.png').convert_alpha()
        backButton = screen.blit(backImg,(420, 12))
        if rainbowMode ==False:
            rainbowImg = pygame.image.load('rainbowoff.png').convert_alpha()
        else:
            rainbowImg = pygame.image.load('rainbowon.png').convert_alpha()
        rainbowButton = screen.blit(rainbowImg,(110,280))

        mousePosition = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type==MOUSEBUTTONDOWN:
                if letterWheel.collidepoint(event.pos):
                    print(screen.get_at(mousePosition))
                    color[0] = (screen.get_at(mousePosition))[0:3]
                elif blockWheel.collidepoint(event.pos):
                    color[1] = (screen.get_at(mousePosition))[0:3]
                elif ballWheel.collidepoint(event.pos):
                    color[2] = (screen.get_at(mousePosition))[0:3]
                elif rainbowButton.collidepoint(event.pos):
                    rainbowMode = not rainbowMode
                    
                elif backButton.collidepoint(event.pos):
                    settin = False
                    canvas.fill(color[3])
                    generate_geometry(canvas, space,color[0],rainbowMode)
                    gameIntro(screen, clock, space, canvas, color,rainbowMode)
            
            elif event.type == QUIT or \
                event.type == KEYDOWN and event.key == K_ESCAPE:  
                sys.exit(0)

        pygame.display.flip()
        space.step(1./fps)
        clock.tick(fps)
        pygame.display.set_caption("Type Mania")
        
def levels(screen, clock, space, canvas, color,rainbowMode):
    draw_options = pymunk.pygame_util.DrawOptions(screen)
    pymunk.pygame_util.positive_y_is_up = False
    levelselect = True

    rainbowLst = [(255, 255, 52, 255),\
            (251, 189, 3, 255),\
            (252, 154, 3, 255),\
            (254, 84, 9, 255),\
            (255, 40, 19, 255),\
            (228, 6, 187, 255),\
            (135, 2, 176, 255),\
            (62, 2, 165, 255),\
            (3, 72, 255, 255),\
            (4, 147, 207, 255),\
            (1, 188, 113, 255),\
            (143, 228, 6, 255)]
    pipeC= random.choice(rainbowLst)

    space.gravity = 1,980
    fps = 100
    while levelselect == True:
        screen.fill(color[3])
        #draw starter pipe
        if rainbowMode == False:
            startPipe = pygame.draw.polygon(canvas, color[0], [(1,80),(1,45),(112,223),(100,239)])
            endPipe =  pygame.draw.polygon(canvas, color[0], [(275,600),(275,582),(570,582),(570,600)])
        else:
            startPipe = pygame.draw.polygon(canvas, pipeC, [(1,80),(1,45),(112,223),(100,239)])
            endPipe =  pygame.draw.polygon(canvas, pipeC, [(275,600),(275,582),(570,582),(570,600)])


        screen.blit(canvas, (0,0))
        space.debug_draw(draw_options)
        #draw game button
        lv1Img = pygame.image.load('lv1.png').convert_alpha()
        lv1Button = screen.blit(lv1Img,(380, 200))

        lv2Img = pygame.image.load('lv2.png').convert_alpha()
        lv2Button = screen.blit(lv2Img,(380, 300))

        lv3Img = pygame.image.load('lv3.png').convert_alpha()
        lv3Button = screen.blit(lv3Img,(380, 400))

        backImg = pygame.image.load('back.png').convert_alpha()
        backButton = screen.blit(backImg,(380, 600))
            
        startingLetters = pygame.sprite.Group()
        if rainbowMode == False:
            L = startingLetters.add(Letter((125,267),0,"L",color[0]))
            E = startingLetters.add(Letter((185,342),0,"E",color[0]))
            V = startingLetters.add(Letter((251,422),90,"V",color[0]))
            E2 = startingLetters.add(Letter((185,475),0,"E",color[0]))
            L2 = startingLetters.add(Letter((252,550),0,"L",color[0]))
        else:
            L = startingLetters.add(Letter((125,267),0,"L",(254, 84, 9)))
            E = startingLetters.add(Letter((185,342),0,"E",(255, 40, 19)))
            V = startingLetters.add(Letter((251,422),90,"V",(228, 6, 187)))
            E2 = startingLetters.add(Letter((185,475),0,"E",(135, 2, 176)))
            L2 = startingLetters.add(Letter((252,550),0,"L",(62, 2, 165)))
        startingLetters.update(canvas)
        generate_geometry(canvas, space,color[0],rainbowMode)
            
        for event in pygame.event.get():
            if event.type==MOUSEBUTTONDOWN:
                if lv1Button.collidepoint(event.pos):
                    levelselect = False
                    canvas.fill(color[3])
                    generate_geometry(canvas, space,color[0],rainbowMode)
                    level1(screen, clock, space, canvas, color,rainbowMode)
                elif lv2Button.collidepoint(event.pos):
                    levelselect = False
                    canvas.fill(color[3])
                    generate_geometry(canvas, space,color[0],rainbowMode)
                    level2(screen, clock, space, canvas, color,rainbowMode)
                elif lv3Button.collidepoint(event.pos):
                    levelselect = False
                    canvas.fill(color[3])
                    generate_geometry(canvas, space,color[0],rainbowMode)
                    level3(screen, clock, space, canvas, color,rainbowMode)
                elif backButton.collidepoint(event.pos):
                    levelselect = False
                    canvas.fill(color[3])
                    generate_geometry(canvas, space,color[0],rainbowMode)
                    gameIntro(screen, clock, space, canvas, color,rainbowMode)
            elif event.type == QUIT or \
                event.type == KEYDOWN and event.key == K_ESCAPE:  
                sys.exit(0)

        pygame.display.flip()
        space.step(1./fps)
        clock.tick(fps)
        pygame.display.set_caption("Type Mania")

def level1(screen, clock, space, canvas, color,rainbowMode): 
    fps = 90        
    draw_options = pymunk.pygame_util.DrawOptions(screen)
    pymunk.pygame_util.positive_y_is_up = False
    
    lv1 = True

    timer = 0
    timing2 = False
    timer2 = 0
    timing = True
    #flag when to check win
    check = False
    canPlace = True
    #document the ball on the screen
    totalBall = 0
    balls = []
    bx = 0
    by = 0
    
    #document the letters and their position on the screen
    path = []
    visited = set()
    #documents the number of letters used
    letterLeft = 20
    countDict = {'A':0,'B':0,'C':0,'D':0,'E':0,'F':0,'G':0,\
                    'H':0,'I':0,'J':0,'K':0,'L':0,'M':0,'N':0,\
                    'O':0,'P':0,'Q':0,'R':0,'S':0,'T':0,'U':0,\
                    'V':0,'W':0,'X':0,'Y':0,'Z':0,}
    rainbowLst = [(255, 255, 52, 255),\
            (251, 189, 3, 255),\
            (252, 154, 3, 255),\
            (254, 84, 9, 255),\
            (255, 40, 19, 255),\
            (228, 6, 187, 255),\
            (135, 2, 176, 255),\
            (62, 2, 165, 255),\
            (3, 72, 255, 255),\
            (4, 147, 207, 255),\
            (1, 188, 113, 255),\
            (143, 228, 6, 255)]
    rColor = 0
    pipeC= random.choice(rainbowLst)
    #initialize ball
    space.gravity = 0,980
    enter = "A"
    angle = 0
    
    (a,b) = random.choice([(90,20),(20,150)])
    if (a,b)==(90,20):
        (x,y) = (480,random.randint(135,770))
    elif (a,b)==(20,150):
        (x,y) = (random.randint(0,480),730)
    print(x,y,a,b)

    while lv1 == True:
        screen.fill(color[3])
        #draw starter pipe
        #------customize-------
        if rainbowMode==False:
            startPipe = pygame.draw.polygon(canvas, color[0], [(-5,70),(-5,45),(62,103),(50,119)])
            endPipe =  pygame.draw.rect(canvas, color[0],(x,y,a,b))
        else:
            startPipe = pygame.draw.polygon(canvas, pipeC, [(-5,70),(-5,45),(62,103),(50,119)])
            endPipe =  pygame.draw.rect(canvas, pipeC,(x,y,a,b))
        #----------------------

        if timing == True:
            timer += 1
            time = timer//30

        if timing2 == True:
            print(timer2)
            timer2 += 1
        if timer2 > 1:
            check = True

        screen.blit(canvas, (0,0))
        space.debug_draw(draw_options)

        levelBasic = levelTamplate(screen,letterLeft,time)
        backButton = levelBasic.drawBackButton()
        playButton = levelBasic.drawPlayButton()
        eraseButton = levelBasic.drawEraseButton()
        blankButton = levelBasic.drawBlankButton()
        levelBasic.drawBottomScreen()


        for ball in balls:
            bx = ball.body.position.x
            by = ball.body.position.y

        #display the letter under mouse
        
        mousePosition = pygame.mouse.get_pos()
        if rainbowMode == False:
            curLetter = Letter(mousePosition,angle, enter,color[0])
        else:
            curLetter = Letter(mousePosition,angle, enter,rainbowLst[rColor%(len(rainbowLst))])
        for event in pygame.event.get():
            
            #quit
            if event.type == QUIT or \
                event.type == KEYDOWN and event.key == K_ESCAPE:  
                sys.exit(0)
            #draw letter only when letterLeft >0
            #and each letter cannot be used more than twice
            elif event.type == KEYDOWN:
                if event.key == K_a and countDict['A']<2: enter = 'A'
                elif event.key == K_b and countDict["B"]<2:enter = 'B'
                elif event.key == K_c and countDict["C"]<2:enter = 'C'            
                elif event.key == K_d and countDict["D"]<2:enter = 'D'
                elif event.key == K_e and countDict["E"]<2:enter = 'E'
                elif event.key == K_f and countDict["F"]<2:enter = 'F'
                elif event.key == K_g and countDict["G"]<2:enter = 'G'
                elif event.key == K_h and countDict["H"]<2:enter = 'H'
                elif event.key == K_i and countDict["I"]<2:enter = 'I'
                elif event.key == K_j and countDict["J"]<2:enter = 'J'
                elif event.key == K_k and countDict["K"]<2:enter = 'K'
                elif event.key == K_l and countDict["L"]<2:enter = 'L'
                elif event.key == K_m and countDict["M"]<2:enter = 'M'
                elif event.key == K_n and countDict["N"]<2:enter = 'N'
                elif event.key == K_o and countDict["O"]<2:enter = 'O'
                elif event.key == K_p and countDict["P"]<2:enter = 'P'
                elif event.key == K_q and countDict["Q"]<2:enter = 'Q'
                elif event.key == K_r and countDict["R"]<2:enter = 'R'
                elif event.key == K_s and countDict["S"]<2:enter = 'S'
                elif event.key == K_t and countDict["T"]<2:enter = 'T'
                elif event.key == K_u and countDict["U"]<2:enter = 'U'
                elif event.key == K_v and countDict["V"]<2:enter = 'V'
                elif event.key == K_w and countDict["W"]<2:enter = 'W'
                elif event.key == K_x and countDict["X"]<2:enter = 'X'
                elif event.key == K_y and countDict["Y"]<2:enter = 'Y'
                elif event.key == K_z and countDict["Z"]<2:enter = 'Z'
                elif event.key == K_RIGHT:
                    angle -= 90
                elif event.key == K_LEFT:
                    angle += 90
                    #rotated = curLetter.rotate(90)
                    #curLetter.output = rotated
                elif event.key == K_4:
                    pygame.image.save(screen, "TypeMania.png")
                    content = ""
                    for line in path:
                        content+= ("\n"+str(line))
                    writeFile("letterlist.txt",content)
                elif event.key == K_2:
                    (x,y,a,b) = (372,730,20,150)
                    check = False
                    timer2 = 0
                    #timing = True
                    #timing2  = False
                    space.remove(balls, space.bodies)
                    
                    balls = []
                    path =[]
                    canvas.fill(color[3])
                    letterLeft = 20
                    for letter in countDict:
                        countDict[letter]=0
                    for s in space.shapes:
                        if hasattr(s, "generated") and s.generated:
                            space.remove(s)
                    startingLetters = pygame.sprite.Group()
                    L = startingLetters.add(Letter((75, 145),0,"L",color[0]))
                    U = startingLetters.add(Letter((135, 220),0,"U",color[0]))
                    P = startingLetters.add(Letter((176, 300),0,"P",color[0]))
                    E = startingLetters.add(Letter((179, 390),90,"E",color[0]))
                    L2 = startingLetters.add(Letter((249, 452),0,"L",color[0]))
                    Y = startingLetters.add(Letter((298, 528),0,"Y",color[0]))
                    Y2 = startingLetters.add(Letter((327,617),0,"Y",color[0]))
                    I = startingLetters.add(Letter((353, 682),0,"I",color[0]))
                    I2 = startingLetters.add(Letter((337, 756),-90,"I",color[0]))
                    letterLeft = 11
                    startingLetters.update(canvas)
                    generate_geometry(canvas, space,color[0],rainbowMode)
                        
             
            elif event.type == MOUSEBUTTONDOWN:
                #click on playButton
                if playButton.collidepoint(event.pos):
                    totalBall += 10
                    for i in range(10):
                        ballShape = generateBall(space,color[2])
                        balls.append(ballShape) 
                    canPlace = False 
                    timing  = False
                    timing2 = True
                    print("timing2",timing2)

                #back to level menu
                elif backButton.collidepoint(event.pos):               
                    #remove ball for levels page
                    space.remove(balls, space.bodies)
                    balls = []
                    lv1 = False
                    canvas.fill(color[3])
                    generate_geometry(canvas, space,color[0],rainbowMode)      
                    levels(screen, clock, space, canvas, color,rainbowMode) 
                #redo all
                elif blankButton.collidepoint(event.pos):
                    canPlace = True
                    check = False
                    timer2 = 0
                    timing2 = False
                    space.remove(balls, space.bodies)
                    balls = []
                    path =[]
                    rColor = 0
                    canvas.fill(color[3])
                    letterLeft = 20
                    for letter in countDict:
                        countDict[letter]=0
                    for s in space.shapes:
                        if hasattr(s, "generated") and s.generated:
                            space.remove(s)
                #erase the previous one
                elif eraseButton.collidepoint(event.pos):
                    if len(path)>0:
                        erasedLetter = path.pop()[0]
                        countDict[erasedLetter]-=1
                        canvas.fill(color[3])
                        letterLeft += 1
                        rColor-=1
                        for s in space.shapes:
                            if hasattr(s, "generated") and s.generated:
                                space.remove(s)
                        for l in path:
                            old = Letter(l[1],l[2], l[0],l[4])
                            old.update(canvas)
                            #old.update(screen)
                    generate_geometry(canvas, space,color[0],rainbowMode)
                #draw letter
                else:
                    if canPlace == True and letterLeft>0  and countDict[curLetter.input]<2:
                        curLetter.update(canvas)
                        generate_geometry(canvas, space,color[0],rainbowMode)
                        #set letter limit
                        countDict[curLetter.input]+=1
                        print(curLetter.input,curLetter.pos,countDict[curLetter.input])
                        letterLeft -= 1
                        #document path
                        path.append((curLetter.input,curLetter.pos,curLetter.angle,countDict[curLetter.input],curLetter.color))
                        rColor +=1
                        #print(path)
        #print(len(space.bodies))
        # if ball goes out of screen, balls remove 
        #larger bb, but set if ball>value, balls remove
        #check win

        for ball in balls:
                if ball.body.position.y<0 or ball.body.position.y>850\
                    or ball.body.position.x<0 or ball.body.position.x>550:
                    space.remove(ball, ball.body)
                    balls.remove(ball)
        #print(check)
        #print("check", check)
        if check == True:
            allStop = checkStop(space)
            print("stop?",allStop)
            if allStop == True:
                ballOnSceen = len(space.bodies)
                space.remove(balls, space.bodies)
                balls = []
                print("!")
                curPg = 1
                lv1 = False
                canvas.fill(color[3])
                generate_geometry(canvas, space,color[0],rainbowMode)
                score = getScore(time, letterLeft, ballOnSceen, totalBall)
                if ballOnSceen < totalBall:   
                    scorePage(screen, clock, space,canvas, color, score,curPg,rainbowMode)
                else:
                    losePage(screen,clock,space,canvas,color,score,curPg,rainbowMode)
                     

        curLetter.update(screen)
        pygame.display.flip()
        space.step(1.0/fps)
        clock.tick(fps)
        pygame.display.set_caption("Type Mania")

def level2(screen, clock, space, canvas, color,rainbowMode): 
    fps = 100                  
    draw_options = pymunk.pygame_util.DrawOptions(screen)
    pymunk.pygame_util.positive_y_is_up = False
    
    lv2 = True

    timer = 0
    timing2 = False
    timer2 = 0
    timing = True
    #flag when to check win
    check = False
    canPlace = True
    #document the ball on the screen
    totalBall = 0
    balls = []
    bx = 0
    by = 0
    
    #document the letters and their position on the screen
    path = []
    visited = set()
    #documents the number of letters used
    letterLeft = 20
    countDict = {'A':0,'B':0,'C':0,'D':0,'E':0,'F':0,'G':0,\
                    'H':0,'I':0,'J':0,'K':0,'L':0,'M':0,'N':0,\
                    'O':0,'P':0,'Q':0,'R':0,'S':0,'T':0,'U':0,\
                    'V':0,'W':0,'X':0,'Y':0,'Z':0,}
    rainbowLst = [(255, 255, 52, 255),\
            (251, 189, 3, 255),\
            (252, 154, 3, 255),\
            (254, 84, 9, 255),\
            (255, 40, 19, 255),\
            (228, 6, 187, 255),\
            (135, 2, 176, 255),\
            (62, 2, 165, 255),\
            (3, 72, 255, 255),\
            (4, 147, 207, 255),\
            (1, 188, 113, 255),\
            (143, 228, 6, 255)]
    rColor = 0
    pipeC= random.choice(rainbowLst)                
    #initialize ball
    space.gravity = 0,980
    enter = "A"
    angle = 0

    horizontal = random.randint(30,200)
    vertical = random.randint(30,300)
    gap = random.choice([horizontal, vertical])
    (ap,bp) = random.choice([(90,20),(20,150)])
    if gap == vertical:
        b2 = random.randint(150,400)
        b1 = 870-b2-gap
        a1 = a2 = random.randint(20,200)
        x1 = x2 = random.randint(135,450-a1)
        y1 = 0
        y2 = b1+gap
        if (ap,bp) == (90,20):
            (xp,yp) = (480, random.randint(b1,780))
        elif (ap,bp) == (20,150):
            (xp,yp) = (random.randint((x2+a2),530),720)
    elif gap == horizontal:
        a2 = random.randint(40,300)
        a1 = 570-a2-gap
        b1=b2= random.randint(20,200)
        x1 = 0
        x2 = a1+gap
        y1 = y2 = random.randint(120,700-b1)
        if (ap,bp) == (90,20):
            (xp,yp) = (480, random.randint(y1+b1,780))
        elif (ap,bp) == (20,150):
            (xp,yp) = (random.randint(10,530),720)
    
    while lv2 == True:
        screen.fill(color[3])

        if timing == True:
            timer += 1
            time = timer//30

        if timing2 == True:
            #print(timer2)
            timer2 += 1
        if timer2 > 1:
            check = True

        screen.blit(canvas, (0,0))
        space.debug_draw(draw_options)

        #draw starter pipe
        if rainbowMode == False:
            #print((xp,yp,ap,bp),(x1,y1,a1,b1),(x2,y2,a2,b2))
            startPipe = pygame.draw.polygon(canvas, color[0], [(-5,70),(-5,45),(62,103),(50,119)])
            endPipe =  pygame.draw.rect(canvas, color[0], (xp,yp,ap,bp))
        else:
            startPipe = pygame.draw.polygon(canvas, pipeC, [(-5,70),(-5,45),(62,103),(50,119)])
            endPipe =  pygame.draw.rect(canvas, pipeC, (xp,yp,ap,bp))
        #draw block
        block1 = Block(screen, (x1,y1),a1,b1,color)
        block1.update(screen)
        block2 = Block(screen,(x2,y2),a2,b2,color)
        block2.update(screen)
        blocks = []
        blocks.append(block1)
        blocks.append(block2)
        blockGroup = pygame.sprite.Group(blocks)


        levelBasic = levelTamplate(screen,letterLeft,time)
        backButton = levelBasic.drawBackButton()
        playButton = levelBasic.drawPlayButton()
        eraseButton = levelBasic.drawEraseButton()
        blankButton = levelBasic.drawBlankButton()
        levelBasic.drawBottomScreen()


        for ball in balls:
            bx = ball.body.position.x
            by = ball.body.position.y

        #display the letter under mouse
        
        mousePosition = pygame.mouse.get_pos()
        if rainbowMode == False:
            curLetter = Letter(mousePosition,angle, enter,color[0])
        else:
            curLetter = Letter(mousePosition,angle, enter,rainbowLst[rColor%(len(rainbowLst))])
        for event in pygame.event.get():
            
            #quit
            if event.type == QUIT or \
                event.type == KEYDOWN and event.key == K_ESCAPE:  
                sys.exit(0)
            #draw letter only when letterLeft >0
            #and each letter cannot be used more than twice
            elif event.type == KEYDOWN:
                if event.key == K_a and countDict['A']<2: enter = 'A'
                elif event.key == K_b and countDict["B"]<2:enter = 'B'
                elif event.key == K_c and countDict["C"]<2:enter = 'C'            
                elif event.key == K_d and countDict["D"]<2:enter = 'D'
                elif event.key == K_e and countDict["E"]<2:enter = 'E'
                elif event.key == K_f and countDict["F"]<2:enter = 'F'
                elif event.key == K_g and countDict["G"]<2:enter = 'G'
                elif event.key == K_h and countDict["H"]<2:enter = 'H'
                elif event.key == K_i and countDict["I"]<2:enter = 'I'
                elif event.key == K_j and countDict["J"]<2:enter = 'J'
                elif event.key == K_k and countDict["K"]<2:enter = 'K'
                elif event.key == K_l and countDict["L"]<2:enter = 'L'
                elif event.key == K_m and countDict["M"]<2:enter = 'M'
                elif event.key == K_n and countDict["N"]<2:enter = 'N'
                elif event.key == K_o and countDict["O"]<2:enter = 'O'
                elif event.key == K_p and countDict["P"]<2:enter = 'P'
                elif event.key == K_q and countDict["Q"]<2:enter = 'Q'
                elif event.key == K_r and countDict["R"]<2:enter = 'R'
                elif event.key == K_s and countDict["S"]<2:enter = 'S'
                elif event.key == K_t and countDict["T"]<2:enter = 'T'
                elif event.key == K_u and countDict["U"]<2:enter = 'U'
                elif event.key == K_v and countDict["V"]<2:enter = 'V'
                elif event.key == K_w and countDict["W"]<2:enter = 'W'
                elif event.key == K_x and countDict["X"]<2:enter = 'X'
                elif event.key == K_y and countDict["Y"]<2:enter = 'Y'
                elif event.key == K_z and countDict["Z"]<2:enter = 'Z'
                elif event.key == K_RIGHT:
                    angle -= 90
                elif event.key == K_LEFT:
                    angle += 90
                    #rotated = curLetter.rotate(90)
                    #curLetter.output = rotated
                elif event.key == K_4:
                    pygame.image.save(screen, "TypeMania.png")
                    content = ""
                    for line in path:
                        content+= ("\n"+str(line))
                    writeFile("letterlist.txt",content)   
                elif event.key == K_2:
                    (x1,y1,a1,b1) = (279, 0, 168, 485)
                    (x2,y2,a2,b2) = (279, 542, 168, 328)
                    (xp,yp,ap,bp) = (480, 595, 90, 20)
                    check = False
                    timer2 = 0
                    #timing = True
                    #timing2  = False
                    space.remove(balls, space.bodies)
                    balls = []
                    path =[]
                    canvas.fill(color[3])
                    letterLeft = 20
                    for letter in countDict:
                        countDict[letter]=0
                    for s in space.shapes:
                        if hasattr(s, "generated") and s.generated:
                            space.remove(s)
                    startingLetters = pygame.sprite.Group()
                    L = startingLetters.add(Letter((461, 550),180,"L",color[0]))
                    I = startingLetters.add(Letter((352, 564),-90,"I",color[0]))
                    I2 = startingLetters.add(Letter((262, 564),-90,"I",color[0]))
                    L2 = startingLetters.add(Letter((219, 491),0,"L",color[0]))
                    Y = startingLetters.add(Letter((80, 144),0,"Y",color[0]))
                    P = startingLetters.add(Letter((104, 231),0,"P",color[0]))
                    Y2 = startingLetters.add(Letter((109, 320),0,"Y",color[0]))
                    E = startingLetters.add(Letter((150, 430),90,"E",color[0]))
                    P2 = startingLetters.add(Letter((132, 403),0,"P",color[0]))
                    letterLeft = 11
                    startingLetters.update(canvas)
                    generate_geometry(canvas, space,color[0],rainbowMode)                 
                        
            elif event.type == MOUSEBUTTONDOWN:
                #click on playButton
                if playButton.collidepoint(event.pos):
                    totalBall += 10
                    for i in range(10):
                        ballShape = generateBall(space,color[2])
                        balls.append(ballShape)
                    canPlace = False
                    timing  = False
                    timing2 = True
                        
                #back to level menu
                elif backButton.collidepoint(event.pos):               
                    #remove ball for levels page
                    space.remove(balls, space.bodies)
                    balls = []
                    lv2 = False
                    canvas.fill(color[3])
                    generate_geometry(canvas, space,color[0],rainbowMode)      
                    levels(screen, clock, space, canvas, color,rainbowMode) 
                #redo all
                elif blankButton.collidepoint(event.pos):
                    check = False
                    timer2 = 0
                    timing2 = False
                    space.remove(balls, space.bodies)
                    balls = []
                    path =[]
                    rColor = 0
                    canvas.fill(color[3])
                    letterLeft = 20
                    for letter in countDict:
                        countDict[letter]=0
                    for s in space.shapes:
                        if hasattr(s, "generated") and s.generated:
                            space.remove(s)
                #erase the previous one
                elif eraseButton.collidepoint(event.pos):
                    if len(path)>0:
                        erasedLetter = path.pop()[0]
                        countDict[erasedLetter]-=1
                        canvas.fill(color[3])
                        letterLeft += 1
                        rColor-=1
                        for s in space.shapes:
                            if hasattr(s, "generated") and s.generated:
                                space.remove(s)
                        for l in path:
                            old = Letter(l[1],l[2], l[0],l[4])
                            old.update(canvas)
                            old.update(screen)
                    generate_geometry(canvas, space,color[0],rainbowMode)
                #draw letter
                else:
                    if canPlace == True and letterLeft>0  and countDict[curLetter.input]<2 and curLetter.collide(blockGroup)==True:
                        curLetter.update(canvas)
                        generate_geometry(canvas, space, color[0],rainbowMode)
                        #set letter limit
                        countDict[curLetter.input]+=1
                        print(curLetter.input,curLetter.pos,countDict[curLetter.input])
                        letterLeft -= 1
                        #document path
                        path.append((curLetter.input,curLetter.pos,curLetter.angle,countDict[curLetter.input],curLetter.color))
                        rColor +=1
                        #print(path)
        #print(len(space.bodies))
        # if ball goes out of screen, balls remove 
        #larger bb, but set if ball>value, balls remove
        #check win

        for ball in balls:
                if ball.body.position.y<0 or ball.body.position.y>850\
                    or ball.body.position.x<0 or ball.body.position.x>550:
                    space.remove(ball, ball.body)
                    balls.remove(ball)
        #print(check)
        if check == True:
            allStop = checkStop(space)
            if allStop == True:
                ballOnSceen = len(space.bodies)
                space.remove(balls, space.bodies)
                balls = []
                #print("!")
                curPg = 2
                lv2 = False
                canvas.fill(color[3])
                generate_geometry(canvas, space,color[0],rainbowMode)
                score = getScore(time, letterLeft, ballOnSceen, totalBall)
                if ballOnSceen < totalBall:   
                    scorePage(screen, clock, space,canvas, color, score,curPg,rainbowMode)
                else:
                    losePage(screen,clock,space,canvas,color,score,curPg,rainbowMode)
                     

        curLetter.update(screen)
        pygame.display.flip()
        space.step(1./fps)
        clock.tick(fps)
        pygame.display.set_caption("Type Mania")

def level3(screen, clock, space, canvas, color,rainbowMode): 
    fps = 100                  
    draw_options = pymunk.pygame_util.DrawOptions(screen)
    pymunk.pygame_util.positive_y_is_up = False
    
    lv3 = True

    timer = 0
    timing2 = False
    timer2 = 0
    timing = True
    #flag when to check win
    check = False
    canPlace = True
    inDemo = False
    #document the ball on the screen
    totalBall = 0
    balls = []
    bx = 0
    by = 0
    
    #document the letters and their position on the screen
    path = []
    visited = set()
    #documents the number of letters used
    letterLeft = 20
    countDict = {'A':0,'B':0,'C':0,'D':0,'E':0,'F':0,'G':0,\
                    'H':0,'I':0,'J':0,'K':0,'L':0,'M':0,'N':0,\
                    'O':0,'P':0,'Q':0,'R':0,'S':0,'T':0,'U':0,\
                    'V':0,'W':0,'X':0,'Y':0,'Z':0,}
    rainbowLst = [(255, 255, 52, 255),\
            (251, 189, 3, 255),\
            (252, 154, 3, 255),\
            (254, 84, 9, 255),\
            (255, 40, 19, 255),\
            (228, 6, 187, 255),\
            (135, 2, 176, 255),\
            (62, 2, 165, 255),\
            (3, 72, 255, 255),\
            (4, 147, 207, 255),\
            (1, 188, 113, 255),\
            (143, 228, 6, 255)]
    pipeC= random.choice(rainbowLst)
    rColor = 0
    #initialize ball
    space.gravity = 0,980
    enter = "A"
    angle = 0

    vertical = random.randint(30,300)
    gap = vertical
    (ap,bp) = random.choice([(90,20),(20,150)])
    b2 = random.randint(80,400)
    b1 = 870-b2-gap
    a1 = a2 = random.randint(20,200)
    x1 = x2 = random.randint(135,450-a1)
    y1 = 0
    y2 = b1+gap
    if (ap,bp) == (90,20):
        (xp,yp) = (480, random.randint(40,b1))
    elif (ap,bp) == (20,150):
        (xp,yp) = (random.randint((x2+a2),530),-10)
    
    while lv3 == True:
        screen.fill(color[3])
        

        if timing == True:
            timer += 1
            time = timer//30

        if timing2 == True:
            #print(timer2)
            timer2 += 1
        if timer2 > 1:
            if inDemo ==False:
                check = True
            else: 
                #print(timer2)
                if timer2>850:
                    ballOnSceen = len(space.bodies)
                    space.remove(balls, space.bodies)
                    balls = []
                    #print("!")
                    curPg = 3
                    lv3 = False
                    canvas.fill(color[3])
                    generate_geometry(canvas, space,color[0],rainbowMode)
                    score = getScore(time, letterLeft, ballOnSceen, totalBall)
                    if ballOnSceen < totalBall:   
                        scorePage(screen, clock, space,canvas, color, score,curPg,rainbowMode)
                    else:
                        losePage(screen,clock,space,canvas,color,score,curPg,rainbowMode)
                

            

        inverse = pygame.surface.Surface((560,860))
        pygame.draw.rect(inverse,THECOLORS["grey"],(0,0,560,860))
        inverse.set_alpha(80)      
        screen.blit(canvas, (0,0))
        screen.blit(inverse,(275,0))
        space.debug_draw(draw_options)

        #draw starter pipe
        if rainbowMode == False:
            startPipe = pygame.draw.polygon(canvas, color[0], [(-5,70),(-5,45),(62,103),(50,119)])
            endPipe =  pygame.draw.rect(canvas, color[0], (xp,yp,ap,bp))
        else:
            startPipe = pygame.draw.polygon(canvas, pipeC, [(-5,70),(-5,45),(62,103),(50,119)])
            endPipe =  pygame.draw.rect(canvas, pipeC, (xp,yp,ap,bp))

        #draw block
        block1 = Block(screen, (x1,y1),a1,b1,color)
        block1.update(screen)
        block2 = Block(screen,(x2,y2),a2,b2,color)
        block2.update(screen)
        blocks = []
        blocks.append(block1)
        blocks.append(block2)
        blockGroup = pygame.sprite.Group(blocks)

        levelBasic = levelTamplate(screen,letterLeft,time)
        backButton = levelBasic.drawBackButton()
        playButton = levelBasic.drawPlayButton()
        eraseButton = levelBasic.drawEraseButton()
        blankButton = levelBasic.drawBlankButton()
        levelBasic.drawBottomScreen()


        for ball in balls:
            bx = ball.body.position.x
            by = ball.body.position.y

        #display the letter under mouse
        
        mousePosition = pygame.mouse.get_pos()
        if rainbowMode == False:
            curLetter = Letter(mousePosition,angle, enter,color[0])
        else:
            curLetter = Letter(mousePosition,angle, enter,rainbowLst[rColor%(len(rainbowLst))])
        for event in pygame.event.get():
            
            #quit
            if event.type == QUIT or \
                event.type == KEYDOWN and event.key == K_ESCAPE:  
                sys.exit(0)
            #draw letter only when letterLeft >0
            #and each letter cannot be used more than twice
            elif event.type == KEYDOWN:
                if event.key == K_a and countDict['A']<2: enter = 'A'
                elif event.key == K_b and countDict["B"]<2:enter = 'B'
                elif event.key == K_c and countDict["C"]<2:enter = 'C'            
                elif event.key == K_d and countDict["D"]<2:enter = 'D'
                elif event.key == K_e and countDict["E"]<2:enter = 'E'
                elif event.key == K_f and countDict["F"]<2:enter = 'F'
                elif event.key == K_g and countDict["G"]<2:enter = 'G'
                elif event.key == K_h and countDict["H"]<2:enter = 'H'
                elif event.key == K_i and countDict["I"]<2:enter = 'I'
                elif event.key == K_j and countDict["J"]<2:enter = 'J'
                elif event.key == K_k and countDict["K"]<2:enter = 'K'
                elif event.key == K_l and countDict["L"]<2:enter = 'L'
                elif event.key == K_m and countDict["M"]<2:enter = 'M'
                elif event.key == K_n and countDict["N"]<2:enter = 'N'
                elif event.key == K_o and countDict["O"]<2:enter = 'O'
                elif event.key == K_p and countDict["P"]<2:enter = 'P'
                elif event.key == K_q and countDict["Q"]<2:enter = 'Q'
                elif event.key == K_r and countDict["R"]<2:enter = 'R'
                elif event.key == K_s and countDict["S"]<2:enter = 'S'
                elif event.key == K_t and countDict["T"]<2:enter = 'T'
                elif event.key == K_u and countDict["U"]<2:enter = 'U'
                elif event.key == K_v and countDict["V"]<2:enter = 'V'
                elif event.key == K_w and countDict["W"]<2:enter = 'W'
                elif event.key == K_x and countDict["X"]<2:enter = 'X'
                elif event.key == K_y and countDict["Y"]<2:enter = 'Y'
                elif event.key == K_z and countDict["Z"]<2:enter = 'Z'
                elif event.key == K_RIGHT:
                    angle -= 90
                elif event.key == K_LEFT:
                    angle += 90
                    #rotated = curLetter.rotate(90)
                    #curLetter.output = rotated
                elif event.key == K_4:
                    pygame.image.save(screen, "TypeMania.png")
                    content = ""
                    for line in path:
                        content+= ("\n"+str(line))
                    writeFile("letterlist.txt",content)
                elif event.key == K_2:
                    (x1,y1,a1,b1) = (250,0,80,200)
                    (x2,y2,a2,b2) = (250,520,80,460)
                    (xp,yp,ap,bp) = (480,120,90,20)
                    check = False
                    timer2 = 0
                    #timing = True
                    #timing2  = False
                    space.remove(balls, space.bodies)
                    balls = []
                    path =[]
                    canvas.fill(color[3])
                    letterLeft = 20
                    for letter in countDict:
                        countDict[letter]=0
                    for s in space.shapes:
                        if hasattr(s, "generated") and s.generated:
                            space.remove(s)
                    startingLetters = pygame.sprite.Group()
                    L = startingLetters.add(Letter((76, 144),0,"L",color[0]))
                    U = startingLetters.add(Letter((131, 220),0,"U",color[0]))
                    L2 = startingLetters.add(Letter((178, 257),90,"L",color[0]))
                    I = startingLetters.add(Letter((268, 298),90,"I",color[0]))
                    S = startingLetters.add(Letter((355, 267),90,"S",color[0]))
                    Y = startingLetters.add(Letter((371, 165),180,"Y",color[0]))
                    J = startingLetters.add(Letter((393, 149),180,"J",color[0]))
                    I2 = startingLetters.add(Letter((425, 163),90,"I",color[0]))
                    V = startingLetters.add(Letter((308, 273),-90,"V",color[0]))
                    W = startingLetters.add(Letter((290, 279),-90,"W",color[0]))
                    letterLeft = 10
                    startingLetters.update(canvas)
                    generate_geometry(canvas, space,color[0],rainbowMode)
                    inDemo = True
                        
             
            elif event.type == MOUSEBUTTONDOWN:
                #click on playButton
                if playButton.collidepoint(event.pos):
                    totalBall += 10
                    for i in range(10):
                        ballShape = generateBall(space,color[2])
                        balls.append(ballShape)  
                    canPlace  = False
                    timing  = False
                    timing2 = True
                        #print(check)
                    
                #back to level menu
                elif backButton.collidepoint(event.pos):               
                    #remove ball for levels page
                    space.remove(balls, space.bodies)
                    balls = []
                    lv3 = False
                    canvas.fill(color[3])
                    generate_geometry(canvas, space,color[0],rainbowMode)      
                    levels(screen, clock, space, canvas, color,rainbowMode) 
                #redo all
                elif blankButton.collidepoint(event.pos):
                    check = False
                    timer2 = 0
                    timing2 = False
                    space.remove(balls, space.bodies)
                    balls = []
                    path =[]
                    rColor=0
                    canvas.fill(color[3])
                    letterLeft = 20
                    for letter in countDict:
                        countDict[letter]=0
                    for s in space.shapes:
                        if hasattr(s, "generated") and s.generated:
                            space.remove(s)
                #erase the previous one
                elif eraseButton.collidepoint(event.pos):
                    if len(path)>0:
                        erasedLetter = path.pop()[0]
                        countDict[erasedLetter]-=1
                        canvas.fill(color[3])
                        letterLeft += 1
                        rColor -= 1
                        for s in space.shapes:
                            if hasattr(s, "generated") and s.generated:
                                space.remove(s)
                        for l in path:
                            old = Letter(l[1],l[2], l[0],l[4])
                            old.update(canvas)
                            generate_geometry(canvas, space,color[0],rainbowMode)
                            old.update(screen)
                #draw letter
                else:
                    if canPlace == True and letterLeft>0  and countDict[curLetter.input]<2 and curLetter.collide(blockGroup)==True:
                        curLetter.update(canvas)
                        generate_geometry(canvas, space,color[0],rainbowMode)
                        #set letter limit
                        countDict[curLetter.input]+=1
                        print(curLetter.input,curLetter.pos,countDict[curLetter.input])
                        letterLeft -= 1
                        #document path
                        path.append((curLetter.input,curLetter.pos,curLetter.angle,countDict[curLetter.input],curLetter.color))
                        rColor +=1
                        #print(path)
        #print(len(space.bodies))
        # if ball goes out of screen, balls remove 
        #larger bb, but set if ball>value, balls remove
        #check gravity
        for ball in space.bodies:
            #print(int(ball.position[0]))
            if int(ball.position[0])>= 275:
                pymunk.Body.update_velocity(ball,(60,-980),1,0.03)
        
        #check win

        for ball in balls:
                if ball.body.position.y<0 or ball.body.position.y>850\
                    or ball.body.position.x<0 or ball.body.position.x>550:
                    space.remove(ball, ball.body)
                    balls.remove(ball)
        #print(check)
        if check == True:
            allStop = checkStop(space)
            if allStop == True:
                ballOnSceen = len(space.bodies)
                space.remove(balls, space.bodies)
                balls = []
                #print("!")
                curPg = 3
                lv3 = False
                canvas.fill(color[3])
                generate_geometry(canvas, space,color[0],rainbowMode)
                score = getScore(time, letterLeft, ballOnSceen, totalBall)
                if ballOnSceen < totalBall:   
                    scorePage(screen, clock, space,canvas, color, score,curPg,rainbowMode)
                else:
                    losePage(screen,clock,space,canvas,color,score,curPg,rainbowMode)
                     

        curLetter.update(screen)
        pygame.display.flip()
        space.step(1./fps)
        clock.tick(fps)
        pygame.display.set_caption("Type Mania")

def checkStop(space):
    print("CHECKING")
    for ball in space.bodies:
        print(int(ball.velocity[1]),int(ball.velocity[0]))
        if int(ball.velocity[1])!= 0 or int(ball.velocity[0])!= 0:
            return False
    return True

def getScore(time, letterLeft,ballOnSceen, totalBall):
    #print(time, letterLeft, ballOnSceen)
    if time<25:
        tScore = 35
    else: tScore = 35 - (time-25)//8
    
    if letterLeft<8:
        lScore = 30
    else: lScore = 30 - (letterLeft-8)*2
    
    bScore = 35 * (1- ballOnSceen/totalBall)
    finalScore = tScore+lScore+bScore
    p = (time, letterLeft, finalScore)
    return p

def scorePage(screen, clock, space, canvas, color, score, curPg,rainbowMode):
    draw_options = pymunk.pygame_util.DrawOptions(screen)
    pymunk.pygame_util.positive_y_is_up = False
    scorepg = True

    space.gravity = 1,980
    fps = 100
    while scorepg == True:
        screen.fill(color[3])

        screen.blit(canvas, (0,0))
        space.debug_draw(draw_options)
        #draw score
        winImg = pygame.image.load('win.png').convert_alpha()
        winButton = screen.blit(winImg,(200, 400))

        nextImg = pygame.image.load('next.png').convert_alpha()
        nextButton = screen.blit(nextImg,(190, 500))

        againImg = pygame.image.load('again.png').convert_alpha()
        againButton = screen.blit(againImg,(200, 600))

        font = pygame.font.Font(None, 120)
        finalScore = str(int(score[2]))
        #print("finalscore", finalScore)
        final = font.render(finalScore,1,THECOLORS["black"])
        screen.blit(final,(250, 300))

        levelBasic = levelTamplate(screen,score[1],score[0])

            
        for event in pygame.event.get():
            if event.type==MOUSEBUTTONDOWN:
                if nextButton.collidepoint(event.pos):
                    scorepg = False
                    canvas.fill(color[3])
                    generate_geometry(canvas, space,color[0],rainbowMode)
                    if curPg == 1:
                        level2(screen, clock, space, canvas, color,rainbowMode)
                    if curPg == 2:
                        level3(screen, clock, space, canvas, color,rainbowMode)
                    if curPg == 3:
                        gameIntro(screen, clock, space, canvas, color,rainbowMode)
                elif againButton.collidepoint(event.pos):
                    scorepg = False
                    canvas.fill(color[3])
                    generate_geometry(canvas, space,color[0],rainbowMode)
                    if curPg == 1:
                        level1(screen, clock, space, canvas, color,rainbowMode)
                    if curPg == 2:
                        level2(screen, clock, space, canvas, color,rainbowMode)
                    if curPg == 3:
                        level3(screen, clock, space, canvas, color,rainbowMode)

            elif event.type == QUIT or \
                event.type == KEYDOWN and event.key == K_ESCAPE:  
                sys.exit(0)

        pygame.display.flip()
        space.step(1./fps)
        clock.tick(fps)
        pygame.display.set_caption("Type Mania")

def losePage(screen, clock, space, canvas, color,score,curPg,rainbowMode):
    draw_options = pymunk.pygame_util.DrawOptions(screen)
    pymunk.pygame_util.positive_y_is_up = False
    losepg = True

    space.gravity = 1,980
    fps = 100
    while losepg == True:
        screen.fill(color[3])

        screen.blit(canvas, (0,0))
        space.debug_draw(draw_options)
        #draw score



        againImg = pygame.image.load('again.png').convert_alpha()
        againButton = screen.blit(againImg,(185, 600))

        font = pygame.font.Font(None, 80)
        text = "YOU LOSE!"
        lose = font.render(text,1,THECOLORS["black"])
        screen.blit(lose,(130, 300))

        levelBasic = levelTamplate(screen,score[1],score[0])

            
        for event in pygame.event.get():
            if event.type==MOUSEBUTTONDOWN:
                if againButton.collidepoint(event.pos):
                    losepg = False
                    canvas.fill(color[3])
                    generate_geometry(canvas, space,color[0],rainbowMode)
                    if curPg == 1:
                        level1(screen, clock, space, canvas, color,rainbowMode)
                    if curPg == 2:
                        level2(screen, clock, space, canvas, color,rainbowMode)
                    if curPg == 3:
                        level3(screen, clock, space, canvas, color,rainbowMode)

            elif event.type == QUIT or \
                event.type == KEYDOWN and event.key == K_ESCAPE:  
                sys.exit(0)

        pygame.display.flip()
        space.step(1./fps)
        clock.tick(fps)
        pygame.display.set_caption("Type Mania")

def main():
    pygame.init()
    screen = pygame.display.set_mode((550,850))
    clock = pygame.time.Clock()
    
    space = pymunk.Space()   
    #create bounding box, make the collision with bounding box unique
    """static= [
                pymunk.Segment(space.static_body, (-10, -10), (560, -10), 5),
                pymunk.Segment(space.static_body, (555,-10), (555, 860), 5),
                pymunk.Segment(space.static_body, (555,860), (-10,860), 5),
                pymunk.Segment(space.static_body, (-10, 860), (-10, -10), 5),
                ] 
    for s in static:
        s.collision_type = 1
    space.add(static)"""
    #only if the ball hits the bounding box, remove the ball
    """def pre_solve(arb, space, data):
        s = arb.shapes[0]
        space.remove(s.body, s)
        return False
    space.add_collision_handler(0, 1).pre_solve = pre_solve"""

    canvas = pygame.Surface((560,860))
    
    LETTERCOLOR = pygame.color.THECOLORS["pink"]
    BLOCKCOLOR = pygame.color.THECOLORS["red"]
    BALLCOLOR = pygame.color.THECOLORS["blue"]
    BACKGROUNDCOLOR = pygame.color.THECOLORS["white"]

    color = [LETTERCOLOR,BLOCKCOLOR,BALLCOLOR,BACKGROUNDCOLOR]
    rainbowMode = False
    canvas.fill(color[3])

    gameIntro(screen, clock, space, canvas,color,rainbowMode)
    

if __name__ == '__main__':
    sys.exit(main())