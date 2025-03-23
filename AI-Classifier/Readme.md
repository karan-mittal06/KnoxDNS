# KnoxDNS: AI-Powered Malicious URL Detection  

This project implements an AI-powered system to classify URLs as **safe (0)** or **malicious (1)** using **GraphSAGE** and **dynamic KNN graph construction**. The system extracts meaningful features from URLs, builds a dynamic graph structure, and classifies new URLs in real-time.

## 1. `url_process.py`
### Description
`url_process.py` contains the **`URLProcessor`** class, responsible for feature extraction from URLs. Since URLs cannot be directly used as numerical data, meaningful feature extraction is performed.

### Features Extracted:
- **Lexical Features:** Number of special characters, hyphens, dots, etc.
- **TF-IDF Word Embeddings:** Frequency-based vectorization of URL components.
- **Root Domain & Subdomain Features:** Structural breakdown of the URL.
- **Dimensionality Reduction:**  
  - **TruncatedSVD (LSA)**: Reduces high-dimensional TF-IDF features to 20 key components.  
  - **PCA**: Further reduces word embedding dimensions to extract the most relevant data.

These features are transformed and stored in a structured manner to ensure effective graph-based learning.

---

## 2. `build_graph.py`
### Description
`build_graph.py` contains the **`DynamicKNNGraph`** class, which builds and updates the KNN-based graph for the model. Since URL classification benefits from relational data, we construct a **graph-based representation**.

### Graph Construction Process:
1. **Initialize KNN Graph**: Load precomputed graph or create a new one.
2. **Determine Node Similarity**:  
   - Uses **KNN (k=7)** with **Minkowski distance (Euclidean)** to find similar nodes.  
   - Constructs edges based on URL feature similarity.
3. **Dynamic Graph Updates**:  
   - **New URLs are dynamically added** instead of constructing an entirely new graph each time.  
   - Saves the updated graph after adding new nodes.

By maintaining an evolving graph, the system adapts to new URLs over time while improving classification accuracy.

---

## 3. `model.py`
### Description
`model.py` contains the **GraphSAGE model** for URL classification. After testing different graph architectures (**GCN, GAT, GIN**), **GraphSAGE** was selected for its ability to scale with large graphs and effectively aggregate neighborhood information.

### Model Architecture:
- **Three-layer GraphSAGE**  
- **ReLU Activation** after each layer  
- **Dropout for Regularization**  
- **Cross-Entropy Loss Function** for classification  

### Training:
- **Initial Model** trained on 100,000 URLs, tested on 25,000.
- **Hyperparameter Tuning** using **GridSearchCV** (best accuracy: **92%**).
- **Optimized Configuration**:  
  - `hidden_size = 128`
  - `dropout = 0.3`
  - `learning_rate = 0.001`

---

## 4. `main.py`
### Description
`main.py` integrates all modules into a **FastAPI** server, allowing real-time URL classification via an API endpoint.

### API Endpoint:
- **`POST /classify_url/`**  
  - Accepts: `{ "url": "<URL_TO_CHECK>" }`  
  - Returns: `{ "url": "<URL>", "prediction": 0/1 }`  

### Workflow:
1. **Receives URL from user.**  
2. **Extracts Features** using `URLProcessor`.  
3. **Adds URL as a new node** in the graph via `DynamicKNNGraph`.  
4. **Loads Pretrained GraphSAGE Model** and passes the new node for classification.  
5. **Returns the classification result** (0 = Safe, 1 = Malicious).  

### Running the API:
To start the FastAPI server, run:
uvicorn main:app --reload

Endpoint can be tested out on Swagger Docs.
