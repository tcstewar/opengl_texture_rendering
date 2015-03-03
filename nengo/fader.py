import numpy as np
import OpenGL.GL as gl
import OpenGL.arrays.vbo as glvbo

import gl_program


class FadeProgram(gl_program.GLProgram):
    """Double-buffered fading algorithm.

    Contains two textures, and renders one onto the other, but slightly
    darker.  Each frame you can indicate how much darker to go using the
    decay uniform variable.
    """
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.texture1 = gl_program.GLUniform()  # which texture core to use
        self.decay = gl_program.GLUniform()     # multiplicative decay
        self.usingA = True                      # which buffer are we using
        super(FadeProgram, self).__init__()

    def vertex_shader(self):
        return """#version 110

            void main()
            {
                // just pass the data on to the fragment shader
                gl_Position = ftransform();
                gl_TexCoord[0] = gl_MultiTexCoord0;
            }
            """
    def fragment_shader(self):
        return """#version 110
            uniform sampler2D texture1;
            uniform float decay;

            void main()
            {
                // look up the texture value, then decay it a bit
                gl_FragColor = texture2D(texture1, gl_TexCoord[0].st) * decay;
            }
            """

    def initialize(self):
        # create the textures
        self.textureA = gl.glGenTextures(1)
        print 'textureA', self.textureA
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.textureA)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER,
                           gl.GL_NEAREST)  # don't blur the texture
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER,
                           gl.GL_NEAREST)  # don't blur the texture
        gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S,
                           gl.GL_CLAMP_TO_EDGE)  # don't wrap around
        gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T,
                           gl.GL_CLAMP_TO_EDGE)  # don't wrap around
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA,
                           self.width, self.height, 0,
                           gl.GL_RGBA, gl.GL_UNSIGNED_SHORT, None)


        self.textureB = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.textureB)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER,
                           gl.GL_NEAREST)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER,
                           gl.GL_NEAREST)
        gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S,
                           gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T,
                           gl.GL_CLAMP_TO_EDGE)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA,
                           self.width, self.height, 0,
                           gl.GL_RGBA, gl.GL_UNSIGNED_SHORT, None)

        # create the frame buffers
        self.fbA = gl.glGenFramebuffers(1)
        self.fbB = gl.glGenFramebuffers(1)

        # create a convenient square for rendering
        # data is in (x, y, z, u, v) format
        self.square = glvbo.VBO(
            np.array( [
                [ -1,-1, 0, 0, 0 ],
                [  1,-1, 0, 1, 0 ],
                [  1, 1, 0, 1, 1 ],
                [ -1,-1, 0, 0, 0 ],
                [  1, 1, 0, 1, 1 ],
                [ -1, 1, 0, 0, 1 ],
            ],'f')
        )

    def swap_frame_buffer(self, swap=True):
        """Switch buffers so we alternate which one we're rendering to."""
        if swap:
            self.usingA = not self.usingA

        if self.usingA:
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbA);
            gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER,
                  gl.GL_COLOR_ATTACHMENT0,
                  gl.GL_TEXTURE_2D, self.textureA, 0);
        else:
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbB);
            gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER,
                  gl.GL_COLOR_ATTACHMENT0,
                  gl.GL_TEXTURE_2D, self.textureB, 0);

        # reset the geometry so we render to the whole image
        gl.glViewport(0, 0, self.width, self.height)


    def paint_faded(self, decay):
        """Draw a faded version of the old texture onto the new texture."""

        # activate the program and set parameters
        gl.glUseProgram(self.program)
        gl.glUniform1i(self.texture1, 0)  # indicate we use GL_TEXTURE0
        gl.glUniform1f(self.decay, decay)

        # set up the texture to map
        gl.glEnable(gl.GL_TEXTURE_2D)
        gl.glActiveTexture(gl.GL_TEXTURE0)
        if self.usingA:
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.textureB)
        else:
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.textureA)

        # a simple square filling the whole view
        self.square.bind()

        # activate using VBOs for the vertices
        gl.glEnableVertexAttribArray(0)

        # indicate that the VBO has texture and vertex data
        gl.glEnableClientState(gl.GL_VERTEX_ARRAY);
        gl.glEnableClientState(gl.GL_TEXTURE_COORD_ARRAY);

        # indicate where the vertex and texture data is
        gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT,
                                 gl.GL_FALSE, 5*4, None)
        gl.glTexCoordPointer(2, gl.GL_FLOAT, 5*4, self.square + 3*4)

        # draw the square
        gl.glDrawArrays(gl.GL_TRIANGLES, 0, 6)

    def get_current_texture(self):
        """Helper function to get a handle to the active texture."""
        if self.usingA:
            return self.textureA
        else:
            return self.textureB

