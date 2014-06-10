from locust import HttpLocust, TaskSet
import settings


def index(l):
    l.client.get("/")

class UserBehavior(TaskSet):
    tasks = {index:2}

    def on_start(self):
        pass

class WebsiteUser(HttpLocust):
    task_set = UserBehavior
    host = settings.LOAD_BAL_IP_ADDR
    min_wait=2000
    max_wait=3000

