python -u run_decode_solver.py \
--model_dir diffusion_models/diffuseq_4or5_by_4or5_mult_h128_lr0.0001_t2000_sqrt_lossaware_seed102_4or5_by_4or5_mult20231201-08:11:09 \
--step 10 \
--split test && \
python -u run_decode_solver.py \
--model_dir diffusion_models/diffuseq_4or5_by_4or5_mult_h128_lr0.0001_t2000_sqrt_lossaware_seed102_4or5_by_4or5_mult20231201-08:11:09 \
--step 100 \
--split test
