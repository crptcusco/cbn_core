# Internal imports
import logging
import random
import time

import matplotlib.colors as mco
import matplotlib.pyplot as plt

# External imports
import networkx as nx

from cbnetwork.utils.customtext import CustomText
from cbnetwork.utils.logging_config import setup_logging

setup_logging()


class GlobalTopology:
    allowed_topologies = {
        1: "complete",
        2: "aleatory_fixed_2_input_edges",
        3: "cycle",
        4: "path",
        5: "aleatory_gn",
        6: "aleatory_gnc",
        7: "dorogovtsev_mendes",
        8: "small_world",
        9: "scale_free",
        10: "random",
    }

    def __init__(self, v_topology, l_edges):
        """
        Initializes the global topology with the specified type and edges.
        """
        self.v_topology = v_topology
        self.l_edges = l_edges
        self.o_graph = nx.DiGraph()
        self.o_graph.add_edges_from(self.l_edges)
        self.d_network_color = {}
        self.generate_local_nets_colors()

    @classmethod
    def show_allowed_topologies(cls):
        """
        Displays the allowed topologies for Directed Graphs.
        """
        CustomText.make_sub_title("List of allowed topologies of Directed Graphs")
        logger = logging.getLogger(__name__)
        for key, value in cls.allowed_topologies.items():
            logger.info("%s - %s", key, value)

    @classmethod
    def generate_sample_topology(cls, v_topology, n_nodes, n_edges=None):
        """
        Generates a global topology based on the specified type.
        :param v_topology: Type of topology to generate.
        :param n_nodes: Number of nodes in the topology.
        :param n_edges: Number of edges in the topology (if applicable).
        :return: Instance of the 5_specific topology class.
        """
        if v_topology not in cls.allowed_topologies:
            msg = f"Invalid topology option: {v_topology}. Valid options are: {list(cls.allowed_topologies.keys())}"
            logging.getLogger(__name__).error(msg)
            raise ValueError(msg)
        if n_nodes <= 1:
            logging.getLogger(__name__).error(
                "ERROR: Number of nodes must be greater than 1"
            )
            return NullTopology(message="Number of nodes must be greater than 1")

        if v_topology == 1:
            return CompleteDigraph(n_nodes=n_nodes)
        elif v_topology == 2:
            return AleatoryFixedDigraph(n_nodes=n_nodes, n_edges=n_edges)
        elif v_topology == 3:
            return CycleDigraph(n_nodes=n_nodes)
        elif v_topology == 4:
            return PathDigraph(n_nodes=n_nodes)
        elif v_topology == 5:
            pass
        elif v_topology == 6:
            pass
        elif v_topology == 7:
            return DorogovtsevMendesDigraph(n_nodes=n_nodes)
        elif v_topology == 8:
            return SmallWorldGraph(n_nodes=n_nodes, k_neighbors=3, p_rewire=0.5)
        elif v_topology == 9:
            return ScaleFreeGraph(n_nodes=n_nodes, m_edges=2)
        elif v_topology == 10:
            return RandomGraph(n_nodes=n_nodes, p_edge=0.5)
        return NullTopology(message="Topology not implemented or unsupported")

    def generate_local_nets_colors(self):
        """
        Generates random colors for local networks.
        """
        l_colors = list(mco.CSS4_COLORS.keys())
        random.shuffle(l_colors)
        for i, color in enumerate(l_colors):
            self.d_network_color[i] = color

    def plot_topology(self, ax=None):
        """
        Plots the topology using matplotlib.
        :param ax: Matplotlib axis to plot on; if None, use the current axis.
        """
        if ax is None:
            ax = plt.gca()

        # If graph has no nodes, show a simple empty plot with message
        if self.o_graph is None or self.o_graph.number_of_nodes() == 0:
            ax.text(0.5, 0.5, "Empty topology", ha="center", va="center")
            ax.axis("off")
            return

        pos = (
            nx.random_layout(self.o_graph)
            if self.v_topology == 1
            else nx.circular_layout(self.o_graph)
        )
        node_colors = [
            self.d_network_color.get(node, "skyblue") for node in self.o_graph.nodes()
        ]
        nx.draw_networkx_nodes(
            self.o_graph, pos, node_color=node_colors, node_size=500, ax=ax
        )
        nx.draw_networkx_labels(
            self.o_graph, pos, font_size=12, font_color="black", ax=ax
        )
        nx.draw_networkx_edges(self.o_graph, pos, arrows=True, ax=ax, width=3)

        # ax.set_title("CBN Topology")
        ax.axis("off")

    def get_edges(self):
        """
        Returns the list of edges in the graph.
        """
        return self.l_edges

    def get_nodes(self):
        """
        Returns the set of nodes in the graph.
        """
        return set(self.o_graph.nodes())


