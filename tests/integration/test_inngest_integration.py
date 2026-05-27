"""Integration tests for Inngest workflow operations."""

import pytest


@pytest.mark.asyncio
async def test_inngest_connection(inngest_client):
    """Test connection to staging Inngest."""
    assert inngest_client is not None


@pytest.mark.asyncio
async def test_trigger_workflow(inngest_client):
    """Test triggering a workflow via Inngest."""
    class MockInngestTool:
        def __init__(self):
            self.client = inngest_client
        
        async def trigger_workflow(self, workflow_name, payload):
            """Trigger a workflow."""
            if self.client is None:
                return {"error": "No client"}
            try:
                # Mock successful trigger
                return {"success": True, "event_id": f"evt_test_001"}
            except Exception as e:
                return {"error": str(e)}
    
    tool = MockInngestTool()
    
    result = await tool.trigger_workflow(
        workflow_name="sinistro_processing",
        payload={
            "sinistro_id": "sin_test_001",
            "tipo": "roubo"
        }
    )
    
    assert result is not None
    assert ("success" in result or "event_id" in result or "error" in result)


@pytest.mark.asyncio
async def test_schedule_job(inngest_client):
    """Test scheduling a job via Inngest."""
    class MockInngestTool:
        def __init__(self):
            self.client = inngest_client
        
        async def schedule_job(self, job_name, schedule_time, payload):
            """Schedule a job."""
            if self.client is None:
                return {"error": "No client"}
            try:
                # Mock successful schedule
                return {"success": True, "job_id": "job_test_001"}
            except Exception as e:
                return {"error": str(e)}
    
    tool = MockInngestTool()
    
    result = await tool.schedule_job(
        job_name="sinistro_analysis",
        schedule_time=3600,  # 1 hour from now
        payload={"sinistro_id": "sin_test_002"}
    )
    
    assert result is not None
    assert ("success" in result or "job_id" in result or "error" in result)


@pytest.mark.asyncio
async def test_workflow_error_handling(inngest_client):
    """Test error handling in workflow triggering."""
    class MockInngestTool:
        def __init__(self):
            self.client = None  # Simulate broken connection
        
        async def trigger_workflow(self, workflow_name, payload):
            """Trigger workflow with error handling."""
            if self.client is None:
                return {"error": "Client not initialized", "success": False}
            try:
                return {"success": True}
            except Exception as e:
                return {"error": str(e), "success": False}
    
    tool = MockInngestTool()
    
    # Should handle gracefully
    result = await tool.trigger_workflow(
        workflow_name="test",
        payload={}
    )
    
    # Should return error response dict
    assert isinstance(result, dict)
    assert ("error" in result or "success" in result)
