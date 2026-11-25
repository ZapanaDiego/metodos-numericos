"""Generador procedural de mallas suaves, materiales y efectos para Panda3D.

Construye geometría orgánica con normales suavizadas por vértice (``V3n3c4``)
mediante *lofting* multi-sección, sin introducir dependencias externas.
"""
from __future__ import annotations

import numpy as np
from panda3d.core import (
    Geom,
    GeomNode,
    GeomTriangles,
    GeomVertexData,
    GeomVertexFormat,
    GeomVertexWriter,
    Material,
    NodePath,
    TransparencyAttrib,
)


def _normales_suaves(vertices: np.ndarray, triangulos: np.ndarray) -> np.ndarray:
    """Calcula normales unitarias suavizadas ponderadas por área de triángulo."""
    v0 = vertices[triangulos[:, 0]]
    v1 = vertices[triangulos[:, 1]]
    v2 = vertices[triangulos[:, 2]]
    caras = np.cross(v1 - v0, v2 - v0)
    normales = np.zeros_like(vertices, dtype=np.float64)
    np.add.at(normales, triangulos[:, 0], caras)
    np.add.at(normales, triangulos[:, 1], caras)
    np.add.at(normales, triangulos[:, 2], caras)
    magnitud = np.linalg.norm(normales, axis=1, keepdims=True)
    seguros = magnitud > 1e-12
    normales = np.where(seguros, normales / np.where(seguros, magnitud, 1.0), np.array([0.0, 0.0, 1.0]))
    return normales


def construir_geom(
    nombre: str,
    vertices: np.ndarray,
    triangulos: np.ndarray,
    colores: np.ndarray | tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
    normales: np.ndarray | None = None,
) -> GeomNode:
    """Empaqueta vértices, normales y colores en un ``GeomNode`` de Panda3D."""
    verts = np.asarray(vertices, dtype=np.float64)
    tris = np.asarray(triangulos, dtype=np.int32)
    if normales is None:
        norms = _normales_suaves(verts, tris)
    else:
        norms = np.asarray(normales, dtype=np.float64)

    cols = np.asarray(colores, dtype=np.float64)
    if cols.ndim == 1:
        cols = np.broadcast_to(cols, (len(verts), 4))

    vdata = GeomVertexData(nombre, GeomVertexFormat.getV3n3c4(), Geom.UHStatic)
    vdata.setNumRows(len(verts))
    w_v = GeomVertexWriter(vdata, "vertex")
    w_n = GeomVertexWriter(vdata, "normal")
    w_c = GeomVertexWriter(vdata, "color")

    for v, n, c in zip(verts, norms, cols, strict=True):
        w_v.addData3f(float(v[0]), float(v[1]), float(v[2]))
        w_n.addData3f(float(n[0]), float(n[1]), float(n[2]))
        w_c.addData4f(float(c[0]), float(c[1]), float(c[2]), float(c[3]))

    prim = GeomTriangles(Geom.UHStatic)
    prim.reserveNumVertices(3 * len(tris))
    for i0, i1, i2 in tris:
        prim.addVertices(int(i0), int(i1), int(i2))
    prim.closePrimitive()

    geom = Geom(vdata)
    geom.addPrimitive(prim)
    nodo = GeomNode(nombre)
    nodo.addGeom(geom)
    return nodo


def adjuntar_geom(
    padre: NodePath,
    geom: GeomNode,
    material: Material | None = None,
    transparente: bool = False,
    doble_cara: bool = False,
) -> NodePath:
    """Adjunta un ``GeomNode`` con material y transparencia opcionales."""
    np_nodo = padre.attachNewNode(geom)
    if material is not None:
        np_nodo.setMaterial(material, 1)
    if transparente:
        np_nodo.setTransparency(TransparencyAttrib.MAlpha)
    if doble_cara:
        np_nodo.setTwoSided(True)
    return np_nodo


def material_superficie(
    nombre: str,
    especular: tuple[float, float, float, float] = (0.18, 0.18, 0.18, 1.0),
    brillo: float = 18.0,
    emision: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0),
) -> Material:
    """Material que respeta el color por vértice y añade especular/emisión.

    En Panda3D, omitir ``setAmbient`` y ``setDiffuse`` conserva los colores
    almacenados en ``V3n3c4`` mientras la iluminación aplica brillo especular.
    """
    mat = Material(nombre)
    mat.setSpecular(especular)
    mat.setShininess(float(brillo))
    if any(c > 0.0 for c in emision[:3]):
        mat.setEmission(emision)
    return mat


