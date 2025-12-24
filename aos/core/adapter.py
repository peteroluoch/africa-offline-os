"""
Adapter Base Contract - Foundation for all I/O adapters.
Defines the interface that all external I/O adapters must implement.
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class Adapter(ABC):
    """
    Base adapter for external I/O operations.
    
    All adapters (DB, Network, File, etc.) must inherit from this class
    and implement the required methods.
    
    Example:
        class DatabaseAdapter(Adapter):
            async def connect(self) -> None:
                self.conn = await create_connection()
            
            async def disconnect(self) -> None:
                await self.conn.close()
            
            async def health_check(self) -> bool:
                return self.conn.is_alive()
    """
    
    @abstractmethod
    async def connect(self) -> None:
        """
        Establish connection to external resource.
        
        This method should be idempotent - calling it multiple times
        should not create multiple connections.
        
        Raises:
            ConnectionError: If connection fails
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """
        Gracefully close connection to external resource.
        
        This method must be idempotent - calling it multiple times
        should be safe and not raise errors.
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Verify adapter is operational.
        
        Returns:
            True if adapter is healthy and connected, False otherwise
        """
        pass
