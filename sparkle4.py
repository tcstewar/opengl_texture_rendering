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
    gl_Position = vec4((x-128)*0.005, (y-128)*0.005, 0., 1.);
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

    def paintGL(self):
        """Paint the scene."""
        # clear the buffer
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

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
