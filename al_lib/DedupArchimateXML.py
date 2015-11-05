__author__ = u'morrj140'
import os
import sys
import pickle

from Logger import *
logger = setupLogging(__name__)
logger.setLevel(INFO)

from Constants import *
from ArchiLib import ArchiLib

class DedupArchimateXML(object):

    def __init__(self, fileArchimate=None):

        if not(fileArchimate is None):
            self.fileArchimate = fileArchimate

        self.al = ArchiLib(fileArchimate)

    @staticmethod
    def saveList(nl, listFile):
        try:
            logger.debug(u"Saving  : %s" % listFile)
            with open(listFile, u"wb") as cf:
                pickle.dump(nl, cf)
        except IOError, msg:
            logger.error(u"%s - %s" % (str(sys.exc_info()[0]), msg))

    @staticmethod
    def loadList(listFile):
        nl = None

        if not os.path.exists(listFile):
            logger.error(u"%s : Does Not Exist!" % listFile)

        try:
            with open(listFile, u"rb") as cf:
                nl = pickle.load(cf)
                logger.debug(u"Loaded : %s" % listFile)
        except IOError, msg:
            logger.error(u"%s - %s" % (str(sys.exc_info()[0]), msg))

        return nl

    @staticmethod
    def logEntities(dictEnty):
        dl = dictEnty.items()

        nl = sorted(dl, key=lambda c: len(c[1]), reverse=True)

        for k, v in nl:
            if isinstance(v, list):
                de = k.split(u"|")
                name = de[0]
                at = de[1]
                logger.info(u"%s[%s]-%d" % (name, at, len(v)))

    @staticmethod
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

        DedupArchimateXML.saveList(tde, u"Archimate_Duplicate_Elements.lp")

        logger.info(u"--------%d Elements Duplicated--------" % len(tde))

        return tde

    def _findDuplicates(self, ae):

        dupElements = dict()
        dupRelations = dict()

        n = 0
        for x in ae:

            xa = x.attrib

            try:
                at = xa[ARCHI_TYPE].rstrip()
                id = xa[u"id"].rstrip()
                name = xa[u"name"].rstrip()
                nat = name + u"|" + at

            except Exception, e:
                if at in relations:
                    logger.error(u"%d %s - %s[%s]" % (n, type(e), e.message, xa[ARCHI_TYPE]))
                continue

            logger.info(u"%d - Checking - %s[%s]" % (n, at[10:], x.get(ID)))

            if at[10:] in entities:
                if nat in dupElements:
                    logger.debug(u"%d    ---- Duplicate Element! - %s[%d] ----" % (n, name, len(dupElements[nat])))
                    lt = dupElements[nat]
                    lt.append(id)
                    dupElements[nat] = lt
                else:
                    dl = list()
                    dl.append(id)
                    dupElements[nat] = dl
                    logger.info(u"entities Skipped %s" % id)

            elif at[10:] in relations:
                logger.info(u"%s" % at[10:])
                if nat in dupRelations:
                    logger.debug(u"%d    ++++ Duplicate Relation! - %s[%d] ++++" % (n, name, len(dupRelations[nat])))
                    lt = dupRelations[nat]
                    lt.append(id)
                    dupRelations[nat] = lt
                else:
                    dl = list()
                    dl.append(id)
                    dupRelations[nat] = dl
                    logger.info(u"relations Skipped %s" % id)
            n += 1

        # Note: you must work through all elements before you find a duplicate
        ne = dict()
        n = 0
        for x, y in dupElements.items():
            if len(y) > 1:
                logger.info(u"%d ----Duplicate Element! = %s ----" % (n, x))
                ne[x] = y
            else:
                logger.info(u"Skipped %s" % y)
            n += 1

        n = 0
        nr = dict()
        for x, y in dupRelations.items():
            if len(y) > 1:
                logger.info(u"%d #### Duplicate Relation! = %s ####" % (n, x))
                nr[x] = y
            else:
                logger.info(u"Skipped %s" % y)

            n += 1

        logger.debug(u"_findDuplicates - Complete")

        return ne, nr

    def _replaceDuplicateElements(self, td):

        # replace duplicate elements
        for k, v in td.items():
            elementID = v[0]
            element = self.al.findElementByID(elementID)[0]
            nameElement = element.get(u"name")

            if len(v[1:]) != 0:
                logger.info(u"Removing %d Duplicate Elements - %s[%s]" %
                            (len(v[1:]),  element.get(u"name"), element.get(u"id")))

            # replace where used in a DiagramObject
            for ni in v[1:]:
                ae = self.al.findElementByID(ni)[0]
                niname = ae.get(u"name")

                de = self.al.findArchimateElement(ni)

                if de is None:
                    logger.warn(u"No Archimate Elements : %s - de" % ni)
                    continue

                # point all DiagramObjects to element
                for dea in de:
                    if dea.get(ARCHI_TYPE) == u"archimate:DiagramObject":
                        logger.debug(u"    replace '%s[%s]' **with** '%s[%s]'" %
                                    (niname, dea.get(u"id"), nameElement, elementID))
                        dea.set(u"archimateElement", elementID)
                    else:
                        logger.info(u"skipped : %s" % dea.get(ARCHI_TYPE))

                self._replaceDuplicateRelations(ni, elementID)

    def _replaceDuplicateRelations(self, oldID, newID):

        logger.info(u"Replace Duplicate Relations : %s - %s" % (oldID, newID))

        td = self.al.findRelationsByID(oldID, Target=True)

        element = self.al.findElementByID(newID)[0]
        nameElement = element.get(NAME)

        if len(td) > 0:
            logger.info(u"Removing %d Duplicate Relations - %s[%s]" % (len(td),  element.get(NAME), element.get(ID)))

        n = 0
        for dea in td:
            if dea.get(u"source") == oldID:
                na = self.al.findElementByID(oldID)[0]
                name = na.get(u"name")
                id = na.get(u"id")
                logger.info(u"%d    %s : replace source '%s[%s]' **with** '%s[%s]'" %
                            (n, dea.get(ARCHI_TYPE)[10:], name, id, nameElement, newID))
                dea.set(u"source", newID)

            elif dea.get(u"target") == oldID:
                na = self.al.findElementByID(oldID)[0]
                name = na.get(u"name")
                id = na.get(u"id")
                logger.info(u"%d    %s : replace target '%s[%s]' **with** '%s[%s]'" %
                            (n, dea.get(ARCHI_TYPE)[10:], name, id, nameElement, newID))
                dea.set(u"target", newID)

            n += 1

    def _replaceDuplicateProperties(self):

        properties = self.al.findProperties()

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


    def Dedup(self, fileArchimateOutput=u"dedup_test.archimate"):

        ae = self.al.findElements()

        self._typeCountStart = self.al.logTypeCounts()

        dupElements, dupRelations = self._findDuplicates(ae)

        self._replaceDuplicateElements(dupElements)

        # self._replaceDuplicateElements(dupRelations)

        self.al.outputXMLtoFile(fileArchimateOutput)

        self.al = ArchiLib(fileArchimateOutput)

        self._typeCountEnd = self.al.logTypeCounts()


if __name__ == u"__main__":

    fileArchimate = os.getcwd() + os.sep + u"test" + os.sep + u"testDup.archimate"
    fileArchimateOutput = os.getcwd() + os.sep + u"dedup_test.archimate"

    da = DedupArchimateXML(fileArchimate)
    da.Dedup(fileArchimateOutput)



