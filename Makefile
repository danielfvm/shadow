build:
	g++ -Wall -lGL -ldl -lGLEW -o sground main.cpp `pkg-config --cflags gtk+-2.0 gtkgl-2.0  --cflags --libs` -lglut -lGLU 

install:
	cp sground /usr/bin/sground
