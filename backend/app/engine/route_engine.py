def recommend_route(ocean: dict):
    pfz = ocean["pfz"]
    return {
        "destination": pfz["name"],
        "direction": pfz["direction"],
        "distance_km": pfz["distance_km"],
        "note": "Prototype straight-line recommendation; replace with risk-weighted A*/Dijkstra route."
    }
