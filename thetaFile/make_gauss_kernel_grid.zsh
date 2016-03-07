#!/usr/bin/zsh

for p in {1..5}; do
  for l in {2..3}; do
    echo ${p}.0 ${l}.0 > gaussKernel-p-${p}-l-${l}
    cat gaussKernel-p-${p}-l-${l}
  done
done
