def sky_condition(sri, temperature, rain):
    if sri == 0 and rain == 0:
        return "sereno" if temperature > 0 else "freddo chiaro"
    elif sri <= 1:
        return "nuvoloso"
    elif sri <= 5:
        return "pioggia moderata"
    else:
        return "temporale"
