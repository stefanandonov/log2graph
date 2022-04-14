import datetime
import json
import logging
import os
import threading

from flask import Flask, request, jsonify
from flask import current_app
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from log_datasets.datasets import NovaDataset, HDFSDataset, BGLDataset

from pyvis.network import Network
from utils.graphs_util import create_networkx_graph, nx2pyvis

app = Flask(__name__)

# necessary datasets from logs2graph library
nova_dataset = NovaDataset(data_folder_path="./data")
nova_dataset.initialize_dataset()
app.datasets = {
    'NOVA': nova_dataset
}

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db.sqlite') + '?check_same_thread=False'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Initialize the DB
db = SQLAlchemy(app)
# Initialize ma
ma = Marshmallow(app)


# model class
class Experiment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    dataset = db.Column(db.String(20))
    window_type = db.Column(db.String(20))
    size = db.Column(db.Integer, nullable=True)
    slide = db.Column(db.Integer, nullable=True)
    include_last_event = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now())
    last_modified_at = db.Column(db.DateTime, default=datetime.datetime.now())
    status = db.Column(db.String, default='CREATED')
    test_id = db.Column(db.Integer, nullable=True)

    def __init__(self, name, dataset, window_type, size, slide, test_id, include_last_event):
        self.name = name
        self.dataset = dataset
        self.window_type = window_type
        self.size = size
        self.slide = slide
        self.include_last_event = include_last_event
        self.test_id = test_id
        self.created_at = datetime.datetime.now()
        self.last_modified_at = datetime.datetime.now()


class ExperimentSchema(ma.Schema):
    class Meta:
        fields = (
            'id', 'name', 'dataset', 'window_type', 'size', 'slide', 'include_last_event', 'test_id', 'created_at',
            'last_modified_at', 'status'
        )


experiment_schema = ExperimentSchema()
experiments_schema = ExperimentSchema(many=True)

def run_experiment(experiment: Experiment):
    with app.app_context():
        # print (app.datasets)
        # print (current_app.datasets)
        logging.info("Thread for experiment ID %d for dataset %s: starting", experiment.id, experiment.dataset)
        result = current_app.datasets.get(experiment.dataset.upper()).create_graphs(window_type=experiment.window_type,
                                                                                    window_size=experiment.size,
                                                                                    window_slide=experiment.slide,
                                                                                    test_id=experiment.test_id,
                                                                                    include_last=experiment.include_last_event)

        logging.info("Thread for experiment for dataset %s: is done. Starting to save results!", experiment.dataset)

        experiment_id = experiment.id
        os.mkdir(f'./experiments/{experiment_id}')

        main_results_file = open(f'./experiments/{experiment_id}/results.json', 'w')
        json.dump(result, main_results_file)
        main_results_file.close()

        for item in result:
            start = item.get('start', None)
            end = item.get('end', None)
            session_id = item.get('session_id', None)
            graph_dict = item.get("graph_dict", dict())

            if len(graph_dict) != 0:
                subdirectory_name = f'{start}___{end}' if session_id is None else session_id
                os.mkdir(f'./experiments/{experiment_id}/{subdirectory_name}')
                graph_dict_file = open(f'./experiments/{experiment_id}/{subdirectory_name}/graph.json', 'w')
                json.dump(graph_dict, graph_dict_file)
                graph_dict_file.close()

        logging.info("Thread for experiment for dataset %s: is done. Results are saved", experiment.dataset)

        # update in the database that the experiment is completed!
        experiment = Experiment.query.get(experiment_id)
        experiment.status = 'SUCCESS'
        experiment.last_modified_at = datetime.datetime.now()
        db.session.commit()


@app.route('/experiment/create', methods=['POST'])
def create_experiment():
    input_json = request.get_json(force=True)
    name = input_json['name']
    dataset = input_json['dataset']
    window_type = input_json['windowType']
    size = input_json['size']
    slide = input_json['slide']
    test_id = input_json.get("testId", None)
    include_last_event = input_json.get('includeLastEvent', False)
    # include_last_event = input_json.get(   Or['includeLastEvent']

    # check if there is already a same experiment like this one
    experiment_already_exists = db.session.query(Experiment).filter(
        Experiment.dataset == dataset, Experiment.window_type == window_type, Experiment.size == size,
        Experiment.slide == slide, Experiment.test_id == test_id,
        Experiment.include_last_event == include_last_event).first() is not None

    if experiment_already_exists:
        response = jsonify(
            {"error_message": "You have already created an experiment similar to this one, please use that "
                              "one in order to save time on experiment creation!"})
        response.headers.add('Access-Control-Allow-Origin', 'localhost:5001')
        return response

    new_experiment = Experiment(name, dataset, window_type, size, slide, test_id, include_last_event)

    db.session.add(new_experiment)
    db.session.commit()

    thread = threading.Thread(target=run_experiment, args=(new_experiment,))
    thread.start()

    response = experiment_schema.jsonify(new_experiment)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@app.route('/experiments', methods=['GET'])
def get_experiments():
    all_experiments = Experiment.query.all()
    result = experiments_schema.dump(all_experiments)
    response = jsonify(result)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@app.route("/experiments/delete", methods=['DELETE'])
def delete_experiment():
    id = request.args.get('experimentId', type=int)
    Experiment.query.filter_by(id=id).delete()
    db.session.commit()
    return jsonify("All good!")


@app.route('/experiment/windows', methods=['GET'])
def get_windows_list():
    experiment_id = request.args.get('experimentId', default=1, type=int)
    experiment = Experiment.query.get(experiment_id)
    window_type = experiment.window_type
    if not experiment.status.startswith('SUCCESS'):
        return jsonify({"error_message": "The experiment is not done yet, or it failed. Check logs!"})
    list_of_windows = []
    for folder in os.listdir(f'./experiments/{experiment_id}'):
        if folder != 'results.json':
            list_of_windows.append(folder)
    dataset_file = open(f'./experiments/{experiment_id}/results.json')
    dataset_content = "".join(dataset_file.readlines())
    dataset_file.close()
    return jsonify({
        "windows": list_of_windows,
        "type": "session" if window_type == "session" else "time",
        "dataset": dataset_content
    })


@app.route('/experiment/window', methods=['GET'])
def get_window_graph_data():
    # input_json = request.get_json(force=True)
    experiment_id = request.args.get('experimentId', default=1, type=int)
    window = request.args.get('window', default="", type=str)
    file = open(f'./experiments/{experiment_id}/{window}/graph.json')
    graph_data = file.read()
    file.close()
    graph_dict = json.loads(graph_data)
    nx_graph = create_networkx_graph(graph_dict)
    nt = nx2pyvis(nx_graph, Network("900px", "100%", bgcolor='#222222', font_color='white'), 15, 0)
    nt.repulsion(node_distance=500, spring_length=300)
    nt.show(f'./experiments/{experiment_id}/{window}/vis.html')
    file = open(f'./experiments/{experiment_id}/{window}/vis.html', 'r')
    content = "".join(file.readlines())
    return jsonify({
        "graph_dict": graph_data,
        "html_content": content
    })


if __name__ == '__main__':
    format = "%(asctime)s: %(message)s"
    app.run(threaded=True, debug=True)
