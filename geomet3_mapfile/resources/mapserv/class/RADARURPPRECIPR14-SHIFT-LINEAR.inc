CLASS
 NAME "0.1 - 1.0 (mm/hr)"
 GROUP "RADARURPPRECIPR14-SHIFT-LINEAR"
 EXPRESSION (0.1 <= [pixel] AND [pixel] < 1.0)
 STYLE
  COLORRANGE 204 230 255 102 178 255
  DATARANGE 0.1 1.0
 END
END
CLASS
 NAME "1.0 - 2.0 (mm/hr)"
 GROUP "RADARURPPRECIPR14-SHIFT-LINEAR"
 EXPRESSION (1.0 <= [pixel] AND [pixel] < 2.0)
 STYLE
  COLORRANGE 102 178 255 000 096 255
  DATARANGE 1.0 2.0
 END
END
CLASS
 NAME "2.0 - 4.0 (mm/hr)"
 GROUP "RADARURPPRECIPR14-SHIFT-LINEAR"
 EXPRESSION (2.0 <= [pixel] AND [pixel] < 4.0)
 STYLE
  COLORRANGE 000 096 255 000 255 000
  DATARANGE 2.0 4.0
 END
END
CLASS
 NAME "4.0 - 8.0 (mm/hr)"
 GROUP "RADARURPPRECIPR14-SHIFT-LINEAR"
 EXPRESSION (4.0 <= [pixel] AND [pixel] < 8.0)
 STYLE
  COLORRANGE 000 255 000 000 180 000
  DATARANGE 4.0 8.0
 END
END
CLASS
 NAME "8.0 - 12.0 (mm/hr)"
 GROUP "RADARURPPRECIPR14-SHIFT-LINEAR"
 EXPRESSION (8.0 <= [pixel] AND [pixel] < 12.0)
 STYLE
  COLORRANGE 000 180 000 000 126 000
  DATARANGE 8.0 12.0
 END
END
CLASS
 NAME "12.0 - 16.0 (mm/hr)"
 GROUP "RADARURPPRECIPR14-SHIFT-LINEAR"
 EXPRESSION (12.0 <= [pixel] AND [pixel] < 16.0)
 STYLE
  COLORRANGE 000 126 000 024 080 000
  DATARANGE 12.0 16.0
 END
END
CLASS
 NAME "16.0 - 24.0 (mm/hr)"
 GROUP "RADARURPPRECIPR14-SHIFT-LINEAR"
 EXPRESSION (16.0 <= [pixel] AND [pixel] < 24.0)
 STYLE
  COLORRANGE 024 080 000 255 255 080
  DATARANGE 16.0 24.0
 END
END
CLASS
 NAME "24.0 - 32.0 (mm/hr)"
 GROUP "RADARURPPRECIPR14-SHIFT-LINEAR"
 EXPRESSION (24.0 <= [pixel] AND [pixel] < 32.0)
 STYLE
  COLORRANGE 255 255 080 255 170 000
  DATARANGE 24.0 32.0
 END
END
CLASS
 NAME "32.0 - 50.0 (mm/hr)"
 GROUP "RADARURPPRECIPR14-SHIFT-LINEAR"
 EXPRESSION (32.0 <= [pixel] AND [pixel] < 50.0)
 STYLE
  COLORRANGE 255 170 000 255 130 000
  DATARANGE 32.0 50.0
 END
END
CLASS
 NAME "50.0 - 64.0 (mm/hr)"
 GROUP "RADARURPPRECIPR14-SHIFT-LINEAR"
 EXPRESSION (50.0 <= [pixel] AND [pixel] < 64.0)
 STYLE
  COLORRANGE 255 130 000 255 074 000
  DATARANGE 50.0 64.0
 END
END
CLASS
 NAME "64.0 - 100.0 (mm/hr)"
 GROUP "RADARURPPRECIPR14-SHIFT-LINEAR"
 EXPRESSION (64.0 <= [pixel] AND [pixel] < 100.0)
 STYLE
  COLORRANGE 255 074 000 255 000 000
  DATARANGE 64.0 100.0
 END
END
CLASS
 NAME "100.0 - 125.0 (mm/hr)"
 GROUP "RADARURPPRECIPR14-SHIFT-LINEAR"
 EXPRESSION (100.0 <= [pixel] AND [pixel] < 125.0)
 STYLE
  COLORRANGE 255 000 000 255 004 255
  DATARANGE 100.0 125.0
 END
END
CLASS
 NAME "125.0 - 200.0 (mm/hr)"
 GROUP "RADARURPPRECIPR14-SHIFT-LINEAR"
 EXPRESSION (125.0 <= [pixel] AND [pixel] < 200.0)
 STYLE
  COLORRANGE 255 004 255 120 032 200
  DATARANGE 125.0 200.0
 END
END
CLASS
 NAME ">= 200.0 (mm/hr)"
 GROUP "RADARURPPRECIPR14-SHIFT-LINEAR"
 EXPRESSION (200.0 <= [pixel] AND [pixel] <= 300.0)
 STYLE
  COLORRANGE 120 032 200 080 000 106
  DATARANGE 200.0 300.0
 END
END