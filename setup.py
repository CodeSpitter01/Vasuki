from setuptools import setup

setup(
    name="vasuki-osint",
    version="1.0.0",
    author="Preet Kapoor",
    description="Terminal OSINT tool with deep dorking and username matching",
    py_modules=["vasuki"],  # because your script is vasuki.py
    install_requires=[
        "requests>=2.25.0",
        "urllib3>=1.26.0",
        "rich>=10.0.0",
        "duckduckgo-search>=3.0.0",
        "ddgs>=9.14.0",
    ],
    entry_points={
        "console_scripts": [
            "vasuki = vasuki:main",  # <-- this creates the 'vasuki' command
        ],
    },
    python_requires=">=3.6",
)
