from OpenGL import GL as gl

from shader import Shader
from config import Config

import pyaudio
import numpy as np
np.set_printoptions(suppress=True)

passed = 0
CHUNK = 512
BARS = 64

shader = Shader({
    gl.GL_VERTEX_SHADER: '''
        #version 330 core
        layout(location = 0) in vec2 pos;
        void main() {
          gl_Position.xy = pos;
          gl_Position.w = 1.0;
        }
        ''',
    gl.GL_FRAGMENT_SHADER: '''
        #version 330 core
        uniform vec2 resolution;
        const int MAX = ''' + str(BARS-1) + ''';
        uniform float bar[MAX+1];
        void main() {
          vec2 p = gl_FragCoord.xy / resolution.xy;
          vec4 color = vec4(0);
          float nr = int(p.x * MAX) % MAX;
          float step = p.x * MAX - nr;
          float level = bar[int(nr)];
          float nlevel = bar[int(nr)+1];
          float dif = distance(p.y, 0.5) - mix(level, nlevel, step);
          color = vec4(vec3(1.0), 1.0 - pow(max(dif, 0), 0.2));
          gl_FragColor = color;
        }
    ''',
})

p=pyaudio.PyAudio()
c = p.get_device_count()
for i in range(c):
  print(p.get_device_info_by_index(i))
stream=p.open(format=pyaudio.paInt16,channels=1,rate=44100, input=True, frames_per_buffer=int(CHUNK*2), input_device_index=6)

def render(dt):
  global passed, stream
  global CHUNK

  passed += dt

  width = int(Config.WIDTH * Config.QUALITY)
  height = int(Config.HEIGHT * Config.QUALITY)

  data = stream.read(CHUNK)
  wf_data = np.frombuffer(data, dtype=np.int16)
  wf_data = wf_data * 0.001

  reduced_data = []
  for i in range(BARS):
    reduced_data.append(wf_data[int(i * (len(wf_data) / BARS))])

  shader.bind()
  gl.glUniform2f(shader.get_uniform("resolution"), width, height)
  gl.glUniform1fv(shader.get_uniform("bar"), BARS, reduced_data)
  gl.glDrawArrays(gl.GL_TRIANGLES, 0, 6)
