__author__ = 'inieto'


def get_query(name, values=None):

    return {

        "DUSIN_SABRE_USERS": (
            "SELECT s.PCC_SABRE pcc, s.Sine_SABRE user_id, u.ID_Usuario id_dusin, "
            "u.Correo_Usuario email, u.Nombre_Apellido_Usuario fullname, "
            "u.Estado_Usuario dusins_user_state, s.Estado_Usuario_SABRE dusins_sabre_state "
            "FROM Usuarios u inner join Usuarios_SABRE s on s.ID_Usuario = u.ID_Usuario "
            "WHERE char_length(s.PCC_SABRE) > 0 AND s.Sine_SABRE > 0;"
        ),
        "DUSIN_EMAIL_USERS": (
            "SELECT u.ID_Usuario, u.Correo_Usuario, u.Nombre_Apellido_Usuario, "
            "u.Gapps, p.Nombre_Pais, u.Estado_Usuario, u.Fecha_Alta_Usuario "
            "FROM Usuarios u INNER JOIN Pais p on u.ID_Pais_Residencia = p.ID_Pais;"
        )
    }[name]
