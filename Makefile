CC = gcc
CFLAGS  = -lm -g -Wall
LDFLAGS = -lm -Wall -lGL -lGLEW `imlib2-config --libs` -L/usr/X11/lib -lX11
TARGET = sground

default:  dir main.o shader.o 
	$(CC) $(LDFLAGS) -o bin/${TARGET} obj/main.o obj/shader.o

dir:
	mkdir -p bin obj

main.o:
	$(CC) $(CFLAGS) -c src/main.c -o obj/main.o

shader.o:
	$(CC) $(CFLAGS) -c src/shader.c -o obj/shader.o

clean:
	$(RM) -rf bin obj
