import OpenGL.GL as gl
import OpenGL.arrays.vbo as glvbo

import gl_program


class RasterProgram(gl_program.GLProgram):
    """Render a series of ints as white dots."""

    def __init__(self, width, height, n_neurons):
        self.width = width      # size of the grid
        self.height = height    # size of the grid
        self.n_neurons = n_neurons          # number of neurons
        self.scale = gl_program.GLUniform()     # brightness of spike
        super(RasterProgram, self).__init__()

    def vertex_shader(self):
        return """#version 330

            // receive data using the vec2 called position
            layout(location = 0) in vec2 position;

            void main()
            {
                // compute x, y indexes
                int x = %(width)d -1;
                int y = int(position.x * (%(height)d) / %(n_neurons)d);

                // covert to a point inside (-1, 1)
                float xx = (x - %(width)d / 2) * 2.0 / %(width)d;
                float yy = (y - %(height)d / 2) * 2.0 / %(height)d;

                // return the final location of the spike
                gl_Position = vec4(0.999, yy, 0., 1);
            }
            """ % dict(width=self.width, height=self.height, 
                       n_neurons=self.n_neurons)

    def fragment_shader(self):
        return """#version 330
            out vec4 out_color;

            void main()
            {
                // draw a white dot
                out_color = vec4(1., 1., 1., 1.);
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

        # draw the spikes
        gl.glDrawArrays(gl.GL_POINTS, 0, len(data))


