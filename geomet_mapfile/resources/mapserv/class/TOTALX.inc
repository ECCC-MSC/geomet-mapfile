CLASS
 NAME "< 44 - Convection not likely"
 GROUP "TOTALX"
 EXPRESSION ([pixel] < 44)
 STYLE
  COLOR 43 131 186
 END
END

CLASS
 NAME "44 50 - Likely thunderstorms"
 GROUP "TOTALX"
 EXPRESSION ([pixel] >= 44 AND [pixel] < 51)
 STYLE
  COLOR 86 104 146
 END
END

CLASS
 NAME "51 52 - Isolated severe storms"
 GROUP "TOTALX"
 EXPRESSION ([pixel] >= 51 AND [pixel] < 53)
 STYLE
  COLOR 129 78 107
 END
END

CLASS
 NAME "53 56 - Widely scattered severe storms"
 GROUP "TOTALX"
 EXPRESSION ([pixel] >= 53 AND [pixel] < 56)
 STYLE
  COLOR 172 51 67
 END
END

CLASS
 NAME "> 56 - Scattered severe storms"
 GROUP "TOTALX"
 EXPRESSION ([pixel] >= 56)
 STYLE
  COLOR 215 25 28
 END
END