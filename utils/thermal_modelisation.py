def get_T_ext_w_voisin(T_ext, consider_neighboors=True):
    if consider_neighboors:
        if T_ext>10:
            T_lim = T_ext
        elif T_ext>0:
            T_lim = 10
        else:
            T_lim = T_ext + 10
        return T_lim
    else:
        return T_ext