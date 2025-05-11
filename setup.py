from setuptools import setup, find_packages

setup(
    name="slide_ai",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "python-dotenv",
        "google-generativeai",
        "python-pptx",
        "pillow",
        "requests",
        "uvicorn",
    ],
)
