from locust import HttpUser, LoadTestShape, between, task


class StressTest(HttpUser):
    host = "http://localhost:8000"
    # Wait between 0.2 and 1 second between each request
    wait_time = between(0.2, 1.0)

    @task(5)
    def test_stress(self) -> None:
        # Simple call to the baseline endpoint
        self.client.get("/hello")


class StepStressShape(LoadTestShape):
    """
    Stress test shape that ramps up users by 50 every 10 seconds.

    0s:   50 users
    10s:  100 users
    20s:  150 users
    ...

    This continues until `max_users` is reached.
    """

    # how many users to add each step
    step_users = 500
    # duration of each step in seconds
    step_time = 10
    # stop increasing after this many users
    max_users = 5000

    def tick(self):
        run_time = self.get_run_time()

        # Which step are we in? 0, 1, 2, ...
        step_index = int(run_time // self.step_time)
        target_users = (step_index + 1) * self.step_users

        if target_users > self.max_users:
            # Returning None tells Locust to stop the test
            return None

        # Constant spawn rate; Locust will ramp up towards target_users
        spawn_rate = self.step_users
        return target_users, spawn_rate