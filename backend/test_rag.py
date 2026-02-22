import asyncio
from app.services.rag_service import rag_service

async def test():
    print("Testing Keyword Query (BM25 focus): 'Ce este indicele BET-TR?'")
    res1 = await rag_service.query("Ce este indicele BET-TR?", use_reranking=False)
    for i, doc in enumerate(res1[:2]):
        print(f"  Result {i+1} [Source: {doc.metadata.get('source_file')}]: {doc.page_content[:150]}...")
        
    print("\nTesting Legal Query (Parent Chunk focus): 'Care sunt exceptiile de la aplicarea legii 126/2018?'")
    res2 = await rag_service.query("Care sunt exceptiile de la aplicarea legii 126/2018?", use_reranking=True)
    for i, doc in enumerate(res2[:2]):
        print(f"  Result {i+1} [Source: {doc.metadata.get('source_file')}, Len: {len(doc.page_content)}]: {doc.page_content[:150]}...")

asyncio.run(test())
