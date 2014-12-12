import numpy as np
import OpenGL.GL as gl
import OpenGL.arrays.vbo as glvbo

import gl_program


class DrawTextureProgram(gl_program.GLProgram):
    """A simple program that draws a given texture to the full viewport."""

    def __init__(self):
        # external input indicating which texture index to use
        self.texture1 = gl_program.GLUniform()
        super(DrawTextureProgram, self).__init__()

    def vertex_shader(self):
        return """#version 110

            // do nothing, and pass the texture coordinates on to the
            // fragment shader
            void main()
            {
                gl_Position = ftransform();
                gl_TexCoord[0] = gl_MultiTexCoord0;
            }
            """
    def fragment_shader(self):
        return """#version 110
            uniform sampler2D texture1;

            // set the color based on the texture coordinates in the
            // given texture
            void main()
            {
                gl_FragColor = texture2D(texture1, gl_TexCoord[0].st);
            }
            """

    def initialize(self):
        # rendering this square will fill the whole screen
        # values are x,y,z,u,v  (vertex, texture coordinates)

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

    def paint(self, texture):
        """Draw the given texture at full screen."""

        # make sure we can use VBOs
        gl.glEnableVertexAttribArray(0)

        # activate the program
        gl.glUseProgram(self.program)

        # indicate the texture will be set by GL_TEXTURE0
        gl.glUniform1i(self.texture1, 0)

        # turn on texture mapping and bind to the given texture
        gl.glEnable(gl.GL_TEXTURE_2D)
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, texture)

        # activate the square to be rendered
        self.square.bind()

        # indicate we are setting vertex and tex_coord data in the VBO
        gl.glEnableClientState(gl.GL_VERTEX_ARRAY);
        gl.glEnableClientState(gl.GL_TEXTURE_COORD_ARRAY);
        # vertex is first 3 floats in the VBO
        gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT,
                                 gl.GL_FALSE, 5*4, None)
        # texture coords are the 2 floats after the first 3 in the VBO
        gl.glTexCoordPointer(2, gl.GL_FLOAT, 5*4, self.square + 3*4)

        # draw the textured square
        gl.glDrawArrays(gl.GL_TRIANGLES, 0, 6)
