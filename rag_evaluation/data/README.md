Place your GDPR text files here.

Expected format:
- One .txt or .md file per article or section
- Plain text, UTF-8 encoded
- Example filenames: article_01.txt, article_17_right_to_erasure.txt, gdpr_full.txt

The ingestion pipeline will automatically:
1. Read all .txt and .md files from this directory
2. Chunk them into overlapping segments
3. Generate embeddings and store in ChromaDB / LightRAG
