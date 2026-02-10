
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def test_local_embedding():
    print("Testing local embedding with transformers...")
    try:
        from transformers import AutoTokenizer, AutoModel
        import torch
        print("Imports successful.")
        
        model_name = "prajjwal1/bert-tiny"
        print(f"Loading {model_name}...")
        
        # Run in thread to avoid blocking async loop if it takes time
        with ThreadPoolExecutor() as executor:
            tokenizer = await asyncio.get_event_loop().run_in_executor(
                executor, lambda: AutoTokenizer.from_pretrained(model_name)
            )
            model = await asyncio.get_event_loop().run_in_executor(
                executor, lambda: AutoModel.from_pretrained(model_name)
            )
            
        print("Model loaded.")
        
        text = "This is a test sentence."
        inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True)
        
        with torch.no_grad():
            outputs = model(**inputs)
            
        # Mean pooling
        embeddings = outputs.last_hidden_state.mean(dim=1).squeeze().tolist()
        print(f"Embedding generated: {len(embeddings)} dimensions")
        print("✅ Success")
        
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_local_embedding())
