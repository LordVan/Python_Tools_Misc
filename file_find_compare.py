#! /usr/bin/env python3

import os
import glob
import hashlib
import difflib
#import magic
from urllib.request import pathname2url

DEBUG = True
DEBUG_DATA = False  # print lots of data (dict contents,..)


class FileProp:
    def __init__(self, fname, fullpath, digest, mime=None):
        self._fname = fname
        self._fullpath = os.path.normpath(fullpath)
        self._digest = digest
        # lists of files with the same name - and weather they match or not
        self._match = []
        self._mismatch = []
        #self._mimetype = mime

    def compare_hash(self, newfile, digest):
        newfile_norm = os.path.normpath(newfile)
        if self._fullpath == newfile_norm:
            # no need to add base file
            return
        if self._digest == digest:
            self._match.append(newfile_norm)
        else:
            self._mismatch.append(newfile_norm)

    def sort_data(self):
        # call this when done with all matching
        self._match.sort()  # just keep it sorted on insert
        self._mismatch.sort()  # just keep it sorted on insert
        if DEBUG:
            print('matches:')
            print(self._match)
            print('mismatches:')
            print(self._mismatch)

    def get_fname(self):
        return self._fname

    def get_matches(self):
        return self._match

    def get_mismatches(self):
        return self._mismatch

    def output_data(self, remove_string=None, gen_diff = True):
        ret = '%s (%s):\n' % (self._fname, self._fullpath)
        if len(self._match) == 0:
            ret += '  Keine gleichen Dateien gefunden.\n'
        else:
            ret += '  Anzahl gleicher Dateien: %d:\n' % (len(self._match))
            for m in self._match:
                ret += '    %s\n' % (m)
        if len(self._mismatch) == 0:
            ret += '  Keine abweichenden Dateien gefunden.\n'
        else:
            ret += '  Anzahl abweichender Dateien: %d:\n' % (len(self._mismatch))
            for m in self._mismatch:
                ret += '    %s\n' % (m)
        if remove_string:
            if DEBUG:
                print(f'removing {remove_string}')
            return ret.replace(remove_string, '')
        else:
            return ret

    def output_html(self, gen_diff = True, remove_string=None):
        #ret = f'<div>\n<h2>{self._fname} ({self._fullpath}, {self._mimetype}):</h2>\n<a href="#index">Zum Index</a>'
        ret = f'<div>\n<h2>{self._fname} ({self._fullpath}):</h2>\n<a href="#index">Zum Index</a>'
        if len(self._match) == 0:
            ret += '<p class="nomatch">Keine gleichen Dateien gefunden.</p>\n'
        else:
            ret += f'<p class="match">Anzahl gleicher Dateien: {len(self._match)}:\n<ul>\n'
            for folder in self._match:
                if remove_string:
                    folder_short = folder.replace(remove_string, '')
                else:
                    folder_short = folder
                ret += f'<li class="matchItem">{folder_short} (<a href="file:{pathname2url(os.path.dirname(folder))}">Ordner öffnen</a>)</li>\n'
            ret += '</ul>\n</p>\n'
        if len(self._mismatch) == 0:
            ret += '<p class="nomatch">Keine abweichenden Dateien gefunden.</p>\n'
        else:
            diffDir = os.path.join(os.path.dirname(self._fullpath), 'diffs')
            if gen_diff and not os.path.exists(diffDir):
                os.makedirs(diffDir)
            ret += f'<p class="differ">Anzahl abweichender Dateien: {len(self._mismatch)}:\n<ul>\n'
            for folder in self._mismatch:
                if remove_string:
                    folder_short = folder.replace(remove_string, '')
                else:
                    folder_short = folder
                ret += f'<li class="differItem">{folder_short}'
                ext = None
                try:
                    ext = self._fullpath.split('.')[-1]
                except IndexError:
                    pass
                delta = []
                if ext and ext.lower() in ('dxf', 'stp', 'sat', 'step'):
                    print('comparing file contents..')
                    try:
                        old_lines = open(folder, 'r').readlines()
                        new_lines = open(self._fullpath, 'r').readlines()
                        delta = list(difflib.unified_diff(old_lines,
                                                          new_lines,
                                                          fromfile=folder,
                                                          tofile=self._fullpath))
                        if gen_diff:
                            with(open(os.path.join(diffDir, self._fname + '.diff'), 'w', encoding='utf-8')) as diffFile:
                                if DEBUG:
                                    print(f'writing diff')
                                diffFile.writelines(delta)
                            with(open(os.path.join(diffDir, self._fname + '.diff.html'), 'w', encoding='utf-8')) as diffHtml:
                                if DEBUG:
                                    print(f'writing HTML diff (this can take a long time)')
                                diffHtmlLines = list(difflib.HtmlDiff().make_file(old_lines, new_lines))
                                diffHtml.writelines(diffHtmlLines)
                        difflines = "<br />".join(delta[:30]) # the diff has been written to a file. now truncate it and add html linebreaks
                        if len(delta) > 30:
                            difflines += '<br />.....'
                        ret += f' [<div class="tooltip">Abweichungen<span class="tooltiptext">{difflines}</span></div>]'

                    except Exception as e:
                        print('Error during diff: %s' % (e))
                ret += f'(<a href="file:{pathname2url(os.path.dirname(folder))}">Order öffnen</a>)</li>\n'
            ret += '</ul>\n</p>\n'
        ret += '</div>\n<hr />\n'
        if remove_string:
            if DEBUG:
                print(f'removing {remove_string}')
        return ret

    def __repr__(self):
        return f'file property: {self._fname} match: {len(self._match)} mismatch: {len(self._mismatch)}'


