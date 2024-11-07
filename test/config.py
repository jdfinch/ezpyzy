
from ezpyzy.config_new import Config, default
import ezpyzy as ez
import dataclasses as dc


with ez.test("Define Config"):
    @dc.dataclass
    class Training(Config):
        shuffle: bool = True
        epochs: int = 1
        tags: list[str] = default(['training'])

with ez.test("Construct Config"):
    train_config_a = Training(shuffle=False)
    assert train_config_a.shuffle == False
    assert train_config_a.tags == ['training']
    train_config_b = Training(epochs=2)
    assert train_config_b.epochs == 2
    assert train_config_b.tags == ['training']

with ez.test("Evolve Config", crash=True):
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

with ez.test("Merge Configs"):
    train_config_e = train_config_d * train_config_b
    assert train_config_e.shuffle == False
    assert train_config_e.epochs == 2
    assert train_config_e.tags == ['training', 'new']

with ez.test("Serialize Config"):
    json_e = train_config_e.configured.dict()
    assert '__class__' in json_e and 'Training' in json_e.pop('__class__')
    assert json_e == {'base': None, 'shuffle': False, 'epochs': 2, 'tags': ['training', 'new']}

with ez.test("Deserialize JSON"):
    json_e = ez.JSON.serialize(json_e)
    train_config_f = Training(json_e)
    assert train_config_f == train_config_e and train_config_f is not train_config_e

with ez.test("Deserialize Config"):
    json_e = train_config_e.configured.json()
    train_config_f = Training(json_e)
    assert train_config_f == train_config_e and train_config_f is not train_config_e

with ez.test("Deserialize Config with Override"):
    json_e = train_config_e.configured.json()
    train_config_f = Training(json_e, epochs=4)
    assert train_config_f.shuffle == train_config_e.shuffle
    assert train_config_f.epochs == 4
    assert train_config_f.tags == train_config_e.tags

with ez.test("Define Config with Nested Config"):
    @dc.dataclass
    class Experiment(Config):
        name: str = None
        training: Training = default(Training())
        metrics: list[str] = default(['accuracy'])

with ez.test("Construct Nested Config"):
    exp_config_a = Experiment(name='exp1', training=Training(epochs=5))
    assert exp_config_a.name == 'exp1'
    assert exp_config_a.training.shuffle == True
    assert exp_config_a.training.epochs == 5
    assert exp_config_a.training.tags == ['training']
    assert exp_config_a.metrics == ['accuracy']

with ez.test("Evolve Nested Config"):
    exp_config_b = Experiment(exp_config_a, training=Training(shuffle=False), metrics=['p', 'r', 'f1'])
    assert exp_config_b.name == 'exp1'
    assert exp_config_b.training.shuffle == False
    assert exp_config_b.training.epochs == 5
    assert exp_config_b.training.tags == ['training']
    assert exp_config_b.metrics == ['p', 'r', 'f1']









