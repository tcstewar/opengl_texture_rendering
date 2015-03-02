import time
import sys

import pygame
import OpenGL.GL as gl
import OpenGL.arrays.vbo as glvbo
import numpy as np

import spiker
import fader
import draw_texture

sparkle_width = 64
sparkle_height = 64
spikes_per_frame = 100
decay_rate = 0.9


class SparklePlot(object):
    # default window size
    width, height = 600, 600
    t_last_msg = time.time()
    spike_count = 0

    def __init__(self):
        pygame.init()
        pygame.display.set_mode((self.width, self.height),
                                pygame.OPENGL | pygame.DOUBLEBUF)

        # program for drawing spikes
        self.spiker = spiker.SpikeProgram(sparkle_width, sparkle_height)
        self.spiker.link()

        # program for fading sparkleplot
        self.fader = fader.FadeProgram(sparkle_width, sparkle_height)
        self.fader.link()

        # program for rendering a texture on the screen
        self.draw_texture = draw_texture.DrawTextureProgram()
        self.draw_texture.link()

        self.resizeGL(self.width, self.height)

    def paintGL(self):
        # fade out the sparkle plot
        self.fader.swap_frame_buffer()
        self.fader.paint_faded(decay=decay_rate)

        data = np.random.randint(sparkle_width * sparkle_height,
                                 size=spikes_per_frame)


        # generate spike data
        self.spike_count += len(data)
        # paint the spikes onto the sparkle plot
        self.spiker.paint_spikes(data)

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

    def resizeGL(self, width, height):
        """Called upon window resizing: reinitialize the viewport."""
        # update the window size
        self.width, self.height = width, height
        # paint within the whole window
        gl.glViewport(0, 0, width, height)

if __name__ == '__main__':
    sp = SparklePlot()

    quit = False
    while not quit:
        for e in pygame.event.get():
            if e.type in (pygame.QUIT, pygame.KEYDOWN):
                quit = True

        sp.paintGL()
        pygame.display.flip()
