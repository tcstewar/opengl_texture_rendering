import OpenGL.GL as gl
import OpenGL.arrays.vbo as glvbo

import gl_program


class SpikeProgram(gl_program.GLProgram):
    """Render a series of ints as white dots."""

    def __init__(self, width, height):
        self.width = width      # size of the grid
        self.height = height    # size of the grid
        self.scale = gl_program.GLUniform()     # brightness of spike
        super(SpikeProgram, self).__init__()

    def vertex_shader(self):
        return """#version 330

            // receive data using the vec2 called position
            layout(location = 0) in vec2 position;

            void main()
            {
                // compute x, y indexes
                int x = int(position.x / %(width)d);
                int y = int(position.x - (x*%(width)d) + 1);

                // covert to a point inside (-1, 1)
                float xx = (x - %(width)d / 2) * 2.0 / %(width)d;
                float yy = (y - %(height)d / 2) * 2.0 / %(height)d;

                // return the final location of the spike
                gl_Position = vec4(xx, yy, 0., 1);
            }
            """ % dict(width=self.width, height=self.height)

    def fragment_shader(self):
        return """#version 330
            out vec4 out_color;
            uniform float scale;

            void main()
            {
                //vec4 alpha = texture2D(texture1, gl_TexCoord[0].st).aaaa;
                // draw a white dot
                out_color = vec4(1., 1., 1., scale);
            }
            """

    def paint_spikes(self, data, scale=1.0):
        """Render the given array of neuron indexes."""

        # convert the data to a VBO
        vbo = glvbo.VBO(data)
        vbo.bind()

        # tell OpenGL that the VBO contains an array of vertices
        gl.glEnableVertexAttribArray(0)

        # array is a list of unsigned ints
        gl.glVertexAttribPointer(0, 1, gl.GL_UNSIGNED_INT,
                                 gl.GL_FALSE, 0, None)

        # activate the program
        gl.glUseProgram(self.program)
        gl.glUniform1f(self.scale, scale)

        # draw the spikes
        gl.glDrawArrays(gl.GL_POINTS, 0, len(data))

