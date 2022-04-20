library(HeatStress)

files = list.files(path="/Users/szelie/OneDrive - ETH Zurich/data/heat/ch2018_buildings/klimaszenarien-raumklima-NABZUE/klimaszenarien-raumklima_2056", pattern="*.csv", full.names=TRUE, recursive=FALSE)
datalist = list()
i=1
for (file in files) {
  df = read.csv(file, header=TRUE)
  df$time.hh <- sprintf("%02d", as.numeric(as.character(df$time.hh)))
  df$time.dd <- sprintf("%02d", as.numeric(as.character(df$time.dd)))
  df$time.mm <- sprintf("%02d", as.numeric(as.character(df$time.mm)))
  df$date = paste(df$time.yy, df$time.mm, df$time.dd, sep="-")
  df$date = paste(df$date, df$time.hh, sep=" ")
  df$date = paste(df$date, "00", "00", sep=":")
  df$dewp = df$tre200h0 - ((100 - df$ure200h0)/5.)
  lat = 46.8
  lon = 8.2
  df$lat = lat
  df$lon = lon
  df$station = i
  df$strinside = 0
  wbgt_sun = wbgt.Liljegren(tas=df$tre200h0, wind=df$fkl010h0, dewp =df$dewp,
                                radiation=df$str.direkt, dates=df$date, lon=lon, lat=lat, tolerance = 1e-04, noNAs = FALSE, swap = FALSE, hour = TRUE)
  wbgt_shadow = wbgt.Liljegren(tas=df$tre200h0, wind=df$fkl010h0,
                               dewp =df$dewp, radiation=df$strinside, dates=df$date, lon=lon, lat=lat, tolerance = 1e-04, noNAs = FALSE, swap = FALSE, hour = TRUE)
  wbgt_bernard = wbgt.Bernard(tas=df$tre200h0,dewp=df$dewp, noNAs = FALSE)
  df$wbgt_sun = wbgt_outside[["data"]]
  df$wbgt_shadow = wbgt_shadow[["data"]]
  df$wbgt_inside = wbgt_bernard[["data"]]
  datalist[[i]] <- df
  i=i+1
}

big_data = do.call(rbind, datalist)
write.csv(big_data,"/Users/szelie/OneDrive - ETH Zurich/data/heat/ch2018_buildings/ch2018_raumklima_wbgt/wbgt.csv", row.names = FALSE)


