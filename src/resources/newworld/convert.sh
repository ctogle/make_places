#!/bin/sh



for i in *.xml; do OgreXMLConverter -e -q -t -ts -4 $i; done
#for i in ${1}/*.xml; do OgreXMLConverter -e -q -t -ts -4 $i; done



