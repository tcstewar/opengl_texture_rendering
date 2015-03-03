import thread

import draw_texture
import fader
import spiker

import OpenGL.GL as gl
import numpy as np

import pygame
class Pygame(object):
    def __init__(self, plot, width, height):
        self.plot = plot
        self.width = width
        self.height = height
        thread.start_new_thread(self.run, ())

    def run(self):
        pygame.init()
        pygame.display.set_mode((self.width, self.height),
                                pygame.OPENGL | pygame.DOUBLEBUF | 
                                pygame.RESIZABLE)
        self.plot.init()
        self.plot.resize(self.width, self.height)
        self.running = True
        while self.running:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.running = False
                if e.type == pygame.VIDEORESIZE:
                    self.plot.resize(*e.dict['size'])
                    pygame.display.set_mode(e.dict['size'],
                                pygame.OPENGL | pygame.DOUBLEBUF | 
                                pygame.RESIZABLE)
                                            

            self.plot.paint()
            pygame.display.flip()
        pygame.display.quit()



class Plot(object):
    def __init__(self):
        pass
    
    def show(self, manager=Pygame, width=600, height=600):
        wm = manager(plot=self, width=width, height=height)


class SparklePlot(Plot):
    def __init__(self, grid_width, grid_height, decay_rate=0.9):
        super(SparklePlot, self).__init__()
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.decay_rate = decay_rate

    def init(self):
        # program for drawing spikes
        self.spiker = spiker.SpikeProgram(self.grid_width, self.grid_height)
        self.spiker.link()

        # program for fading sparkleplot
        self.fader = fader.FadeProgram(self.grid_width, self.grid_height)
        self.fader.link()

        # program for rendering a texture on the screen
        self.draw_texture = draw_texture.DrawTextureProgram()
        self.draw_texture.link()

    def paint(self):
        # fade out the sparkle plot
        self.fader.swap_frame_buffer()
        self.fader.paint_faded(decay=self.decay_rate)

        spikes_per_frame = 100
        data = np.random.randint(self.grid_width * self.grid_height,
                                 size=spikes_per_frame)

        # paint the spikes onto the sparkle plot
        self.spiker.paint_spikes(data)

        # switch to rendering on the screen
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        gl.glViewport(0, 0, self.width, self.height)

        # draw the sparkle plot on the screen
        self.draw_texture.paint(self.fader.get_current_texture())

    def resize(self, width, height):
        # update the window size
        self.width, self.height = width, height
        # paint within the whole window
        gl.glViewport(0, 0, width, height)




    
if __name__ == '__main__':
    sp = SparklePlot(64, 64)
    sp.show()

    import time
    while True:
        time.sleep(1)
