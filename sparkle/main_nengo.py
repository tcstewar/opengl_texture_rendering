import time
import sys
import thread

from PyQt4 import QtGui, QtCore, QtOpenGL
from PyQt4.QtOpenGL import QGLWidget
import OpenGL.GL as gl
import OpenGL.arrays.vbo as glvbo
import numpy as np

import nengo

import spiker
import fader
import draw_texture
import qt_helpers

class QTApp(object):
    def __init__(self):
        self.app = QtGui.QApplication(sys.argv)
        self.app.references = set()
        self.execed = False

    def add(self, window):
        self.app.references.add(window)
        window.show()
        if not self.execed:
            self.app.exec_()
            self.execed = True


app = QTApp()


class SparklePlot(object):
    def __init__(self, ens, width=None, height=None, decay_time=0.1):
        self.ens = ens
        if width is None:
            width = int(np.sqrt(ens.n_neurons))
        self.width = width
        if height is None:
            height = ens.n_neurons // width
            if width * height < ens.n_neurons:
                height += 1
        self.height = height
        self.decay_time = decay_time
        self.win = None

        self.node = nengo.Node(self.gather_data, size_in=ens.n_neurons)
        nengo.Connection(ens.neurons, self.node, synapse=None)

    def gather_data(self, t, x):
        if self.win is not None:
            spikes = np.nonzero(x)[0]
            self.win.widget.add_spikes(spikes)

    def show(self):
        self.win = SparklePlotWindow(self.width, self.height,
                                             self.decay_time)
        app.add(self.win)


class SparklePlotWindow(QtGui.QMainWindow):
    def __init__(self, sparkle_width, sparkle_height, decay_time):
        super(SparklePlotWindow, self).__init__()
        # initialize the GL widget
        self.widget = GLSparklePlotWidget(sparkle_width, sparkle_height,
                                          decay_time)
        # put the window at the screen position (100, 100)
        self.setGeometry(100, 100, self.widget.width, self.widget.height)
        self.setCentralWidget(self.widget)
        self.show()


class GLSparklePlotWidget(QGLWidget):
    # default window size
    width, height = 600, 600
    t_last_msg = time.time()
    spike_count = 0

    def __init__(self, sparkle_width, sparkle_height, decay_time):
        self.sparkle_width = sparkle_width
        self.sparkle_height = sparkle_height
        self.decay_time = decay_time
        self.data = []
        self.last_time = None
        super(GLSparklePlotWidget, self).__init__()

    def initializeGL(self):
        # program for drawing spikes
        self.spiker = spiker.SpikeProgram(self.sparkle_width,
                                          self.sparkle_height)
        self.spiker.link()

        # program for fading sparkleplot
        self.fader = fader.FadeProgram(self.sparkle_width, self.sparkle_height)
        self.fader.link()

        # program for rendering a texture on the screen
        self.draw_texture = draw_texture.DrawTextureProgram()
        self.draw_texture.link()

    def add_spikes(self, spikes):
        #self.fader.swap_frame_buffer(swap=False)
        #self.spiker.paint_spikes(spikes.astype('int32'))
        self.data.append(np.copy(spikes).astype('int32'))
        if len(self.data) > 5:
            self.data = self.data[-5:]

    def paintGL(self):
        now = time.time()
        if self.last_time is None:
            decay = 1.0
        else:
            decay = np.exp((self.last_time - now) / self.decay_time)
        decay = 0.9
        self.last_time = now

        # fade out the sparkle plot
        self.fader.swap_frame_buffer()
        self.fader.paint_faded(decay=decay)

        while len(self.data) > 0:
            data = self.data.pop()
            self.spike_count += len(data)
            # paint the spikes onto the sparkle plot
            self.spiker.paint_spikes(data, scale=1)

        # switch to rendering on the screen
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        gl.glViewport(0, 0, self.width, self.height)

        # draw the sparkle plot on the screen
        self.draw_texture.paint(self.fader.get_current_texture())

        # print out spike rate
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
    model = nengo.Network()
    with model:
        ens = nengo.Ensemble(n_neurons=16*16, dimensions=1)
        stim = nengo.Node(np.sin)
        nengo.Connection(stim, ens)

        p = SparklePlot(ens)

    def runner():
        sim = nengo.Simulator(model)
        while True:
            sim.run(0.001, progress_bar=False)
            time.sleep(0.001)
    thread.start_new_thread(runner, ())
    p.show()