def _aplicar_color_seccion(
    color_base: tuple[float, float, float, float],
    factor: float,
    seno_z: np.ndarray,
    sombra_dorsal: float,
) -> np.ndarray:
    """Modula suavemente el tono por sección y cara dorsal para dar volumen."""
    # Cara ventral (+Z) ligeramente más luminosa; cara dorsal (-Z) más cálida/oscura.
    mod = factor * (1.0 + sombra_dorsal * 0.5 * seno_z)
    rgb = np.clip(np.asarray(color_base[:3])[None, :] * mod[:, None], 0.0, 1.0)
    alpha = np.full((len(seno_z), 1), float(color_base[3]))
    return np.hstack([rgb, alpha])


def malla_loft_eje(
    nombre: str,
    secciones: list[dict] | tuple[dict, ...],
    *,
    eje: str = "x",
    n_lados: int = 24,
    color: tuple[float, float, float, float] = (0.8, 0.8, 0.8, 1.0),
    sombra_dorsal: float = 0.08,
    cerrar_inicio: bool = True,
    cerrar_fin: bool = True,
) -> GeomNode:
    """Construye un volumen orgánico suave a partir de secciones transversales.

    Cada sección es un diccionario con:
    - ``pos``: coordenada a lo largo de ``eje`` (``"x"``, ``"y"`` o ``"z"``).
    - ``c1``, ``c2``: desplazamiento del centro en los dos ejes transversales.
    - ``r1``: semieje en el primer eje transversal (o tupla ``(r1_pos, r1_neg)``).
    - ``r2``: semieje en el segundo eje transversal (o tupla ``(r2_pos, r2_neg)``).
    - ``tono`` (opcional): multiplicador de luminosidad/oclusión ambiental (1.0).
    - ``color`` (opcional): color RGBA específico para ese anillo.
    - ``deformar`` (opcional): ``fn(theta, u1, u2) -> (du1, du2, dpos)`` para
      esculpido fino (busto, nariz, pómulos, solapas, tacón).
    """
    angulos = np.linspace(0.0, 2.0 * np.pi, n_lados, endpoint=False)
    cos_t = np.cos(angulos)
    sen_t = np.sin(angulos)

    n_sec = len(secciones)
    if n_sec < 2:
        raise ValueError("malla_loft_eje requiere al menos 2 secciones.")

    # Base ortonormal dextrógira (U, V, T) con U × V = T (sentido positivo de 'eje').
    if eje == "x":
        # U = +Y, V = +Z, T = +X
        def a_xyz(pos, u1, u2):
            return np.column_stack([pos, u1, u2])
    elif eje == "y":
        # U = +Z, V = +X, T = +Y
        def a_xyz(pos, u1, u2):
            return np.column_stack([u2, pos, u1])
    elif eje == "z":
        # U = +X, V = +Y, T = +Z
        def a_xyz(pos, u1, u2):
            return np.column_stack([u1, u2, pos])
    else:
        raise ValueError(f"Eje desconocido: {eje}")

    lista_verts = []
    lista_cols = []
    centros = []
    colores_centro = []

    for sec in secciones:
        pos0 = float(sec["pos"])
        c1 = float(sec.get("c1", 0.0))
        c2 = float(sec.get("c2", 0.0))
        r1 = sec["r1"]
        r2 = sec["r2"]
        r1_p, r1_n = (float(r1[0]), float(r1[1])) if isinstance(r1, (tuple, list)) else (float(r1), float(r1))
        r2_p, r2_n = (float(r2[0]), float(r2[1])) if isinstance(r2, (tuple, list)) else (float(r2), float(r2))

        rad1 = np.where(cos_t >= 0.0, r1_p, r1_n)
        rad2 = np.where(sen_t >= 0.0, r2_p, r2_n)
        u1 = c1 + rad1 * cos_t
        u2 = c2 + rad2 * sen_t
        pos = np.full(n_lados, pos0, dtype=np.float64)

        deformar = sec.get("deformar")
        if deformar is not None:
            du1, du2, dpos = deformar(angulos, u1, u2)
            u1 = u1 + du1
            u2 = u2 + du2
            pos = pos + dpos

        verts_anillo = a_xyz(pos, u1, u2)
        lista_verts.append(verts_anillo)

        col_sec = sec.get("color", color)
        tono = float(sec.get("tono", 1.0))
        # Modulación vertical según coordenada Z real del anillo
        z_rel = verts_anillo[:, 2] - np.mean(verts_anillo[:, 2])
        z_escala = max(float(np.max(np.abs(z_rel))), 1e-6)
        cols_anillo = _aplicar_color_seccion(col_sec, tono, z_rel / z_escala, sombra_dorsal)
        lista_cols.append(cols_anillo)

        centros.append(a_xyz(np.array([pos0]), np.array([c1]), np.array([c2]))[0])
        rgb_c = np.clip(np.asarray(col_sec[:3]) * tono, 0.0, 1.0)
        colores_centro.append(np.array([rgb_c[0], rgb_c[1], rgb_c[2], float(col_sec[3])]))

    vertices = np.vstack(lista_verts)
    colores = np.vstack(lista_cols)

    # Sentido de triangulación con normal estrictamente saliente.
    creciente = secciones[-1]["pos"] >= secciones[0]["pos"]
    tris = []
    for k in range(n_sec - 1):
        b0 = k * n_lados
        b1 = (k + 1) * n_lados
        for j in range(n_lados):
            jn = (j + 1) % n_lados
            p00, p01 = b0 + j, b0 + jn
            p10, p11 = b1 + j, b1 + jn
            if creciente:
                tris.append((p00, p01, p11))
                tris.append((p00, p11, p10))
            else:
                tris.append((p00, p11, p01))
                tris.append((p00, p10, p11))

    extra_v = []
    extra_c = []
    if cerrar_inicio:
        idx_c = len(vertices) + len(extra_v)
        extra_v.append(centros[0])
        extra_c.append(colores_centro[0])
        for j in range(n_lados):
            jn = (j + 1) % n_lados
            if creciente:
                tris.append((idx_c, jn, j))
            else:
                tris.append((idx_c, j, jn))

    if cerrar_fin:
        idx_c = len(vertices) + len(extra_v)
        extra_v.append(centros[-1])
        extra_c.append(colores_centro[-1])
        base = (n_sec - 1) * n_lados
        for j in range(n_lados):
            jn = (j + 1) % n_lados
            if creciente:
                tris.append((idx_c, base + j, base + jn))
            else:
                tris.append((idx_c, base + jn, base + j))

    if extra_v:
        vertices = np.vstack([vertices, np.asarray(extra_v)])
        colores = np.vstack([colores, np.asarray(extra_c)])

    return construir_geom(nombre, vertices, np.asarray(tris, dtype=np.int32), colores)


