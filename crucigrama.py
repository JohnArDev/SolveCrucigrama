class Variable():

    DERECHA = "izquierdaderecha"
    ABAJO = "arribaabajo"

    def __init__(self, i, j, direccion, longitud):
        """Crea una nueva variable con punto de inicio, dirección y longitud."""
        self.i = i
        self.j = j
        self.direccion = direccion
        self.longitud = longitud
        self.celdas = []
        for k in range(self.longitud):
            self.celdas.append(
                (self.i + (k if self.direccion == Variable.ABAJO else 0),
                 self.j + (k if self.direccion == Variable.DERECHA else 0))
            )

    def __hash__(self):
        return hash((self.i, self.j, self.direccion, self.longitud))

    def __eq__(self, other):
        return (
            (self.i == other.i) and
            (self.j == other.j) and
            (self.direccion == other.direccion) and
            (self.longitud == other.longitud)
        )

    def __str__(self):
        return f"({self.i}, {self.j}) {self.direccion} : {self.longitud}"

    def __repr__(self):
        direccion = repr(self.direccion)
        return f"Variable({self.i}, {self.j}, {direccion}, {self.longitud})"


class Crucigrama():

    def __init__(self, archivo_estructura, archivo_palabras):

        # Determina la estructura del crucigrama
        with open(archivo_estructura) as f:
            contenidos = f.read().splitlines()
            self.alto = len(contenidos)
            self.ancho = max(len(linea) for linea in contenidos)

            self.estructura = []
            for i in range(self.alto):
                row = []
                for j in range(self.ancho):
                    if j >= len(contenidos[i]):
                        row.append(False)
                    elif contenidos[i][j] == "_":
                        row.append(True)
                    else:
                        row.append(False)
                self.estructura.append(row)

        # Guardar la lista vocabulario
        with open(archivo_palabras) as f:
            self.words = set(f.read().upper().splitlines())

        # Determinar el conjunto de variables
        self.variables = set()
        for i in range(self.alto):
            for j in range(self.ancho):

                # Palabras verticales
                inicio_palabra = (
                    self.estructura[i][j]
                    and (i == 0 or not self.estructura[i - 1][j])
                )
                if inicio_palabra:
                    longitud = 1
                    for k in range(i + 1, self.alto):
                        if self.estructura[k][j]:
                            longitud += 1
                        else:
                            break
                    if longitud > 1:
                        self.variables.add(Variable(
                            i=i, j=j,
                            direccion=Variable.ABAJO,
                            longitud=longitud
                        ))

                # Palabras horizontales
                inicio_palabra = (
                    self.estructura[i][j]
                    and (j == 0 or not self.estructura[i][j - 1])
                )
                if inicio_palabra:
                    longitud = 1
                    for k in range(j + 1, self.ancho):
                        if self.estructura[i][k]:
                            longitud += 1
                        else:
                            break
                    if longitud > 1:
                        self.variables.add(Variable(
                            i=i, j=j,
                            direccion=Variable.DERECHA,
                            longitud=longitud
                        ))

        # Calcular solapan para cada palabra
        # Para cada par de variables v1, v2, su solapamiento es:
        #    Ninguna, si las dos palabras no se solapan; o
        #    (i, j), donde v1 es el i-caracter que se solapan con el j-caracter de v2
        self.solapamientos = dict()
        for v1 in self.variables:
            for v2 in self.variables:
                if v1 == v2:
                    continue
                celdas1 = v1.celdas
                celdas2 = v2.celdas
                interseccion = set(celdas1).intersection(celdas2)
                if not interseccion:
                    self.solapamientos[v1, v2] = None
                else:
                    interseccion = interseccion.pop()
                    self.solapamientos[v1, v2] = (
                        celdas1.index(interseccion),
                        celdas2.index(interseccion)
                    )

    def vecinos(self, var):
        """Dada una variable, retornar un conjunto de variables que solapan."""
        return set(
            v for v in self.variables
            if v != var and self.solapamientos[v, var]
        )
