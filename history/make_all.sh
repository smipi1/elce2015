#!/bin/sh

URI="https://www.kernel.org/pub/linux/kernel"
IMAGES="
	linux-3.0
	linux-3.1
	linux-3.2
	linux-3.3
	linux-3.4
	linux-3.5
	linux-3.6
	linux-3.7
	linux-3.8
	linux-3.9
	linux-3.10
	linux-3.11
	linux-3.12
	linux-3.13
	linux-3.14
	linux-3.15
	linux-3.16
	linux-3.17
	linux-3.18
	linux-3.19
	linux-4.0
	linux-4.1
"
EXT=tar.xz

mkdir -p dl
mkdir -p build_dir
mkdir -p bin
DL=`readlink -e dl`
BUILD_DIR=`readlink -e build_dir`
BIN_DIR=`readlink -e bin`

cd ${DL}
for i in ${IMAGES}; do
	
	VERSION=${i##*-}
	BASE_VER=${VERSION%%.*}
	URL_DIR=v${BASE_VER}.x
	ARCHIVE=$i.${EXT}
	URL=${URI}/${URL_DIR}/${ARCHIVE}
	SRC_DIR=${BUILD_DIR}/$i
	DEST_DIR=${BIN_DIR}/$i
	
	mkdir -p ${DEST_DIR}
	cd ${DL} && wget ${URL} && \
	cd ${BUILD_DIR} && tar -xf ${DL}/${ARCHIVE} && \
	cd ${SRC_DIR} && \
		make -j allnoconfig && \
		make -j && \
		cp vmlinux ${DEST_DIR} && \
		cp arch/x86/boot/bzImage ${DEST_DIR} && \
		rm -rf ${SRC_DIR}

done

