import sys
from crucigrama import *

class CreadorCrucigrama():

    def __init__(self, crucigrama):
        """
        Crear un nuevo CSP (problema de satisfacción de restricciones) - crucigrama.
        """
        self.crucigrama = crucigrama
        self.dominios = {
            var: self.crucigrama.words.copy()
            for var in self.crucigrama.variables
        }

    def cuadricula_letras(self, asignacion):
        """
        Retornar una matriz (2D) representando una asignación dada.
        """
        letras = [
            [None for _ in range(self.crucigrama.ancho)]
            for _ in range(self.crucigrama.alto)
        ]
        for variable, palabra in asignacion.items():
            direccion = variable.direccion
            for k in range(len(palabra)):
                i = variable.i + (k if direccion == Variable.ABAJO else 0)
                j = variable.j + (k if direccion == Variable.DERECHA else 0)
                letras[i][j] = palabra[k]
        return letras

    def print(self, asignacion):
        """
        Imprimir el crucigrama asignado al terminal.
        """
        letras = self.cuadricula_letras(asignacion)
        for i in range(self.crucigrama.alto):
            for j in range(self.crucigrama.ancho):
                if self.crucigrama.estructura[i][j]:
                    print(letras[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, asignacion, filename):
        """
        Guardar el crucigrama a un archivo imagen.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letras = self.cuadricula_letras(asignacion)

        # Crear un lienzo blanco
        img = Image.new(
            "RGBA",
            (self.crucigrama.ancho * cell_size,
             self.crucigrama.alto * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crucigrama.alto):
            for j in range(self.crucigrama.ancho):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crucigrama.estructura[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letras[i][j]:
                        _, _, w, h = draw.textbbox((0, 0), letras[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letras[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Aplique la consistencia de nodos y arcos y, a continuación, resuelva el CSP.
        """
        self.consistencia_nodo()
        self.ac3()
        return self.backtrack(dict())

    def consistencia_nodo(self):
        """
        Actualizar `self.dominios` de forma que cada variable sea nodo-consistente.
        (Elimina cualquier valor que sea inconsistente con las restricciones unarias de una variable;
        en este caso, la longitud de la palabra).
        """
        for var in self.dominios:
            self.dominios[var] = {palabra for palabra in self.dominios[var] if len(palabra) == var.longitud}

    def revisar(self, x, y):
        """
        Hacer que la variable `x` tenga consistencia de arco con la variable `y`.
        Para ello, elimine los valores de `self.dominios[x]` para los que no hay
        valor correspondiente posible para `y` en `self.dominios[y]`.

        Devuelve True si se ha hecho una revisión al dominio de `x`; devuelve
        False si no se ha hecho ninguna revisión.
        """
        revisado = False

        solapamiento = self.crucigrama.solapamientos.get((x, y))
        if not solapamiento:
            return revisado

        i, j = solapamiento

        for palabra_x in set(self.dominios[x]):
            cumple_restriccion = any(palabra_x[i] == palabra_y[j] for palabra_y in self.dominios[y])
            if not cumple_restriccion:
                self.dominios[x].remove(palabra_x)
                revisado = True
        return revisado

    def ac3(self, arcs=None): 
        """
        Actualizar `self.dominios` de tal manera que cada variable sea consistencia de arco.
        Si `arcs` es None, comienza con la lista inicial de todos los arcos del problema.
        Si no, usa `arcs` como lista inicial de arcos para hacer consistencia.

        Devuelve True si se cumple la consistencia de arcos y no hay dominios vacíos;
        devuelve False si uno o más dominios terminan vacíos.
        """
        if arcs is None:
            arcs = [(x, y) for x in self.dominios for y in self.crucigrama.vecinos(x)]
        else:
            arcs = list(arcs)

        while arcs:
            (x, y) = arcs.pop()
            if self.revisar(x, y):
                if not self.dominios[x]:
                    return False
                for z in self.crucigrama.vecinos(x) - {y}:
                    arcs.append((z, x))
        return True

    def asignacion_completa(self, asignacion):
        """
        Devuelve True si `asignacion` está completa (es decir, asigna un valor a cada
        variable crucigrama); devuelve False en caso contrario.
        """
        return set(asignacion.keys()) == set(self.crucigrama.variables)

    def consistencia(self, asignacion):
        """
        Devuelve True si `asignacion` es consistencia (es decir, las palabras encajan en crucigrama
        sin caracteres conflictivos); devuelve False en caso contrario.
        """
        for (var1, palabra1) in asignacion.items():
            if var1.longitud != len(palabra1):
                return False
            for var2 in self.crucigrama.vecinos(var1):
                if var2 in asignacion:
                    palabra2 = asignacion[var2]
                    i, j = self.crucigrama.solapamientos[var1, var2]
                    if palabra1[i] != palabra2[j]:
                        return False
        return True

    def ordenar_valores_dominio(self, var, asignacion):
        """
        Devuelve una lista de valores en el dominio de `var`
        - Puede NO estar ordenada.
        - Puede estar ordenada por el número de valores que descartan para las variables vecinas (menor a mayor).
        """
        def conflictos(palabra):
            return sum(
                1
                for vecino in self.crucigrama.vecinos(var)
                if vecino not in asignacion and palabra in self.dominios[vecino]
            )
        return sorted(self.dominios[var], key=conflictos)

    def seleccionar_variable_no_asignada(self, asignacion):
        """
        Devuelve una variable no asignada que no forme ya parte de `asignacion`.
        - Puede seleccionar la siguiente variable no asignada.
        - Puede elegir la variable con el minimo número de valores restantes en el dominio.
        - Puede elegir la variable con el minimo número de valores restantes en el dominio; y
          si hay empate, elige la variable con el mayor grado.
        """
        no_asignadas = [v for v in self.crucigrama.variables if v not in asignacion]

        # Heurística combinada: primero mínimo número de valores restantes y luego grado
        no_asignadas.sort(key=lambda var: (len(self.dominios[var]), -len(self.crucigrama.vecinos(var))))

        return no_asignadas[0]

    def inferencia(self, asignacion, var):
        """
        Realiza la inferencia de AC-3 en los dominios.
        """
        inferences = {}
        queue = [(x, var) for x in self.crucigrama.vecinos(var)]

        while queue:
            (x, y) = queue.pop()
            if self.revisar(x, y):
                if not self.dominios[x]:
                    return None
                inferences[x] = self.dominios[x].copy()
                for z in self.crucigrama.vecinos(x) - {y}:
                    queue.append((z, x))
        return inferences

    def backtrack(self, asignacion):
        """
        Utiliza el algoritmo de backtracking para encontrar una asignación.
        """
        if self.asignacion_completa(asignacion):
            return asignacion

        var = self.seleccionar_variable_no_asignada(asignacion)

        for valor in self.ordenar_valores_dominio(var, asignacion):
            nueva_asignacion = asignacion.copy()
            nueva_asignacion[var] = valor

            if self.consistencia(nueva_asignacion):
                inferences = self.inferencia(nueva_asignacion, var)

                if inferences is not None:
                    for variable, valores in inferences.items():
                        self.dominios[variable] = valores

                    resultado = self.backtrack(nueva_asignacion)

                    if resultado:
                        return resultado

                    for variable in inferences:
                        self.dominios[variable] = inferences[variable]

        return None

if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Usage: python generate.py estructura palabras")
    estructura = sys.argv[1]
    palabras = sys.argv[2]

    crucigrama = Crucigrama(estructura, palabras)
    creador = CreadorCrucigrama(crucigrama)
    asignacion = creador.solve()

    if asignacion is None:
        print("No se encontró una solución.")
    else:
        creador.print(asignacion)
        creador.save(asignacion, "salida.png")