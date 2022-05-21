project('Show','C')
cc = meson.get_compiler('c')

sources = [ './src/main.c', './src/shader.c', './src/arghandler.c', './src/opengl.c' ]

deps  = [ dependency('imlib2') ]
deps += [ dependency('GLEW'),dependency('GL') ]
deps += [ dependency('X11') ]
deps += [ dependency('xrandr') ]
deps += [ cc.find_library('m') ]

executable('show', sources, dependencies: deps, install: true )
