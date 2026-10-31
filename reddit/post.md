## Title

[OC] 313 river basins cross a national border: they drain 47% of the world's land and hold 45% of its people. The Danube basin is shared by 19 countries

## Body

I mapped every international river basin in the Transboundary Freshwater Dispute Database (313 basins), coloured by how many countries share each one. Most (235) are shared by just two neighbours; the Danube reaches 19 countries, the Nile and the Niger 11 each, the Congo 10. I also measured the longest rivers on one consistent map (Natural Earth 1:10m lines, mouth to farthest source): the Nile comes out at 6,151 km, the Yangtze 5,320 and the Amazon 5,230, all shorter than published lengths (Britannica gives the Nile 6,650 km), because a coarser map smooths away the bends. Caveat: disputed areas such as Abyei are not counted as countries, and map lengths are not survey lengths. Interactive map: https://maps.tristanhotham.com/shared-rivers/

## Source comment

Source: Transboundary Freshwater Dispute Database, Oregon State University (2024 International River Basins register; 2018 basin and basin country unit outlines); Natural Earth 1:10m and 1:50m river and lake centrelines, land and countries (public domain); FAO AQUASTAT dependency ratio (CC BY-NC-SA 3.0 IGO); World Bank population (CC BY 4.0); Encyclopaedia Britannica for the published lengths of the Nile, Amazon and Yangtze.

Tools: Python (shapely, networkx, pyproj, matplotlib); Leaflet for the interactive map. River lengths are my own network measurement of the Natural Earth lines.

Interactive version: https://maps.tristanhotham.com/shared-rivers/
Paper: https://doi.org/10.5281/zenodo.23848927
Blog post: https://blog.tristanhotham.com/2026/10/31/shared-rivers/
