# Commands

Get node title
`xmlstarlet sel -N t="http://www.tei-c.org/ns/1.0" -t -m "//t:title[@type='bibl']" -c . -n v01_003_095_Detstvo.xml`

Get node text
`xmlstarlet sel -N t="http://www.tei-c.org/ns/1.0" -t -m "//t:title[@type='bibl']" -v . -n v01_003_095_Detstvo.xml`

Get node pb
`xmlstarlet sel -N t="http://www.tei-c.org/ns/1.0" -t -m "//t:pb[@n]" -c . -n v01_003_095_Detstvo.xml`


To find a node title with attribute type='bibl' which has ref node with attr xml:id='v51_031_031_1890_03_27'
```shell
xmlstarlet sel \
  -N t="http://www.tei-c.org/ns/1.0" \
  -N x="http://www.w3.org/XML/1998/namespace" \
  -t -m "//t:relatedItem[t:ref[@x:id='v51_031_031_1890_03_27']]/t:title[@type='bibl']" \
  -c . -n bibllist_bio.xml
```