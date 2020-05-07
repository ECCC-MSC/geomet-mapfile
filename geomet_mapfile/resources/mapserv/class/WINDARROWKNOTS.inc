CLASS
 NAME "0 kts"
 GROUP "WINDARROWKNOTS"
 EXPRESSION ([uv_length] = 270)
 STYLE
  COLOR 0 0 127
  SYMBOL "circle_wind"
  SIZE 12
 END
END

CLASS
 NAME "0 5 kts"
 GROUP "WINDARROWKNOTS"
 EXPRESSION ([uv_length] > 0.00 AND [uv_length] < 2.57)
 STYLE
  COLOR 0 0 127
  SYMBOL "arrow_wind"
   ANGLE [uv_angle]
  SIZE 12
 END
END

CLASS
 NAME "5 10 kts"
 GROUP "WINDARROWKNOTS"
 EXPRESSION ([uv_length] >= 2.57 AND [uv_length] < 5.14)
 STYLE
  COLOR 0 0 203
  SYMBOL "arrow_wind"
   ANGLE [uv_angle]
  SIZE 12
 END
END

CLASS
 NAME "10 15 kts"
 GROUP "WINDARROWKNOTS"
 EXPRESSION ([uv_length] >= 5.14 AND [uv_length] < 7.72)
 STYLE
  COLOR  0 40 254
  SYMBOL "arrow_wind"
   ANGLE [uv_angle]
  SIZE 12
 END
END

CLASS
 NAME "15 20 kts"
 GROUP "WINDARROWKNOTS"
 EXPRESSION ([uv_length] >= 7.72 AND [uv_length] < 10.29)
 STYLE
  COLOR 0 155 254
  SYMBOL "arrow_wind"
   ANGLE [uv_angle]
  SIZE 12
 END
END

CLASS
 NAME "20 25 kts"
 GROUP "WINDARROWKNOTS"
 EXPRESSION ([uv_length] >= 10.29 AND [uv_length] < 12.86)
 STYLE
  COLOR 13 253 241
  SYMBOL "arrow_wind"
   ANGLE [uv_angle]
  SIZE 12
 END
END

CLASS
 NAME "25 30 kts"
 GROUP "WINDARROWKNOTS"
 EXPRESSION ([uv_length] >= 12.86 AND [uv_length] < 15.43)
 STYLE
  COLOR 106 253 148
  SYMBOL "arrow_wind"
   ANGLE [uv_angle]
  SIZE 12
 END
END

CLASS
 NAME "30 35 kts"
 GROUP "WINDARROWKNOTS"
 EXPRESSION ([uv_length] >= 15.43 AND [uv_length] < 18.01)
 STYLE
  COLOR 199 254 55
  SYMBOL "arrow_wind"
   ANGLE [uv_angle]
  SIZE 12
 END
END

CLASS
 NAME "35 40 kts"
 GROUP "WINDARROWKNOTS"
 EXPRESSION ([uv_length] >= 18.01 AND [uv_length] < 20.58)
 STYLE
  COLOR 254 217 0
  SYMBOL "arrow_wind"
   ANGLE [uv_angle]
  SIZE 12
 END
END

CLASS
 NAME "40 45 kts"
 GROUP "WINDARROWKNOTS"
 EXPRESSION ([uv_length] >= 20.58 AND [uv_length] < 23.15)
 STYLE
  COLOR 254 125 0
  SYMBOL "arrow_wind"
   ANGLE [uv_angle]
  SIZE 12
 END
END

CLASS
 NAME "45 50 kts"
 GROUP "WINDARROWKNOTS"
 EXPRESSION ([uv_length] >= 23.15 AND [uv_length] < 25.72)
 STYLE
  COLOR 254 32 0
  SYMBOL "arrow_wind"
   ANGLE [uv_angle]
  SIZE 12
 END
END

CLASS
 NAME "50 55 kts"
 GROUP "WINDARROWKNOTS"
 EXPRESSION ([uv_length] >= 25.72 AND [uv_length] < 28.29)
 STYLE
  COLOR 203 0 0
  SYMBOL "arrow_wind"
   ANGLE [uv_angle]
  SIZE 12
 END
END

CLASS
 NAME "55 kts +"
 GROUP "WINDARROWKNOTS"
 EXPRESSION ([uv_length] >= 28.29)
 STYLE
  COLOR 127 0 0
  SYMBOL "arrow_wind"
   ANGLE [uv_angle]
  SIZE 12
 END
END
