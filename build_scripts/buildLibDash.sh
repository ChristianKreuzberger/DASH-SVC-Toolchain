#!/bin/bash

cd libdash/libdash
mkdir build
cd build
cmake ../
make

if [ $? -ne 0 ] ; then
    echo "Failed building libdash";
    # go back to the main directory
    cd ../../../
    exit -3
fi

# go back to the main directory
cd ../../../
exit 0
