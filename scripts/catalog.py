"""Maps things found on GitHub (languages, topics, dependencies) to tech-stack badges.
To teach the profile a new technology, add one line here."""
from urllib.parse import quote

# label, simple-icons slug ("" = no logo), category, aliases (lowercase)
CATALOG = [
    ("Python", "python", "Languages", ["python"]),
    ("TypeScript", "typescript", "Languages", ["typescript"]),
    ("JavaScript", "javascript", "Languages", ["javascript"]),
    ("HTML", "html5", "Languages", ["html"]),
    ("CSS", "css3", "Languages", ["css", "scss"]),
    ("Java", "openjdk", "Languages", ["java"]),
    ("C", "c", "Languages", ["c"]),
    ("C++", "cplusplus", "Languages", ["c++", "cpp"]),
    ("C#", "csharp", "Languages", ["c#", "csharp"]),
    ("Go", "go", "Languages", ["go"]),
    ("Rust", "rust", "Languages", ["rust"]),
    ("Kotlin", "kotlin", "Languages", ["kotlin"]),
    ("Swift", "swift", "Languages", ["swift"]),
    ("PHP", "php", "Languages", ["php"]),
    ("Ruby", "ruby", "Languages", ["ruby"]),
    ("Dart", "dart", "Languages", ["dart"]),
    ("R", "r", "Languages", ["r"]),
    ("Shell", "gnubash", "Languages", ["shell", "bash"]),

    ("Pandas", "pandas", "Data & AI", ["pandas"]),
    ("NumPy", "numpy", "Data & AI", ["numpy"]),
    ("SciPy", "scipy", "Data & AI", ["scipy"]),
    ("scikit-learn", "scikitlearn", "Data & AI", ["scikit-learn", "sklearn"]),
    ("Matplotlib", "", "Data & AI", ["matplotlib"]),
    ("Plotly", "plotly", "Data & AI", ["plotly"]),
    ("TensorFlow", "tensorflow", "Data & AI", ["tensorflow"]),
    ("PyTorch", "pytorch", "Data & AI", ["torch", "pytorch"]),
    ("Keras", "keras", "Data & AI", ["keras"]),
    ("OpenCV", "opencv", "Data & AI", ["opencv", "opencv-python", "opencv-python-headless", "cv2"]),
    ("MediaPipe", "", "Data & AI", ["mediapipe"]),
    ("Jupyter", "jupyter", "Data & AI", ["jupyter", "jupyter notebook", "jupyterlab", "notebook"]),
    ("Hugging Face", "huggingface", "Data & AI", ["huggingface", "transformers", "huggingface-hub", "huggingface_hub", "hugging face"]),
    ("LangChain", "langchain", "Data & AI", ["langchain"]),
    ("OpenAI", "openai", "Data & AI", ["openai"]),
    ("Gemini", "googlegemini", "Data & AI", ["gemini", "google-generativeai", "google-genai"]),
    ("FastF1", "formula1", "Data & AI", ["fastf1"]),

    ("Streamlit", "streamlit", "Web & backend", ["streamlit"]),
    ("Gradio", "gradio", "Web & backend", ["gradio"]),
    ("FastAPI", "fastapi", "Web & backend", ["fastapi"]),
    ("Flask", "flask", "Web & backend", ["flask"]),
    ("Django", "django", "Web & backend", ["django"]),
    ("React", "react", "Web & backend", ["react"]),
    ("Next.js", "nextdotjs", "Web & backend", ["next", "nextjs", "next.js"]),
    ("Vue", "vuedotjs", "Web & backend", ["vue"]),
    ("Tailwind CSS", "tailwindcss", "Web & backend", ["tailwindcss", "tailwind css"]),
    ("Vite", "vite", "Web & backend", ["vite"]),
    ("Node.js", "nodedotjs", "Web & backend", ["node", "nodejs", "node.js"]),
    ("Express", "express", "Web & backend", ["express"]),
    ("Tauri", "tauri", "Web & backend", ["tauri", "@tauri-apps/api", "@tauri-apps/cli"]),
    ("Electron", "electron", "Web & backend", ["electron"]),
    ("SQLite", "sqlite", "Web & backend", ["sqlite"]),
    ("PostgreSQL", "postgresql", "Web & backend", ["postgresql", "postgres", "psycopg2", "asyncpg"]),
    ("MongoDB", "mongodb", "Web & backend", ["mongodb", "pymongo"]),
    ("Redis", "redis", "Web & backend", ["redis"]),
    ("Supabase", "supabase", "Web & backend", ["supabase"]),
    ("Firebase", "firebase", "Web & backend", ["firebase"]),

    ("Docker", "docker", "Tools & infra", ["docker", "dockerfile"]),
    ("Git", "git", "Tools & infra", ["git"]),
    ("GitHub Actions", "githubactions", "Tools & infra", ["github-actions", "github actions"]),
    ("Cloudflare", "cloudflare", "Tools & infra", ["cloudflare"]),
    ("Vercel", "vercel", "Tools & infra", ["vercel"]),
    ("Linux", "linux", "Tools & infra", ["linux"]),
    ("PyCharm", "pycharm", "Tools & infra", ["pycharm"]),
]
CATEGORIES = ["Languages", "Data & AI", "Web & backend", "Tools & infra"]

_BY_ALIAS = {}
for _e in CATALOG:
    _BY_ALIAS[_e[0].lower()] = _e
    for _a in _e[3]:
        _BY_ALIAS.setdefault(_a, _e)


def find(name):
    """Look up a technology by any known name. Returns (label, slug, category) or None."""
    e = _BY_ALIAS.get(str(name).strip().lower())
    return (e[0], e[1], e[2]) if e else None


def badge_url(label, slug):
    lab = quote(label.replace("-", "--").replace("_", "__").replace(" ", "_"), safe="_-.")
    logo = f"&amp;logo={slug}&amp;logoColor=E10600" if slug else ""
    return f"https://img.shields.io/badge/{lab}-1B1D21?style=for-the-badge{logo}"
