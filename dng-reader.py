'''
Reads specified subtree and finds all dng images.
It outputs camera, lens, aperture, exposure, focal length and date of each
image.
Output is tab separated file that can be used for data mining in Excel like
program.
Run it with dng-reader.py -h for help.
'''

import exifread
import os
import re

from optparse import OptionParser

TEMPLATE_1 = re.compile(r'.*?(\d+)\.\d+(?:-(\d+)\.\d+)? mm f/(\d\.\d)(?:-(\d\.\d))?.*')
TEMPLATE_2 = re.compile(r'.*?(\d+)(?:-(\d+)) F(\d)(?:\.(\d))?.*')
TEMPLATE_3 = re.compile(r'.*?(\d+)mm F(\d)(?:\.(\d))?.*')
TEMPLATE_4 = re.compile(r'.*?(\d+)(?:-(\d+))?mm f/(\d\.\d)(?:-(\d\.\d))?.*')

def dateOnly(full_date):
  '''
  EXIF date is in YYYY:MM:DD HH:MM:SS format.
  We want only YYYY part for data processing.
  '''
  return full_date.split(':')[0]

def simplifyLensModel(lens_model):
  '''
  Lens models come in various level of details.
  Try to simplify them for data processing, e.g.
    70.0-200.0 mm f/4.0, Tokina AT-X 17-35 F4 PRO FX into 70-200 f/4.0
  '''
  lens_match = TEMPLATE_1.fullmatch(lens_model)
  if (lens_match != None):
    lens_match = lens_match.groups()
    result = lens_match[0]
    if (lens_match[1] != None):
      result += '-' + lens_match[1]
    result += ' f/' + lens_match[2]
    if (lens_match[3] != None):
      result += '-' + lens_match[3]
    return result

  lens_match = TEMPLATE_2.fullmatch(lens_model)
  if (lens_match != None):
    lens_match = lens_match.groups()
    result = lens_match[0]
    if (lens_match[1] != None):
      result += '-' + lens_match[1]
    result += ' f/' + lens_match[2]
    if (lens_match[3] != None):
      result += '.' + lens_match[3]
    else:
      result += '.0'
    return result

  lens_match = TEMPLATE_3.fullmatch(lens_model)
  if (lens_match != None):
    lens_match = lens_match.groups()
    result = lens_match[0] + ' f/' + lens_match[1]
    if (lens_match[2] != None):
      result += '.' + lens_match[2]
    else:
      result += '.0'
    return result

  lens_match = TEMPLATE_4.fullmatch(lens_model)
  if (lens_match != None):
    lens_match = lens_match.groups()
    result = lens_match[0]
    if (lens_match[1] != None):
      result += '-' + lens_match[1]
    result += ' f/' + lens_match[2]
    if (lens_match[3] != None):
      result += '-' + lens_match[3]
    return result

  print('Failed on:', lens_model)
  exit(1)

  return lens_model

def formatTSVLine(filename):
  '''
  Formats EXIF tags into a tab separated line
  '''
  with open(filename, 'rb') as f:
    tags = exifread.process_file(f)

  results = []
  try:
    results.append(str(tags['Image Model']))
    results.append(simplifyLensModel(str(tags['EXIF LensModel'])))
    results.append(str(eval(str(tags['EXIF FNumber']))))
    results.append(str(tags['EXIF ExposureTime']))
    results.append(str(tags['EXIF FocalLength']))
    results.append(dateOnly(str(tags['EXIF DateTimeOriginal'])))
  except KeyError:
    return ''

  return '\t'.join(results)

parser = OptionParser()
parser.add_option('-r', '--root', dest = 'root',
                  help = 'Root directory for images')
parser.add_option('-o', '--outfile', dest = 'outfile',
                  help = 'Output TSV file with photo information')
(options, args) = parser.parse_args()

count = 0
errors = 0
outfile = open(options.outfile, 'wt')
outfile.write('Model\tLens\tAperture\tExposure\tFocal Length\tDate\n')
for root, dirs, files in os.walk(options.root):
  print('Processing:', root)
  for file in files:
    if file.lower().endswith('dng'):
      line = formatTSVLine(os.path.join(root, file))
      count += 1
      if (count % 100 == 0):
        print('Processed', count, 'photos so far.')
      if line == '':
        errors += 1
        continue
      outfile.write(line + '\n')
outfile.close()
print('Total photos processed:', count)
print('Total errors:', errors)