class NullTopology(GlobalTopology):
    """A safe Null Object replacement for cases where a topology cannot be
    generated. Provides a `plot_topology` that draws an informative empty plot
    and implements the same minimal API as `GlobalTopology`.
    """

    def __init__(self, message="Empty topology"):
        self.v_topology = 0
        self.l_edges = []
        self.o_graph = nx.DiGraph()
        self.d_network_color = {}
        self._message = message

    def plot_topology(self, ax=None):
        if ax is None:
            ax = plt.gca()
        ax.text(0.5, 0.5, str(self._message), ha="center", va="center")
        ax.axis("off")

    def get_edges(self):
        return []

    def get_nodes(self):
        return set()


class PathDigraph(GlobalTopology):
    def __init__(self, n_nodes):
        """
        Initializes a path graph with the given number of nodes.
        """
        G = nx.path_graph(n_nodes, create_using=nx.DiGraph())
        G = nx.relabel_nodes(G, {i: i + 1 for i in range(n_nodes)})
        l_edges = list(G.edges())
        self.n_nodes = n_nodes
        super().__init__(v_topology=4, l_edges=l_edges)

    def add_node(self):
        """
        Adds a new node to the path graph and maintains the linear structure.
        """
        new_node = self.n_nodes + 1
        last_node = self.n_nodes
        self.o_graph.add_node(new_node)
        self.o_graph.add_edge(last_node, new_node)
        self.l_edges = list(self.o_graph.edges())
        self.n_nodes += 1


class CycleDigraph(GlobalTopology):
    def __init__(self, n_nodes):
        """
        Initializes a cycle graph with the given number of nodes.
        """
        G = nx.cycle_graph(n_nodes, create_using=nx.DiGraph())
        G = nx.relabel_nodes(G, {i: i + 1 for i in range(n_nodes)})
        l_edges = list(G.edges())
        self.n_nodes = n_nodes
        super().__init__(v_topology=3, l_edges=l_edges)

    def add_node(self):
        """
        Adds a new node to the cycle graph and maintains the cyclic structure.
        """
        new_node = self.n_nodes + 1
        last_node = self.n_nodes
        first_node = 1
        self.o_graph.remove_edge(last_node, first_node)
        self.o_graph.add_node(new_node)
        self.o_graph.add_edge(last_node, new_node)
        self.o_graph.add_edge(new_node, first_node)
        self.l_edges = list(self.o_graph.edges())
        self.n_nodes += 1


class CompleteDigraph(GlobalTopology):
    def __init__(self, n_nodes):
        """
        Initializes a complete graph with the given number of nodes.
        """
        G = nx.complete_graph(n_nodes, create_using=nx.DiGraph())
        G = nx.relabel_nodes(G, {i: i + 1 for i in G.nodes()})
        l_edges = list(G.edges())
        self.n_nodes = n_nodes
        super().__init__(v_topology=1, l_edges=l_edges)

    def add_node(self):
        """
        Adds a new node to the complete graph and connects it to all existing nodes.
        """
        new_node = max(self.o_graph.nodes()) + 1
        self.o_graph.add_node(new_node)
        for node in self.o_graph.nodes():
            if node != new_node:
                self.o_graph.add_edge(new_node, node)
                self.o_graph.add_edge(node, new_node)
        self.l_edges = list(self.o_graph.edges())
        self.n_nodes += 1


