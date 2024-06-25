# -*- coding: utf-8 -*-


import sys
import argparse
from .lats.lats_main import lats_main
      
def make_args(instruction, tree_depth, tree_width, iterations,model='gpt-4-1106-preview'):
    parser = argparse.ArgumentParser()

    parser.add_argument("--strategy", default="mcts", help="Strategy to use")
    parser.add_argument("--language", default="py", help="Programming language")
    parser.add_argument("--model", default=model, help="Model type")
    parser.add_argument("--max_iters", default=iterations, help="Maximum iterations")
    parser.add_argument("--instruction", default=instruction, help="Instruction text")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--is_leetcode", action='store_true',
                        help="To run the leetcode benchmark")  # Temporary
    parser.add_argument("--n_samples", type=int,
                        help="The number of nodes added during expansion", default=tree_width)
    parser.add_argument("--depth", type=int,
                        help="Tree depth", default=tree_depth)
    args = parser.parse_args()
    return args

def use_lats(text,tree_depth=2, tree_width=2, iterations=1,model='gpt-4-1106-preview'):
    args = make_args(text, tree_depth, tree_width, iterations,model)  
    response = lats_main(args)
    return response
