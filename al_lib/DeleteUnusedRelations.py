__author__ = u'morrj140'
import os
import sys
import pickle

from Logger import *
logger = setupLogging(__name__)
logger.setLevel(INFO)

from Constants import *
from ArchiLib import ArchiLib

def RemoveUsedRelations(al):
    dupElements = dict()

    for k, v in al.dictEdges.items():

        try:
            node_type = v.get(ARCHI_TYPE)[10:]
            if node_type in relations:
                x = al.findElementByID(k)[0]
                xa = x.attrib

                sid = xa[u"source"]
                tid = xa[u"target"]

                al.findDiagramObject()

                if sid not in al.dictNodes:
                    dupElements[sid] = x
                    logger.debug(u"%s - %s" % (sid, x.attrib))

                if tid not in al.dictNodes:
                    dupElements[tid] = x
                    logger.debug(u"%s - %s" % (x.get(ARCHI_TYPE), x.attrib))

        except Exception, e:
            if xa[ARCHI_TYPE] in relations:
                logger.error(u"%s - %s[%s]" % (type(e), e.message, xa[ARCHI_TYPE]))
            continue


    for k, v in dupElements.items():
        logger.info(u"Removing : %s" % k)
        parent = v.getparent()
        parent.remove(v)


if __name__ == u"__main__":

    fileArchimate = u"/Users/morrj140/Documents/SolutionEngineering/Archimate Models/DVC v2.1.archimate"

    fileOutput = u"Remove_Relations.archimate"

    al = ArchiLib(fileArchimate)

    dupElements = RemoveUsedRelations(al)

    al.outputXMLtoFile(fileOutput)