def malla_elipsoide(
    nombre: str,
    rx: float,
    ry: float,
    rz: float,
    color: tuple[float, float, float, float],
    n_lon: int = 20,
    n_lat: int = 12,
    *,
    sombra_dorsal: float = 0.06,
) -> GeomNode:
    """Elipsoide suave parametrizado a lo largo de X."""
    phis = np.linspace(0.05 * np.pi, 0.95 * np.pi, n_lat)
    secciones = [
        {
            "pos": -rx * np.cos(p),
            "r1": max(1e-4, ry * np.sin(p)),
            "r2": max(1e-4, rz * np.sin(p)),
        }
        for p in phis
    ]
    return malla_loft_eje(
        nombre,
        secciones,
        eje="x",
        n_lados=n_lon,
        color=color,
        sombra_dorsal=sombra_dorsal,
        cerrar_inicio=True,
        cerrar_fin=True,
    )


def malla_toroide(
    nombre: str,
    radio_mayor: float,
    radio_menor: float,
    *,
    eje: str = "x",
    color: tuple[float, float, float, float] = (1.0, 0.28, 0.25, 0.85),
    n_u: int = 28,
    n_v: int = 10,
) -> GeomNode:
    """Anillo 3D suave para indicadores de estrés articular u ondas de choque."""
    u = np.linspace(0.0, 2.0 * np.pi, n_u, endpoint=False)
    v = np.linspace(0.0, 2.0 * np.pi, n_v, endpoint=False)
    uu, vv = np.meshgrid(u, v, indexing="ij")
    r_tot = radio_mayor + radio_menor * np.cos(vv)
    a = r_tot * np.cos(uu)
    b = r_tot * np.sin(uu)
    c = radio_menor * np.sin(vv)

    if eje == "x":
        verts = np.column_stack([c.ravel(), a.ravel(), b.ravel()])
    elif eje == "y":
        verts = np.column_stack([b.ravel(), c.ravel(), a.ravel()])
    else:
        verts = np.column_stack([a.ravel(), b.ravel(), c.ravel()])

    tris = []
    for i in range(n_u):
        inext = (i + 1) % n_u
        for j in range(n_v):
            jnext = (j + 1) % n_v
            p00 = i * n_v + j
            p10 = inext * n_v + j
            p11 = inext * n_v + jnext
            p01 = i * n_v + jnext
            tris.append((p00, p10, p11))
            tris.append((p00, p11, p01))

    return construir_geom(nombre, verts, np.asarray(tris, dtype=np.int32), color)


