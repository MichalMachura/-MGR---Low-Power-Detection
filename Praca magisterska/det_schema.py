import numpy as np
import cv2 as cv


def draw_grid(img,G_R, G_C, p_beg, p_end, color=(0)):
    
    for row in range(G_R+1):
        step = (p_end[1]-p_beg[1])/G_R
        r = int(p_beg[1]+row*step)
        p1 = (p_beg[0],r)
        p2 = (p_end[0],r)
        img = cv.line(img, p1, p2,color)
    
    for col in range(G_C+1):
        step = (p_end[0]-p_beg[0])/G_C
        c = int(p_beg[0]+col*step)
        p1 = (c,p_beg[1])
        p2 = (c,p_end[1])
        img = cv.line(img, p1, p2, color)
    
    return img

def fill_grid(img, row, col, G_R, G_C, p_beg, p_end, color=(0)):
    W = (p_end[0]-p_beg[0])/G_C
    H = (p_end[1]-p_beg[1])/G_R
    c0 = int(p_beg[0]+col*W)+1
    r0 = int(p_beg[1]+row*H)+1
    c1 = int(p_beg[0]+(col+1)*W)-1
    r1 = int(p_beg[1]+(row+1)*H)-1
    p1 = (c0,r0)
    p2 = (c1,r1)
    img = cv.rectangle(img, p1, p2, color,-1)
    
    return img

def draw_bbox(img, row_beg, col_beg, row_end, col_end, G_R, G_C, p_beg, p_end, color=(0)):
    W = (p_end[0]-p_beg[0])/G_C
    H = (p_end[1]-p_beg[1])/G_R
    c0 = int(p_beg[0]+col_beg*W+W/2)
    r0 = int(p_beg[1]+row_beg*H+W/2)
    c1 = int(p_beg[0]+col_end*W-W/2)
    r1 = int(p_beg[1]+row_end*H-W/2)
    p1 = (c0,r0)
    p2 = (c1,r1)
    img = cv.rectangle(img, p1, p2, color)
    
    return img

def grid():
    img = np.zeros((400,600, 3), dtype=np.uint8)+255

    p_beg = (40,40)
    p_end = (600-p_beg[0],400-p_beg[1])
    G_R = 40
    G_C = 60
    img = draw_grid(img, G_R, G_C,p_beg,p_end, color=(0,0,0))
    img = draw_bbox(img, 10,13, 20, 45,G_R, G_C,p_beg,p_end, color=(0,0,255))
    # img = fill_grid(img, 20,20,G_R, G_C,p_beg,p_end, color=150)


    cv.imwrite("grid.png", img)


def move(vx,vy,vz):
    
    def local(offset, vz=vz,vy=vy,vx=vx):
        x,y,z = offset
        return z*vz+y*vy+x*vx
    
    return local

def coord(p):
    return tuple(p.astype(np.int).tolist())

def draw(img, pos, commands, xy_map=lambda v:v):
    color = 0
    thickness = 1
    for c in commands:
        name = c[0]
        if name == 'go':
            offset = xy_map(c[1])
            pos = pos + offset
        if name == 'move':
            pos = c[1]
        elif name == 'color':
            color = c[1]
        elif name == 'thickness':
            thickness = c[1]
        elif name == 'draw line':
            offset = xy_map(c[1])
            p = pos + offset
            img = cv.line(img, coord(pos), coord(p), color, thickness)
            pos = p
        elif name == 'draw point':
            offset = xy_map(c[1])
            p_col = c[2]
            p = coord(pos + offset)
            img[p[1],p[0],:] = p_col
        elif name == 'draw img':
            dst_shape = c[2]
            sub_img = cv.resize(c[1], dst_shape)
            for x in range(sub_img.shape[1]):
                for y in range(sub_img.shape[0]):
                    p = coord(pos + xy_map((x,y,0)))
                    if 0 <= p[0] < img.shape[1] and 0 <= p[1] < img.shape[0]:
                        img[p[1],p[0],:] = sub_img[sub_img.shape[0]-y-1,sub_img.shape[1]-x-1,:]
        elif name == 'draw rect':
            xyz = c[1]
            offset = xy_map(xyz)
            p0 = coord(pos)
            p1 = coord(pos+xy_map((xyz[0],0,0)))
            p2 = coord(pos+offset)
            p3 = coord(pos+xy_map((0,xyz[1],0)))
            img = cv.line(img, p0, p1, color, thickness)
            img = cv.line(img, p1, p2, color, thickness)
            img = cv.line(img, p2, p3, color, thickness)
            img = cv.line(img, p3, p0, color, thickness)
            pos = pos+offset
        elif name == 'draw circle':
            r = c[1]
            img = cv.circle(img, coord(pos), r, color, thickness)
        # print(c)
        # print(pos)
        # print()
        
    return img

