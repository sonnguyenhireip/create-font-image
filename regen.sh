#!/bin/bash
cd /Users/hireip-02/Documents/techverse/create-font-image
# Remove generated output and recreate both PNG thumbnails and SVGs
rm -rf thumbnails svgs
./run_png.sh
./run_svg.sh
