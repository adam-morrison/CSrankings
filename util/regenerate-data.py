from csrankings import csv2dict_str_str, csv2dict_str_list, startyear, endyear, areadict, confdict, arealist, venues, pagecount, startpage, ElementTree, pageCountThreshold, ISMB_Bioinformatics, ICSE_ShortPaperStart

def parseDBLP(facultydict):
    authlogs = {}
    interestingauthors = {}
    authorscores = {}
    authorscoresAdjusted = {}
    coauthors = {}
    papersWritten = {}
    counter = 0

    with open('dblp.xml', mode='r') as f:

    # with gzip.open('dblp.xml.gz') as f:

        oldnode = None

        for (event, node) in ElementTree.iterparse(f, events=['start', 'end']):
            if (oldnode is not None):
                oldnode.clear()
            oldnode = node

            foundArticle = False
            inRange = False
            authorsOnPaper = 0
            authorName = ""
            confname = ""
            year = -1
            pageCount = -1
            startPage = -1
            foundOneInDict = False
            number = 0
            volume = 0
            
            if (node.tag == 'inproceedings' or node.tag == 'article'):

                # First, check if this is one of the conferences we are looking for.

                for child in node:
                    if (child.tag == 'booktitle' or child.tag == 'journal'):
                        confname = child.text
                        if (confname in confdict):
                            foundArticle = True
                    if (child.tag == 'volume'):
                        volume = child.text
                    if (child.tag == 'number'):
                        number = child.text
                    if child.tag == 'year':
                        if child.text is not None:
                            year = int(child.text)
                    if child.tag == 'pages':
                        pageCount = pagecount(child.text)
                        startPage = startpage(child.text)
                    if child.tag == 'author':
                        authorName = child.text
                        if authorName is not None:
                            authorName = authorName.strip()
                            authorsOnPaper += 1
                            if authorName in facultydict:
                                foundOneInDict = True

                if (not foundArticle):
                    # Not one of our conferences.
                    continue

                areaname = confdict[confname]
                
                # Special handling for ISMB.
                if (confname == 'Bioinformatics'):
                    if ISMB_Bioinformatics.has_key(year):
                        (vol, num) = ISMB_Bioinformatics[year]
                        if (volume != str(vol)) or (number != str(num)):
                            continue
                    else:
                        continue

                # Special handling for ICSE.
                if ((confname == 'ICSE') or (confname == 'ICSE (1)') or (confname == 'ICSE (2)')):
                    if ICSE_ShortPaperStart.has_key(year):
                        pageno = ICSE_ShortPaperStart[year]
                        if startPage >= pageno:
                            # Omit papers that start at or beyond this page,
                            # since they are "short papers" (regardless of their length).
                            continue
                
                # Check that dates are in the specified range.
                if ((year >= startyear) and (year <= endyear)):
                    inRange = True
                    
                if year == -1:
                    # No year.
                    print "NO YEAR WAT", confname
                    continue
               
                tooFewPages = False
                if ((pageCount != -1) and (pageCount < pageCountThreshold)):
                    tooFewPages = True
                    exceptionConference = ((confname == 'SC') or (confname == 'SIGSOFT FSE') or (confname == 'PLDI') or (confname == 'ACM Trans. Graph.'))
                    if ((pageCount == 0) and exceptionConference):
                        tooFewPages = False

                    # SPECIAL CASE FOR conferences that have incorrect entries (as of 6/22/2016).
                    # Only skip papers with a very small paper count,
                    # but above 1. Why?
                    # DBLP has real papers with incorrect page counts
                    # - usually a truncated single page. -1 means no
                    # pages found at all => some problem with journal
                    # entries in DBLP.
                    # print "Skipping article with "+str(pageCount)+" pages."

                for child in node:
                    if child.tag == 'author':
                        authorName = child.text
                        # if authorName is not None:
                        # print authorName.encode('utf-8') + "," + areaname + "," + str(volume) + "," + str(number) + "," + str(year) + "," + str(pageCount) + "," + str(startPage) + "," + str(authorsOnPaper)
                

                if ((confname == 'ASE') and (pageCount <= 6)):
                    tooFewPages = True

                if (not inRange) or (not foundOneInDict) or tooFewPages:
                    continue
               
                # If we got here, we have a winner.

                for child in node:
                    if child.tag == 'author':
                        authorName = child.text
                        authorName = authorName.strip()
                        if authorName in facultydict:
                            # print "here we go",authorName, confname, authorsOnPaper, year
                            logstring = authorName.encode('utf-8') + " ; " + confname + " " + str(year)
                            tmplist = authlogs.get(authorName, [])
                            tmplist.append(logstring)
                            authlogs[authorName] = tmplist
                            interestingauthors[authorName] = interestingauthors.get(authorName, 0) + 1
                            authorscores[(authorName, areaname, year)] = authorscores.get((authorName, areaname, year), 0) + 1.0
                            authorscoresAdjusted[(authorName, areaname, year)] = authorscoresAdjusted.get((authorName, areaname, year), 0) + 1.0 / authorsOnPaper

    return (interestingauthors, authorscores, authorscoresAdjusted, authlogs)


fdict = csv2dict_str_str('faculty-affiliations.csv')
fdict_list = csv2dict_str_list('faculty-affiliations.csv')

(intauthors_gl, authscores_gl, authscoresAdjusted_gl, authlog_gl) = parseDBLP(fdict)

f = open('generated-author-info.csv','w')
f.write('"name","dept","area","count","adjustedcount","year"\n')
for (authorName, area, year) in authscores_gl:
    count = authscores_gl[(authorName, area, year)]
    countAdjusted = authscoresAdjusted_gl[(authorName, area, year)]
    depts = fdict_list[authorName]
    for dept in depts:
        f.write(authorName.encode('utf-8'))
        f.write(',')
        f.write(dept.encode('utf-8'))
        f.write(',')
        f.write(area)
        f.write(',')
        f.write(str(count/len(depts)))
        f.write(',')
        f.write(str(countAdjusted/len(depts)))
        f.write(',')
        f.write(str(year))
        f.write('\n')
f.close()

f = open('rankings-all.log','w')
for v, l in authlog_gl.items():
    if intauthors_gl.has_key(v):
        if (intauthors_gl[v] >= 1):
            f.write("Papers for " + v.encode('utf-8') + ', ' + (fdict[v]).encode('utf-8') + "\n")
            for s in l:
                f.write(s)
                f.write('\n')
                f.write('\n')
f.close()



