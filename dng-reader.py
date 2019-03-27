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

FOCAL_LENGTH = re.compile(r'.*?(\d+(\.\d+)?)(-\d+(\.\d+)?)?.*')
F_NUMBER = re.compile(r'.*?(?:F|f/)(\d+(\.\d+)?)(-\d+(\.\d+)?)?.*')

def dateOnly(full_date):
  '''
  EXIF date is in YYYY:MM:DD HH:MM:SS format.
  We want only YYYY part for data processing.
  '''
  return full_date.split(':')[0]

def simplifyLensModel(lens_model):
  '''
  Lens models come in various level of details.
  Try to simplify them for data processing, e.g. removing .0 and replacing F with f/.
  '''
  focal_length = FOCAL_LENGTH.match(lens_model)
  f_number = F_NUMBER.match(lens_model)
  if (focal_length != None and f_number != None):
    focal_length = focal_length.groups()
    if (focal_length[2] != None):
      result = ''.join([focal_length[0], focal_length[2]])
    else:
      result = focal_length[0]

    result += ' f/'
    f_number = f_number.groups()
    if (f_number[2] != None):
      result += ''.join([f_number[0], f_number[2]])
    else:
      result += f_number[0]

    return result.replace('.0', '')

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