def draw_piramid():
    pos = np.array([0.0,399.0])
    axis = (np.array([1.0,0.0]),
            np.array([8.0,-10.0])/np.sqrt(64+144),
            np.array([0.0,-1.0]))
    img = np.zeros((400,600,3), dtype=np.uint8) + 255

    W = 640*4//7
    H = 360*4//7
    w = 40
    h = 60
    stride_x,stride_y = 30, 40
    dist = H*3//4
    scale = 4/5

    def window(sx,sy,color, dx=1,dy=1):
        return [('go', (sx*stride_x,sy*stride_y,0)), 
                ('color', color), 
                ('draw rect', (dx*w,dy*h,0)), 
                ('go', (-dx*w,-dy*h,0)),
                ('go', (-sx*stride_x,-sy*stride_y,0)), 
                ]

    def scaling(mul, sub_img):
        nW,nH = int(W*scale**mul),int(H*scale**mul)
        sub_img = cv.resize(sub_img,(nW,nH))
        w1 = sub_img[:,::-1,:][0:h,0:w,:][:,::-1,:]
        w2 = sub_img[:,::-1,:][stride_y:stride_y+h,0:w,:][:,::-1,:]
        w3 = sub_img[:,::-1,:][0:h,stride_x:stride_x+w,:][:,::-1,:]
        
        step = (stride_x/2,stride_y/2,5)
        return [
                ('move', pos),
                ('go', (0,0,mul*dist)),
                ('draw img', sub_img, (nW,nH)),
                ('go', (0,nH,0)),
                *window(1, 0,(0,255,0), dx=1,dy=-1),
                *window(0, -1,(0,0,255), dx=1,dy=-1),
                *window(0, 0,(255,0,0), dx=1,dy=-1),
                # draw sliding windows
                ('move', pos),
                ('go', (W*1.2,0,mul*dist)),
                ('draw img', w2, (w,h)),
                *window(0, 0,(0,0,255)),
                ('go', step),
                ('draw img', w1, (w,h)),
                *window(0, 0,(255,0,0)),
                ('go', step),
                ('draw img', w3, (w,h)),
                *window(0, 0,(0,255,0)),
                ('move', pos),
                ]

    sub_img = cv.imread("sw_img.jpg")

    cmd = [
        ('thickness', 1),
        ('color', (0,0,100)),
        ('go', (0,0,0)),
        ('thickness', 1),
        *scaling(0,sub_img),
        *scaling(1,sub_img),
        *scaling(2,sub_img),
        ]

    img = draw(img, pos, cmd, move(*axis))

    cv.imwrite("piramid.png",img)


def left_grid(W,H,D,S):
    cmd = []
    
    # vertical lines
    for i in range(H+1):
        cmd.append(('draw line', (0,0,D*S)))
        cmd.append(('go', (0,1*S,-D*S)))
    cmd.append(('go', (0,(-H-1)*S,0)))
    
    # horizontal lines
    for i in range(D+1):
        cmd.append(('draw line', (0,H*S,0)))
        cmd.append(('go', (0,-H*S,1*S)))
    cmd.append(('go', (0,0,(-D-1)*S)))
    
    return cmd

