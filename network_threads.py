#!/usr/bin/python3
# -*- coding: utf-8 -*-
from __future__ import division, print_function, unicode_literals, absolute_import
from threading import Thread
from PyQt5.QtCore import QObject, pyqtSignal
from datetime import datetime, timedelta
import json


class GoogleFitAPIRequestThread(Thread, QObject):
    data_loaded = pyqtSignal(list)

    def __init__(self, google_fit, *args):
        super(GoogleFitAPIRequestThread, self).__init__()
        QObject.__init__(self, *args)
        self.google_fit = google_fit


class SingleRequestThread(Thread):
    def __init__(self, google_fit, callback,
                 request_type='GET', url='https://www.googleapis.com/fitness/v1/users/me/dataSources'):
        super(SingleRequestThread, self).__init__()
        self.google_fit = google_fit
        self.callback = callback
        self.request_type = request_type
        self.url = url

    def run(self):
        response = self.google_fit.request(method=self.request_type, url=self.url)
        self.callback(response.json())
        super(SingleRequestThread, self).run()


class LoadDataSources(GoogleFitAPIRequestThread):
    def run(self):
        try:
            response = self.google_fit.get("https://www.googleapis.com/fitness/v1/users/me/dataSources")
            self.data_loaded.emit(response.json()['dataSource'])
        except ValueError:
            self.data_loaded.emit(["ValueError"])
        super(LoadDataSources, self).run()


class LoadWorkouts(GoogleFitAPIRequestThread):
    def __init__(self, google_fit, data_sources, *args, time_window=timedelta(days=7)):
        super(LoadWorkouts, self).__init__(google_fit, *args)
        self.data_sources = data_sources
        self.time_window = time_window
        self.load_threads = []
        self.raw_workouts = []

    def run(self):
        self.load_threads = []
        self.raw_workouts = []
        for source in self.data_sources:
            if source['dataType']['name'] == "com.google.activity.segment":
                load_thread = SingleRequestThread(
                    self.google_fit, self.load_callback, request_type='GET',
                    url="https://www.googleapis.com/fitness/v1/users/me/dataSources/{}/datasets/{}-{}".format(
                        source['dataStreamId'],
                        int((datetime.now() - self.time_window).timestamp() * 1000000000),
                        int(datetime.now().timestamp() * 1000000000)))
                self.load_threads.append(load_thread)
                load_thread.start()
        for thread in self.load_threads:
            thread.join()
        self.data_loaded.emit(self.raw_workouts)
        super(LoadWorkouts, self).run()

    def load_callback(self, json_data):
        self.raw_workouts.append(json_data)


class LoadCaloriesExpended(GoogleFitAPIRequestThread):
    def __init__(self, google_fit, data_sources, *args, time_window=timedelta(days=7)):
        super(LoadCaloriesExpended, self).__init__(google_fit, *args)
        self.data_sources = data_sources
        self.time_window = time_window
        self.load_threads = []
        self.raw_calories_expended = []

    def run(self):
        self.load_threads = []
        self.raw_calories_expended = []
        for source in self.data_sources:
            if source['dataType']['name'] == "com.google.calories.expended":
                load_thread = SingleRequestThread(
                    self.google_fit, self.load_callback, request_type='GET',
                    url="https://www.googleapis.com/fitness/v1/users/me/dataSources/" +
                    source['dataStreamId'] + "/datasets/" +
                    str(int((datetime.now() - self.time_window).timestamp() * 1000000000)) + "-" +
                    str(int(datetime.now().timestamp() * 1000000000)))
                self.load_threads.append(load_thread)
                load_thread.start()
        for thread in self.load_threads:
            thread.join()
        self.data_loaded.emit(self.raw_calories_expended)
        super(LoadCaloriesExpended, self).run()

    def load_callback(self, json_data):
        self.raw_calories_expended.append(json_data)


class LoadWeights(GoogleFitAPIRequestThread):
    def __init__(self, google_fit, data_sources, *args, time_window=timedelta(days=365)):
        super(LoadWeights, self).__init__(google_fit, *args)
        self.data_sources = data_sources
        self.time_window = time_window
        self.load_threads = []
        self.weights = []

    def run(self):
        self.load_threads = []
        self.weights = []
        for source in self.data_sources:
            if source['dataType']['name'] == "com.google.weight":
                load_thread = SingleRequestThread(
                    self.google_fit, self.load_callback, request_type='GET',
                    url="https://www.googleapis.com/fitness/v1/users/me/dataSources/" +
                    source['dataStreamId'] + "/datasets/" +
                    str(int((datetime.now() - self.time_window).timestamp() * 1000000000)) + "-" +
                    str(int(datetime.now().timestamp() * 1000000000)))
                self.load_threads.append(load_thread)
                load_thread.start()
        for thread in self.load_threads:
            thread.join()
        self.data_loaded.emit(self.weights)
        super(LoadWeights, self).run()

    def load_callback(self, json_data):
        for activity in json_data['point']:
            self.weights.append({
                "time": datetime.fromtimestamp(int(activity['startTimeNanos']) / 1000000000),
                "weight": activity['value'][0]['fpVal']
            })


