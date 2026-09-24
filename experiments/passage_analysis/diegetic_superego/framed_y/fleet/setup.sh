#!/bin/bash
# Runs ON a fresh RunPod pod (runpod/pytorch image). Installs vLLM and the repo.
set -e
export PIP_BREAK_SYSTEM_PACKAGES=1 PIP_ROOT_USER_ACTION=ignore
cd /root
[ -d malignment ] || git clone --depth 1 https://github.com/quadrismegistus/malignment.git
pip install -q "vllm==0.22.1" hf_transfer 2>&1 | tail -2
cd malignment && pip install -q -e . 2>&1 | tail -1
#: vllm 0.22.1 accepts transformers>=4.56 but its xgrammar needs <5, and the
#: unpinned `-e .` pulls 5.17. 4.57.1 is also the runbook's floor for OLMo 3
#: and Zamba2 (docs/cloud_runbook.md section 3).
pip install -q "transformers==4.57.1" 2>&1 | tail -1
python3 -c "import vllm, torch, transformers; print('vllm', vllm.__version__, 'torch', torch.__version__, 'tf', transformers.__version__, 'cuda', torch.cuda.is_available())"
