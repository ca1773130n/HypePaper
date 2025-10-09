#!/bin/bash

MODEL_PATH=$1
PORT=$2
python -m llama_cpp.server --model $MODEL_PATH --host 0.0.0.0 --port $PORT --n_gpu_layers 256 --n_ctx 163840

