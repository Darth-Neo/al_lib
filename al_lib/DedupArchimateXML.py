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

    saveList(tde, u"Archimate_Duplicate_Elements.lp")

    logger.info(u"--------%d Elements Duplicated--------" % len(tde))

    return tde

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

        if at[10:] not in relations:
            if nat in dupElements:
                logger.debug(u"Duplicate - %s[%d]" % (name, len(dupElements[nat])))
                vl = dupElements[nat]
                vl.append(id)
            else:
                dl = list()
                dl.append(id)
                dupElements[nat] = dl

    return dupElements


def replaceDuplicateProperties(al):

    properties = al.findProperties()

    pd = dict()
    for x in properties:
        parent = x.getparent()

        if parent in pd:
            p = pd[parent]
            pd[parent] = p + 1
        else:
            pd[parent] = 1

    logger.debug(u"Found %d properties duplicated" % len(pd))

    for parent in pd.keys():

        if parent.get(ARCHI_TYPE)[:10] in relations:
            continue

        pa = parent.attrib
        children = parent.getchildren()

        dpa = dict()
        child_list = list()

        # get all properties
        for child in children:

            tag = child.tag
            key = child.get(u"key")
            value = child.get(u"value")

            logger.debug(u"<%s %s[%s]/>" % (tag, key, value))

            if key in dpa and dpa[key] == value:
                child_list.append(child)
            else:
                dpa[key] = value

        logger.info(u"Removing %d Duplicate Properties - %s[%s]" % (len(child_list), pa[u"name"], pa[u"id"]))

        for child in child_list:
            parent.remove(child)

def replaceDuplicateElements(al, td):

    # replace duplicate elements
    for k, v in td.items():
        elementID = v[0]
        element = al.findElementByID(elementID)[0]
        nameElement = element.get(u"name")

        logger.info(u"Removing %d Duplicate Elements - %s[%s]" % (len(v[1:]),  element.get(u"name"), element.get(u"id")))

        # replace where used in a DiagramObject
        for ni in v[1:]:
            ae = al.findElementByID(ni)[0]
            niname = ae.get(u"name")

            de = al.findArchimateElement(ni)

            if de is None:
                logger.warn(u"No Archimate Elements : %s - de" % ni)
                continue

            # remove all DiagramObjects pointing to dump element
            for dea in de:
                if dea.get(ARCHI_TYPE) == u"archimate:DiagramObject":
                    logger.debug(u"    replace '%s[%s]' **with** '%s[%s]'" %
                                (niname, dea.get(u"id"), nameElement, elementID))

                    replaceDuplicateRelations(al, dea.get(u"id"), elementID)

                    dea.set(u"archimateElement", elementID)
                else:
                    logger.info(u"skipped : %s" % dea.get(ARCHI_TYPE))


def replaceDuplicateRelations(al, oldID, newID):

    td = al.findRelationsByID(oldID, Target=True)

    # replace duplicate relations
    element = al.findElementByID(newID)[0]
    nameElement = element.get(u"name")

    logger.info(u"Removing %d Duplicate Relations - %s[%s]" % (len(td),  element.get(u"name"), element.get(u"id")))

    for dea in td:
        if dea.get(u"source") == oldID:
            na = al.findElementByID(oldID)[0]
            name = na.get(u"name")
            id = na.get(u"id")
            logger.info(u"    %s : replace source '%s[%s]' **with** '%s[%s]'" %
                        (dea.get(ARCHI_TYPE)[10:], name, id, nameElement, newID))

            dea.set(u"source", newID)

        elif dea.get(u"target") == oldID:
            na = al.findElementByID(oldID)[0]
            name = na.get(u"name")
            id = na.get(u"id")
            logger.info(u"    %s : replace target '%s[%s]' **with** '%s[%s]'" %
                        (dea.get(ARCHI_TYPE)[10:], name, id, nameElement, newID))
            dea.set(u"target", newID)

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

@pytest.mark.Archi
def test_DedupArchimateXML ():

    fileArchimate = u"test" + os.sep + u"Testing.archimate"

    fileOutput = u"test" + os.sep + u"deduped.archimate"

    al = ArchiLib(fileArchimate)

    ae = al.findElements()

    logger.info(u"Length : %d" % len(ae))

    dupElements = findDups(ae)

    tde, tdr = logDupElements(dupElements)

    replaceDuplicateElements(al, tde)

    replaceDuplicateRelations(al, tde)

    validateArchimateXML(al)

    al.outputXMLtoFile(fileOutput)

if __name__ == u"__main__":

    # These were bad nodes in the file before anythng else
    # Argh...
    removeNodes = (u'd5805eef', u'58e158b8', u'e9f564f8', u'2f2190de', u'edf6ea10', u'5d99f417', u'f8d0a988',
                   u'5f20e703', u'ed8313b6', u'3b11a056', u'ccfceb63', u'761b2d00')

    fileArchimate = u"/Users/morrj140/Documents/SolutionEngineering/Archimate Models/DVC v51.archimate"

    fileOutput = u"deduped.archimate"

    al = ArchiLib(fileArchimate)

    ae = al.findElements()

    logger.info(u"Length : %d" % len(ae))

    dupElements = findDups(ae)

    tde = logDupElements(dupElements)

    replaceDuplicateElements(al, tde)

    replaceDuplicateProperties(al)

    #validateArchimateXML(al)

    al.outputXMLtoFile(fileOutput)


