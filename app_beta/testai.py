from pandasai.llm import Ollama
from pandasai import SmartDataframe
import pandas as pd

# 🧪 Sample Data
df = pd.DataFrame({
    "name": ["Alice", "Bob", "Charlie"],
    "sales": [100, 150, 200]
})

# 🤖 Connect to local Ollama (uses dolphin-mistral model)
llm = Ollama(model="dolphin-mistral")
sdf = SmartDataframe(df, config={"llm": llm})

# 🧠 Ask a question
response = sdf.chat("Who sold the most?")
print(response)
