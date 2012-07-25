#/bin/bash
# Increment release number of manifest file

MANIFESTNAME=$1

REL=`awk '/^#rel/{$2++; print}' $MANIFESTNAME`
sed "s/^#rel.*\+/${REL}/g" $MANIFESTNAME > $MANIFESTNAME.edited
mv $MANIFESTNAME.edited $MANIFESTNAME