def right_grid(W,H,D,S):
    cmd = []
    
    # vertical lines
    for i in range(W+1):
        cmd.append(('draw line', (0,0,D*S)))
        cmd.append(('go', (1*S,0,-D*S)))
    cmd.append(('go', ((-W-1)*S,0,0)))
    
    # horizontal lines
    for i in range(D+1):
        cmd.append(('draw line', (W*S,0,0)))
        cmd.append(('go', (-W*S,0,1*S)))
    cmd.append(('go', (0,0,(-D-1)*S)))
    
    return cmd

def top_grid(W,H,D,S):
    cmd = []
    
    cmd.append(('go', (0,0,D*S)))
    # vertical lines
    for i in range(W+1):
        cmd.append(('draw line', (0,H*S,0)))
        cmd.append(('go', (1*S,-H*S,0)))
    cmd.append(('go', ((-W-1)*S,0,0)))
    
    # horizontal lines
    for i in range(H+1):
        cmd.append(('draw line', (W*S,0,0)))
        cmd.append(('go', (-W*S,1*S,0)))
    cmd.append(('go', (0,(-H-1)*S,0)))
    cmd.append(('go', (0,0,-D*S)))
    
    return cmd

def ssd():
            
    pos = np.array([150.0,370.0])
    axis = (np.array([1.0,0.0]),
            np.array([-10.0,-10.0])/np.sqrt(100+100),
            np.array([0.0,-1.0]))
    img = np.zeros((400,600,3), dtype=np.uint8) + 255

    W = 15
    H = 10
    D = 8*2
    S = 15

    cmd = [
        ('thickness', 1),
        ('color', (0,0,0)),
        ('go', (0,0,0)),
        ('thickness', 1),
        ('color', (255*2//3,0,0)),
        *left_grid(W,H,D//2,S),
        *right_grid(W,H,D//2,S),
        ('go', (0,0,D//2*S)),
        ('color', (0,255*2//3,0)),
        *left_grid(W,H,D//2,S),
        *right_grid(W,H,D//2,S),
        ('color', (0,0,255*2//3)),
        *top_grid(W,H,D//2,S),
        ('go', (0,0,D//2*S)),
        ('go', (W//2*S,H//2*S,0)),
        ('thickness', 2),
        ('color', (0,0,255)),
        *top_grid(1,1,0,S),
        # back to origin
        ('go', (-W//2*S,-H//2*S,-D*S)),
        # go to right 
        ('thickness', 1),
        ('go', ((W+6)*S,0,0)),
        ('color', (255,0,0)),
        *left_grid(1,1,D//2,S),
        *right_grid(1,1,D//2,S),
        ('go', (0,0,D//2*S)),
        ('color', (0,255,0)),
        *left_grid(1,1,D//2,S),
        *right_grid(1,1,D//2,S),
        ('color', (0,0,255)),
        ('thickness', 2),
        *top_grid(1,1,D//2,S),
        # ('go', ((W-1)*S,0,0)),
        # ('thickness', 2),
        # ('color', (255,0,0)),
        # *right_grid(1,1,8,S),
        ]

    img = draw(img, pos, cmd, move(*axis))

    cv.imwrite("ssd_grid.png",img)


    
def depthwise():
    pos = np.array([60.0,370.0/2])
    axis = (np.array([1.0,0.0]),
            np.array([-10.0,-10.0])/np.sqrt(100+100),
            np.array([0.0,-1.0]))
    img = np.zeros((200,800,3), dtype=np.uint8) + 255

    W = 8
    H = 5
    D = 3
    S = 15
    sep = 3.5
    dist = 6
    cmd = [
        ('thickness', 1),
        ('color', (0,0,0)),
        ('go', (0,0,0)),
        ('thickness', 2),
        ('go', (0,0,0.5*S*sep)),
        ('color', (255*2//3,0,0)),
        *left_grid(W,H,1,S),
        *right_grid(W,H,1,S),
        ('go', (0,0,S)),
        ('color', (0,255*2//3,0)),
        *left_grid(W,H,1,S),
        *right_grid(W,H,1,S),
        ('go', (0,0,S)),
        ('color', (0,0,255*2//3)),
        *left_grid(W,H,1,S),
        *right_grid(W,H,1,S),
        *top_grid(W,H,1,S),
        ('go', (0,0,-0.5*S*sep)),
        # draw filters
        ('thickness', 2),
        ('go', ((W+dist)*S,0,-2*S)),
        ('color', (0,100,100)),
        *left_grid(3,3,1,S),
        *right_grid(3,3,1,S),
        *top_grid(3,3,1,S),
        ('go', (0,0,S*sep)),
        ('color', (100,0,100)),
        *left_grid(3,3,1,S),
        *right_grid(3,3,1,S),
        *top_grid(3,3,1,S),
        ('go', (0,0,S*sep)),
        ('color', (100,100,0)),
        *left_grid(3,3,1,S),
        *right_grid(3,3,1,S),
        *top_grid(3,3,1,S),
        # draw results
        ('thickness', 2),
        ('go', ((3+dist)*S,0,-2*S*sep)),
        ('color', (255*2//3,0,0)),
        *left_grid(W-2,H-2,1,S),
        *right_grid(W-2,H-2,1,S),
        *top_grid(W-2,H-2,1,S),
        ('go', (0,0,S*sep)),
        ('color', (0,255*2//3,0)),
        *left_grid(W-2,H-2,1,S),
        *right_grid(W-2,H-2,1,S),
        *top_grid(W-2,H-2,1,S),
        ('go', (0,0,S*sep)),
        ('color', (0,0,255*2//3)),
        *left_grid(W-2,H-2,1,S),
        *right_grid(W-2,H-2,1,S),
        *top_grid(W-2,H-2,1,S),
        # merged
        ('go', ((W-2+dist)*S,0,-1.5*S*sep)),
        ('color', (255*2//3,0,0)),
        *left_grid(W-2,H-2,1,S),
        *right_grid(W-2,H-2,1,S),
        ('go', (0,0,S)),
        ('color', (0,255*2//3,0)),
        *left_grid(W-2,H-2,1,S),
        *right_grid(W-2,H-2,1,S),
        ('go', (0,0,S)),
        ('color', (0,0,255*2//3)),
        *left_grid(W-2,H-2,1,S),
        *right_grid(W-2,H-2,1,S),
        *top_grid(W-2,H-2,1,S),
        
        ]

    img = draw(img, pos, cmd, move(*axis))

    cv.imwrite("dw_conv_grid.png",img)
    
def std_conv():
    
    pos = np.array([60.0,385.0/2*1.5])
    axis = (np.array([1.0,0.0]),
            np.array([-10.0,-10.0])/np.sqrt(100+100),
            np.array([0.0,-1.0]))
    img = np.zeros((330,800,3), dtype=np.uint8) + 255

    W = 8
    H = 5
    D = 3
    S = 15
    sep = 3.5*1.3
    dist = 4
    cmd = [
        ('thickness', 1),
        ('color', (0,0,0)),
        ('go', (0,0,0)),
        ('thickness', 2),
        ('go', (0,0,1.5*S*sep)),
        ('color', (255*2//3,0,0)),
        *left_grid(W,H,1,S),
        *right_grid(W,H,1,S),
        ('go', (0,0,S)),
        ('color', (0,255*2//3,0)),
        *left_grid(W,H,1,S),
        *right_grid(W,H,1,S),
        ('go', (0,0,S)),
        ('color', (0,0,255*2//3)),
        *left_grid(W,H,1,S),
        *right_grid(W,H,1,S),
        *top_grid(W,H,1,S),
        ('go', (0,0,-1.5*S*sep)),
        # draw filters
        ('thickness', 2),
        ('go', ((W+dist)*S,0,-2*S)),
        ('color', (0,0,255*2//3)),
        *left_grid(3,3,3,S),
        *right_grid(3,3,3,S),
        *top_grid(3,3,3,S),
        ('color', (0,255*2//3,0)),
        *left_grid(3,3,2,S),
        *right_grid(3,3,2,S),
        ('color', (255*2//3,0,0)),
        *left_grid(3,3,1,S),
        *right_grid(3,3,1,S),
        ('go', (2*S,0,S*sep)),
        ('color', (0,0,255*2//3)),
        *left_grid(3,3,3,S),
        *right_grid(3,3,3,S),
        *top_grid(3,3,3,S),
        ('color', (0,255*2//3,0)),
        *left_grid(3,3,2,S),
        *right_grid(3,3,2,S),
        ('color', (255*2//3,0,0)),
        *left_grid(3,3,1,S),
        *right_grid(3,3,1,S),
        ('go', (2*S,0,S*sep)),
        ('color', (0,0,255*2//3)),
        *left_grid(3,3,3,S),
        *right_grid(3,3,3,S),
        *top_grid(3,3,3,S),
        ('color', (0,255*2//3,0)),
        *left_grid(3,3,2,S),
        *right_grid(3,3,2,S),
        ('color', (255*2//3,0,0)),
        *left_grid(3,3,1,S),
        *right_grid(3,3,1,S),
        ('go', (2*S,0,S*sep)),
        ('color', (0,0,255*2//3)),
        *left_grid(3,3,3,S),
        *right_grid(3,3,3,S),
        *top_grid(3,3,3,S),
        ('color', (0,255*2//3,0)),
        *left_grid(3,3,2,S),
        *right_grid(3,3,2,S),
        ('color', (255*2//3,0,0)),
        *left_grid(3,3,1,S),
        *right_grid(3,3,1,S),
        ('go', (2*S,0,S*sep)),
        
        ('go', (-3*2*S,0,-4*S*sep)),
        # draw results
        ('go', ((W-2+dist)*S,0,0)),
        ('color', (0,100,100)),
        *left_grid(W-2,H-2,1,S),
        *right_grid(W-2,H-2,1,S),
        *top_grid(W-2,H-2,1,S),
        ('go', (2*S,0,S*sep)),
        ('color', (100,100,0)),
        *left_grid(W-2,H-2,1,S),
        *right_grid(W-2,H-2,1,S),
        *top_grid(W-2,H-2,1,S),
        ('go', (2*S,0,S*sep)),
        ('color', (100,0,100)),
        *left_grid(W-2,H-2,1,S),
        *right_grid(W-2,H-2,1,S),
        *top_grid(W-2,H-2,1,S),
        ('go', (2*S,0,S*sep)),
        ('color', (255,100,100)),
        *left_grid(W-2,H-2,1,S),
        *right_grid(W-2,H-2,1,S),
        *top_grid(W-2,H-2,1,S),
        ('go', (2*S,0,S*sep)),
        ('go', (-3*2*S,0,-4*S*sep)),
        ('go', (0,0,S*sep)),
        # merged
        ('go', ((W+dist+4)*S,0,0)),
        ('color', (0,100,100)),
        *left_grid(W-2,H-2,1,S),
        *right_grid(W-2,H-2,1,S),
        ('go', (0,0,S)),
        ('color', (100,100,0)),
        *left_grid(W-2,H-2,1,S),
        *right_grid(W-2,H-2,1,S),
        ('go', (0,0,S)),
        ('color', (100,0,100)),
        *left_grid(W-2,H-2,1,S),
        *right_grid(W-2,H-2,1,S),
        ('go', (0,0,S)),
        ('color', (255,100,100)),
        *left_grid(W-2,H-2,1,S),
        *right_grid(W-2,H-2,1,S),
        *top_grid(W-2,H-2,1,S),
        
        ]

    img = draw(img, pos, cmd, move(*axis))

    cv.imwrite("std_conv_grid.png",img)


def pointwise():
    pos = np.array([60.0,370.0/2*1.5])
    axis = (np.array([1.0,0.0]),
            np.array([-10.0,-10.0])/np.sqrt(100+100),
            np.array([0.0,-1.0]))
    img = np.zeros((300,800,3), dtype=np.uint8) + 255

    W = 6
    H = 3
    D = 3
    S = 15
    sep = 3.5
    dist = 4
    cmd = [
        ('thickness', 1),
        ('color', (0,0,0)),
        ('go', (0,0,0)),
        ('thickness', 2),
        ('go', (0,0,1.5*S*sep)),
        ('color', (255*2//3,0,0)),
        *left_grid(W,H,1,S),
        *right_grid(W,H,1,S),
        ('go', (0,0,S)),
        ('color', (0,255*2//3,0)),
        *left_grid(W,H,1,S),
        *right_grid(W,H,1,S),
        ('go', (0,0,S)),
        ('color', (0,0,255*2//3)),
        *left_grid(W,H,1,S),
        *right_grid(W,H,1,S),
        *top_grid(W,H,1,S),
        ('go', (0,0,-1.5*S*sep)),
        # draw filters
        ('thickness', 2),
        ('go', ((W+dist)*S,0,-2*S)),
        ('color', (0,0,255*2//3)),
        *left_grid(1,1,3,S),
        *right_grid(1,1,3,S),
        *top_grid(1,1,3,S),
        ('color', (0,255*2//3,0)),
        *left_grid(1,1,2,S),
        *right_grid(1,1,2,S),
        ('color', (255*2//3,0,0)),
        *left_grid(1,1,1,S),
        *right_grid(1,1,1,S),
        ('go', (2*S,0,S*sep)),
        ('color', (0,0,255*2//3)),
        *left_grid(1,1,3,S),
        *right_grid(1,1,3,S),
        *top_grid(1,1,3,S),
        ('color', (0,255*2//3,0)),
        *left_grid(1,1,2,S),
        *right_grid(1,1,2,S),
        ('color', (255*2//3,0,0)),
        *left_grid(1,1,1,S),
        *right_grid(1,1,1,S),
        ('go', (2*S,0,S*sep)),
        ('color', (0,0,255*2//3)),
        *left_grid(1,1,3,S),
        *right_grid(1,1,3,S),
        *top_grid(1,1,3,S),
        ('color', (0,255*2//3,0)),
        *left_grid(1,1,2,S),
        *right_grid(1,1,2,S),
        ('color', (255*2//3,0,0)),
        *left_grid(1,1,1,S),
        *right_grid(1,1,1,S),
        ('go', (2*S,0,S*sep)),
        ('color', (0,0,255*2//3)),
        *left_grid(1,1,3,S),
        *right_grid(1,1,3,S),
        *top_grid(1,1,3,S),
        ('color', (0,255*2//3,0)),
        *left_grid(1,1,2,S),
        *right_grid(1,1,2,S),
        ('color', (255*2//3,0,0)),
        *left_grid(1,1,1,S),
        *right_grid(1,1,1,S),
        ('go', (2*S,0,S*sep)),
        
        ('go', (-3*2*S,0,-4*S*sep)),
        # draw results
        ('go', ((W-2+dist)*S,0,0)),
        ('color', (0,100,100)),
        *left_grid(W,H,1,S),
        *right_grid(W,H,1,S),
        *top_grid(W,H,1,S),
        ('go', (2*S,0,S*sep)),
        ('color', (100,100,0)),
        *left_grid(W,H,1,S),
        *right_grid(W,H,1,S),
        *top_grid(W,H,1,S),
        ('go', (2*S,0,S*sep)),
        ('color', (100,0,100)),
        *left_grid(W,H,1,S),
        *right_grid(W,H,1,S),
        *top_grid(W,H,1,S),
        ('go', (2*S,0,S*sep)),
        ('color', (255,100,100)),
        *left_grid(W,H,1,S),
        *right_grid(W,H,1,S),
        *top_grid(W,H,1,S),
        ('go', (2*S,0,S*sep)),
        ('go', (-3*2*S,0,-4*S*sep)),
        ('go', (0,0,S*sep)),
        # merged
        ('go', ((W+dist+4)*S,0,0)),
        ('color', (0,100,100)),
        *left_grid(W,H,1,S),
        *right_grid(W,H,1,S),
        ('go', (0,0,S)),
        ('color', (100,100,0)),
        *left_grid(W,H,1,S),
        *right_grid(W,H,1,S),
        ('go', (0,0,S)),
        ('color', (100,0,100)),
        *left_grid(W,H,1,S),
        *right_grid(W,H,1,S),
        ('go', (0,0,S)),
        ('color', (255,100,100)),
        *left_grid(W,H,1,S),
        *right_grid(W,H,1,S),
        *top_grid(W,H,1,S),
        
        ]

    img = draw(img, pos, cmd, move(*axis))

    cv.imwrite("pw_conv_grid.png",img)


def mul_depthwise():
    pos = np.array([60.0,430.0/2])
    axis = (np.array([1.0,0.0]),
            np.array([-10.0,-10.0])/np.sqrt(100+100),
            np.array([0.0,-1.0]))
    img = np.zeros((250,800,3), dtype=np.uint8) + 255

    W = 8
    H = 5
    D = 2
    S = 15
    sep = 3.5
    dist = 6
    cmd = [
        ('thickness', 1),
        ('color', (0,0,0)),
        ('go', (0,0,0)),
        ('thickness', 2),
        ('go', (0,0,0.5*S*sep)),
        ('color', (255*2//3,0,0)),
        *left_grid(W,H,1,S),
        *right_grid(W,H,1,S),
        ('go', (0,0,S)),
        ('color', (0,0,255*2//3)),
        *left_grid(W,H,1,S),
        *right_grid(W,H,1,S),
        *top_grid(W,H,1,S),
        ('go', (0,0,-0.5*S*sep)),
        # draw filters
        ('thickness', 2),
        ('go', ((W+dist)*S,0,-2*S)),
        ('color', (0,100,100)),
        *left_grid(3,3,1,S),
        *right_grid(3,3,1,S),
        *top_grid(3,3,1,S),
        ('go', (0,0,S*sep)),
        ('color', (100,0,100)),
        *left_grid(3,3,1,S),
        *right_grid(3,3,1,S),
        *top_grid(3,3,1,S),
        ('go', (0,0,S*sep)),
        ('color', (100,100,0)),
        *left_grid(3,3,1,S),
        *right_grid(3,3,1,S),
        *top_grid(3,3,1,S),
        ('go', (0,0,S*sep)),
        ('color', (200,40,100)),
        *left_grid(3,3,1,S),
        *right_grid(3,3,1,S),
        *top_grid(3,3,1,S),
        # draw results
        ('thickness', 2),
        ('go', ((3+dist)*S,0,-3*S*sep)),
        ('color', (255*2//3,0,0)),
        *left_grid(W-2,H-2,1,S),
        *right_grid(W-2,H-2,1,S),
        *top_grid(W-2,H-2,1,S),
        ('go', (0,0,S*sep)),
        ('color', (255*2//3,0,0)),
        *left_grid(W-2,H-2,1,S),
        *right_grid(W-2,H-2,1,S),
        *top_grid(W-2,H-2,1,S),
        ('go', (0,0,S*sep)),
        ('color', (0,0,255*2//3)),
        *left_grid(W-2,H-2,1,S),
        *right_grid(W-2,H-2,1,S),
        *top_grid(W-2,H-2,1,S),
        ('go', (0,0,S*sep)),
        ('color', (0,0,255*2//3)),
        *left_grid(W-2,H-2,1,S),
        *right_grid(W-2,H-2,1,S),
        *top_grid(W-2,H-2,1,S),
        # merged
        ('go', ((W-2+dist)*S,0,-2*S*sep)),
        ('color', (255*2//3,0,0)),
        *left_grid(W-2,H-2,2,S),
        *right_grid(W-2,H-2,2,S),
        ('go', (0,0,2*S)),
        ('color', (0,0,255*2//3)),
        *left_grid(W-2,H-2,2,S),
        *right_grid(W-2,H-2,2,S),
        *top_grid(W-2,H-2,2,S),
        
        ]

    img = draw(img, pos, cmd, move(*axis))

    cv.imwrite("mul_dw_conv_grid.png",img)
    

# std_conv()
mul_depthwise()
# pointwise()