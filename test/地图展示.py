import folium

# 在[0,0]处显示世界地图
world_map = folium.Map(location=[0, 0], zoom_start=2)
world_map.save("world_map.html")