from fastapi import FastAPI
from pydantic import BaseModel
from url_process import URLProcessor
from build_graph import DynamicKNNGraph
from model import GraphSAGE, best_params
import torch
import numpy as np

app = FastAPI()

url_processor = URLProcessor(
    tfidf_vectorizer_path="tfidf_vectorizer.pkl", 
    tfidf_reducer_path="tfidf_reducer.pkl",
    embedding_reducer_path="embedding_reducer.pkl"
)

graph = DynamicKNNGraph("knn_graph.pt")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
updated_graph = torch.load("updated_knn_graph.pt", map_location=device)
updated_graph = updated_graph.to(device)

loaded_model = GraphSAGE(
    in_channels=updated_graph.x.shape[1], 
    hidden_channels=best_params['hidden_size'], 
    out_channels=2, 
    dropout=best_params['dropout']
).to(device)

loaded_model.load_state_dict(torch.load("graphsage_model.pth", map_location=device))
loaded_model.eval()

class URLRequest(BaseModel):
    url: str

@app.post("/predict")
def predict_url(request: URLRequest):
    url = request.url
    
    features = url_processor.transform_url(url)
    
    graph.add_new_url(features, url)
    graph.save_updated_graph("updated_knn_graph.pt")

    updated_graph = torch.load("updated_knn_graph.pt", map_location=device)
    updated_graph = updated_graph.to(device)

    new_url_index = updated_graph.x.shape[0] - 1
    with torch.no_grad():
        logits = loaded_model(updated_graph)
        predicted_label = torch.argmax(logits[new_url_index]).item()

    return {"url": url, "predicted_label": predicted_label}

