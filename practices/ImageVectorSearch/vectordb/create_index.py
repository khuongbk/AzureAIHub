
import os
import json  
import wget
import pandas as pd
import zipfile
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.core.credentials import AzureKeyCredential  
from azure.search.documents import SearchClient, SearchIndexingBufferedSender  
from azure.search.documents.indexes import SearchIndexClient  
from azure.search.documents.models import (
    QueryAnswerType,
    QueryCaptionType,
    QueryType,
    VectorizedQuery,
)
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    HnswParameters,
    SearchField,
    SearchableField,
    SearchFieldDataType,
    SearchIndex,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
    SimpleField,
    VectorSearch,
    VectorSearchAlgorithmKind,
    VectorSearchAlgorithmMetric,
    VectorSearchProfile,
)


endpoint: str =  os.getenv("AZURE_OPENAI_ENDPOINT")
api_key: str = os.getenv("AZURE_OPENAI_API_KEY")
api_version: str = os.getenv("AZURE_OPENAI_API_VERSION")


# Use API key authentication
client = AzureOpenAI(
    api_key=api_key,
    api_version=api_version,
    azure_endpoint=endpoint,
)
print("khuong")


SEARCH_SERVICE_ENDPOIBT = os.getenv("SEARCH_SERVICE_ENDPOIBT")
SEARCH_SERVICE_API_KEY = os.getenv("SEARCH_SERVICE_API_KEY")

# Configuration
search_service_endpoint: str = SEARCH_SERVICE_ENDPOIBT
search_service_api_key: str = SEARCH_SERVICE_API_KEY
index_name: str = "azure-ai-search-openai-cookbook-demo"

# Set this flag to True if you are using Azure Active Directory
use_aad_for_search = True  


# Use API key authentication
credential = AzureKeyCredential(search_service_api_key)

# Initialize the SearchClient with the selected authentication method
search_client = SearchClient(
    endpoint=search_service_endpoint, index_name=index_name, credential=credential
)

# Initialize the SearchIndexClient
index_client = SearchIndexClient(
    endpoint=search_service_endpoint, credential=credential
)

# Define the fields for the index
fields = [
    SimpleField(name="id", type=SearchFieldDataType.String),
    SimpleField(name="vector_id", type=SearchFieldDataType.String, key=True),
    SimpleField(name="url", type=SearchFieldDataType.String),
    SearchableField(name="title", type=SearchFieldDataType.String),
    SearchableField(name="text", type=SearchFieldDataType.String),
    SearchField(
        name="title_vector",
        type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
        vector_search_dimensions=1536,
        vector_search_profile_name="adas-llm-vector-config",
    ),
    SearchField(
        name="content_vector",
        type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
        vector_search_dimensions=1536,
        vector_search_profile_name="adas-llm-vector-config",
    ),
]

# Configure the vector search configuration
vector_search = VectorSearch(
    algorithms=[
        HnswAlgorithmConfiguration(
            name="adas-llm-hnsw",
            kind=VectorSearchAlgorithmKind.HNSW,
            parameters=HnswParameters(
                m=4,
                ef_construction=400,
                ef_search=500,
                metric=VectorSearchAlgorithmMetric.COSINE,
            ),
        )
    ],
    profiles=[
        VectorSearchProfile(
            name="adas-llm-vector-config",
            algorithm_configuration_name="adas-llm-hnsw",
        )
    ],
)

# Configure the semantic search configuration
semantic_search = SemanticSearch(
    configurations=[
        SemanticConfiguration(
            name="adas-llm-semantic-config",
            prioritized_fields=SemanticPrioritizedFields(
                title_field=SemanticField(field_name="title"),
                keywords_fields=[SemanticField(field_name="url")],
                content_fields=[SemanticField(field_name="text")],
            ),
        )
    ]
)

# Create the search index with the vector search and semantic search configurations
index = SearchIndex(
    name=index_name,
    fields=fields,
    vector_search=vector_search,
    semantic_search=semantic_search,
)

# Create or update the index
result = index_client.create_or_update_index(index)
print(f"{result.name} created")