class AleatoryFixedDigraph(GlobalTopology):
    def __init__(self, n_nodes, n_edges=None):
        """
        Initializes a random directed graph with fixed edges.
        """
        self.n_nodes = n_nodes
        self.l_nodes = list(range(1, n_nodes + 1))
        self.n_edges = n_edges if n_edges is not None else n_nodes
        self.l_edges = []
        self.generate_edges()
        super().__init__(v_topology=2, l_edges=self.l_edges)

    def generate_edges(self):
        """
        Generates edges for the random directed graph, ensuring that:
          1. The number of edges does not exceed twice the number of nodes.
          2. The graph is connected (i.e., the underlying undirected graph is connected).

        This implementation creates a spanning tree (to guarantee connectivity) and then adds
        additional random edges until reaching the desired number of edges.
        """

        # check minimum edges!!!
        # minimun: bn - 1

        # Limit the number of edges if it exceeds 2 * number of nodes
        max_edges = 2 * self.n_nodes
        if self.n_edges > max_edges:
            logging.getLogger(__name__).warning(
                "Warning: n_edges (%d) exceeds 2 * n_nodes. Setting n_edges = %d.",
                self.n_edges,
                max_edges,
            )
            self.n_edges = max_edges

        # Use nodes as numbers 0 to n_nodes - 1
        nodes = list(range(self.n_nodes))

        # Try to generate a connected graph
        while True:
            G = nx.DiGraph()
            G.add_nodes_from(nodes)

            # Create a spanning tree to guarantee connectivity.
            # For each node (except the first), add an edge from a random previous node.
            for i in range(1, self.n_nodes):
                u = random.randint(0, i - 1)
                G.add_edge(u, i)

            attempts = 0
            max_attempts = self.n_nodes * 10  # Limit attempts to avoid endless loop
            while G.number_of_edges() < self.n_edges and attempts < max_attempts:
                u, v = random.sample(nodes, 2)
                if not G.has_edge(u, v):
                    G.add_edge(u, v)
                attempts += 1

            if G.number_of_edges() < self.n_edges:
                logging.getLogger(__name__).warning(
                    "Warning: Could not reach the desired number of edges."
                )

            # Check connectivity on the undirected version of the graph.
            if nx.is_weakly_connected(G):
                break
            else:
                logging.getLogger(__name__).warning(
                    "Graph is not connected, retrying..."
                )

        # Optionally, relabel nodes if they are numeric (e.g., start numbering at 1)
        if all(isinstance(node, int) for node in G.nodes()):
            mapping = {node: node + 1 for node in G.nodes()}
            G = nx.relabel_nodes(G, mapping)

        # Update edge list
        self.l_edges = list(G.edges())
        return G

    def add_edge(self, u, v):
        """
        Adds a specific edge (u, v) to the graph.
        """
        if u in self.l_nodes and v in self.l_nodes:
            G = nx.DiGraph()
            G.add_nodes_from(self.l_nodes)
            G.add_edges_from(self.l_edges)

            if not G.has_edge(u, v):
                G.add_edge(u, v)
                self.l_edges.append((u, v))
                self.n_edges = len(self.l_edges)
                self.update_parent_graph()

    def generate_edge(self):
        """
        Generates a new random edge to the graph while maintaining constraints.
        """
        G = nx.DiGraph()
        G.add_nodes_from(self.l_nodes)
        G.add_edges_from(self.l_edges)

        while True:
            u, v = random.sample(self.l_nodes, 2)
            if G.in_degree(v) < 2 and not G.has_edge(u, v):
                G.add_edge(u, v)
                self.l_edges.append((u, v))
                break

        self.n_edges = len(self.l_edges)
        self.update_parent_graph()

    def add_node(self):
        """
        Adds a new node to the graph and updates the edges.
        """
        start_time = time.time()

        G = nx.DiGraph()
        G.add_nodes_from(self.l_nodes)
        G.add_edges_from(self.l_edges)

        new_node = max(self.l_nodes) + 1
        self.l_nodes.append(new_node)
        G.add_node(new_node)
        logging.getLogger(__name__).info("Adding new node: %s", new_node)

        edge_to_remove = random.choice(list(G.edges))
        G.remove_edge(*edge_to_remove)
        self.l_edges.remove(edge_to_remove)
        logging.getLogger(__name__).info("Removed edge: %s", edge_to_remove)

        while True:
            u = random.choice(self.l_nodes[:-1])
            if not G.has_edge(u, new_node):
                G.add_edge(u, new_node)
                self.l_edges.append((u, new_node))
                logging.getLogger(__name__).info(
                    "Added edge from %s to %s", u, new_node
                )
                break

        while True:
            v = random.choice(self.l_nodes[:-1])
            if G.in_degree(v) < 2 and not G.has_edge(new_node, v):
                G.add_edge(new_node, v)
                self.l_edges.append((new_node, v))
                logging.getLogger(__name__).info(
                    "Added edge from %s to %s", new_node, v
                )
                break

        for node in self.l_nodes:
            if G.in_degree(node) == 0 and G.out_degree(node) == 0:
                u = random.choice([n for n in self.l_nodes if n != node])
                G.add_edge(u, node)
                self.l_edges.append((u, node))
                logging.getLogger(__name__).info(
                    "Ensured connectivity by adding edge from %s to %s", u, node
                )

        self.n_nodes += 1
        self.n_edges = len(self.l_edges)
        self.update_parent_graph()

        end_time = time.time()
        logging.getLogger(__name__).info(
            "Node %s added in %s seconds", new_node, end_time - start_time
        )

    def update_parent_graph(self):
        """
        Updates the graph representation after modifications.
        """
        self.o_graph = nx.DiGraph()
        self.o_graph.add_nodes_from(self.l_nodes)
        self.o_graph.add_edges_from(self.l_edges)


