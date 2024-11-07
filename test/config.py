
from ezpyzy.config import Config, default
import ezpyzy as ez
import dataclasses as dc
import textwrap as tw


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
    assert json_e == {'shuffle': False, 'epochs': 2, 'tags': ['training', 'new']}

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

with ez.test("Serialize All"):
    serial_all = exp_config_a.configured.json()

with ez.test("Serialize Configured Only, No Subconfigs"):
    serial_configured = exp_config_a.configured.configured.json()
    assert serial_configured == tw.dedent('''
    {
      "name": "exp1"
    }
    ''').strip()

with ez.test("Serialize Configured Only With Subconfigs"):
    serial_configured_and_subconfigs = exp_config_a.configured.and_subconfigs.json()
    assert serial_configured_and_subconfigs == tw.dedent('''
    {
      "name": "exp1",
      "training": {
        "epochs": 5
      }
    }
    ''').strip()

with ez.test("Serialize Configured and Unconfigured, No Subconfigs"):
    serial_no_subconfigs = exp_config_a.configured.and_unconfigured.json()
    assert serial_no_subconfigs == tw.dedent('''
    {
      "name": "exp1",
      "metrics": [
        "accuracy"
      ]
    }
    ''').strip()

with ez.test("Load Configured Only, No Subconfigs"):
    exp_config_c = Experiment(serial_configured,
        training=Training(shuffle=False), metrics=['p', 'r', 'f1'])
    assert exp_config_c.name == 'exp1'
    assert exp_config_c.training.shuffle == False
    assert exp_config_c.training.epochs == 1
    assert exp_config_c.training.tags == ['training']
    assert exp_config_c.metrics == ['p', 'r', 'f1']

with ez.test("Load Configured Only With Subconfigs"):
    exp_config_d = Experiment(serial_configured_and_subconfigs,
        training=Training(shuffle=False), metrics=['p', 'r', 'f1'])
    assert exp_config_d.name == 'exp1'
    assert exp_config_d.training.shuffle == False
    assert exp_config_d.training.epochs == 5
    assert exp_config_d.training.tags == ['training']
    assert exp_config_d.metrics == ['p', 'r', 'f1']

with ez.test("Merge Nested Configs"):
    exp_config_e = Experiment(
        name='exp_e', training=Training(shuffle=False, epochs=6))
    exp_config_f = Experiment(
        name='exp_f', training=Training(shuffle=True, tags=['f']), metrics=['f1'])
    exp_config_g = exp_config_e * exp_config_f
    assert exp_config_g == Experiment(
        name='exp_f', training=Training(shuffle=True, epochs=6, tags=['f']), metrics=['f1'])
    exp_config_h = exp_config_f * exp_config_e
    assert exp_config_h == Experiment(
        name='exp_e', training=Training(shuffle=False, epochs=6, tags=['f']), metrics=['f1'])

with ez.test("Merge Nested Configs, No Override"):
    exp_config_i = exp_config_e + exp_config_f
    assert exp_config_i == Experiment(
        name='exp_e', training=Training(shuffle=False, epochs=6, tags=['f']), metrics=['f1'])
    exp_config_j = exp_config_f + exp_config_e
    assert exp_config_j == Experiment(
        name='exp_f', training=Training(shuffle=True, epochs=6, tags=['f']), metrics=['f1'])

with ez.test("Inherit Config with Overrides"):
    @dc.dataclass
    class MyTraining(Training):
        epochs: int = 20
    my_training = MyTraining()
    assert my_training.shuffle == True
    assert my_training.epochs == 20
    assert my_training.tags == ['training']

with ez.test("Inherit and Extend Config with Overrides"):
    @dc.dataclass
    class MyExtendedTraining(Training):
        epochs: int = 30
        extension: str = 'extension!'
    my_extended_training = MyExtendedTraining()
    assert my_extended_training.shuffle == True
    assert my_extended_training.epochs == 30
    assert my_extended_training.tags == ['training']
    assert my_extended_training.extension == 'extension!'

with ez.test("Inherit Nested Config with Overrides"):
    @dc.dataclass
    class MyExperiment(Experiment):
        name: str = 'my_exp'
        training: Training = default(Training(epochs=10))
    my_exp = MyExperiment()
    assert my_exp.name == 'my_exp'
    assert my_exp.training.shuffle == True
    assert my_exp.training.epochs == 10
    assert my_exp.training.tags == ['training']
    assert my_exp.metrics == ['accuracy']

with ez.test("Inherit and Extend Nested Config with Overrides"):
    @dc.dataclass
    class MyExtendedExperiment(Experiment):
        name: str = 'my_exp'
        training: Training = default(Training(epochs=10))
        extension: str = 'extension!'
    my_exp = MyExtendedExperiment()
    assert my_exp.name == 'my_exp'
    assert my_exp.training.shuffle == True
    assert my_exp.training.epochs == 10
    assert my_exp.training.tags == ['training']
    assert my_exp.metrics == ['accuracy']
    assert my_exp.extension == 'extension!'













