"""Locust load testing configuration."""

from locust import HttpUser, task, between
import json


class SinistroAgentLoadTest(HttpUser):
    """Load testing scenarios for sinistro agent."""
    
    wait_time = between(1, 3)
    
    @task
    def extract_sinistro(self):
        """Load test: Extract fields from document."""
        self.client.post(
            "/tools/sinistro_extract_fields",
            json={
                "documento": "BO: 12345\nValor: R$ 25000"
            }
        )
    
    @task
    def score_sinistro(self):
        """Load test: Score fraud risk."""
        self.client.post(
            "/tools/sinistro_fraud_score",
            json={
                "sinistro_fields": {
                    "sinistro_tipo": "roubo",
                    "veiculo_tipo": "carro",
                    "valor": 25000
                }
            }
        )
    
    @task
    def save_state(self):
        """Load test: Save conversation state."""
        self.client.post(
            "/tools/langraph_save_state",
            json={
                "conversation_id": "conv_load_test",
                "estado": {"etapa": "validacao"}
            }
        )
    
    @task
    def inject_context(self):
        """Load test: Inject context into prompt."""
        self.client.post(
            "/tools/context_inject",
            json={
                "prompt": "Analise este sinistro",
                "context_type": "insurance",
                "sinistro_tipo": "roubo"
            }
        )


if __name__ == "__main__":
    print("Run with: locust -f tests/load/locustfile.py --host=http://localhost:8000")
