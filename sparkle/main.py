import time

from PyQt4 import QtGui, QtCore, QtOpenGL
from PyQt4.QtOpenGL import QGLWidget
import OpenGL.GL as gl
import OpenGL.arrays.vbo as glvbo
import numpy as np

import spiker
import fader
import draw_texture
import qt_helpers

sparkle_width = 64
sparkle_height = 64
spikes_per_frame = 1
decay_time = 0.01


class GLPlotWidget(QGLWidget):
    # default window size
    width, height = 600, 600
    t_last_msg = time.time()
    spike_count = 0
    data = np.random.randint(sparkle_width * sparkle_height,
                                 size=spikes_per_frame)


    def initializeGL(self):
        # program for drawing spikes
        self.spiker = spiker.SpikeProgram(sparkle_width, sparkle_height)
        self.spiker.link()

        # program for fading sparkleplot
        self.fader = fader.FadeProgram(sparkle_width, sparkle_height)
        self.fader.link()

        # program for rendering a texture on the screen
        self.draw_texture = draw_texture.DrawTextureProgram()
        self.draw_texture.link()

        self.last_time = None

    def paintGL(self):
        now = time.clock()
        if self.last_time is None:
            decay = 0.0
            self.dt = None
        else:
            dt = now - self.last_time
            if self.dt is None:
                self.dt = dt
            else:
                self.dt = (0.9) * self.dt + (0.1) * dt
            decay = np.exp(-self.dt / decay_time)
        self.last_time = now

        # fade out the sparkle plot
        self.fader.swap_frame_buffer()
        self.fader.paint_faded(decay=decay)

        #data = self.data
        data = np.random.randint(sparkle_width * sparkle_height,
                                 size=spikes_per_frame)

        # generate spike data
        self.spike_count += len(data)
        # paint the spikes onto the sparkle plot
        self.spiker.paint_spikes(data, scale = 1.0 - decay)

        # switch to rendering on the screen
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        gl.glViewport(0, 0, self.width, self.height)

        # draw the sparkle plot on the screen
        self.draw_texture.paint(self.fader.get_current_texture())

        # print out spike rate
        now = time.time()
        if now > self.t_last_msg + 1:
            dt = now - self.t_last_msg
            rate = self.spike_count * 0.000001 / dt
            print 'Mspikes per second = %g' % rate
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
    win = qt_helpers.create_window(TestWindow)
