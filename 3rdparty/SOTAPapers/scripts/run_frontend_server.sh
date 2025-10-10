#!/bin/bash
PORT=$1
streamlit run sotapapers/app/streamlit_app.py --server.port $PORT
