# Pygame/PyopenGL example by Bastiaan Zapf, Jul/Aug 2009

# render a fire effect via blurring and displacing feedback
# (similar to video feedback)

# this effect was ubiquitous in the 90's, often used in
# cracker's intros, demos and the like

from OpenGL.GL import *
from OpenGL.GLU import *

from OpenGL.GL.ARB.framebuffer_object import *
from OpenGL.GL.EXT.framebuffer_object import *

from ctypes import *

from math import *
import pygame
import random
import time
import numpy # for black textures
#from shaderlib import *

def createAndCompileShader(type,source):
    shader=glCreateShader(type)
    glShaderSource(shader,source)
    glCompileShader(shader)

    # get "compile status" - glCompileShader will not fail with
    # an exception in case of syntax errors

    result=glGetShaderiv(shader,GL_COMPILE_STATUS)

    if (result!=1): # shader didn't compile
        raise Exception("Couldn't compile shader\nShader compilation Log:\n"+glGetShaderInfoLog(shader))
    return shader


pygame.init()

screenx=400
screeny=300

pygame.display.set_mode((screenx,screeny), pygame.OPENGL|pygame.DOUBLEBUF)

glClearColor(0.0, 0.0, 0.0, 1.0)
glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)

# Create and Compile fragment and vertex shaders

# Texturing

vertex_shader=createAndCompileShader(GL_VERTEX_SHADER,"""
varying vec4 v;
varying vec3 N;

void main(void)
{

   v = gl_ModelViewMatrix * gl_Vertex;
   N = gl_NormalMatrix * gl_Normal;

   gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
   gl_TexCoord[0]=gl_TextureMatrix[0] * gl_MultiTexCoord0;
}
""");

# Convolution shader - this is the Code that implements
# the blur between two frames
# this will be expensive.

fire_shader=createAndCompileShader(GL_FRAGMENT_SHADER,"""

const int MaxKernelSize=25;
uniform vec3 OffsetWeight[MaxKernelSize];
uniform int KernelSize;
uniform sampler2D BaseImage;
varying vec3 N;
varying vec3 v;

void main(void)
{
  int i;
  vec4 sum=vec4(0.0);
  for (i=0;i<KernelSize;i++) {
     sum+=texture2D(BaseImage,gl_TexCoord[0].st+OffsetWeight[i].st)*OffsetWeight[i].z;
  }
  gl_FragColor=sum;
}
""");

# build fire shader program

fire_program=glCreateProgram()
glAttachShader(fire_program,vertex_shader)
glAttachShader(fire_program,fire_shader)
glLinkProgram(fire_program)

# reference the shader variables

locOW = glGetUniformLocation(fire_program,"OffsetWeight");
locKS = glGetUniformLocation(fire_program,"KernelSize");
locBI = glGetUniformLocation(fire_program,"BaseImage");

# try to activate/enable shader program
# handle errors wisely

try:
    glUseProgram(fire_program)
except OpenGL.error.GLError:
    print glGetProgramInfoLog(fire_program)
    raise


# Monochrome to fire colors shader

color_shader=createAndCompileShader(GL_FRAGMENT_SHADER,"""

const int MaxKernelSize=25;
uniform sampler2D BaseImage;
varying vec3 N;
varying vec3 v;

void main(void)
{
  int i;
  vec4 sum=vec4(0.0);
  sum=texture2D(BaseImage,gl_TexCoord[0].st+vec2(0,0));

  if (sum.x<0.1) {
    gl_FragColor=vec4(0.0,0.0,0.0,0.0);
  } else if (sum.x<0.2) {
    gl_FragColor=vec4((sum.x-0.1)*10.0,0.0,0.0,0.0);
  } else if (sum.x<0.3) {
    gl_FragColor=vec4(1.0,(sum.x-0.2)*10.0,0.0,0.0);
  } else if (sum.x<0.4) {
    gl_FragColor=vec4(1.0,1.0,(sum.x-0.3)*10.0,0.0);
  } else {
    gl_FragColor=vec4(1.0,1.0,1.0,0.0);
  }
}
""");



colors_program=glCreateProgram()
glAttachShader(colors_program,vertex_shader)
glAttachShader(colors_program,color_shader)
glLinkProgram(colors_program)

# try to activate/enable shader program
# handle errors wisely

try:
    glUseProgram(colors_program)
except OpenGL.error.GLError:
    print glGetProgramInfoLog(colors_program)
    raise

# return to fire program to set variables

glUseProgram(fire_program);
glMatrixMode(GL_MODELVIEW);

# set a cheap convolution kernel of length 3

