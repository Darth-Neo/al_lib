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
    except IOError, msg:
        logger.error(u"%s - %s" % (str(sys.exc_info()[0]), msg))

def loadList(listFile):
    nl = None

    if not os.path.exists(listFile):
        logger.error(u"%s : Does Not Exist!" % listFile)

    try:
        with open(listFile, u"rb") as cf:
            nl = pickle.load(cf)
            logger.debug(u"Loaded : %s" % (listFile))
    except IOError, msg:
        logger.error(u"%s - %s" % (str(sys.exc_info()[0]), msg))

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
            at = xa[ARCHI_TYPE].rstrip()
            id = xa[u"id"].rstrip()
            name = xa[u"name"].rstrip()
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

        if len(child_list) != 0:
            logger.info(u"Removing %d Duplicate Properties - %s[%s]" % (len(child_list), pa[u"name"], pa[u"id"]))

        for child in child_list:
            parent.remove(child)

def replaceDuplicateElements(al, td):

    # replace duplicate elements
    for k, v in td.items():
        elementID = v[0]
        element = al.findElementByID(elementID)[0]
        nameElement = element.get(u"name")

        if len(v[1:]) != 0:
            logger.info(u"Removing %d Duplicate Elements - %s[%s]" % (len(v[1:]),  element.get(u"name"), element.get(u"id")))

        # replace where used in a DiagramObject
        for ni in v[1:]:
            ae = al.findElementByID(ni)[0]
            niname = ae.get(u"name")

            de = al.findArchimateElement(ni)

            if de is None:
                logger.warn(u"No Archimate Elements : %s - de" % ni)
                continue

            # point all DiagramObjects to element
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

def DedupArchimate(fileArchimateDedupInput, fileArchimateDedupOutput):

    assert (os.path.isfile(fileArchimateDedupInput) is True)
    logger.info(u"Exists : %s" % fileArchimateDedupInput)

    al = ArchiLib(fileArchimateDedupInput)
    assert (al is not None)

    ae = al.findElements()

    lea = len(ae)
    assert (lea > 0)
    logger.info(u"Length : %d" % lea)

    dupElements = findDups(ae)

    tde = logDupElements(dupElements)

    replaceDuplicateElements(al, tde)

    al.outputXMLtoFile(fileArchimateDedupOutput)


if __name__ == u"__main__":

    fileArchimate = os.getcwd() + os.sep + u"test" + os.sep + u"testDup"

    fileArchimate = u"deduped.archimate"

    DedupArchimate(fileArchimate, fileArchimate)


