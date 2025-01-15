from setuptools import setup, find_packages

setup(
    name="rag-cs",
    version="0.1.0",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "fastapi",
        "uvicorn",
        "torch",
        "transformers",
        "pillow",
        "numpy",
        "neo4j",
        "pytest",
        "requests",
        "python-multipart",
    ],
    python_requires=">=3.9",
) 