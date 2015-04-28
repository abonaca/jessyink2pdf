#! /usr/bin/env python2
# -*- coding: utf-8; -*-

# Copyright © 2014 Émilien Tlapale
# 
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
#    Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
#    Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS “AS IS”
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

from codecs import open
from os import unlink
from os.path import splitext
import subprocess
from sys import argv
from xml.dom import minidom

import cairo
import rsvg

INKSCAPE = "http://www.inkscape.org/namespaces/inkscape"
JESSYINK = "https://launchpad.net/jessyink"

def showSlide (g):
  g.setAttribute ('style', 'display:inline')

def hideSlide (g):
  g.setAttribute ('style', 'display:none')

if __name__ == '__main__':
  if len (argv) != 2:
    exit ('Usage: %s presentation.svg'%argv[0])
  doc = minidom.parse (argv[1])
  root = doc.documentElement
  #print ('\n'.join (dir (root)))

  # Search for slides
  masterSlide = None
  slides = []
  for g in root.childNodes:
    if g.nodeName == 'g' and \
        g.getAttributeNS (INKSCAPE, 'groupmode') == 'layer':
      if g.getAttributeNS (JESSYINK, 'masterSlide') == 'masterSlide':
        masterSlide = g
      else:
        slides.append (g)

  # Hide all slides
  for g in slides:
    hideSlide (g)

  # Show master slide
  showSlide (masterSlide)

  # Output
  output = splitext (argv[1])[0] + '.pdf'

  if False:
    # Create a PDF
    width = float (root.getAttribute ('width'))
    height = float (root.getAttribute ('width'))
    surf = cairo.PDFSurface ('slides.pdf', width, height)
    cr = cairo.Context (surf)

  # Display each slide
  for (i,g) in enumerate (slides):
    print ('Processing slide %d of %d'%(i+1,len(slides)))
    # Get slide info
    slideTitle = g.getAttributeNS (INKSCAPE, 'label')
    # Generate master slide auto-texts
    for t in masterSlide.getElementsByTagName ('tspan'):
      a = t.getAttributeNS (JESSYINK, 'autoText')
      if a == 'slideTitle':
        t.firstChild.data = slideTitle
    # Show the slide
    showSlide (g)
    # Make a temporary SVG for the slide
    xml = doc.toxml ()
    fp = open ('slide.svg', 'w', 'utf-8')
    fp.write (xml)
    fp.close ()
    if False:
      # Parse the generated SVG slide
      svg = rsvg.Handle (file='slide.svg')
      # Render the SVG on the cairo surface
      svg.render_cairo (cr)
      cr.show_page ()
    else:
      subprocess.call (['inkscape', '--export-pdf',
                        'slide-%04d.pdf'%i, 'slide.svg'])
    # Hide the slide
    hideSlide (g)

  # Combine the final PDF
  slideFiles = ['slide-%04d.pdf'%i for i in range(len(slides))]
  subprocess.call (['pdftk'] + slideFiles + ['cat', 'output', output])

  # Cleanup
  unlink ('slide.svg')
  for s in slideFiles:
    unlink (s)
