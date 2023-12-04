import jsonlines
import statistics
import matplotlib.pyplot as plt

def summarize_len_z(jsonl_file):
    max_len_z = float('-inf')
    min_len_z = float('inf')
    len_z_values = []

    with jsonlines.open(jsonl_file) as reader:
        for entry in reader:
            len_z = entry.get('len_z')
            if len_z is not None:
                max_len_z = max(max_len_z, len_z)
                min_len_z = min(min_len_z, len_z)
                len_z_values.append(len_z)

    median_len_z = statistics.median(len_z_values)
    mean_len_z = statistics.mean(len_z_values)

    return {
        'max_len_z': max_len_z,
        'min_len_z': min_len_z,
        'median_len_z': median_len_z,
        'mean_len_z': mean_len_z,
        'len_z_values': len_z_values
    }

# Usage example
summary = summarize_len_z('stat_train_data5_by_5_mult.jsonl')

print('Max len_z:', summary['max_len_z'])
print('Min len_z:', summary['min_len_z'])
print('Median len_z:', summary['median_len_z'])
print('Mean len_z:', summary['mean_len_z'])

# Plotting the distribution
plt.hist(summary['len_z_values'], bins='auto', alpha=0.7, rwidth=0.85)
plt.xlabel('len_z')
plt.ylabel('Frequency')
plt.title('Distribution of len_z')
plt.grid(True)
plt.savefig('len_z_distribution.png')