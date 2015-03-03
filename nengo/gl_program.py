import inspect

import numpy as np
import OpenGL.GL as gl


class GLUniform(object):
    """Simple class for marking uniform variables.

    These are variables that are passed in to shader programs.
    """
    pass

class GLProgram(object):

    # list of known types of shaders
    SHADER_TYPES = dict(vertex_shader=gl.GL_VERTEX_SHADER,
                        fragment_shader=gl.GL_FRAGMENT_SHADER)

    def link(self):
        """Initialize the program for use."""
        program = gl.glCreateProgram()

        # compile all the shaders
        for name, code in self.SHADER_TYPES.items():
            source = getattr(self, name)()
            if source is not None:
                shader = gl.glCreateShader(code)
                gl.glShaderSource(shader, source)
                gl.glCompileShader(shader)
                success = gl.glGetShaderiv(shader, gl.GL_COMPILE_STATUS)
                if success != gl.GL_TRUE:
                    raise RuntimeError(gl.glGetShaderInfoLog(shader))
                gl.glAttachShader(program, shader)
        # link them into a program
        gl.glLinkProgram(program)
        success = gl.glGetProgramiv(program, gl.GL_LINK_STATUS)
        if success != gl.GL_TRUE:
            raise RuntimeError(gl.glGetProgramInfoLog(program))

        self.program = program

        # initialize everything else as needed
        self.initialize_uniforms()
        self.initialize()

    def initialize_uniforms(self):
        """Register the identified variables so we can pass data in later."""
        for name, v in inspect.getmembers(self):
            if isinstance(v, GLUniform):
                setattr(self, name,
                        gl.glGetUniformLocation(self.program, name))

    def initialize(self):
        # override to initialize whatever you need in the subclass
        pass
