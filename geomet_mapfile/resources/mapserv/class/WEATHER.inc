CLASS
 NAME "Single symbol"
 MAXSCALEDENOM 10000000
 EXPRESSION ("[temp]" ~ "[0-9]$")
 LABEL
  FONT "arial"
  TYPE TRUETYPE
  TEXT "[temp]°C"
  SIZE 9
  POSITION cr
  STYLE
   SYMBOL [icon]
   SIZE 25
  END
 END
END
CLASS
 NAME "Single symbol"
 MINSCALEDENOM 10000000
 EXPRESSION ("[temp]" ~ "[0-9]$")
 LABEL
  TEXT '      '
  SIZE giant
  POSITION cr
  STYLE
   SYMBOL [icon]
   SIZE 25
  END
 END
END
