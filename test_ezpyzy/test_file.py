
import signal
import shutil
import os
import pathlib as pl
import pickle as pkl

import ezpyzy as ez


shutil.rmtree('test/foo', ignore_errors=True)
os.mkdir('test/foo')
pl.Path('test/foo/bar.txt').write_text('hello world')
pl.Path('test/foo/bat.json').write_text('{"x": 1, "y": 2, "z": 3}')
pl.Path('test/foo/baz.pkl').write_bytes(pkl.dumps({'x', 'y', 'z'}))


def test_text_file():
    file = ez.File('test/foo/bar.txt')
    content = file.load()
    assert content == 'hello world'


def test_json_file():
    file = ez.File('test/foo/bat.json')
    content = file.load()
    assert content == {'x': 1, 'y': 2, 'z': 3}


def test_pickle_file():
    file = ez.File('test/foo/baz.pkl')
    content = file.load()
    assert content == {'x', 'y', 'z'}

def test_path_singleton():
    file_1 = ez.File('test/foo/bar.txt')
    file_2 = ez.File('test/foo/bar.txt')
    assert file_1 is file_2

def test_update_log():
    file = ez.File('test/foo/bar.txt')
    file.log('\nanother day')
    content = file.load()
    assert content == 'hello world\nanother day'

def test_synced():
    file = ez.File('test/foo/bat.json').init()
    assert file.data == {'x': 1, 'y': 2, 'z': 3}
    file.data['w'] = 0
    assert file.autosaving
    file.push()
    assert file.load() == {'x': 1, 'y': 2, 'z': 3, 'w': 0}

def test_autosave():
    file = ez.File('test/foo/bak.json').init({})
    file.data.update(a=1, b=2, c=3)
    assert file.autosaving

def test_data_init():
    file = ez.File('test/foo/cal.json').init({1:'one', 2:'two'})
    uppered = file.data[1].upper()
    file.push()
    assert file.load() == {'1':'one', '2':'two'}

def test_data_push():
    file = ez.File('test/foo/cal.json', [1, 2, 3])
    imaginary = file.data[0].imag
    file.push()
    assert file.load() == [1, 2, 3]





