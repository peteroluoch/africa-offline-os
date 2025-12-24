"""
Module Contract Tests - PHASE 1 BATCH 2
Tests for the base Module contract that all business logic modules must implement.

Following TDD: These tests define the Module requirements.
"""
from __future__ import annotations

import asyncio
import pytest

from aos.core.module import Module
from aos.bus.events import Event
from aos.bus.dispatcher import EventDispatcher


class MockModule(Module):
    """Mock module for testing."""
    
    def __init__(self, name: str) -> None:
        self._name = name
        self._initialized = False
        self._events_handled: list[Event] = []
    
    @property
    def name(self) -> str:
        """Return module name."""
        return self._name
    
    async def initialize(self) -> None:
        """Initialize module."""
        self._initialized = True
    
    async def shutdown(self) -> None:
        """Shutdown module."""
        self._initialized = False
    
    async def handle_event(self, event: Event) -> None:
        """Handle event."""
        self._events_handled.append(event)


class TestModuleLifecycle:
    """Test module lifecycle management."""
    
    @pytest.mark.asyncio
    async def test_module_has_name(self) -> None:
        """Module must have a unique name."""
        module = MockModule("test.module")
        assert module.name == "test.module", "Module must have a name"
    
    @pytest.mark.asyncio
    async def test_module_initialize(self) -> None:
        """Module must implement initialize method."""
        module = MockModule("test.module")
        assert not module._initialized
        
        await module.initialize()
        assert module._initialized, "Module must be initialized after initialize()"
    
    @pytest.mark.asyncio
    async def test_module_shutdown(self) -> None:
        """Module must implement shutdown method."""
        module = MockModule("test.module")
        await module.initialize()
        assert module._initialized
        
        await module.shutdown()
        assert not module._initialized, "Module must be shutdown after shutdown()"
    
    @pytest.mark.asyncio
    async def test_module_lifecycle_flow(self) -> None:
        """Module must support full lifecycle: initialize -> use -> shutdown."""
        module = MockModule("test.module")
        
        # Initial state
        assert not module._initialized
        
        # Initialize
        await module.initialize()
        assert module._initialized
        
        # Use (handle event)
        event = Event(name="test.event", payload={"data": "test"})
        await module.handle_event(event)
        assert len(module._events_handled) == 1
        
        # Shutdown
        await module.shutdown()
        assert not module._initialized


class TestModuleEventHandling:
    """Test module event handling."""
    
    @pytest.mark.asyncio
    async def test_module_handles_events(self) -> None:
        """Module must implement handle_event method."""
        module = MockModule("test.module")
        await module.initialize()
        
        event = Event(name="test.event", payload={"data": "test"})
        await module.handle_event(event)
        
        assert len(module._events_handled) == 1
        assert module._events_handled[0].name == "test.event"
    
    @pytest.mark.asyncio
    async def test_module_handles_multiple_events(self) -> None:
        """Module must handle multiple events sequentially."""
        module = MockModule("test.module")
        await module.initialize()
        
        events = [
            Event(name="test.event1", payload={"id": 1}),
            Event(name="test.event2", payload={"id": 2}),
            Event(name="test.event3", payload={"id": 3}),
        ]
        
        for event in events:
            await module.handle_event(event)
        
        assert len(module._events_handled) == 3
        assert module._events_handled[0].name == "test.event1"
        assert module._events_handled[2].name == "test.event3"


class TestModuleContract:
    """Test that Module enforces its contract."""
    
    def test_module_is_abstract(self) -> None:
        """Module must be an abstract base class."""
        from abc import ABC
        
        assert issubclass(Module, ABC), "Module must be an ABC"
    
    def test_module_requires_name_property(self) -> None:
        """Module must require name property."""
        assert hasattr(Module, 'name'), "Module must define name property"
    
    def test_module_requires_initialize(self) -> None:
        """Module must require initialize() implementation."""
        assert hasattr(Module, 'initialize'), "Module must define initialize()"
    
    def test_module_requires_shutdown(self) -> None:
        """Module must require shutdown() implementation."""
        assert hasattr(Module, 'shutdown'), "Module must define shutdown()"
    
    def test_module_requires_handle_event(self) -> None:
        """Module must require handle_event() implementation."""
        assert hasattr(Module, 'handle_event'), "Module must define handle_event()"
    
    def test_cannot_instantiate_module_directly(self) -> None:
        """Cannot instantiate Module without implementing abstract methods."""
        with pytest.raises(TypeError):
            Module()  # type: ignore


class TestModuleErrorHandling:
    """Test module error handling."""
    
    @pytest.mark.asyncio
    async def test_module_handles_initialization_failure(self) -> None:
        """Module must handle initialization failures gracefully."""
        
        class FailingModule(Module):
            @property
            def name(self) -> str:
                return "failing.module"
            
            async def initialize(self) -> None:
                raise RuntimeError("Simulated initialization failure")
            
            async def shutdown(self) -> None:
                pass
            
            async def handle_event(self, event: Event) -> None:
                pass
        
        module = FailingModule()
        
        with pytest.raises(RuntimeError):
            await module.initialize()
    
    @pytest.mark.asyncio
    async def test_module_shutdown_is_idempotent(self) -> None:
        """Calling shutdown() multiple times must be safe."""
        module = MockModule("test.module")
        await module.initialize()
        
        # Shutdown multiple times
        await module.shutdown()
        await module.shutdown()
        await module.shutdown()
        
        assert not module._initialized, "Multiple shutdowns must be safe"
    
    @pytest.mark.asyncio
    async def test_module_handles_event_processing_error(self) -> None:
        """Module must handle event processing errors gracefully."""
        
        class ErrorModule(Module):
            @property
            def name(self) -> str:
                return "error.module"
            
            async def initialize(self) -> None:
                pass
            
            async def shutdown(self) -> None:
                pass
            
            async def handle_event(self, event: Event) -> None:
                raise ValueError("Simulated event processing error")
        
        module = ErrorModule()
        await module.initialize()
        
        event = Event(name="test.event", payload={})
        
        with pytest.raises(ValueError):
            await module.handle_event(event)


class TestModuleIntegration:
    """Test module integration with event system."""
    
    @pytest.mark.asyncio
    async def test_module_can_subscribe_to_events(self) -> None:
        """Module must be able to subscribe to events via dispatcher."""
        dispatcher = EventDispatcher()
        module = MockModule("test.module")
        await module.initialize()
        
        # Subscribe module to events
        async def event_handler(event: Event) -> None:
            await module.handle_event(event)
        
        dispatcher.subscribe("test.event", event_handler)
        
        # Emit event
        event = Event(name="test.event", payload={"data": "test"})
        await dispatcher.dispatch(event)
        
        # Wait for async task to complete
        await asyncio.sleep(0.1)
        
        # Verify module received event
        assert len(module._events_handled) == 1
        assert module._events_handled[0].name == "test.event"
