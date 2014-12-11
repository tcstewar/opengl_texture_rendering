from OpenGLContext import testingcontext
BaseContext = testingcontext.getInteractive()

from OpenGL.GL import *

from OpenGL.arrays import vbo
from OpenGLContext.arrays import *

from OpenGL.GL import shaders

import numpy as np

class TestContext( BaseContext ):
    """Creates a simple vertex shader..."""

    def OnInit( self ):
        VERTEX_SHADER = shaders.compileShader("""#version 120
        void main() {
            gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
        }""", GL_VERTEX_SHADER)

        FRAGMENT_SHADER = shaders.compileShader("""#version 120
        uniform vec4 color;
        void main() {
            gl_FragColor = color;
        }""", GL_FRAGMENT_SHADER)

        self.shader = shaders.compileProgram(VERTEX_SHADER,FRAGMENT_SHADER)


        self.vbo = vbo.VBO(
            array( [
                [ -2,-2, 0 ],
                [  2,-2, 0 ],
                [  2, 2, 0 ],
                [ -2,-2, 0 ],
                [  2, 2, 0 ],
                [ -2, 2, 0 ],
            ],'f')
        )

    counter = 0
    def Render( self, mode):
        """Render the geometry for the scene."""
        shaders.glUseProgram(self.shader)
        self.counter +=1
        r = np.sin(self.counter * 0.01)
        glUniform4f(glGetUniformLocation(self.shader, 'color'), r , 0.0, 0.0, 1.0)
        try:
            self.vbo.bind()
            try:
                glEnableClientState(GL_VERTEX_ARRAY);
                glVertexPointerf( self.vbo )
                glDrawArrays(GL_TRIANGLES, 0, 9)
            finally:
                self.vbo.unbind()
                glDisableClientState(GL_VERTEX_ARRAY);
        finally:
            shaders.glUseProgram( 0 )

        self.triggerRedraw()


if __name__ == "__main__":
    TestContext.ContextMainLoop()