class LoadNutrition(GoogleFitAPIRequestThread):
    def __init__(self, google_fit, data_sources, *args, time_window=timedelta(days=365)):
        super(LoadNutrition, self).__init__(google_fit, *args)
        self.data_sources = data_sources
        self.time_window = time_window
        self.load_threads = []
        self.raw_nutrition_data = []

    def run(self):
        self.load_threads = []
        self.raw_nutrition_data = []
        for source in self.data_sources:
            if source['dataType']['name'] == "com.google.nutrition":
                load_thread = SingleRequestThread(
                    self.google_fit, self.load_callback, request_type='GET',
                    url="https://www.googleapis.com/fitness/v1/users/me/dataSources/" +
                    source['dataStreamId'] + "/datasets/" +
                    str(int((datetime.now() - self.time_window).timestamp() * 1000000000)) + "-" +
                    str(int(datetime.now().timestamp() * 1000000000)))
                self.load_threads.append(load_thread)
                load_thread.start()
        for thread in self.load_threads:
            thread.join()
        self.data_loaded.emit(self.raw_nutrition_data)
        super(LoadNutrition, self).run()

    def load_callback(self, json_data):
        self.raw_nutrition_data.append(json_data)


class LoadHeight(GoogleFitAPIRequestThread):
    def __init__(self, google_fit, data_sources, *args):
        super(LoadHeight, self).__init__(google_fit, *args)
        self.data_sources = data_sources
        self.load_threads = []
        self.raw_height_data = []

    def run(self):
        self.load_threads = []
        self.raw_height_data = []
        for source in self.data_sources:
            if source['dataType']['name'] == "com.google.height":
                load_thread = SingleRequestThread(
                    self.google_fit, self.load_callback, request_type='GET',
                    url="https://www.googleapis.com/fitness/v1/users/me/dataSources/" +
                    source['dataStreamId'] + "/datasets/0-" +
                    str(int(datetime.now().timestamp() * 1000000000)))
                self.load_threads.append(load_thread)
                load_thread.start()
        for thread in self.load_threads:
            thread.join()
        self.data_loaded.emit(self.raw_height_data)
        super(LoadHeight, self).run()

    def load_callback(self, json_data):
        self.raw_height_data.append(json_data)


class LoadBirthday(GoogleFitAPIRequestThread):
    def __init__(self, google_fit, data_sources, *args):
        super(LoadBirthday, self).__init__(google_fit, *args)
        self.data_sources = data_sources

    def run(self):
        raw_height_data = []
        for source in self.data_sources:
            if source['dataType']['name'] == "net.pinae.fit.birthdate":
                response = self.google_fit.get(
                    "https://www.googleapis.com/fitness/v1/users/me/dataSources/" +
                    source['dataStreamId'] + "/datasets/0-" +
                    str(int(datetime.now().timestamp() * 1000000000)))
                raw_height_data.append(response.json())
        self.data_loaded.emit(raw_height_data)
        super(LoadBirthday, self).run()


class CreateDataSource(GoogleFitAPIRequestThread):
    def __init__(self, google_fit, data_source_name, *args, data_source_type="floatPoint"):
        super(CreateDataSource, self).__init__(google_fit, *args)
        self.data_source_name = data_source_name
        self.data_source_type = data_source_type

    def run(self):
        data = {
            "name": "fit.py-" + self.data_source_name.rsplit(".", 1)[1],
            "type": "raw",
            "dataType": {
                "name": self.data_source_name,
                "field": [
                    {
                        "name": self.data_source_name.rsplit(".", 1)[1],
                        "format": self.data_source_type
                    }
                ]
            },
            "application": {
                "name": "fit.py",
                "version": "1.0"
            },
        }
        with open("client_id.json", 'r') as f:
            developer_project_number = json.load(f)['installed']['client_id'].split('-', 1)[0]
        data["dataStreamId"] = ":".join([data["type"], data["dataType"]["name"], developer_project_number])
        response = self.google_fit.post(
            "https://www.googleapis.com/fitness/v1/users/me/dataSources", json=data)
        self.data_loaded.emit([response.json()])
        super(CreateDataSource, self).run()


class WriteBirthday(GoogleFitAPIRequestThread):
    def __init__(self, google_fit, age_data_source, *args):
        super(WriteBirthday, self).__init__(google_fit, *args)
        self.age_data_source = age_data_source

    def run(self):
        response = self.google_fit.patch(
            "https://www.googleapis.com/fitness/v1/users/me/dataSources/" +
            self.age_data_source['dataSourceId'] + "/datasets/" +
            self.age_data_source['minStartTimeNs'] + '-' +
            self.age_data_source['maxEndTimeNs'],
            json=self.age_data_source)
        self.data_loaded.emit([response.json()])
        super(WriteBirthday, self).run()


class WriteWorkout(GoogleFitAPIRequestThread):
    def __init__(self, google_fit, patched_workout_data_source, *args):
        super(WriteWorkout, self).__init__(google_fit, *args)
        self.patched_workout_data_source = patched_workout_data_source

    def run(self):
        response = self.google_fit.patch(
            "https://www.googleapis.com/fitness/v1/users/me/dataSources/" +
            self.patched_workout_data_source['dataSourceId'] + "/datasets/" +
            self.patched_workout_data_source['minStartTimeNs'] + '-' +
            self.patched_workout_data_source['maxEndTimeNs'],
            json=self.patched_workout_data_source)
        self.data_loaded.emit([response.json()])
        super(WriteWorkout, self).run()


class WriteCaloriesExpended(GoogleFitAPIRequestThread):
    def __init__(self, google_fit, patched_calories_expended_data_source, *args):
        super(WriteCaloriesExpended, self).__init__(google_fit, *args)
        self.patched_calories_expended_data_source = patched_calories_expended_data_source

    def run(self):
        response = self.google_fit.patch(
            "https://www.googleapis.com/fitness/v1/users/me/dataSources/" +
            self.patched_calories_expended_data_source['dataSourceId'] + "/datasets/" +
            self.patched_calories_expended_data_source['minStartTimeNs'] + '-' +
            self.patched_calories_expended_data_source['maxEndTimeNs'],
            json=self.patched_calories_expended_data_source)
        self.data_loaded.emit([response.json()])
        super(WriteCaloriesExpended, self).run()
