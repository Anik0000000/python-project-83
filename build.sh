#!/usr/bin/env bash  

# Установка uv  
curl -LsSf https://astral.sh/uv/install.sh | sh  
source $HOME/.cargo/env  

# Установка зависимостей  
make install  