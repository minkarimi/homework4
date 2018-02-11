from collections import deque
import string
import time
import _thread
from multiprocessing import Process, Queue
import math

valid_letters = list(string.ascii_lowercase)


def find_transformations(word):
    transformations = set()
    for x in range(0, len(word)):
        for y in range(0, len(valid_letters)):
            # new_word is a poor name here... it's probably not an actual word
            new_word = list(word)
            if new_word[x] == valid_letters[y]:
                continue
            new_word[x] = valid_letters[y]
            transformations.add("".join(new_word))
    return transformations


def import_file():
    words = set()
    for word in open('word_list.txt', 'r').read().split():
        words.add(word)
    return words


def search_word_set(word_objs, finish, dictionary, already_visited_words, return_value):
    queued_words = set()
    queued_word_objs = list()
    for word_obj in word_objs:
        transformations = find_transformations(word_obj[0])
        for transformation in transformations:
            if transformation == finish:
                path = list(word_obj[1])
                path.append(word_obj[0])
                path.append(transformation)
                return_value.put((True, path))
                return
            if (transformation in dictionary and transformation not in already_visited_words and transformation not in queued_words):
                queued_words.add(transformation)
                path = list(word_obj[1])
                path.append(word_obj[0])
                queued_word_objs.append((transformation, path))
    return_value.put((False, queued_word_objs, queued_words))


def find_path(start, finish, dictionary):
    if start == finish:
        return list([start])
    queued_word_objs = list(([start, list()],))
    queued_words = set(start)
    # make this a global var, or something
    num_processes = 4.0
    return_value = None
    while 1:
        queue_length = len(queued_word_objs)
        if queue_length == 0:
            # return an empty list if we couldn't find a path
            return list()
        process_returns = Queue()
        chunk_size = int(math.ceil(queue_length / num_processes))
        for chunk_start in range(0, queue_length, chunk_size):
            # todo: investigate using pipes so we can keep the processes alive
            # rather than having to create them for each block of work
            p = Process(target=search_word_set,
                        args=(queued_word_objs[chunk_start:chunk_start + chunk_size],
                              finish, dictionary, queued_words, process_returns))
            p.start()

        # clear the work queue
        queued_word_objs = list()

        # process_returns doesn't know how much data it should receive back, so
        # just iterate over the same number of chunks as we assigned work for
        # (may be less than num_processes if there wasn't enough work for all
        # processes)
        for process in range(0, queue_length, chunk_size):
            child_return_value = process_returns.get()
            if child_return_value[0]:
                # done, but we need to empty the queue otherwise the child processes
                # won't exit properly
                return_value = child_return_value[1]
            elif return_value is None:
                queued_word_objs.extend(child_return_value[1])
                queued_words.update(child_return_value[2])

        if return_value is not None:
            return return_value


def timed_find_path(start, finish, dictionary):
    start_time = time.time()
    path = find_path(start, finish, dictionary)
    print('search took', time.time() - start_time, 'seconds')
    return path


def main():
    valid_words = import_file()
    # Consider computing the graph of transformations that exist in the set of
    # valid_words.
    while 1:
        word_one = input('Please enter the first word: ').lower()
        word_two = input('Please enter the second word: ').lower()
        # todo: accept some input to break out of the loop
        path = timed_find_path(word_one, word_two, valid_words)
        if len(path) == 0:
            print('could not find a series of transformations between {} and {}').format(word_one, word_two)
        else:
            print('found a series of transformations:')
            for word in path:
                print(word)


if __name__ == '__main__':
    main()