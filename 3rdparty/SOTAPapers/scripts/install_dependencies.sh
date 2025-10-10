#!/bin/bash
sudo apt update
sudo apt install -y python3 python3-pip build-essential libcurl4-openssl-dev gcc-11 g++-11

sudo update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-11 100 --slave /usr/bin/g++ g++ /usr/bin/g++-11

echo "export CC=/usr/bin/gcc-11" >> ~/.bashrc
echo "export CXX=/usr/bin/g++-11" >> ~/.bashrc

wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install -y ./google-chrome-stable_current_amd64.deb

rm google-chrome-stable_current_amd64.deb

curl -sSL https://rvm.io/pkuczynski.asc | gpg --import -
curl -sSL https://get.rvm.io | bash -s stable

echo "source ~/.rvm/scripts/rvm" >> ~/.bashrc
source ~/.rvm/scripts/rvm

pip install uv uvicorn anyio starlette sse_starlette fastapi starlette_context

rvm install 2.7.8
rvm use 2.7.8
gem install anystyle-cli

unset CONDA_BUILD_SYSROOT  # Disable Conda's sysroot
export PATH=/usr/local/cuda/bin:$PATH
export LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:/usr/local/cuda/lib64:$LD_LIBRARY_PATH
export LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:/usr/local/cuda/lib64:$LIBRARY_PATH
export CC=/usr/bin/gcc
export CXX=/usr/bin/g++
sudo apt install -y libcuda1 libc6-dev librt-dev libgomp1 libomp-dev pymupdf-tools

echo "export PATH=/usr/local/cuda/bin:$PATH" >> ~/.bashrc
echo "export LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:/usr/local/cuda/lib64:$LD_LIBRARY_PATH" >> ~/.bashrc
echo "export LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:/usr/local/cuda/lib64:$LIBRARY_PATH" >> ~/.bashrc

CMAKE_ARGS="-DGGML_CUDA=ON" FORCE_CMAKE=1 pip install --force-reinstall --no-cache-dir --verbose llama-cpp-python
