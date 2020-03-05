# Darknet

## Compile Darknet with OpenCV
`cd $HOME/GitHub`

`git clone https://github.com/HEBOS/darknet.git`

`cd $HOME/GitHub`

 `make -j8`
 
## Compile Darknet for DEBUG mode
`cd $HOME/GitHub/darknet`
`vi Makefile`

    Change the following lines:
    
    DEBUG=1
    
    ifeq ($(DEBUG), 1)
    OPTS= -O1 -g
 
    Compile Darknet as described in the previous section.
    
## Check Memory Leaks Using Valgrind

### Install Valgrind

`cd $HOME/GitHub`

`wget https://sourceware.org/pub/valgrind/valgrind-3.15.0.tar.bz2`

`tar -xvf valgrind-3.15.0.tar.bz2`

`cd valgrind-3.15.0`

`export CC=aarch64-linux-gnu-gcc`

`export LD=aarch64-linux-gnu-ld`

`export AR=aarch64-linux-gnu-ar`

`./autogen.sh`

`mkdir Inst`

`./configure --prefix=`pwd`/Inst --host=aarch64-unknown-linux --enable-only64bit`

`make -j4`

`make -j4 install`

### Check Memory Leaks
    
    Compile Darknet for DEBUG mode, as described above.
    
`cd $HOME/GitHub/darknet`

    Run the following line before the first time only.

`cp $HOME/GitHub/sports-replay-local/networks/yolov3/yolov3.weights .`

`$HOME/GitHub/valgrind/valgrind-3.15.0/Inst/bin/valgrind --leak-check=full --show-reachable=yes ./darknet detector test ./cfg/coco.data ./cfg/yolov3.cfg ./yolov3.weights data/dog.jpg -i 0 -thresh 0.25`