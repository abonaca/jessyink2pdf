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
import os
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
    dirpath = os.path.dirname(os.path.realpath(argv[1]))
    #print(dirpath)

    # Search for slides
    masterSlide = None
    slides = []
    for g in root.childNodes:
        if g.nodeName == 'g' and g.getAttributeNS (INKSCAPE, 'groupmode') == 'layer':
            if g.getAttributeNS (JESSYINK, 'masterSlide') == 'masterSlide':
                masterSlide = g
            else:
                slides.append (g)
    slides = slides[:]

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

    cnt = 0
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
    
        # Find number of reveals
        max_order = 0
        slide_elements = []
        order_in = []
        order_out = []
        
        # get actual slide elements (remove new lines)
        for j,c in enumerate(g.childNodes):
            if c.attributes != None:
                slide_elements += [c]
        
        jmovie = -1
        for j, c in enumerate(slide_elements):
                effect_in = c.getAttribute('ns1:effectIn')
                effect_out = c.getAttribute('ns1:effectOut')

                if len(effect_in):
                    keys = effect_in.split(';')
                    order = [int(key.split(':')[1]) for key in keys if 'order' in key][0]
                    if order > max_order:
                        max_order = order
                    
                    order_in += [order]
                else:
                    order_in += [0]
                
                if len(effect_out):
                    keys = effect_out.split(';')
                    order = [int(key.split(':')[1]) for key in keys if 'order' in key][0]
                    if order > max_order:
                        max_order = order
                    
                    order_out += [order]
                else:
                    order_out += [100]
                
                # workaround for movies
                if c.getAttribute('ns1:element'):
                    if c.getAttribute('ns1:element')=='core.video':
                        jmovie = j
                    
                        # get origin for the movie position
                        transform = c.getAttribute('transform')
                        #print(transform)
                        if 'translate' in transform:
                            x0 = float(transform.split('(')[1].split(',')[0])
                            y0 = float(transform.split(',')[1].split(')')[0])
                        elif 'matrix' in transform:
                            x0 = float(transform.split(',')[4])
                            y0 = float(transform.split(',')[5].split(')')[0])
                        else:
                            x0 = 0.
                            y0 = 0.
                        #print(x0, y0)
                        
                        # get movie position
                        movie_elements = c.getElementsByTagName('rect')
                        for me in movie_elements:
                            if me.getAttribute('ns1:video')=='rect':
                                w = float(me.getAttribute('width'))
                                h = float(me.getAttribute('height'))
                                x = float(me.getAttribute('x'))
                                y = float(me.getAttribute('y'))
                                print(x + x0, y + y0, w, h)
                            
                        # get movie url
                        movie_elements = c.getElementsByTagName('text')
                        for me in movie_elements:
                            movie_text = me.getElementsByTagName('tspan')
                            for mt in movie_text:
                                if mt.getAttribute('ns1:video')=='url':                                    
                                    movie_url = '{:s}/{:s}'.format(dirpath, mt.firstChild.nodeValue)
                                    print(movie_url)
                                    movie_name = splitext(movie_url)[0].split('/')[-1]
                                    print(movie_name)
                        
                        # extract last frame from the movie
                        img_name = '{:s}.png'.format(movie_name)
                        subprocess.call (['ffmpeg', '-sseof', '-1', '-i', movie_url, '-update', '1', '-q:v', '1', '-y', img_name])
        
        if jmovie>=0:
            # add the last movie frame to the slide
            img_movie = doc.createElement('image')
            img_movie.setAttribute('sodipodi:absref', os.path.realpath(img_name))
            img_movie.setAttribute('xlink:href', os.path.realpath(img_name))
            img_movie.setAttribute('x', '{:f}'.format(x+x0))
            img_movie.setAttribute('y', '{:f}'.format(y+y0))
            img_movie.setAttribute('width', '{:f}'.format(w))
            img_movie.setAttribute('height', '{:f}'.format(h))
            img_movie.setAttribute('id', 'movieframe{:d}'.format(jmovie))
            
            g.appendChild(img_movie)
            slide_elements += [g.childNodes[-1]]
            
            # show frame as movie in slide
            order_in += [order_in[-1]]
            order_out += [order_out[-1]]
            
            # hide the actual movie
            order_out[jmovie] = -1
                        
        
        print('Number of reveals:', max_order)
        print(order_in, order_out)
    
        # produce a slide for every build-up step
        for j in range(max_order+1):
            #print(j)
            for k, element in enumerate(slide_elements):
                style = element.getAttribute('style')
                if style:
                    style += ';'
                if (order_in[k]<=j) & (order_out[k]>j):
                    element.setAttribute ('style', style+'display:inline')
                else:
                    element.setAttribute ('style', style+'display:none')
    
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
                subprocess.call (['inkscape', '--export-filename=slide-%04d.pdf'%cnt, 'slide.svg'])
                cnt += 1
                print('Output slide', cnt)
            
            # Hide the slide
            hideSlide (g)

    # Combine the final PDF
    slideFiles = ['slide-%04d.pdf'%i for i in range(cnt)]
    subprocess.call (['pdftk'] + slideFiles + ['cat', 'output', output])

    # Cleanup
    unlink ('slide.svg')
    for s in slideFiles:
        unlink (s)
