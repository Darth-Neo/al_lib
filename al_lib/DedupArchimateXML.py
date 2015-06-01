__author__ = u'morrj140'
import os
import sys
import pickle

from Logger import *
logger = setupLogging(__name__)
logger.setLevel(INFO)

from Constants import *
from ArchiLib import ArchiLib

def saveList(nl, listFile):
    try:
        logger.debug(u"Saving  : %s" % (listFile))
        with open(listFile, u"wb") as cf:
            pickle.dump(nl, cf)
    except:
        logger.error(str(sys.exc_info()[0]))

def loadList(listFile):
    nl = None

    if not os.path.exists(listFile):
        logger.error(u"%s : Does Not Exist!" % listFile)

    try:
        with open(listFile, u"rb") as cf:
            nl = pickle.load(cf)
            logger.debug(u"Loaded : %s" % (listFile))
    except:
        logger.error(str(sys.exc_info()[0]))

    return nl

def logEntities(dictEnty):
    dl = dictEnty.items()

    nl = sorted(dl, key=lambda c: len(c[1]), reverse=True)

    for k, v in nl:
        if isinstance(v, list):
            de = k.split(u"|")
            name = de[0]
            at = de[1]
            logger.info(u"%s[%s]-%d" % (name, at, len(v)))

def logDupElements(dupElements):
    logger.debug(u"--------Elements and Relations---------")

    tde = dict()
    tdr = dict()

    for k, v in dupElements.items():
        if len(dupElements[k]) > 1:
            de = k.split(u"|")
            name = de[0]
            at = de[1]

            if at[10:] not in relations:
                logger.debug(u"%s[%s] => %d" % (name, at, len(v)))
                tde[k] = v
            else:
                logger.debug(u"%s[%s] => %d" % (name, at, len(v)))
                tdr[k] = v

    saveList(tde, u"Archimate_Duplicate_Elements.lp")
    saveList(tdr, u"Archimate_Duplicate_Relations.lp")

    logger.info(u"--------%d Elements Duplicated--------" % len(tde))
    logEntities(tde)

    logger.info(u"--------%d Relations Duplicated--------" % len(tdr))
    logEntities(tdr)

    return tde, tdr

def findDups(ae):
    dupElements = dict()

    for x in ae:

        xa = x.attrib

        try:
            at = xa[ARCHI_TYPE]
            id = xa[u"id"]
            name = xa[u"name"]
            nat = name + u"|" + at

        except Exception, e:
            if xa[ARCHI_TYPE] in relations:
                logger.error(u"%s - %s[%s]" % (type(e), e.message, xa[ARCHI_TYPE]))

            continue

        logger.debug(u"%s - %s" % (x.get(ARCHI_TYPE), x.attrib))

        if nat in dupElements:
            logger.debug(u"Duplicate - %s[%d]" % (name, len(dupElements[nat])))
            vl = dupElements[nat]
            vl.append(id)
        else:
            dl = list()
            dl.append(id)
            dupElements[nat] = dl

    return dupElements

def replaceDuplicateElements(al, td):

    # replace duplicate elements
    for k, v in td.items():
        elementID = v[0]

        # replace where used in a DiagramObject
        for ni in v[1:]:
            de = al.findArchimateElement(ni)

            if de is None:
                continue

            try:
                dee = de[0]
            except:
                logger.warn(u"No Archimate Elements : %s" % ni)
                continue

            for dea in dee:
                if dea.get(ARCHI_TYPE) == u"archimate:DiagramObject":
                    logger.info(u"replace %s with %s" % (ni, elementID))
                    dee.set(u"archimateElement", elementID)

def replaceDuplicateRelations(al, td):

    # replace duplicate elements
    for k, v in td.items():
        elementID = v[0]

        # replace where used in a DiagramObject
        for ni in v[1:]:

            de = al.findRelationsByID(ni)

            if de is None:
                continue

            for dea in de:
                if dea.get(ARCHI_TYPE)[10:] in relations:
                    if dea.get(u"source") == ni:
                        logger.info(u"replace source %s with %s" % (ni, elementID))
                        dea.set(u"source", elementID)

                    elif dea.get(u"target") == ni:
                        logger.info(u"replace target %s with %s" % (ni, elementID))
                        dea.set(u"target", elementID)

if __name__ == u"__main__":

    fileArchimate = u"/Users/morrj140/Documents/SolutionEngineering/Archimate Models/DVC v47.archimate"

    al = ArchiLib(fileArchimate)

    al.logTypeCounts()

    ae = al.findElements()

    logger.info(u"Length : %d" % len(ae))

    dupElements = findDups(ae)

    tde, tdr = logDupElements(dupElements)

    replaceDuplicateElements(al, tde)

    replaceDuplicateRelations(al, tde)

    al.outputXMLtoFile(u"deduped.archimate")

    al.logTypeCounts()
