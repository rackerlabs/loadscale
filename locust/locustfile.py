from locust import HttpLocust, TaskSet


def index(l):
    l.client.get("/")


class UserBehavior(TaskSet):
    tasks = {index: 2}

    def on_start(self):
        pass


class WebsiteUser(HttpLocust):
    task_set = UserBehavior
    host = "http://**.***.***.**" #put in your ip address here
    min_wait = 2000
    max_wait = 3000
