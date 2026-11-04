#!/bin/sh
# Copy the tested core into each sketch folder (the Arduino IDE only compiles files inside the sketch folder).
set -e
here=$(dirname "$0"); core="$here/../core"
cp "$core"/include/saos_core.h "$core"/include/saos_proto.h "$core"/include/saos_calib.h "$core"/src/saos_core.cpp "$core"/src/saos_proto.cpp "$core"/src/saos_calib.cpp "$here/mega_v2/"
cp "$core"/include/saos_core.h "$core"/include/saos_proto.h "$core"/include/saos_gateway.h "$core"/src/saos_core.cpp "$core"/src/saos_proto.cpp "$core"/src/saos_gateway.cpp "$here/esp32_gateway/"
echo "synced"