def malla_grietas_piso(
    nombre: str,
    radio: float = 0.55,
    n_rayos: int = 9,
    color_centro: tuple[float, float, float, float] = (0.06, 0.04, 0.03, 0.92),
    color_borde: tuple[float, float, float, float] = (0.14, 0.08, 0.06, 0.72),
) -> GeomNode:
    """Marca radial de fractura/impacto sobre la superficie del piso (plano XY)."""
    verts = [[0.0, 0.0, 0.004]]
    cols = [list(color_centro)]
    tris = []

    # Disco central hundido visualmente por color oscuro
    n_disco = 16
    r_centro = 0.14 * radio
    for i in range(n_disco):
        ang = 2.0 * np.pi * i / n_disco
        r_var = r_centro * (0.85 + 0.25 * np.sin(3 * ang + 0.6))
        verts.append([r_var * np.cos(ang), r_var * np.sin(ang), 0.003])
        cols.append(list(color_centro))
    for i in range(n_disco):
        tris.append((0, 1 + i, 1 + (i + 1) % n_disco))

    # Grietas radiales quebradas
    for k in range(n_rayos):
        ang = 2.0 * np.pi * k / n_rayos + 0.19 * np.sin(2.3 * k)
        largo = radio * (0.68 + 0.34 * ((k * 37) % 10) / 9.0)
        ancho = 0.022 * radio
        dir_x, dir_y = np.cos(ang), np.sin(ang)
        perp_x, perp_y = -dir_y, dir_x
        quiebre = 0.07 * radio * np.sin(1.7 * k + 0.4)

        p_base_l = [0.06 * radio * dir_x + ancho * perp_x, 0.06 * radio * dir_y + ancho * perp_y, 0.004]
        p_base_r = [0.06 * radio * dir_x - ancho * perp_x, 0.06 * radio * dir_y - ancho * perp_y, 0.004]
        p_mid_l = [0.52 * largo * dir_x + (quiebre + 0.55 * ancho) * perp_x,
                   0.52 * largo * dir_y + (quiebre + 0.55 * ancho) * perp_y, 0.004]
        p_mid_r = [0.52 * largo * dir_x + (quiebre - 0.55 * ancho) * perp_x,
                   0.52 * largo * dir_y + (quiebre - 0.55 * ancho) * perp_y, 0.004]
        p_punta = [largo * dir_x + 0.3 * quiebre * perp_x, largo * dir_y + 0.3 * quiebre * perp_y, 0.004]

        idx = len(verts)
        verts.extend([p_base_l, p_base_r, p_mid_l, p_mid_r, p_punta])
        cols.extend([list(color_centro), list(color_centro), list(color_borde), list(color_borde), list(color_borde)])
        tris.append((idx, idx + 1, idx + 3))
        tris.append((idx, idx + 3, idx + 2))
        tris.append((idx + 2, idx + 3, idx + 4))

    verts_arr = np.asarray(verts, dtype=np.float64)
    norms = np.tile(np.array([0.0, 0.0, 1.0]), (len(verts_arr), 1))
    return construir_geom(nombre, verts_arr, np.asarray(tris, dtype=np.int32), np.asarray(cols), normales=norms)