class DorogovtsevMendesDigraph(GlobalTopology):
    def __init__(self, n_nodes):
        """
        Initializes a directed Dorogovtsev-Mendes graph.
        """

        if n_nodes < 3:
            raise ValueError("El número mínimo de nodos para este modelo es 3.")

        self.n_nodes = n_nodes
        self.l_nodes = list(range(1, n_nodes + 1))
        self.l_edges = [(1, 2), (2, 3), (3, 1)]  # Triángulo inicial
        self.n_edges = len(self.l_edges)

        # Agregar nodos adicionales
        for new_node in range(4, self.n_nodes + 1):
            self.add_node(new_node)

        super().__init__(v_topology=7, l_edges=self.l_edges)

    def add_node(self, new_node=None):
        """
        Adds a new node to the Dorogovtsev-Mendes directed graph while maintaining its structural properties.
        """
        if new_node is None:
            new_node = max(self.l_nodes) + 1

        self.l_nodes.append(new_node)

        # Seleccionar una arista existente aleatoriamente
        u, v = random.choice(self.l_edges)

        # Conectar el nuevo nodo a ambos extremos de la arista seleccionada
        self.l_edges.append((new_node, u))
        self.l_edges.append((new_node, v))

        self.n_nodes += 1
        self.update_parent_graph()

    def update_parent_graph(self):
        """
        Updates the graph representation after modifications.
        """
        self.o_graph = nx.DiGraph()
        self.o_graph.add_nodes_from(self.l_nodes)
        self.o_graph.add_edges_from(self.l_edges)

    def generate_edge(self):
        """
        Agrega una nueva arista al grafo dirigido Dorogovtsev-Mendes mientras mantiene sus propiedades estructurales.
        """
        if len(self.l_edges) >= (self.n_nodes - 1) * 2:
            raise ValueError(
                "No se pueden agregar más aristas manteniendo la estructura de Dorogovtsev-Mendes."
            )

        # Seleccionar una arista existente aleatoriamente
        u, v = random.choice(self.l_edges)

        # Crear un nuevo nodo
        new_node = max(self.l_nodes) + 1
        self.l_nodes.append(new_node)

        # Conectar el nuevo nodo a ambos extremos de la arista seleccionada
        self.l_edges.append((new_node, u))
        self.l_edges.append((new_node, v))

        self.n_nodes += 1
        self.n_edges = len(self.l_edges)

        self.update_parent_graph()


