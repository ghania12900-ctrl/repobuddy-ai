# RepoBuddy AI

RepoBuddy AI helps beginners understand GitHub issues so they can
contribute to open-source projects. Paste an issue and the app returns
5 sections:

1. Beginner-friendly explanation
2. Step-by-step implementation
3. Files to inspect
4. Suggested tests
5. Completion checklist

## AI model
Llama 3.2 3B (under 8B parameters), run locally with Ollama.

## Built with
Python, Flask, HTML, CSS and JavaScript.

## How to run
1. Install Python 3.10+ and Ollama
2. Run: ollama pull llama3.2:3b
3. Run: pip install -r requirements.txt
4. Run: python app.py
5. Open http://127.0.0.1:5000

## License
MIT
