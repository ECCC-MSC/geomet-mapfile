CLASS
 NAME "< 44 - Convection peu probable"
 GROUP "TOTALX_FR"
 EXPRESSION ([pixel] < 44)
 STYLE
  COLOR 43 131 186
 END
END

CLASS
 NAME "44 50 - Orages probables"
 GROUP "TOTALX_FR"
 EXPRESSION ([pixel] >= 44 AND [pixel] < 51)
 STYLE
  COLOR 86 104 146
 END
END

CLASS
 NAME "51 52 - Tempêtes violentes isolées"
 GROUP "TOTALX_FR"
 EXPRESSION ([pixel] >= 51 AND [pixel] < 53)
 STYLE
  COLOR 129 78 107
 END
END

CLASS
 NAME "53 56 - Tempêtes violentes largement dispersées"
 GROUP "TOTALX_FR"
 EXPRESSION ([pixel] >= 53 AND [pixel] < 56)
 STYLE
  COLOR 172 51 67
 END
END

CLASS
 NAME "> 56 - Tempêtes violentes dispersées"
 GROUP "TOTALX_FR"
 EXPRESSION ([pixel] >= 56)
 STYLE
  COLOR 215 25 28
 END
END