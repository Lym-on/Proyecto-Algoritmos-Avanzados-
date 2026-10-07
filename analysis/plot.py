#!/usr/bin/env python3
"""
Visualization scripts for experiment results.

Generates plots from CSV/JSON experiment results.
"""
import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Optional

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 12


def load_results(csv_path: str) -> pd.DataFrame:
    """Load experiment results from CSV."""
    df = pd.read_csv(csv_path)
    return df


def plot_cost_vs_n(df: pd.DataFrame, output_dir: str):
    """Plot total cost vs n (blockchain size) for each algorithm."""
    # Average over seeds for each n, workload, algorithm
    agg = df.groupby(['n_blocks', 'workload', 'algorithm'])['cost_total'].mean().reset_index()
    
    g = sns.relplot(data=agg, x='n_blocks', y='cost_total', hue='algorithm', 
                    col='workload', kind='line', marker='o', facet_kws={'sharey': False})
    g.set_titles("{col_name}")
    g.set_axis_labels("Blockchain size (blocks)", "Total cost (comparisons + λ·rotations)")
    g.fig.suptitle("Cost vs Blockchain Size by Workload", y=1.02)
    plt.tight_layout()
    plt.savefig(Path(output_dir) / "cost_vs_n.png", dpi=150, bbox_inches='tight')
    plt.close()


def plot_comparisons_per_query(df: pd.DataFrame, output_dir: str):
    """Plot comparisons per query vs workload."""
    agg = df.groupby(['workload', 'algorithm'])['comparisons_avg'].mean().reset_index()
    
    plt.figure(figsize=(12, 6))
    sns.barplot(data=agg, x='workload', y='comparisons_avg', hue='algorithm')
    plt.title("Average Comparisons per Query by Workload")
    plt.xlabel("Workload")
    plt.ylabel("Comparisons per Query")
    plt.xticks(rotation=45, ha='right')
    plt.legend(title="Algorithm")
    plt.tight_layout()
    plt.savefig(Path(output_dir) / "comparisons_vs_workload.png", dpi=150, bbox_inches='tight')
    plt.close()


def plot_height_vs_algorithm(df: pd.DataFrame, output_dir: str):
    """Plot tree height by algorithm and workload."""
    agg = df.groupby(['workload', 'algorithm'])['height'].mean().reset_index()
    
    plt.figure(figsize=(12, 6))
    sns.barplot(data=agg, x='workload', y='height', hue='algorithm')
    plt.title("Tree Height by Workload and Algorithm")
    plt.xlabel("Workload")
    plt.ylabel("Tree Height")
    plt.xticks(rotation=45, ha='right')
    plt.legend(title="Algorithm")
    plt.tight_layout()
    plt.savefig(Path(output_dir) / "height_vs_workload.png", dpi=150, bbox_inches='tight')
    plt.close()


def plot_depth_metrics(df: pd.DataFrame, output_dir: str):
    """Plot average depth, p95, p99 by algorithm."""
    metrics = ['avg_depth', 'p95_depth', 'p99_depth']
    agg = df.groupby(['workload', 'algorithm'])[metrics].mean().reset_index()
    agg_melt = agg.melt(id_vars=['workload', 'algorithm'], value_vars=metrics,
                        var_name='metric', value_name='depth')
    
    g = sns.catplot(data=agg_melt, x='workload', y='depth', hue='algorithm',
                    col='metric', kind='bar', sharey=False)
    g.set_axis_labels("Workload", "Depth")
    g.set_titles("{col_name}")
    g.fig.suptitle("Depth Metrics by Workload", y=1.02)
    plt.tight_layout()
    plt.savefig(Path(output_dir) / "depth_metrics.png", dpi=150, bbox_inches='tight')
    plt.close()


def plot_splay_rotations(df: pd.DataFrame, output_dir: str):
    """Plot Splay rotations per access by workload."""
    splay_df = df[df['algorithm'] == 'SplayTree'].copy()
    if splay_df.empty:
        return
    
    agg = splay_df.groupby('workload')['rotations_per_access'].mean().reset_index()
    
    plt.figure(figsize=(10, 5))
    sns.barplot(data=agg, x='workload', y='rotations_per_access')
    plt.title("Splay Tree Rotations per Access by Workload")
    plt.xlabel("Workload")
    plt.ylabel("Rotations per Access")
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(Path(output_dir) / "splay_rotations.png", dpi=150, bbox_inches='tight')
    plt.close()


