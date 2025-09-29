#!/usr/bin/env bash
export STREAMLIT_SERVER_PORT=$PORT
streamlit run home.py --server.port $PORT --server.address 0.0.0.0