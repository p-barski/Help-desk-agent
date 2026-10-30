### Setup

##### Install python dependencies
```
pip install -r requirements.txt
```

##### Setup environment variables (local model example)
```
MODEL=qwen3.5
LLM_PROVIDER=ollama
```

##### Setup environment variables (remote model example)
```
MODEL=qwen/qwen3.8-27b
LLM_PROVIDER=openai
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_API_KEY=key
```

##### Ollama setup for local model
Install ollama from https://ollama.com/download/ or appropiate distro package
Start ollama
```
ollama serve
```

Download model
```
ollama pull qwen3.5
```

##### Run tests
```
./run_tests.sh
or on windows:
./run_tests.ps1
```

##### Run the agent
```
python main.py
```

### Which model and provider you chose, and why
Ollama with qwen3.5 and groq with qwen/qwen3.8-27b. First thing that came up and was free.

### How your agent works: the loop, the tools and the instructions you give the model
Main chooses whether to use local or remote model based on env variables, takes input from the user and passes it to the agent. Agent loop provides model with prompts, calls tools if model asks for it and provides results from tools back to the model until model return final answer. get_booking takes id and returns dict with "found" boolean, all of the fields from booking.json if booking was found or just error message if not. search_policies takes "cancellations", "prices", "faq" as argument and returns whole markdown. calculate_refund takes id, calls get_booking, and if booking was found then calculates refund based on rules specified in cancellations.md and returns refund amount as string.

###  Your evaluation results: what failed, why you think it failed, and what you tried to fix
Even though model recognizes that the question isn't about the bike rental, it will still provide an answer in some roundabout way. It also has issues getting information from policies, sometimes not even using search_policies. I tried changing tool description and system prompt.

###  How you used AI coding assistants (for example GitHub Copilot, Claude or ChatGPT) while building this, including at least one example where their output was wrong or needed changes, and how you noticed
Mostly asking Claude and GPT about code snippets. Most issues I had were not coding related but with setting up ollama (different package with cuda support, changing where ollama downloads models, running ollama as systemd service having issues with downloading models to NTFS).

###  The limitations of your solution
It's not great with search_policies tool, so any question regarding that can sometimes result in "can't access that info". There is no memory of previous user prompts. Full exceptions are printed to the user. And probably more.

###  What you would do next with more time
Testing different models, different system prompts and tools descriptions.
