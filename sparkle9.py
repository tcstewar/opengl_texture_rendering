# PyQt4 imports
from PyQt4 import QtGui, QtCore, QtOpenGL
from PyQt4.QtOpenGL import QGLWidget
# PyOpenGL imports
import OpenGL.GL as gl
import OpenGL.arrays.vbo as glvbo

import glhelpers
import numpy as np

import time

# Vertex shader
VS = """
#version 330
// Attribute variable that contains coordinates of the vertices.
layout(location = 0) in vec2 position;

// Main function, which needs to set `gl_Position`.
void main()
{
    // The final position is transformed from a null signal to a sinewave here.
    // We pass the position to gl_Position, by converting it into
    // a 4D vector. The last coordinate should be 0 when rendering 2D figures.
    int x = int(position.x / 256);
    int y = int(position.x - (x*256));
    gl_Position = vec4((x-128)*(1.0/128), (y-128)*(1.0/128), 0., 1);
}
"""

# Fragment shader
FS = """
#version 330
// Output variable of the fragment shader, which is a 4D vector containing the
// RGBA components of the pixel color.
out vec4 out_color;

// Main fragment shader function.
void main()
{
    // We simply set the pixel color to white.
    out_color = vec4(1., 1., 1., 1.);
}
"""

VS_fade = """
#version 110

void main()
{
    gl_Position = ftransform();
    gl_TexCoord[0] = gl_MultiTexCoord0;
}
"""

FS_fade = """
#version 110
uniform sampler2D texture1;

void main()
{
    gl_FragColor = texture2D(texture1, gl_TexCoord[0].st) * 0.5;
    gl_FragColor.y = 0.0;
}
"""

class GLPlotWidget(QGLWidget):
    # default window size
    width, height = 600, 600
    t_last_msg = time.time()
    spike_count = 0


    def initializeGL(self):
        """Initialize OpenGL, VBOs, upload data on the GPU, etc."""
        # background color
        gl.glClearColor(0, 0, 0, 0)

        vs = glhelpers.compile_vertex_shader(VS)
        fs = glhelpers.compile_fragment_shader(FS)
        self.shaders_program = glhelpers.link_shader_program(vs, fs)

        vs_fade = glhelpers.compile_vertex_shader(VS_fade)
        fs_fade = glhelpers.compile_fragment_shader(FS_fade)
        self.shaders_program_fade = glhelpers.link_shader_program(vs_fade, fs_fade)
        self.fade_texture1 = gl.glGetUniformLocation(self.shaders_program_fade, 'texture1')


        # create the texture
        self.texture = gl.glGenTextures(1, ['sparkle'])
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER,
                           gl.GL_NEAREST)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER,
                           gl.GL_NEAREST)
        gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S,
                           gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T,
                           gl.GL_CLAMP_TO_EDGE)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, 256, 256, 0,
                           gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)

        self.fb = gl.glGenFramebuffers(1)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fb);
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0,
                  gl.GL_TEXTURE_2D, self.texture, 0);
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0);   # unbind the framebuffer

        self.square = glvbo.VBO(
            np.array( [
                [ -1,-1, 0, 0, 0 ],
                [  1,-1, 0, 0, 1 ],
                [  1, 1, 0, 1, 1 ],
                [ -1,-1, 0, 0, 0 ],
                [  1, 1, 0, 1, 1 ],
                [ -1, 1, 0, 0, 1 ],
            ],'f')
        )
    def paintGL(self):
        """Paint the scene."""


        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fb);
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0,
                  gl.GL_TEXTURE_2D, self.texture, 0);
        gl.glViewport(0, 0, 256, 256)
        # clear the buffer
        #gl.glClearColor(255, 0, 0, 0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT + gl.GL_DEPTH_BUFFER_BIT)


        data = np.random.randint(65536, size=10000)
        vbo = glvbo.VBO(data)
        vbo.bind()
        self.spike_count += len(data)

        # tell OpenGL that the VBO contains an array of vertices
        # prepare the shader
        gl.glEnableVertexAttribArray(0)

        # identify what's in the array
        gl.glVertexAttribPointer(0, 1, gl.GL_UNSIGNED_SHORT,
                                 gl.GL_FALSE, 0, None)

        gl.glUseProgram(self.shaders_program)
        # draw "count" points from the VBO
        gl.glDrawArrays(gl.GL_POINTS, 0, len(data))



        gl.glUseProgram(self.shaders_program_fade)
        gl.glUniform1i(self.fade_texture1, 0)  # use GL_TEXTURE0
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)   # unbind the framebuffer
        gl.glViewport(0, 0, self.width, self.height)

        gl.glEnable(gl.GL_TEXTURE_2D)
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture)

        self.square.bind()

        gl.glEnableClientState(gl.GL_VERTEX_ARRAY);
        gl.glEnableClientState(gl.GL_TEXTURE_COORD_ARRAY);
        gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT,
                                 gl.GL_FALSE, 5*4, None)
        gl.glTexCoordPointer(2, gl.GL_FLOAT, 5*4, self.square + 3*4)
        gl.glDrawArrays(gl.GL_TRIANGLES, 0, 6)






        now = time.time()
        if now > self.t_last_msg + 1:
            dt = now - self.t_last_msg
            print 'Mspikes per second = %1.1f' % (self.spike_count*0.000001/dt)
            self.spike_count = 0
            self.t_last_msg = now


        # flag a redraw
        self.update()

    def resizeGL(self, width, height):
        """Called upon window resizing: reinitialize the viewport."""
        # update the window size
        self.width, self.height = width, height
        # paint within the whole window
        gl.glViewport(0, 0, width, height)

if __name__ == '__main__':
    # define a Qt window with an OpenGL widget inside it
    class TestWindow(QtGui.QMainWindow):
        def __init__(self):
            super(TestWindow, self).__init__()
            # initialize the GL widget
            self.widget = GLPlotWidget()
            # put the window at the screen position (100, 100)
            self.setGeometry(100, 100, self.widget.width, self.widget.height)
            self.setCentralWidget(self.widget)
            self.show()

    # show the window
    win = glhelpers.create_window(TestWindow)
