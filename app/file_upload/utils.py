from llama_index.core.node_parser import SentenceSplitter
from transformers import AutoTokenizer, AutoModel
import uuid
import time

# Initialize tokenizer and model for embeddings
tokenizer = AutoTokenizer.from_pretrained("thenlper/gte-small")
model = AutoModel.from_pretrained("thenlper/gte-small")


# Function to generate embeddings using 'thenlper/gte-small'
def generate_embedding(text: str):
    inputs = tokenizer(
        text, return_tensors="pt", padding=True, truncation=True, max_length=512
    )
    outputs = model(**inputs)
    embeddings = (
        outputs.last_hidden_state.mean(dim=1).detach().numpy().flatten().tolist()
    )
    return embeddings


# Function to chunk document using LlamaIndex SentenceSplitter
def chunk_document(content: str, chunk_size=512):
    splitter = SentenceSplitter(chunk_size=chunk_size)  # Specify chunk size in tokens
    chunks = splitter.split_text(content)
    return chunks


# Function to create metadata
def create_metadata(
    document_title,
    source_type,
    doc_updated_at,
    primary_owners,
    secondary_owners,
    metadata_list,
    access_control_list,
    document_sets,
):
    return {
        "document_id": str(uuid.uuid4()),
        "semantic_identifier": document_title,
        "title": document_title,
        "source_type": source_type,
        "doc_updated_at": time.time(),
        "primary_owners": primary_owners,
        "secondary_owners": secondary_owners,
        "metadata_list": metadata_list,
        "access_control_list": access_control_list,
        "document_sets": document_sets,
    }