class SmallWorldGraph(GlobalTopology):
    def __init__(self, n_nodes, k_neighbors, p_rewire):
        """
        Modelo Small-World de Watts-Strogatz.

        :param n_nodes: Número de nodos
        :param k_neighbors: Cada nodo se conecta a k vecinos más cercanos en un anillo
        :param p_rewire: Probabilidad de reconectar una arista
        """
        self.n_nodes = n_nodes
        self.k_neighbors = k_neighbors
        self.p_rewire = p_rewire
        self.graph = nx.watts_strogatz_graph(n_nodes, k_neighbors, p_rewire)

        # Renumerar nodos para que comiencen en 1
        mapping = {node: node + 1 for node in self.graph.nodes()}
        self.graph = nx.relabel_nodes(self.graph, mapping)

        # Actualizar listas
        self.l_nodes = list(self.graph.nodes)
        self.l_edges = list(self.graph.edges)

        super().__init__(v_topology=8, l_edges=self.l_edges)

    def add_edge(self, u, v):
        """
        Añade una nueva arista entre los nodos u y v manteniendo la estructura Small-World.
        """
        if (u, v) in self.l_edges or (v, u) in self.l_edges:
            return  # Evita duplicar aristas

        # Respetar la proximidad del modelo Small-World
        if abs(u - v) <= self.k_neighbors // 2 or random.random() < self.p_rewire:
            self.graph.add_edge(u, v)
            self.l_edges.append((u, v))

        self.update_parent_graph()

    def add_node(self):
        """Añade un nuevo nodo y lo conecta a k vecinos al azar manteniendo la estructura Small-World."""
        new_node = (
            max(self.l_nodes) + 1 if self.l_nodes else 1
        )  # Si está vacío, empieza en 1
        self.graph.add_node(new_node)
        self.l_nodes.append(new_node)

        # Conectar con `k_neighbors` nodos existentes
        neighbors = random.sample(
            self.l_nodes[:-1], min(self.k_neighbors, len(self.l_nodes) - 1)
        )
        for neighbor in neighbors:
            self.add_edge(new_node, neighbor)

        self.update_parent_graph()

    def generate_edge(self):
        """
        Genera una nueva arista aleatoria manteniendo las restricciones del modelo Small-World.
        """
        # Seleccionar un nodo al azar
        u = random.choice(self.l_nodes)

        # Definir posibles vecinos respetando la distancia en la topología anillo
        possible_neighbors = [
            v for v in self.l_nodes if v != u and abs(v - u) <= self.k_neighbors // 2
        ]

        # Con probabilidad p_rewire, conectar con un nodo aleatorio
        if random.random() < self.p_rewire:
            possible_neighbors = [v for v in self.l_nodes if v != u]

        # Si no hay vecinos posibles, salir
        if not possible_neighbors:
            return None

        # Elegir un nodo vecino válido
        v = random.choice(possible_neighbors)

        # Evitar duplicar aristas
        if (u, v) in self.l_edges or (v, u) in self.l_edges:
            return None

        # Agregar la arista
        self.add_edge(u, v)
        return (u, v)

    def update_parent_graph(self):
        """
        Actualiza la representación del grafo después de modificaciones.
        """
        self.o_graph = nx.DiGraph()
        self.o_graph.add_nodes_from(self.l_nodes)
        self.o_graph.add_edges_from(self.l_edges)


