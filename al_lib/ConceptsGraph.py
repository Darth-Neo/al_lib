#!/usr/bin/python
#
# Natural Language Processing of Archimate Information
#
__author__ = u'morrj140'
__VERSION__ = u'0.1'

import os
from Logger import *
logger = setupLogging(__name__)
logger.setLevel(INFO)

from nl_lib.Constants import *
from nl_lib.Concepts import Concepts
from nl_lib.ConceptGraph import PatternGraph, GraphVizGraph, NetworkXGraph

from Constants import *

def logGraph(gl, title, scale=1):
    logger.info(u"---%s---" % title)
    n = 0
    for x in gl:
        n += 1
        if isinstance(gl, dict):
            logger.info(u"%s [%d]:%s=%3.4f" % (title, n, x, gl[x]*scale))

        else:
            logger.info(u"%s [%d]" % (x, n))

def graphConcepts(graph, conceptFile):

    concepts = Concepts.loadConcepts(conceptFile)
    # concepts.logConcepts()

    graph.addGraphNodes(concepts)
    graph.addGraphEdges(concepts)

    if isinstance(graph, NetworkXGraph):
        graph.saveJSON(concepts)

    if isinstance(graph, GraphVizGraph):
        graph.exportGraph()

    if isinstance(graph, PatternGraph):
        graph.exportGraph()

def test_ConceptsGraph(graph):

    conceptFile = fileConceptsNGramsSubject

    if not os.path.exists(conceptFile):
        logger.info(u"File does not exist : %s" % conceptFile)

    else:
        graphConcepts(graph, conceptFile)

if __name__ == u"__main__":

    # graph = PatternGraph()
    graph = GraphVizGraph()
    # graph = NetworkXGraph(conceptFile[:-2]+u".png")

    test_ConceptsGraph(graph)





