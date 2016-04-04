#!/bin/bash
rm -r wiki.d
mkdir wiki.d
scp -P 222 demeter.dtek.se:/home/dtekse/www/wiki/wiki.d/* wiki.d/
chmod 766 -R wiki.d/
convmv -f ISO-8859-1 -t UTF-8 -r wiki.d/ --notest
files=`find wiki.d/*`
for file in ${files}
do
  iconv -f ISO-8859-1 -t UTF-8 -o "$file.new" "$file" &&
  mv -f "$file.new" "$file"
done
