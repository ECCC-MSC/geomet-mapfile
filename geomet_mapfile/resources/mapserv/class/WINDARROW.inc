CLASS
 NAME "0 km/hr"
 GROUP "WINDARROWKMH"
 EXPRESSION ([uv_length] = 0.00)
 STYLE
  COLOR 0 0 127
  SYMBOL "circle_wind"
  SIZE 12
 END
END

CLASS
 NAME "0 10 km/hr"
 GROUP "WINDARROWKMH"
 EXPRESSION ([uv_length] > 0.00 AND [uv_length] < 2.78)
 STYLE
  COLOR 0 0 127
  SYMBOL "arrow_wind"
   ANGLE [uv_angle]
  SIZE 12
 END
END

CLASS
 NAME "10 20 km/hr"
 GROUP "WINDARROWKMH"
 EXPRESSION ([uv_length] >= 2.78 AND [uv_length] < 5.56)
 STYLE
  COLOR 0 0 203
  SYMBOL "arrow_wind"
   ANGLE [uv_angle]
  SIZE 12
 END
END

CLASS
 NAME "20 30 km/hr"
 GROUP "WINDARROWKMH"
 EXPRESSION ([uv_length] >= 5.56 AND [uv_length] < 8.33)
 STYLE
  COLOR  0 40 254
  SYMBOL "arrow_wind"
   ANGLE [uv_angle]
  SIZE 12
 END
END

CLASS
 NAME "30 40 km/hr"
 GROUP "WINDARROWKMH"
 EXPRESSION ([uv_length] >= 8.33 AND [uv_length] < 11.11)
 STYLE
  COLOR 0 155 254
  SYMBOL "arrow_wind"
   ANGLE [uv_angle]
  SIZE 12
 END
END

CLASS
 NAME "40 50 km/hr"
 GROUP "WINDARROWKMH"
 EXPRESSION ([uv_length] >= 11.11 AND [uv_length] < 13.89)
 STYLE
  COLOR 13 253 241
  SYMBOL "arrow_wind"
   ANGLE [uv_angle]
  SIZE 12
 END
END

CLASS
 NAME "50 60 km/hr"
 GROUP "WINDARROWKMH"
 EXPRESSION ([uv_length] >= 13.89 AND [uv_length] < 16.67)
 STYLE
  COLOR 106 253 148
  SYMBOL "arrow_wind"
   ANGLE [uv_angle]
  SIZE 12
 END
END

CLASS
 NAME "60 70 km/hr"
 GROUP "WINDARROWKMH"
 EXPRESSION ([uv_length] >= 16.67 AND [uv_length] < 19.44)
 STYLE
  COLOR 199 254 55
  SYMBOL "arrow_wind"
   ANGLE [uv_angle]
  SIZE 12
 END
END

CLASS
 NAME "70 80 km/hr"
 GROUP "WINDARROWKMH"
 EXPRESSION ([uv_length] >= 19.44 AND [uv_length] < 22.22)
 STYLE
  COLOR 254 217 0
  SYMBOL "arrow_wind"
   ANGLE [uv_angle]
  SIZE 12
 END
END

CLASS
 NAME "80 90 km/hr"
 GROUP "WINDARROWKMH"
 EXPRESSION ([uv_length] >= 22.22 AND [uv_length] < 25.00)
 STYLE
  COLOR 254 125 0
  SYMBOL "arrow_wind"
   ANGLE [uv_angle]
  SIZE 12
 END
END

CLASS
 NAME "90 100 km/hr"
 GROUP "WINDARROWKMH"
 EXPRESSION ([uv_length] >= 25.00 AND [uv_length] < 27.78)
 STYLE
  COLOR 254 32 0
  SYMBOL "arrow_wind"
   ANGLE [uv_angle]
  SIZE 12
 END
END

CLASS
 NAME "100 110 km/hr"
 GROUP "WINDARROWKMH"
 EXPRESSION ([uv_length] >= 27.78 AND [uv_length] < 30.56)
 STYLE
  COLOR 203 0 0
  SYMBOL "arrow_wind"
   ANGLE [uv_angle]
  SIZE 12
 END
END

CLASS
 NAME "110 km/hr +"
 GROUP "WINDARROWKMH"
 EXPRESSION ([uv_length] >= 30.56)
 STYLE
  COLOR 127 0 0
  SYMBOL "arrow_wind"
   ANGLE [uv_angle]
  SIZE 12
 END
END

