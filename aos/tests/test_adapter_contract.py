"""
Adapter Contract Tests - PHASE 1 BATCH 2
Tests for the base Adapter contract that all I/O adapters must implement.

Following TDD: These tests define the Adapter requirements.
"""
from __future__ import annotations

import pytest

from aos.core.adapter import Adapter


class MockAdapter(Adapter):
    """Mock adapter for testing."""
    
    def __init__(self) -> None:
        self.connected = False
        self.health_status = True
    
    async def connect(self) -> None:
        """Simulate connection."""
        self.connected = True
    
    async def disconnect(self) -> None:
        """Simulate disconnection."""
        self.connected = False
    
    async def health_check(self) -> bool:
        """Return health status."""
        return self.health_status and self.connected


class TestAdapterLifecycle:
    """Test adapter lifecycle management."""
    
    @pytest.mark.asyncio
    async def test_adapter_connect(self) -> None:
        """Adapter must implement connect method."""
        adapter = MockAdapter()
        assert not adapter.connected
        
        await adapter.connect()
        assert adapter.connected, "Adapter must be connected after connect()"
    
    @pytest.mark.asyncio
    async def test_adapter_disconnect(self) -> None:
        """Adapter must implement disconnect method."""
        adapter = MockAdapter()
        await adapter.connect()
        assert adapter.connected
        
        await adapter.disconnect()
        assert not adapter.connected, "Adapter must be disconnected after disconnect()"
    
    @pytest.mark.asyncio
    async def test_adapter_lifecycle_flow(self) -> None:
        """Adapter must support full lifecycle: connect -> use -> disconnect."""
        adapter = MockAdapter()
        
        # Initial state
        assert not adapter.connected
        
        # Connect
        await adapter.connect()
        assert adapter.connected
        
        # Use (health check)
        health = await adapter.health_check()
        assert health is True
        
        # Disconnect
        await adapter.disconnect()
        assert not adapter.connected


class TestAdapterHealthCheck:
    """Test adapter health monitoring."""
    
    @pytest.mark.asyncio
    async def test_health_check_when_connected(self) -> None:
        """Health check must return True when adapter is healthy and connected."""
        adapter = MockAdapter()
        await adapter.connect()
        
        health = await adapter.health_check()
        assert health is True, "Healthy connected adapter must report True"
    
    @pytest.mark.asyncio
    async def test_health_check_when_disconnected(self) -> None:
        """Health check must return False when adapter is disconnected."""
        adapter = MockAdapter()
        
        health = await adapter.health_check()
        assert health is False, "Disconnected adapter must report False"
    
    @pytest.mark.asyncio
    async def test_health_check_when_degraded(self) -> None:
        """Health check must return False when adapter is degraded."""
        adapter = MockAdapter()
        await adapter.connect()
        
        # Simulate degradation
        adapter.health_status = False
        
        health = await adapter.health_check()
        assert health is False, "Degraded adapter must report False"


class TestAdapterContract:
    """Test that Adapter enforces its contract."""
    
    def test_adapter_is_abstract(self) -> None:
        """Adapter must be an abstract base class."""
        from abc import ABC
        
        assert issubclass(Adapter, ABC), "Adapter must be an ABC"
    
    def test_adapter_requires_connect(self) -> None:
        """Adapter must require connect() implementation."""
        # This test verifies the contract exists
        assert hasattr(Adapter, 'connect'), "Adapter must define connect()"
    
    def test_adapter_requires_disconnect(self) -> None:
        """Adapter must require disconnect() implementation."""
        assert hasattr(Adapter, 'disconnect'), "Adapter must define disconnect()"
    
    def test_adapter_requires_health_check(self) -> None:
        """Adapter must require health_check() implementation."""
        assert hasattr(Adapter, 'health_check'), "Adapter must define health_check()"
    
    def test_cannot_instantiate_adapter_directly(self) -> None:
        """Cannot instantiate Adapter without implementing abstract methods."""
        with pytest.raises(TypeError):
            Adapter()  # type: ignore


class TestAdapterErrorHandling:
    """Test adapter error handling."""
    
    @pytest.mark.asyncio
    async def test_adapter_handles_connection_failure(self) -> None:
        """Adapter must handle connection failures gracefully."""
        
        class FailingAdapter(Adapter):
            async def connect(self) -> None:
                raise ConnectionError("Simulated connection failure")
            
            async def disconnect(self) -> None:
                pass
            
            async def health_check(self) -> bool:
                return False
        
        adapter = FailingAdapter()
        
        with pytest.raises(ConnectionError):
            await adapter.connect()
    
    @pytest.mark.asyncio
    async def test_adapter_disconnect_is_idempotent(self) -> None:
        """Calling disconnect() multiple times must be safe."""
        adapter = MockAdapter()
        await adapter.connect()
        
        # Disconnect multiple times
        await adapter.disconnect()
        await adapter.disconnect()
        await adapter.disconnect()
        
        assert not adapter.connected, "Multiple disconnects must be safe"
