#!/bin/bash
pip install python-dotenv
pip install streamlit
pip install streamlit-ace
pip install OpenAI

python -m streamlit run app.py --server.port 8000 --server.address 0.0.0.0