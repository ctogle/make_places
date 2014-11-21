#!/bin/sh



for i in *.xml; do OgreXMLConverter -e -q -t -ts -4 $i; done



