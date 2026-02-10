"""Performance tests using Locust."""

from locust import HttpUser, between, task


class DCISUser(HttpUser):
    """
    Simulated user for load testing.
    
    Target: 100 queries per minute sustained load.
    """
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """Called when a simulated user starts."""
        self.user_id = f"load_test_user_{self.environment.runner.user_count}"
    
    @task(5)
    def query_simple(self):
        """Submit simple query (most common operation)."""
        self.client.post("/api/v1/query", json={
            "query": "What is machine learning?",
            "user_id": self.user_id,
        })
    
    @task(3)
    def query_complex(self):
        """Submit complex query requiring reasoning."""
        self.client.post("/api/v1/query", json={
            "query": "Explain the differences between supervised and unsupervised learning, "
                    "with examples of algorithms for each category.",
            "user_id": self.user_id,
        })
    
    @task(2)
    def list_tasks(self):
        """List user tasks."""
        self.client.get(f"/api/v1/tasks?user_id={self.user_id}")
    
    @task(1)
    def start_debate(self):
        """Start a multi-agent debate."""
        self.client.post("/api/v1/debate/start", json={
            "topic": "Is AGI achievable in the next decade?",
            "participants": ["logician", "creative"],
            "rounds": 1,
        })
    
    @task(1)
    def get_memory(self):
        """Query episodic memory."""
        self.client.get("/api/v1/memory/recent?limit=10")
    
    @task(1)
    def health_check(self):
        """Health check endpoint."""
        self.client.get("/health")


class StressTestUser(HttpUser):
    """
    Aggressive user for stress testing.
    
    Finds system breaking point.
    """
    
    wait_time = between(0.1, 0.5)  # Very short wait time
    
    @task
    def rapid_fire_queries(self):
        """Submit queries rapidly."""
        self.client.post("/api/v1/query", json={
            "query": "Quick test query",
            "user_id": "stress_test",
        })


class MemoryLeakTestUser(HttpUser):
    """
    User for memory leak testing.
    
    Performs long-running operations repeatedly.
    """
    
    wait_time = between(0.5, 1)
    
    @task
    def create_and_delete_agents(self):
        """Create and delete agents repeatedly."""
        # Create agent
        response = self.client.post("/api/v1/agents", json={
            "name": "leak_test_agent",
            "type": "coder",
        })
        
        if response.status_code in [200, 201]:
            agent_id = response.json().get("id")
            # Delete agent
            self.client.delete(f"/api/v1/agents/{agent_id}")
