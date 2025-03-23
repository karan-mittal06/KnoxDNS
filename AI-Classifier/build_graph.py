import torch
import networkx as nx
import numpy as np
from sklearn.neighbors import NearestNeighbors
from torch_geometric.data import Data

class DynamicKNNGraph:
    def __init__(self, graph_path="knn_graph.pt", k=7):
        """
        Initialize the dynamic KNN graph by loading the precomputed graph.
        :param graph_path: Path to the saved KNN graph file.
        :param k: Number of nearest neighbors.
        """
        self.k = k

        self.graph_data = torch.load(graph_path)
        self.feature_matrix = self.graph_data.x.numpy() 
        self.labels = self.graph_data.y.numpy() 
        self.edge_index = self.graph_data.edge_index.numpy().T.tolist()

        self.graph = nx.Graph()
        for i, label in enumerate(self.labels):
            self.graph.add_node(i, label=label)
        for edge in self.edge_index:
            self.graph.add_edge(edge[0], edge[1])

    def add_new_url(self, new_feature_vector, url_id):
        """
        Dynamically add a new URL using k-nearest neighbors.
        :param new_feature_vector: Feature vector of the new URL.
        :param url_id: Unique ID for the new URL.
        """
        knn = NearestNeighbors(n_neighbors=self.k, metric="euclidean")
        knn.fit(self.feature_matrix)
        distances, indices = knn.kneighbors(new_feature_vector)

        self.feature_matrix = np.vstack([self.feature_matrix, new_feature_vector])

        new_idx = len(self.feature_matrix) - 1
        self.graph.add_node(new_idx)

        for i, neighbor_idx in enumerate(indices[0]):
            self.graph.add_edge(new_idx, neighbor_idx, weight=distances[0][i])

        print(f"Added URL {url_id} as node {new_idx} with {self.k} nearest neighbors.")

    def save_updated_graph(self, save_path="updated_knn_graph.pt"):
        """
        Save the updated graph in PyTorch Geometric format.
        """
        edge_index = torch.tensor(list(self.graph.edges), dtype=torch.long).t().contiguous()
        x_tensor = torch.tensor(self.feature_matrix, dtype=torch.float)

        updated_graph = Data(x=x_tensor, edge_index=edge_index)
        torch.save(updated_graph, save_path)
        print(f"Updated graph saved to {save_path}")
