ENTRY_TEMPLATE = """
<TEI xmlns="http://www.tei-c.org/ns/1.0" xmlns:math="http://www.w3.org/1998/Math/MathML" xmlns:svg="http://www.w3.org/2000/svg" xmlns:xi="http://www.w3.org/2001/XInclude">
 <teiHeader>
  <fileDesc>
   <titleStmt>
    <title>
     {title}
    </title>
    <title type="main">
     {main_title}
    </title>
    <title xml:id="{document_id}"/>
   </titleStmt>
   <sourceDesc>
    <biblStruct>
     <analytic>
      <author>
       <person ref="3589">
        Александр Борисович Гольденвейзер
       </person>
      </author>
     </analytic>
    </biblStruct>
   </sourceDesc>
  </fileDesc>
  <encodingDesc>
   <classDecl>
    <xi:include href="../../../../../../reference/taxonomy.xml"/>
   </classDecl>
  </encodingDesc>
  <profileDesc>
   <creation>
    <date when="{date}" />
   </creation>
   <textClass>
    <catRef ana="#materials" target="library"/>
    <catRef ana="#testimonies" target="type"/>
    <catRef ana="#diaries_materials" target="testimonies_type"/>
   </textClass>
  </profileDesc>
 </teiHeader>
 <text>
  <body/>
 </text>
</TEI>
"""

def get_entry_template(
    *, 
    document_id, 
    date,
    title="Вблизи Толстого. (Записки за пятнадцать лет)",
    main_title="Гольденвейзер А.Б. Вблизи Толстого. (Записки за пятнадцать лет)"
) -> str:
    return ENTRY_TEMPLATE.format(
        document_id=document_id, 
        date=date, 
        title=title, 
        main_title=main_title
    )
    