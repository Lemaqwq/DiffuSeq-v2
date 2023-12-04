python -m torch.distributed.launch --nproc_per_node=4 --master_port=12231 --use_env run_train.py \
--diff_steps 2000 \
--lr 0.0001 \
--learning_steps 60000 \
--save_interval 5000 \
--seed 102 \
--noise_schedule sqrt \
--hidden_dim 128 \
--bsz 128 \
--microbatch 128 \
--dataset 4or5_by_4or5_mult \
--data_dir datasets/4or5_by_4or5_mult \
--learned_mean_embed True \
--denoise True \
--vocab bert \
--seq_len 128 \
--use_fp16 \
--denoise_rate 0.5 \
--schedule_sampler lossaware \
--notes 4or5_by_4or5_mult
