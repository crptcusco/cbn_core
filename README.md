# Coupled Boolean Network Library (cbnetwork)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/release/python-380/)

`cbnetwork` es una librería en Python para la creación, simulación y análisis de Redes Booleanas Acopladas (CBNs). Desarrollada como parte de una investigación académica en Ciencias de la Computación, esta herramienta provee los recursos necesarios para modelar y entender sistemas dinámicos complejos que pueden ser representados como redes booleanas interconectadas.

La librería permite una definición flexible de topologías de red, dinámicas locales y funciones de acoplamiento, convirtiéndola en una herramienta poderosa para investigadores en biología computacional, teoría de sistemas e inteligencia artificial. El análisis de atractores se realiza utilizando un solver SAT, lo que permite una búsqueda eficiente en el espacio de estados.

## Fundamento Teórico

Las Redes Booleanas Acopladas (CBNs) son un formalismo de modelado para describir sistemas compuestos por subsistemas interconectados, donde cada subsistema es una red booleana. El estado de cada variable en una red local es determinado por una función booleana que depende del estado de otras variables dentro de la misma red y de las señales recibidas desde redes vecinas.

El objetivo principal de esta librería es identificar los **atractores** del sistema global. Un atractor puede ser un estado estable (atractor puntual) o un ciclo de estados (atractor cíclico) hacia el cual el sistema tiende a evolucionar. En el contexto de las CBNs, estos atractores globales son denominados **Campos de Atractores (Attractor Fields)**, que representan las configuraciones estables del sistema completo.

Esta librería utiliza un enfoque basado en SAT (problema de satisfacibilidad booleana) para encontrar de manera eficiente los atractores del sistema global.

## Instalación

Para utilizar la librería, clona este repositorio e instala las dependencias utilizando `pip`:

```bash
git clone https://github.com/j-one-k/cbnetwork.git
cd cbnetwork
pip install -r requirements.txt
```

> **Nota sobre Dependencias Opcionales:** Si deseas utilizar el solver basado en SAT (método `find_attractors_duvrova`), es necesario tener instalado el binario `minisat` en tu sistema (ej. `sudo apt-get install minisat` en sistemas basados en Debian). Para la mayoría de los casos de uso estándar y benchmarks, el método de fuerza bruta (`find_attractors_brute_force`) es suficiente y no requiere dependencias externas adicionales.

## Guía de Inicio Rápido

A continuación, se muestra un ejemplo mínimo de cómo crear y analizar una Red Booleana Acoplada simple:

```python
from cbnetwork.cbnetwork import CBN
from cbnetwork.coupling import OrCoupling, AndCoupling

# 1. Definir la topología y parámetros de la red
# Se creará un sistema de 3 redes locales totalmente conectadas,
# cada una con 2 variables internas.
cbn = CBN.cbn_generator(
    v_topology=1,  # 1 = Grafo Completo
    n_networks=3,
    n_var_network=2,
    n_input_variables=1,
    n_output_variables=1,
    coupling_strategy=OrCoupling()  # Estrategia de acoplamiento (puede ser OrCoupling, AndCoupling, etc.)
)

# 2. Encontrar los atractores locales para cada red bajo todas las señales externas posibles
# Este es el paso computacionalmente más intensivo.
cbn.find_local_attractors_parallel()

# 3. Encontrar los pares de atractores compatibles entre redes conectadas
cbn.find_compatible_pairs_parallel()

# 4. Ensamblar los pares compatibles para encontrar los atractores globales (Campos de Atractores)
cbn.mount_stable_attractor_fields()

# 5. Mostrar los resultados
print(f"Número de campos de atractores encontrados: {cbn.get_n_attractor_fields()}")
cbn.show_stable_attractor_fields()

```

## Citando este trabajo

Si utilizas esta librería en una investigación publicada, por favor cita el trabajo original donde fue desarrollada. (Detalles de la citación por añadir).

## Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo `LICENSE` para más detalles.