class ScaleFreeGraph(GlobalTopology):
    def __init__(self, n_nodes, m_edges):
        """
        Modelo Scale-Free de Barabási-Albert.

        :param n_nodes: Número de nodos
        :param m_edges: Número de aristas a añadir por cada nuevo nodo
        """
        self.n_nodes = n_nodes
        self.m_edges = m_edges
        self.graph = nx.barabasi_albert_graph(n_nodes, m_edges)
        self.l_nodes = list(self.graph.nodes)
        self.l_edges = list(self.graph.edges)

        # Renumerar nodos para que comiencen en 1
        mapping = {node: node + 1 for node in self.graph.nodes()}
        self.graph = nx.relabel_nodes(self.graph, mapping)

        # Actualizar listas
        self.l_nodes = list(self.graph.nodes)
        self.l_edges = list(self.graph.edges)

        super().__init__(v_topology=9, l_edges=self.l_edges)

    def add_edge(self, u, v):
        """Añade una nueva arista entre los nodos u y v."""
        self.graph.add_edge(u, v)  # FIX: Usa add_edge en lugar de generate_edge
        self.l_edges.append((u, v))

        self.update_parent_graph()

    def add_node(self):
        """Añade un nuevo nodo y lo conecta a m nodos existentes con probabilidad proporcional a su grado."""
        new_node = max(self.l_nodes) + 1
        self.l_nodes.append(new_node)

        degrees = dict(self.graph.degree())
        existing_nodes = list(self.graph.nodes)
        total_degree = sum(degrees.values())

        if total_degree == 0:
            targets = random.sample(existing_nodes, self.m_edges)
        else:
            probabilities = [degrees[node] / total_degree for node in existing_nodes]
            targets = random.choices(
                existing_nodes, weights=probabilities, k=self.m_edges
            )

        for target in targets:
            self.add_edge(new_node, target)

        self.update_parent_graph()

    def update_parent_graph(self):
        """
        Updates the graph representation after modifications.
        """
        self.o_graph = nx.DiGraph()
        self.o_graph.add_nodes_from(self.l_nodes)
        self.o_graph.add_edges_from(self.l_edges)

    def generate_edge(self):
        """Genera una nueva arista basada en el modelo de adjunción preferencial."""
        if not self.l_nodes:
            raise ValueError("No hay nodos disponibles para generar una arista.")

        u = random.choice(self.l_nodes)

        degrees = dict(self.graph.degree(self.l_nodes))  # FIX: Pasar lista completa
        total_degree = sum(degrees.values())

        if total_degree == 0:
            target = random.choice(self.l_nodes)
        else:
            probabilities = [degrees[node] / total_degree for node in self.l_nodes]
            target = random.choices(self.l_nodes, weights=probabilities, k=1)[0]

        self.add_edge(u, target)


class RandomGraph(GlobalTopology):
    def __init__(self, n_nodes, p_edge):
        """
        Modelo Aleatorio de Erdős-Rényi.

        :param n_nodes: Número de nodos
        :param p_edge: Probabilidad de que exista una arista entre cualquier par de nodos
        """
        self.n_nodes = n_nodes
        self.p_edge = p_edge
        self.graph = nx.erdos_renyi_graph(n_nodes, p_edge)
        self.l_nodes = list(self.graph.nodes)
        self.l_edges = list(self.graph.edges)

        # Renumerar nodos para que comiencen en 1
        mapping = {node: node + 1 for node in self.graph.nodes()}
        self.graph = nx.relabel_nodes(self.graph, mapping)

        # Actualizar listas
        self.l_nodes = list(self.graph.nodes)
        self.l_edges = list(self.graph.edges)

        super().__init__(v_topology=10, l_edges=self.l_edges)

    def add_edge(self, u, v):
        """Añade una nueva arista entre los nodos u y v."""
        self.graph.add_edge(u, v)  # FIX: Usa add_edge en lugar de generate_edge
        self.l_edges.append((u, v))

        self.update_parent_graph()

    def add_node(self):
        """Añade un nuevo nodo y lo conecta a nodos existentes con probabilidad p_edge."""
        new_node = max(self.l_nodes) + 1
        self.l_nodes.append(new_node)
        for node in self.l_nodes[:-1]:
            if random.random() < self.p_edge:
                self.add_edge(new_node, node)

        self.update_parent_graph()

    def generate_edge(self):
        """Genera una nueva arista entre dos nodos aleatorios con probabilidad p_edge."""
        if len(self.l_nodes) < 2:
            return  # No se pueden generar aristas si hay menos de dos nodos

        u, v = random.sample(self.l_nodes, 2)  # Selecciona dos nodos distintos
        if (u, v) not in self.l_edges and (v, u) not in self.l_edges:
            if random.random() < self.p_edge:
                self.add_edge(u, v)

    def update_parent_graph(self):
        """
        Updates the graph representation after modifications.
        """
        self.o_graph = nx.DiGraph()
        self.o_graph.add_nodes_from(self.l_nodes)
        self.o_graph.add_edges_from(self.l_edges)
