CLASS
 NAME " 0 15 - Convection peu probable"
 GROUP "KINDEX_FR"
 EXPRESSION ([pixel] >= 0 AND [pixel] < 15)
 STYLE
  COLOR 5 113 176
 END
END

CLASS
 NAME "15 25 - Faible potentiel convectif"
 GROUP "KINDEX_FR"
 EXPRESSION ([pixel] >= 15 AND [pixel] < 25)
 STYLE
  COLOR 146 197 222
 END
END

CLASS
 NAME "25 40 - Potentiel convectif modéré"
 GROUP "KINDEX_FR"
 EXPRESSION ([pixel] >= 25 AND [pixel] < 40)
 STYLE
  COLOR 244 165 130
 END
END

CLASS
 NAME "> 40 - Potentiel convectif élevé"
 GROUP "KINDEX_FR"
 EXPRESSION ([pixel] >= 40)
 STYLE
  COLOR 202 0 32
 END
END