glUniform1i(locKS,3);
glUniform3fv(locOW,3,
             [[  0.001,  0.0  , 0.32],
              [ -0.001,  0.0  , 0.32],
              [  0    , -0.001, 0.32],
              ]); # just some blur

glUniform1i(locBI,0); # we will be using the first texturing unit

# get a monochromatic texture of the size specified below - low resolution
# will mean large flames and cheap calculation

firew=64
fireh=64

texture=glGenTextures( 1 )

glBindTexture( GL_TEXTURE_2D, texture );
glTexEnvf( GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE );
glTexParameterf( GL_TEXTURE_2D, GL_TEXTURE_WRAP_S,
                 GL_REPEAT);
glTexParameterf( GL_TEXTURE_2D, GL_TEXTURE_WRAP_T,
                     GL_REPEAT );
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)

glTexImage2D(GL_TEXTURE_2D, 0,GL_LUMINANCE,
             firew,fireh,0,GL_LUMINANCE,GL_FLOAT,numpy.zeros([firew,fireh,1],float))

glEnable( GL_TEXTURE_2D );
glBindTexture( GL_TEXTURE_2D, texture );


# generate another texture we render the fire to, and set parameters

newtexture=glGenTextures( 1 )

glBindTexture( GL_TEXTURE_2D, newtexture );
glTexEnvf( GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE );
glTexParameterf( GL_TEXTURE_2D, GL_TEXTURE_WRAP_S,
                 GL_REPEAT );
glTexParameterf( GL_TEXTURE_2D, GL_TEXTURE_WRAP_T,
                 GL_REPEAT );
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)

glTexImage2D(GL_TEXTURE_2D, 0,GL_LUMINANCE,firew,fireh,0,GL_LUMINANCE,
             GL_FLOAT, numpy.zeros([firew,fireh,1],float))


# other choices for the texture wrapping options might be
# benefitial

done = False

t=0

# prepare a frame buffer object

#fbo=c_uint(1)  # WTF? Did not find a way to get there easier
# A simple number would always result in a "Segmentation
# Fault" for me

fbo = glGenFramebuffers(1)

while not done:
    print 'tick'

    t=t+1

    # rotation and displacement during fire blur

    alpha=sin(t/73.0)

    x=0
    y=0.004+(cos(t/43.0)+1.0)/50.0

    # render to texture (render next step of fire effect)

    glBindFramebufferEXT(GL_FRAMEBUFFER_EXT, fbo)

    glFramebufferTexture2DEXT(GL_FRAMEBUFFER_EXT, GL_COLOR_ATTACHMENT0_EXT,
                              GL_TEXTURE_2D, newtexture, 0)

    glPushAttrib(GL_VIEWPORT_BIT) # save viewport

    glViewport(0, 0, firew, fireh) # set to fire effect dimensions

    glUseProgram(fire_program) # use fire blur

    # first draw blurred/displaced fire

    glBindTexture( GL_TEXTURE_2D, texture )
    glLoadIdentity()

    glTranslatef(x,y,0)
    glRotatef(alpha,0,0,1)

    glBegin(GL_QUADS)

    glTexCoord2f(0,0)
    glVertex2f(-1,-1)
    glTexCoord2f(1,0)
    glVertex2f( 1,-1)
    glTexCoord2f(1,1)
    glVertex2f( 1, 1)
    glTexCoord2f(0,1)
    glVertex2f(-1, 1)

    glEnd()


    # then draw a few random pixels at the bottom to get the fire going

    glUseProgram(0) # shaders interfer with pure pixel drawing

    glBindTexture( GL_TEXTURE_2D, 0 ) # textures do so as well

    for i in range(0,firew):
        glRasterPos2f(-1+2*i/(firew+0.0),-0.999)
        glDrawPixelsf(GL_LUMINANCE,[[[random.random()]]])

    # restore viewport

    glPopAttrib()#GL_VIEWPORT_BIT)

    # don't render to texture anymore

    glBindFramebufferEXT(GL_FRAMEBUFFER_EXT, 0)

    # fire "palette"
    glLoadIdentity()
    glUseProgram(colors_program)
    glBindTexture( GL_TEXTURE_2D, texture )

    # draw fire once, however, clip noise from top and bottom

    glBegin(GL_QUADS)

    glTexCoord2f(0,0.03)
    glVertex3f(-1,-1,0)
    glTexCoord2f(1,0.03)
    glVertex3f( 1,-1,0)
    glTexCoord2f(1,0.97)
    glVertex3f( 1, 1,0)
    glTexCoord2f(0,0.97)
    glVertex3f(-1, 1,0)

    glEnd()

    pygame.display.flip()

    # flip textures

    oldtexture=texture
    texture=newtexture
    newtexture=oldtexture

    time.sleep(0.01)
    t=t+1
