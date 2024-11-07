
from ezpyzy.config_new import Config
import ezpyzy as ez
import dataclasses as dc


with ez.test("Define Config"):

    @dc.dataclass
    class Training(Config):
        shuffle: bool = True
        epochs: int = 1
        tags: list[str] = ez.default(['training'])

with ez.test("Construct Config"):
    train_config_a = Training(shuffle=False)
    assert train_config_a.shuffle == False
    assert train_config_a.tags == ['training']
    train_config_b = Training(epochs=2)
    assert train_config_b.epochs == 2
    assert train_config_b.tags == ['training']

with ez.test("Evolve Config"):
    train_config_c = Training(train_config_a, tags=['training', 'new'])
    assert train_config_c.shuffle == False
    assert train_config_c.epochs == 1
    assert train_config_c.tags == ['training', 'new']

with ez.test("Evolve Mutated Config"):
    train_config_a.epochs = 3
    train_config_d = Training(train_config_a, tags=['training', 'new'])
    assert train_config_d.shuffle == False
    assert train_config_d.epochs == 3
    assert train_config_d.tags == ['training', 'new']

with ez.test("Merge Configs", crash=True):
    train_config_e = train_config_d * train_config_b
    assert train_config_e.shuffle == False
    assert train_config_e.epochs == 2
    assert train_config_e.tags == ['training', 'new']



