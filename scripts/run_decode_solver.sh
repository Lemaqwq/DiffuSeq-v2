CUDA_VISIBLE_DEVICES=2 python -u run_decode_solver.py \
--model_dir diffusion_models/diffuseq_AQuA_h128_lr0.0001_t2000_sqrt_lossaware_seed102_AQuA20231029-14:58:15 \
--seed 110 \
--bsz 100 \
--step 100 \
--split debug
