CLASS
 NAME "0.000001 - 0.003751 "
 GROUP "HUMIDITYSPEC"
 EXPRESSION ([pixel] < 0.003751)
 STYLE
  COLOR 0 0 127
 END
END

CLASS
 NAME "0.003751 - 0.008751"
 GROUP "HUMIDITYSPEC"
 EXPRESSION ([pixel] >= 0.003751 AND [pixel] < 0.008751)
 STYLE
  COLOR 0 63 254
 END
END

CLASS
 NAME "0.008751 - 0.015"
 GROUP "HUMIDITYSPEC"
 EXPRESSION ([pixel] >= 0.008751 AND [pixel] < 0.015)
 STYLE
  COLOR 51 253 203
 END
END

CLASS
 NAME "0.015 - 0.02125"
 GROUP "HUMIDITYSPEC"
 EXPRESSION ([pixel] >= 0.015 AND [pixel] < 0.02125)
 STYLE
  COLOR 255 255 0
 END
END

CLASS
 NAME "0.02125 - 0.025"
 GROUP "HUMIDITYSPEC"
 EXPRESSION ([pixel] >= 0.02125)
 STYLE
  COLOR 254 50 0
 END
END