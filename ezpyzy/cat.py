
import copy as cp


def cat(*sequences):
    assert sequences
    if len(sequences) == 1:
        return cp.copy(sequences[0])
    concatenated = sequences[0] + sequences[1]
    for sequence in sequences[2:]:
        concatenated += sequence
    return concatenated
    


if __name__ == '__main__':

    print(cat([1, 2, 3], [4, 5], [6]))
    print(cat('hello', 'this', 'is', 'a', 'seq'))
    print(cat((1, 2), (3, 4), (5, 6)))
    print(cat(1, 2, 3, 4, 5, 6))
