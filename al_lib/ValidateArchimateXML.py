__author__ = u'morrj140'
import os
import sys
import pickle

from Logger import *
logger = setupLogging(__name__)
logger.setLevel(INFO)

from Constants import *
from ArchiLib import ArchiLib

import pytest

def validateArchimateXML(al):
    deleteNodes = list()

    # Collect all elements
    # ae = al.findElements()

    folder = u"Relations"
    eff = al.getElementsFromFolder(folder)[0]
    ae = eff.getchildren()

    n = len(ae)
    # Find relations with source or target invalid
    for node in ae:
        if (n % 100) == 0:
            logger.info(u"Count Down : %d" % n)

        n -= 1
        logger.debug(u"Element - %s[%s]" % (node.get(ARCHI_TYPE)[10:], node.get(u"id")))

        if node.get(ARCHI_TYPE)[10:] in relations:
            id = node.get(u"id")
            source = node.get(u"source")
            target = node.get(u"target")

            logger.debug(u"    Source[%s] - Target[%s]" % (source, target))

            se = al.findElementByID(source)
            te = al.findElementByID(target)

            if se[0] == u" " or te[0] == u" ":
                logger.info(u"Invalid Relation : %s" % node.get(u"id"))
                deleteNodes.append(node)

    for node in deleteNodes:
        logger.info(u"Remove : %s" % node.get(u"id"))
        node.getparent().remove(node)

if __name__ == u"__main__":

    fileArchimate = u"/Users/morrj140/Documents/SolutionEngineering/Archimate Models/DVC v53.archimate"

    fileOutput = u"deduped.archimate"

    al = ArchiLib(fileArchimate)

    validateArchimateXML(al)

    al.outputXMLtoFile(fileOutput)


