# in order to build d2n2, run 
# 	make d2n2_exe
#

CC = gcc

#CFLAGS = -O2 -Wall    # with optimization
CFLAGS = -Wall        # without optimization

OBJS = 	shield2fluka.o

################################################
# the main target
shield2fluka.exe: ${OBJS}
	${CC} -o shield2fluka ${CFLAGS} ${OBJS}

# last function to conatain main fuction
shield2fluka.o: shield2fluka.c
	${CC} ${CFLAGS} -c shield2fluka.c


# removes generated object files:
clean:
	rm -f shield2fluka ${OBJS}
	@echo "all cleaned up!"

