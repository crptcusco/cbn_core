# Resumen del Paso 3: Mount Stable Attractor Fields

## Los 3 Pasos del Workflow CBN

### Paso 1: Find Local Attractors
- **Objetivo:** Encontrar todos los atractores locales para cada red local en cada escena posible
- **Input:** Redes locales con sus funciones booleanas
- **Output:** `LocalAttractor` objects almacenados en `LocalScene.l_attractors`
- **Métodos disponibles:**
  - `find_local_attractors_sequential()` - SAT solver secuencial
  - `find_local_attractors_parallel()` - SAT solver paralelo
  - `find_local_attractors_brute_force_sequential()` - Brute force Python
  - `find_local_attractors_brute_force_turbo_sequential()` - **Turbo (Numba)** ⚡ 35x-100x más rápido

### Paso 2: Find Compatible Pairs
- **Objetivo:** Identificar pares de atractores que son compatibles a través de señales de acoplamiento
- **Input:** Atractores locales del Paso 1 + señales de acoplamiento (DirectedEdges)
- **Output:** `d_comp_pairs_attractors_by_value` en cada `DirectedEdge`
- **Lógica:** Para cada señal de acoplamiento, encontrar qué atractores de la red fuente producen un valor específico (0 o 1) y qué atractores de la red destino esperan ese mismo valor
- **Métodos disponibles:**
  - `find_compatible_pairs()` - Secuencial (Python) ⭐ **Más rápido**
  - `find_compatible_pairs_parallel()` - Paralelo (multiprocessing)
  - `find_compatible_pairs_turbo()` - Turbo (Numba) - más lento debido a overhead

### Paso 3: Mount Stable Attractor Fields ⬅️ **ESTE ES EL PASO 3**
- **Objetivo:** Ensamblar "campos de atractores" globales que sean mutuamente compatibles
- **Input:** Pares compatibles del Paso 2
- **Output:** `d_attractor_fields` - diccionario de campos de atractores globales
- **Lógica:**
  1. **Ordenar edges por compatibilidad** (`order_edges_by_compatibility()`)
  2. **Inicializar con el primer edge:** Tomar todos los pares del primer edge como base
  3. **Producto cartesiano modificado:** Para cada edge subsecuente:
     - Intentar agregar sus pares a los campos existentes
     - **Condición de compatibilidad:** Un par candidato es compatible si:
       - Las redes ya visitadas en el campo tienen los mismos atractores
       - Las redes nuevas agregan exactamente 2 nuevos atractores (uno por cada extremo del par)
  4. **Resultado:** Cada campo de atractores representa un estado global estable del sistema completo

- **Métodos disponibles:**
  - `mount_stable_attractor_fields()` - Secuencial
  - `mount_stable_attractor_fields_parallel()` - Paralelo (multiprocessing)
  - `mount_stable_attractor_fields_parallel_chunks()` - Paralelo con chunks

## Características del Paso 3

### Complejidad Computacional
- **Tipo:** Combinatorial explosion - el número de campos crece exponencialmente con el número de edges
- **Bottleneck:** `cartesian_product_mod()` y `evaluate_pair()` - muchas comparaciones de conjuntos
- **Escalabilidad:** Puede ser muy lento para sistemas con muchas señales de acoplamiento

### Estructura de Datos
```python
# Input (del Paso 2)
DirectedEdge.d_comp_pairs_attractors_by_value = {
    0: [(attr_src_1, attr_dst_1), (attr_src_2, attr_dst_2), ...],
    1: [(attr_src_3, attr_dst_3), ...]
}

# Output (Paso 3)
CBN.d_attractor_fields = {
    1: [attr_1, attr_2, attr_3, ...],  # Campo 1: lista de índices globales de atractores
    2: [attr_4, attr_5, attr_6, ...],  # Campo 2
    ...
}
```

### Ejemplo Conceptual
Si tienes 3 redes (A, B, C) con señales A→B y B→C:
- Paso 1: Encuentra atractores en A, B, C
- Paso 2: Encuentra pares compatibles (A_i, B_j) y (B_k, C_l)
- Paso 3: Encuentra combinaciones donde B_j == B_k (mismo atractor en B)
  - Campo válido: {A_i, B_j, C_l} ✅
  - Campo inválido: {A_i, B_j, C_m} donde B_j no es compatible con C_m ❌

## Oportunidades de Optimización

### Posibles Mejoras
1. **Numba/JIT:** Reemplazar operaciones de conjuntos con arrays NumPy
2. **Paralelismo más eficiente:** Dividir el trabajo de manera más granular
3. **Poda temprana:** Detectar incompatibilidades antes de generar todos los productos
4. **Estructuras de datos optimizadas:** Usar bitmasks en lugar de sets de Python

### Desafíos
- Las operaciones son inherentemente sobre conjuntos/listas de Python
- Mucha lógica condicional (difícil de vectorizar)
- Dependencias entre iteraciones (difícil de paralelizar completamente)
