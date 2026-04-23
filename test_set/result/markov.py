#! /usr/bin/env python3

import sys
import random
import argparse
import string

class Markov:
    def __init__(self, history_size, choice):
        self.history_size = history_size
        self.choice = choice
        self.transition = {}

    def add(self, state, next_state):
        if state not in self.transition:
            self.transition[state] = [next_state]
        else:
            self.transition[state].append(next_state)

    def put(self, sequence):
        history_size = self.history_size
        add = self.add
        add(None, sequence[:0])
        for i in range(len(sequence)):
            add(sequence[max(0, i-history_size):i], sequence[i:i+1])
        add(sequence[len(sequence)-history_size:], None)

    def get(self):
        choice = self.choice
        transition = self.transition
        history_size = self.history_size
        sequence = choice(transition[None])
        while True:
            sub_sequence = sequence[max(0, len(sequence)-history_size):]
            options = transition[sub_sequence]
            next_state = choice(options)
            if not next_state:
                break
            sequence = sequence + next_state
        return sequence

def parse_args():
    parser = argparse.ArgumentParser(description='Markov chain generator')
    parser.add_argument('-h', '--history-size', type=int, default=2, help='History size')
    parser.add_argument('-c', action='store_true', help='Characters')
    parser.add_argument('-w', action='store_true', help='Words')
    parser.add_argument('-d', action='count', default=1, help='Debug level')
    parser.add_argument('-q', action='count', default=0, help='Quiet level')
    parser.add_argument('files', nargs='*', default=['-'], help='Input files')
    return parser.parse_args()

def process_file(filename, markov, debug):
    try:
        with open(filename, 'r') as file:
            text = file.read()
            paragraphs = text.split('\n\n')
            for paragraph in paragraphs:
                words = paragraph.split()
                if words:
                    if debug > 1:
                        print('Feeding ...')
                    if markov.choice:
                        data = tuple(words)
                    else:
                        data = ' '.join(words)
                    markov.put(data)
    except KeyboardInterrupt:
        print('Interrupted -- continue with data read so far')
    except Exception as e:
        print(f'Error processing file {filename}: {e}')

def main():
    args = parse_args()
    history_size = args.history_size
    choice = random.choice
    markov = Markov(history_size, choice)
    debug = args.d - args.q
    if debug > 1:
        print('Debug level:', debug)
    for filename in args.files:
        if filename == '-':
            file = sys.stdin
            if file.isatty():
                print('Sorry, need stdin from file')
                continue
        else:
            file = filename
        process_file(file, markov, debug)
    if not markov.transition:
        print('No valid input files')
        return
    if debug:
        print('Done.')
    while True:
        sequence = markov.get()
        words = sequence.split() if args.w else sequence
        for word in words:
            print(word, end=' ')
        print()
        print()

if __name__ == '__main__':
    main()