def plot_normalized_cost(df: pd.DataFrame, output_dir: str):
    """Plot normalized cost (vs OptimalBST) by workload and algorithm."""
    # Exclude OptimalBST itself
    df_plot = df[df['algorithm'] != 'OptimalBST'].copy()
    agg = df_plot.groupby(['workload', 'algorithm'])['normalized_cost'].mean().reset_index()
    
    plt.figure(figsize=(12, 6))
    sns.barplot(data=agg, x='workload', y='normalized_cost', hue='algorithm')
    plt.axhline(y=1.0, color='red', linestyle='--', label='Optimal (ratio=1)')
    plt.title("Normalized Cost vs Optimal BST by Workload")
    plt.xlabel("Workload")
    plt.ylabel("Cost Ratio (algorithm / optimal)")
    plt.xticks(rotation=45, ha='right')
    plt.legend(title="Algorithm")
    plt.tight_layout()
    plt.savefig(Path(output_dir) / "normalized_cost.png", dpi=150, bbox_inches='tight')
    plt.close()


def plot_lambda_effect(df: pd.DataFrame, output_dir: str):
    """Plot effect of lambda on total cost for Splay vs others."""
    # Focus on algorithms with rotations/rehashes
    algos = ['SplayTree', 'AVL', 'BST', 'BaselineTree']
    df_plot = df[df['algorithm'].isin(algos)].copy()
    
    # For each workload, show cost vs lambda
    workloads = df_plot['workload'].unique()
    for workload in workloads:
        wdf = df_plot[df_plot['workload'] == workload]
        agg = wdf.groupby(['lambda', 'algorithm'])['cost_total'].mean().reset_index()
        
        plt.figure(figsize=(10, 5))
        sns.lineplot(data=agg, x='lambda', y='cost_total', hue='algorithm', marker='o')
        plt.title(f"Total Cost vs λ (Workload: {workload})")
        plt.xlabel("λ (reorganization cost weight)")
        plt.ylabel("Total Cost")
        plt.xscale('log')
        plt.tight_layout()
        plt.savefig(Path(output_dir) / f"lambda_effect_{workload}.png", dpi=150, bbox_inches='tight')
        plt.close()


def plot_splay_amortized(df: pd.DataFrame, output_dir: str):
    """Plot Splay amortized behavior: cumulative cost vs query number (single run)."""
    # This would need per-query data; we only have aggregate.
    # Skip for now - would need instrumented run.
    pass


def generate_all_plots(csv_path: str, output_dir: str):
    """Generate all plots from results CSV."""
    print(f"Loading results from {csv_path}")
    df = load_results(csv_path)
    print(f"Loaded {len(df)} rows, columns: {list(df.columns)}")
    
    os.makedirs(output_dir, exist_ok=True)
    
    print("Generating cost_vs_n.png...")
    plot_cost_vs_n(df, output_dir)
    
    print("Generating comparisons_vs_workload.png...")
    plot_comparisons_per_query(df, output_dir)
    
    print("Generating height_vs_workload.png...")
    plot_height_vs_algorithm(df, output_dir)
    
    print("Generating depth_metrics.png...")
    plot_depth_metrics(df, output_dir)
    
    print("Generating splay_rotations.png...")
    plot_splay_rotations(df, output_dir)
    
    print("Generating normalized_cost.png...")
    plot_normalized_cost(df, output_dir)
    
    print("Generating lambda_effect plots...")
    plot_lambda_effect(df, output_dir)
    
    print(f"All plots saved to {output_dir}/")


def main():
    parser = argparse.ArgumentParser(description="Generate plots from experiment results")
    parser.add_argument("csv_file", help="Path to experiment results CSV")
    parser.add_argument("-o", "--output", default="plots", help="Output directory for plots")
    args = parser.parse_args()
    
    generate_all_plots(args.csv_file, args.output)


if __name__ == "__main__":
    main()