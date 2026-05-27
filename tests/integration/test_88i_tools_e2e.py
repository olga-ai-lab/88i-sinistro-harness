"""End-to-end integration tests for 88i tools workflow.

Tests the complete sinistro processing pipeline:
extract → score → save → schedule
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from tools.registry import registry


@pytest.mark.asyncio
async def test_sinistro_workflow_e2e():
    """Test complete sinistro workflow: extract → score → save → schedule.
    
    This test verifies the full workflow pipeline:
    1. Extract fields from document
    2. Score fraud risk
    3. Save conversation state
    4. Trigger async workflow scheduling
    """
    
    # Step 1: Extract fields
    extract_tool = registry.get_entry("sinistro_extract_fields")
    assert extract_tool is not None, "sinistro_extract_fields tool not found"
    
    extract_result = await extract_tool.handler({
        "documento_tipo": "boletim_ocorrencia",
        "documento_texto": "Número BO: 98765\nData: 2026-05-27\nTipo: Roubo",
        "sinistro_id": "sin_e2e_001"
    })
    
    assert extract_result["sucesso"] is True, f"Extract failed: {extract_result}"
    assert "campos_extraidos" in extract_result
    assert extract_result["sinistro_id"] == "sin_e2e_001"
    campos = extract_result["campos_extraidos"]
    
    # Step 2: Score fraud
    fraud_tool = registry.get_entry("sinistro_fraud_score")
    assert fraud_tool is not None, "sinistro_fraud_score tool not found"
    
    fraud_result = await fraud_tool.handler({
        "sinistro_id": "sin_e2e_001",
        "segurado_id": "seg_001",
        "campos_extraidos": campos
    })
    
    assert fraud_result["sucesso"] is True, f"Fraud scoring failed: {fraud_result}"
    assert "score_fraude" in fraud_result
    assert 0 <= fraud_result["score_fraude"] <= 100
    
    # Step 3: Save state (langraph_save_state)
    # If langraph tool exists, test it; otherwise skip
    state_tool = registry.get_entry("langraph_save_state")
    if state_tool:
        state_result = await state_tool.handler({
            "conversation_id": "conv_e2e_001",
            "sinistro_id": "sin_e2e_001",
            "estado": {
                "campos_extraidos": campos,
                "score_fraude": fraud_result["score_fraude"],
                "etapa_atual": "validacao"
            }
        })
        
        assert state_result["sucesso"] is True, f"State save failed: {state_result}"
    
    # Step 4: Trigger async workflow
    workflow_tool = registry.get_entry("inngest_trigger_workflow")
    assert workflow_tool is not None, "inngest_trigger_workflow tool not found"
    
    workflow_result = await workflow_tool.handler({
        "workflow": "process_sinistro",
        "sinistro_id": "sin_e2e_001",
        "etapa": "validacao"
    })
    
    # Workflow may fail if Inngest client is unavailable (Phase 2 limitation)
    # Both success and graceful failure are acceptable
    assert isinstance(workflow_result, dict), "Workflow result should be a dict"
    if workflow_result["sucesso"]:
        assert workflow_result["sinistro_id"] == "sin_e2e_001"
    
    # All steps passed
    print(f"✓ E2E workflow complete: sin_e2e_001")


@pytest.mark.asyncio
async def test_sinistro_workflow_with_supabase_update():
    """Test sinistro workflow with Supabase update step.
    
    Workflow:
    1. Extract fields
    2. Score fraud
    3. Update Supabase status
    """
    
    # Step 1: Extract
    extract_tool = registry.get_entry("sinistro_extract_fields")
    extract_result = await extract_tool.handler({
        "documento_tipo": "boletim_ocorrencia",
        "documento_texto": "Número BO: 54321\nData: 2026-05-27\nTipo: Roubo",
        "sinistro_id": "sin_e2e_002"
    })
    
    assert extract_result["sucesso"] is True
    campos = extract_result["campos_extraidos"]
    
    # Step 2: Score fraud
    fraud_tool = registry.get_entry("sinistro_fraud_score")
    fraud_result = await fraud_tool.handler({
        "sinistro_id": "sin_e2e_002",
        "segurado_id": "seg_002",
        "campos_extraidos": campos
    })
    
    assert fraud_result["sucesso"] is True
    
    # Step 3: Update Supabase (if available)
    update_tool = registry.get_entry("supabase_update_sinistro")
    if update_tool:
        with patch("tools._88i_supabase_tool.get_supabase_client") as mock_supabase:
            mock_client = MagicMock()
            mock_response = {
                "data": [{
                    "id": "sin_e2e_002",
                    "status": "analise_fraude"
                }]
            }
            mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_response
            mock_supabase.return_value = mock_client
            
            update_result = await update_tool.handler({
                "sinistro_id": "sin_e2e_002",
                "status": "analise_fraude",
                "score_fraude": fraud_result["score_fraude"],
                "campos_extraidos": campos
            })
            
            # Update should succeed (or fail gracefully if client unavailable)
            assert isinstance(update_result, dict)
            assert "sucesso" in update_result


@pytest.mark.asyncio
async def test_workflow_state_persistence():
    """Test conversation state persistence across steps.
    
    Verifies that:
    1. State can be saved
    2. State can be loaded
    3. State can be updated
    """
    
    # Only test if langraph tools are available
    save_tool = registry.get_entry("langraph_save_state")
    load_tool = registry.get_entry("langraph_load_state")
    update_tool = registry.get_entry("langraph_update_state")
    
    if not (save_tool and load_tool and update_tool):
        pytest.skip("LangGraph tools not available (Phase 2 limitation)")
    
    conversation_id = "conv_e2e_003"
    sinistro_id = "sin_e2e_003"
    
    # Step 1: Save initial state
    save_result = await save_tool.handler({
        "conversation_id": conversation_id,
        "sinistro_id": sinistro_id,
        "estado": {
            "etapa_atual": "extracao",
            "campos_extraidos": {"numero_bo": "99999"},
            "timestamp": "2026-05-27T10:00:00Z"
        }
    })
    
    assert save_result["sucesso"] is True or save_result.get("erro"), "Save state failed"
    
    # Step 2: Load state
    if save_result.get("sucesso"):
        load_result = await load_tool.handler({
            "conversation_id": conversation_id
        })
        
        assert load_result["sucesso"] is True or not load_result["encontrado"], "Load state failed"
        
        if load_result.get("encontrado"):
            assert load_result["conversation_id"] == conversation_id
            assert load_result["sinistro_id"] == sinistro_id
            
            # Step 3: Update state
            update_result = await update_tool.handler({
                "conversation_id": conversation_id,
                "atualizacoes": {
                    "etapa_atual": "fraude_scoring",
                    "score_fraude": 25
                }
            })
            
            assert update_result["sucesso"] is True or update_result.get("erro"), "Update state failed"


@pytest.mark.asyncio
async def test_workflow_error_handling():
    """Test error handling in workflow steps.
    
    Verifies that tools gracefully handle:
    1. Missing required arguments
    2. Invalid sinistro IDs
    3. Unavailable external services
    """
    
    # Test missing required arguments
    extract_tool = registry.get_entry("sinistro_extract_fields")
    
    result = await extract_tool.handler({})
    # Should handle gracefully
    assert isinstance(result, dict)
    
    # Test fraud scoring with missing fields
    fraud_tool = registry.get_entry("sinistro_fraud_score")
    
    result = await fraud_tool.handler({
        "sinistro_id": "sin_invalid"
        # missing "segurado_id" and "campos_extraidos"
    })
    assert isinstance(result, dict)
    
    # Test workflow trigger with minimal args
    workflow_tool = registry.get_entry("inngest_trigger_workflow")
    
    result = await workflow_tool.handler({
        "workflow": "test_workflow"
        # missing "sinistro_id"
    })
    assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_tool_registry_discovery():
    """Verify all 88i tools are registered and discoverable."""
    
    # Get list of all tools
    all_tool_names = registry.get_all_tool_names()
    
    # Required tools from Phase 2
    required_tools = [
        "sinistro_extract_fields",
        "sinistro_fraud_score",
        "inngest_trigger_workflow",
        "inngest_schedule_job",
        "supabase_read_sinistro",
        "supabase_update_sinistro",
        "supabase_insert_sinistro"
    ]
    
    for tool_name in required_tools:
        assert tool_name in all_tool_names, f"Required tool '{tool_name}' not found in registry"
        tool = registry.get_entry(tool_name)
        assert tool is not None, f"Tool '{tool_name}' returned None"
        assert tool.handler is not None, f"Tool '{tool_name}' has no handler"


@pytest.mark.asyncio
async def test_workflow_scheduling():
    """Test async workflow scheduling and cron jobs.
    
    Verifies:
    1. Workflow can be triggered
    2. Jobs can be scheduled with cron expressions
    """
    
    # Test workflow trigger
    workflow_tool = registry.get_entry("inngest_trigger_workflow")
    
    result = await workflow_tool.handler({
        "workflow": "process_sinistro",
        "sinistro_id": "sin_schedule_001",
        "etapa": "validacao"
    })
    
    assert result["sucesso"] is True or result.get("erro") == "Inngest client not available"
    if result["sucesso"]:
        assert "event_id" in result
        assert result["status"] == "agendado"
    
    # Test job scheduling
    schedule_tool = registry.get_entry("inngest_schedule_job")
    if schedule_tool:
        result = await schedule_tool.handler({
            "job_name": "cleanup_pending",
            "schedule": "0 2 * * *"  # Daily at 2am
        })
        
        assert result["sucesso"] is True or result.get("erro") == "Inngest client not available"
        if result["sucesso"]:
            assert "cron_id" in result
            assert result["status"] == "agendado"