class FileFindCompare:
    def __init__(self, fin, fout, basedir):
        self._files = {}
        self._fin = fin
        self._finBasedir = os.path.dirname(self._fin)
        self._fout = fout
        self._basedir = basedir  # where do we search

        if DEBUG:
            print('Input file list: %s' % (fin))
            print('Output file list: %s' % (fout))
            print('Basedir: %s' % (basedir))

        self._load_file_list()

    def _load_file_list(self):
        #mime = magic.Magic(mime=True)
        with open(self._fin, 'r', encoding='utf-8') as infile:
            for line in infile:
                # need to split in case of sub-dirs
                fdir, fname = os.path.split(line.strip('\n\r'))
                fullname = os.path.join(self._finBasedir, fdir, fname)
                #self._files[fname] = FileProp(fname, fullname, self._create_hash(fullname), mime.from_file(fullname))
                self._files[fname] = FileProp(fname, fullname, self._create_hash(fullname))
                if DEBUG_DATA:
                    if len(self._files) > 2:
                        # don't get loads of data while testing
                        print('DEBUG: stopping after 3 files')
                        break
        infile.close()
        if DEBUG:
            print('Got list of %d files' % (len(self._files)))
        if DEBUG_DATA:
            print(self._files)

    def _create_hash(self, fname, block_size=65536):
        # copied from https://gist.github.com/rji/b38c7238128edf53a181
        sha256 = hashlib.sha256()
        with open(fname, 'rb') as f:
            for block in iter(lambda: f.read(block_size), b''):
                sha256.update(block)
        return sha256.hexdigest()

    def find_compare(self):
        cnt = 0
        total = len(self._files)
        for fname, prop in self._files.items():
            cnt += 1
            if DEBUG:
                print('Processing file %d of %d' % (cnt, total))
            for fmatch in glob.iglob(os.path.join(self._basedir, '**', fname), recursive=True):
                newhash = self._create_hash(fmatch)
                prop.compare_hash(fmatch, newhash)
            prop.sort_data()
            if DEBUG:
                print('File: %s found %d matches and %d mismatches' % (fname,
                                                                       len(prop.get_matches()),
                                                                       len(prop.get_mismatches())))

    def generate_output(self, gen_diff = True):
        ret = ''
        for fname, prop in self._files.items():
            ret += prop.output_data(os.path.normpath(self._basedir), gen_diff)
            ret += '\n'
            # TODO: support textual Diff here
        return ret

    def process(self, gen_text = True, gen_html = True, gen_diff = True, gen_html_diff = False):
        self.find_compare()  # browse the directory structure and compare hashes
        if gen_diff and not gen_html:
            print('Error: Diffs currently only supported when generating HTML')
            return -1
        if gen_text:
            with open(self._fout, 'w', encoding='utf-8') as outp:
                outp.write(self.generate_output())
        if gen_html:
            with open(self._fout.replace('.txt', '.html'), 'w', encoding='utf-8') as outphtml:
                outphtml.write(self.generate_html(gen_html_diff))
        if not gen_text and not gen_html:
            print('No output generated!!!')
            return -1
        return 0


    def generate_html(self, gen_diff = True):
        title = f'Dateivergleich {self._finBasedir}'
        ret = '''<html>
<head>
<title>%s</title>
<style>
.match { color: green; font-weight: bold; }
.matchItem { color: green; font-weight: normal; }
.nomatch { color: blue; font-weight: bold; }
.differ { color: red; font-weight: bold; }
.differ { color: red; font-weight: normal; }

/* https://www.w3schools.com/css/css_tooltip.asp */
/* Tooltip container */
.tooltip {
  position: relative;
  display: inline-block;
  border-bottom: 1px dotted black; /* If you want dots under the hoverable text */
}

/* Tooltip text */
.tooltip .tooltiptext {
  visibility: hidden;
  width: 800px;
  background-color: black;
  color: #fff;
  text-align: center;
  padding: 5px 0;
  border-radius: 6px;
 
  /* Position the tooltip text - see examples below! */
  position: absolute;
  z-index: 1;
}

/* Show the tooltip text when you mouse over the tooltip container */
.tooltip:hover .tooltiptext {
  visibility: visible;
}
</style>
</head>
<body>
<h1>%s</h1>
<div>
<h3>Index</h3>
<ul id="index"> </ul>
</div> 
''' % (title, title)
        for fname, prop in self._files.items():
            ret += prop.output_html(gen_diff, os.path.normpath(self._basedir))
            ret += '\n'
        ret += '''
<script>
//let headers = document.querySelectorAll("h1, h2, h3, h4, h5, h6")//get all the H tags
let headers = document.querySelectorAll("h2")
let i = 1;
let indexHtml = '';
let indexHolder = document.getElementById('index'); 
headers.forEach(function(header) {
  header.id = "header-" + i;//give each H tag an unique ID
  indexHtml = indexHtml + '<li><a href="#header-' + i + '">'+header.innerHTML+'</a></li>' ;//make the index HTML
  ++i;
});//
indexHolder.innerHTML = indexHtml;//put the html in the #index div
</script>
</body>
</html>'''
        return ret


if __name__ == '__main__':
    #  for i in [0-9]*; do for j in $i/*; do echo $j;done ;done |grep -v DOKU|grep -v Thumbs > filelist.txt
    basedir = 'y:/Zeichnungen-Projekte/Wurmb/'
    subdir = 'Bestellungen/Bestellungen 2025 - 2029/Bestellungen 2026/Bestellung --- 2026-06-24'
    #basedir = 'y:/Zeichnungen-Projekte/BremTechnik/'
    #subdir = 'Bestellungen/Bestellungen 2023/Bestellung --- 2023-06-26'
    #basedir = 'Y:/Zeichnungen-Projekte/Dlouhy/'
    #subdir = 'Bestellungen/Bestellungen 2024/Bestellung --- 2024-01-18-2'
    fin = os.path.join(basedir, subdir, 'filelist.txt')
    fout = os.path.join(basedir, subdir, 'filelist_output.txt')
    app = FileFindCompare(fin, fout, basedir)
    app.process(gen_text = True,
                gen_html = True,
                gen_diff = True,
                gen_html_diff = False)  # save the text and html files ## html diff is painfully slow
    # with open(fout, 'w', encoding='utf-8') as outp:
    #     outp.write(app.generate_output())
    # outp.close()
